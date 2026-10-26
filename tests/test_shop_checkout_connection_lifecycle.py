"""Prevent checkout descriptor exhaustion without relying on garbage collection."""
from contextlib import closing
from types import SimpleNamespace
import hashlib
import sqlite3
import pytest
from core.shopping.order_core import guest_checkout
from core.shopping.guest_operator import GuestOperatorAdapter
from test_shop_guest_checkout import draft

@pytest.fixture
def tracked(monkeypatch):
    original=sqlite3.connect
    opened=[]
    class Connection(sqlite3.Connection):
        closed=False
        fail_after_insert=False
        fail_select=False
        def close(self):
            super().close()
            self.closed=True
        def execute(self, sql, *args, **kwargs):
            if self.fail_select and sql.startswith("SELECT"):
                raise sqlite3.OperationalError("synthetic read failure")
            result=super().execute(sql,*args,**kwargs)
            if self.fail_after_insert and sql.startswith("INSERT"):
                raise sqlite3.OperationalError("synthetic transaction failure")
            return result
    def connect(*args,**kwargs):
        connection=original(*args,**kwargs,factory=Connection)
        opened.append(connection)  # Retain references so GC cannot mask the leak.
        return connection
    monkeypatch.setattr(sqlite3,"connect",connect)
    return opened,Connection,original

def setup_store(tmp_path):
    store=guest_checkout.PrivateCheckoutStore(tmp_path/"checkout.sqlite3")
    value=draft(store)
    store.confirm(value["draft_id"],"customer","session")
    row={"operation_key":value["operation_key"],"provider_order_id":15,
         "state":"CONFIRMED","reference":"a"*24}
    operator=GuestOperatorAdapter(ledger=SimpleNamespace(operator_orders=lambda:[row]),store=store)
    return store,value,operator

def test_repeated_checkout_reads_close_every_connection(tmp_path,tracked):
    opened,_,_=tracked
    store,value,_=setup_store(tmp_path)
    tag=hashlib.sha256(("aicc-order:"+value["operation_key"]).encode()).hexdigest()
    for _ in range(100):
        assert store.get(value["draft_id"],"customer","session")["state"]=="CONFIRMED"
        assert store.operation(value["operation_key"],"customer","session")["state"]=="CONFIRMED"
        assert store.by_customer_operation(value["operation_key"],"customer")["state"]=="CONFIRMED"
        assert store.by_provider_tag(tag)["state"]=="CONFIRMED"
    with pytest.raises(ValueError):store.get(value["draft_id"],"other","session")
    assert opened and all(c.closed for c in opened)

def test_repeated_operator_poll_reads_close_every_connection(tmp_path,tracked):
    opened,_,_=tracked
    _,value,operator=setup_store(tmp_path)
    for _ in range(100):
        assert operator.rows()[0]["operation_key"]==value["operation_key"]
    assert all(c.closed for c in opened)

@pytest.mark.parametrize("target",["checkout","operator"])
def test_read_failure_closes_connections(tmp_path,tracked,target):
    opened,connection,_=tracked
    store,value,operator=setup_store(tmp_path)
    connection.fail_select=True
    with pytest.raises(sqlite3.OperationalError,match="synthetic"):
        if target=="checkout":store.get(value["draft_id"],"customer","session")
        else:operator.rows()
    assert all(c.closed for c in opened)

def test_failed_write_rolls_back_and_closes_connection(tmp_path,tracked):
    opened,connection,original=tracked
    store,_,_=setup_store(tmp_path)
    connection.fail_after_insert=True
    with pytest.raises(sqlite3.OperationalError,match="synthetic"):
        draft(store)
    with closing(original(store.path)) as check:
        assert check.execute("SELECT COUNT(*) FROM checkout_delivery").fetchone()==(1,)
    assert all(c.closed for c in opened)


