import json,os,sqlite3
import pytest
from test_shop_customer_order_lookup import sms_fixture,PHONE
from test_shop_aftersales_dev import ORDER
from ops.macos.shopping.dev_solapi_sms import SolapiSMS,payload
from test_shop_solapi_sms import CFG

def configured(tmp_path,sent,purposes=None):
    sms,store,rows=sms_fixture(tmp_path,lambda cfg,to,text:sent.append((to,text)))
    path=tmp_path/"solapi.private.json"
    path.write_text(json.dumps({**CFG,"provider":"solapi","enabled":True,
        "purposes":purposes or {"order_confirmation":True,"shipping_started":True}}))
    os.chmod(path,0o600);sms.solapi_config_path=path
    return sms,store,rows

def fresh_order(sms):
    # This fixture has one already-created synthetic order; emulate its arrival after arming.
    with sqlite3.connect(sms.path) as c:c.execute("DELETE FROM notices WHERE order_id=?",(ORDER,))

def test_solapi_activation_is_explicit_and_historical_pending_is_not_backfilled(tmp_path):
    sent=[];sms,store,rows=configured(tmp_path,sent)
    assert sms.dispatch_one()=="CONFIGURATION_REQUIRED" and not sent
    with sqlite3.connect(sms.path) as c:c.execute("UPDATE notices SET state='PENDING'")
    sms.arm_solapi_from_now()
    assert sms.state(ORDER)=="HISTORICAL" and sms.dispatch_one()=="IDLE" and not sent
    fresh_order(sms)
    assert sms.dispatch_one()=="ACCEPTED"
    assert len(sent)==1 and sent[0][0]==PHONE and "입금계좌" in sent[0][1]
    assert payload(CFG["sender_number"],PHONE,sent[0][1],"order:15")["type"]=="LMS"
    assert sms.dispatch_one()=="IDLE" and len(sent)==1

def test_paid_confirmation_never_requests_another_deposit(tmp_path):
    sent=[];sms,store,rows=configured(tmp_path,sent);sms.arm_solapi_from_now();fresh_order(sms)
    store.confirm_payment(ORDER)
    assert sms.dispatch_one()=="ACCEPTED"
    assert "입금 확인 완료" in sent[0][1] and "입금계좌" not in sent[0][1]

def test_shipping_only_purpose_and_final_delivery_status_do_not_resend(tmp_path,monkeypatch):
    sent=[];sms,store,rows=configured(tmp_path,sent,{"order_confirmation":False,"shipping_started":True})
    sms.arm_solapi_from_now();store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    sms.transport=lambda cfg,to,text:(sent.append((to,text)) or {"provider":"SOLAPI","state":"ACCEPTED","group_id":"GTEST1234567890"})
    assert sms.dispatch_one()=="ACCEPTED" and len(sent)==1 and "운송장번호" in sent[0][1]
    with sqlite3.connect(sms.path) as c:c.execute("UPDATE provider_receipts SET next_check=0")
    monkeypatch.setattr(SolapiSMS,"status",lambda *_:{"state":"DELIVERED","status_code":"4000"})
    assert sms.dispatch_one()=="DELIVERED" and len(sent)==1
    assert sms.dispatch_one()=="IDLE" and len(sent)==1
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT state FROM shipping_notices").fetchone()[0]=="DELIVERED"

def test_non_test_recipient_is_suppressed_without_network(tmp_path):
    sent=[];sms,store,rows=configured(tmp_path,sent);sms.arm_solapi_from_now();fresh_order(sms)
    store.lookup=lambda *_:(_ for _ in ()).throw(ValueError("PHONE_MISMATCH"))
    assert sms.dispatch_one()=="IDLE" and not sent
    assert sms.state(ORDER)=="RECIPIENT_NOT_ALLOWED"

def test_long_order_is_compacted_with_bank_and_authenticated_lookup_link(tmp_path):
    sent=[];sms,store,rows=configured(tmp_path,sent);sms.arm_solapi_from_now();fresh_order(sms)
    original=store.lookup
    store.lookup=lambda *a:{**original(*a),"items":[{"name":"긴 상품명"*20,"option":"L","quantity":1} for _ in range(40)]}
    assert sms.dispatch_one()=="ACCEPTED"
    text=sent[0][1]
    assert "상품 40종" in text and "입금계좌" in text and "my-orders" in text and len(text.encode("euc-kr"))<=2000

def test_ambiguous_provider_send_is_not_retried_after_restart(tmp_path):
    sent=[];sms,store,rows=configured(tmp_path,sent);sms.arm_solapi_from_now();fresh_order(sms)
    def unknown(*args):
        sent.append(args)
        raise TimeoutError()
    sms.transport=unknown
    assert sms.dispatch_one()=="UNKNOWN" and sms.dispatch_one()=="IDLE" and len(sent)==1
