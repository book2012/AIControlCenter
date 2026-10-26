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