def test_idle_inquiry_polling_closes_every_connection(tmp_path,tracked):
    from ops.macos.shopping.dev_inquiry_queue import DevInquiryQueue
    opened,_,_=tracked
    queue=DevInquiryQueue(tmp_path/"inquiries.sqlite3",SimpleNamespace(
        send_message=lambda *_:pytest.fail("idle queue must not send")))
    for _ in range(100):
        assert queue.dispatch_one() is None
    assert opened and all(c.closed for c in opened)


def test_inquiry_unknown_delivery_is_not_retried_and_connections_close(tmp_path,tracked):
    from ops.macos.shopping.dev_inquiry_queue import DevInquiryQueue
    opened,_,_=tracked
    calls=[]
    def send(text):
        calls.append(text)
        raise TimeoutError("synthetic ambiguous delivery")
    queue=DevInquiryQueue(tmp_path/"inquiries.sqlite3",SimpleNamespace(send_message=send))
    receipt=queue.submit("product-1","재고 문의")
    queue.dispatch_one()
    queue.dispatch_one()
    assert len(calls)==1
    assert queue.admin_rows()[0]["delivery"]=="UNKNOWN_OUTCOME"
    assert queue.status(receipt["inquiry_token"])["state"]=="PENDING"
    assert all(c.closed for c in opened)


def test_inquiry_answer_and_export_close_connections(tmp_path,tracked):
    from ops.macos.shopping.dev_inquiry_queue import DevInquiryQueue
    opened,_,_=tracked
    sent=[]
    queue=DevInquiryQueue(tmp_path/"inquiries.sqlite3",SimpleNamespace(
        send_message=lambda text:sent.append(text) or 123))
    receipt=queue.submit("product-1","색상 문의")
    queue.dispatch_one()
    assert len(sent)==1 and queue.admin_rows()[0]["delivery"]=="SENT"
    queue.command("문의 #"+receipt["inquiry_id"]+" 답변 베이지 색상입니다",1)
    assert queue.lookup("product-1","색상 문의")=="베이지 색상입니다"
    assert queue.history_answer(receipt["inquiry_token"])=="베이지 색상입니다"
    assert queue.export(tmp_path/"faq.jsonl")==1
    assert all(c.closed for c in opened)


@pytest.mark.parametrize("ttl",[0,1800])
def test_environment_router_closes_connections_after_dispatch_and_replay(tmp_path,tracked,ttl):
    from core.shopping.operator_environment import DurableOperatorEnvironmentRouter
    opened,_,_=tracked
    calls=[]
    def handle(text,update):calls.append((text,update));return "done"
    router=DurableOperatorEnvironmentRouter(database_path=tmp_path/"router.sqlite3",
        dev=handle,prod=handle,default="PROD",chat_id=1,user_ids={2},conversation_seconds=ttl)
    first=router.dispatch("DEV status",chat_id=1,user_id=2,update_id=3)
    assert router.dispatch("DEV status",chat_id=1,user_id=2,update_id=3)==first
    assert calls==[("status",3)]
    with pytest.raises(ValueError,match="UPDATE_CONFLICT"):
        router.dispatch("PROD changed",chat_id=1,user_id=2,update_id=3)
    assert len(calls)==1 and all(c.closed for c in opened)


def test_environment_router_handler_failure_keeps_claim_and_closes_connections(tmp_path,tracked):
    from core.shopping.operator_environment import DurableOperatorEnvironmentRouter
    opened,_,_=tracked
    calls=[]
    def handle(text,update):calls.append(update);raise TimeoutError("ambiguous")
    router=DurableOperatorEnvironmentRouter(database_path=tmp_path/"router.sqlite3",
        dev=handle,prod=handle,default="PROD",chat_id=1,user_ids={2})
    with pytest.raises(TimeoutError):router.dispatch("status",chat_id=1,user_id=2,update_id=3)
    with pytest.raises(ValueError,match="UPDATE_REQUIRES_INSPECTION"):
        router.dispatch("status",chat_id=1,user_id=2,update_id=3)
    assert calls==[3] and all(c.closed for c in opened)
