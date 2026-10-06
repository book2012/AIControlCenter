import sqlite3
import pytest
from test_shop_aftersales_dev import fixture,CUSTOMER,ORDER
from test_shop_customer_order_lookup import sms_fixture,PHONE
from ops.macos.shopping.dev_order_operator import DevOperatorAdapter
from ops.macos.shopping.dev_customer_messages import GREETING,chunks
from ops.macos.shopping.dev_order_sms import DevOrderSMS

def adapter(store,draft):
    value=DevOperatorAdapter(ledger=store.ledger,store=store.checkout,aftersales=store)
    value.rows=lambda:[{"provider_order_id":ORDER,"phone":"01012345678","state":"CONFIRMED","reference":"a"*24,"quote":draft["body"]["quote"],"delivery":draft["body"]["shipping"]}]
    return value

def test_paid_shipping_delivery_state_machine_and_durable_receipt(tmp_path):
    clock=[1000.0];store,draft=fixture(tmp_path,clock);op=adapter(store,draft)
    assert op.display_state(op.rows()[0])=="AWAITING_DEPOSIT"
    assert "입금확인 후" in op.resolve("배송 #15 CJ대한통운 1234567890",1)[2]
    assert store._fulfillment(ORDER)["state"]=="NOT_SHIPPED"
    assert "배송준비" in op.resolve("01012345678 입금 확인",2)[2]
    assert op.display_state(op.rows()[0])=="READY_TO_SHIP"
    assert "배송중" in op.resolve("01012345678 배송 CJ대한통운 1234567890",3)[2]
    assert op.display_state(op.rows()[0])=="SHIPPED"
    assert "CJ대한통운" in op.resolve("01012345678 주문상태",4)[2]
    assert "배송완료" in op.resolve("배송 완료 #15",5)[2]
    assert "배송완료" in op.resolve("입금확인 #15",8)[2]
    delivered=store._fulfillment(ORDER)["delivered"]
    clock[0]+=20
    assert "배송완료" in op.resolve("배송 #15 CJ대한통운 1234567890",6)[2]
    assert store._fulfillment(ORDER)["delivered"]==delivered and op.display_state(op.rows()[0])=="COMPLETED"
    assert "기존 배송정보" in op.resolve("배송 #15 한진택배 9999999999",7)[2]
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT count(*) FROM shipping_notices").fetchone()[0]==1
        assert c.execute("SELECT tracking FROM shipping_notices").fetchone()[0]=="1234567890"

def test_all_orders_and_phone_query_are_complete_and_phone_mutation_is_unambiguous(tmp_path):
    store,draft=fixture(tmp_path,[1000.0]);op=adapter(store,draft);base=op.rows()[0]
    op.rows=lambda:[{**base,"provider_order_id":i} for i in range(1,27)]+[{**base,"provider_order_id":90,"phone":"01099999999"}]
    reply=op.resolve("주문내역",1)[2]
    assert "전체 주문 27건" in reply and "#26" in reply and "#90" in reply
    mine=op.resolve("01012345678",2)[2]
    assert "주문 26건" in mine and "#26" in mine and "#90" not in mine
    assert "주문번호를 함께" in op.resolve("01012345678 입금확인",3)[2]
    assert store.payment(ORDER)["state"]=="AWAITING_DEPOSIT"
    assert "해당 고객 주문" in op.resolve("01099999999 배송완료 #15",4)[2]

def test_shipping_sms_is_greeted_bound_to_phone_and_sent_once(tmp_path):
    sent=[];sms,store,rows=sms_fixture(tmp_path,lambda cfg,to,text:sent.append((to,text)))
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    assert sms.dispatch_one()=="ACCEPTED" and len(sent)==1
    assert sent[0][0]==PHONE and sent[0][1].startswith(GREETING+"\n")
    assert "배송이 시작" in sent[0][1] and "운송장번호: 1234567890" in sent[0][1]
    store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    assert sms.dispatch_one()=="IDLE" and len(sent)==1
    with sqlite3.connect(store.path) as c:assert c.execute("SELECT state FROM shipping_notices").fetchone()[0]=="ACCEPTED"

def test_unknown_shipping_send_never_retries_after_restart(tmp_path):
    def fail(*args):raise TimeoutError()
    sms,store,rows=sms_fixture(tmp_path,fail);store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    assert sms.dispatch_one()=="UNKNOWN"
    restarted=DevOrderSMS(sms.path,aftersales=store,phone_cfg=sms.phone_cfg,config_path=sms.config_path,transport=lambda *a:pytest.fail("duplicate SMS"))
    assert restarted.dispatch_one()=="IDLE"
    with sqlite3.connect(store.path) as c:assert c.execute("SELECT state FROM shipping_notices").fetchone()[0]=="UNKNOWN"

def test_completed_before_sms_configuration_suppresses_obsolete_start_notice(tmp_path):
    sent=[];sms,store,rows=sms_fixture(tmp_path,lambda *a:sent.append(a))
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890");store.mark_delivered(ORDER)
    assert sms.dispatch_one()=="IDLE" and not sent
    with sqlite3.connect(store.path) as c:assert c.execute("SELECT state FROM shipping_notices").fetchone()[0]=="SUPPRESSED"

def test_telegram_long_lists_are_split_with_greeting_and_no_truncation():
    body="😀 주문내역\n"*1800
    parts=list(chunks(body))
    assert len(parts)>1 and all(p.startswith(GREETING+"\n") and len(p.encode("utf-16-le"))//2<=4096 for p in parts)
    assert "".join(p[len(GREETING)+1:] for p in parts)==body
    assert list(chunks(GREETING+"\n짧은 메시지"))==[GREETING+"\n짧은 메시지"]

def test_shipping_requires_tracking_and_unconfirmed_order_cannot_be_paid(tmp_path):
    store,draft=fixture(tmp_path,[1000.0]);op=adapter(store,draft)
    assert "운송장번호" in op.resolve("배송 #15",1)[2]
    assert "운송장번호" in op.resolve("01012345678 배송",2)[2]
    store.ledger.operator_orders=lambda:[]
    with pytest.raises(ValueError):store.confirm_payment(ORDER)
    assert store.payment(ORDER)["state"]=="AWAITING_DEPOSIT"
