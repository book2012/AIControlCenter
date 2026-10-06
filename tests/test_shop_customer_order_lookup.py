import json,sqlite3
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_shop_aftersales_dev import fixture,Boundary,CUSTOMER,ORDER
from ops.macos.shopping.dev_aftersales import mount_aftersales
from ops.macos.shopping.dev_order_sms import DevOrderSMS
PHONE="+821012345678"
def client_for(tmp_path):
    store,_=fixture(tmp_path,[1000.0]);app=FastAPI()
    mount_aftersales(app,store=store,boundary=Boundary(),phone_cfg={"guest_customer_id":CUSTOMER,"test_phone":PHONE})
    client=TestClient(app,base_url="https://dev.bokstory.duckdns.org")
    return client,store
def test_lookup_requires_verified_session_origin_csrf_number_and_phone(tmp_path):
    client,store=client_for(tmp_path)
    payload={"order_number":str(ORDER),"phone":"01012345678"}
    h={"Origin":"https://dev.bokstory.duckdns.org","X-CSRF-Token":"csrf"}
    denied=client.post("/__order-dev/orders/lookup",json=payload,headers=h)
    assert denied.status_code==403 and "배송 주소" not in denied.text
    client.cookies.set("__Host-aicc_customer","secret")
    for body,headers in [(payload,{}),({**payload,"phone":"01099999999"},h),({**payload,"order_number":"999999"},h),({**payload,"customer_id":CUSTOMER},h)]:
        response=client.post("/__order-dev/orders/lookup",json=body,headers=headers)
        assert response.status_code==403 and "delivery" not in response.text
    response=client.post("/__order-dev/orders/lookup",json=payload,headers=h)
    assert response.status_code==200 and response.headers["cache-control"]=="no-store"
    order=response.json()["order"]
    assert order["delivery"]["address_1"]=="DEV 테스트 배송 주소" and order["payment"]["state"]=="AWAITING_DEPOSIT"
    assert client.get("/__order-dev/aftersales/orders").status_code==403
    assert "입금완료" in store.operator_command("입금확인 #15",101)
    assert store.operator_command("입금확인 #15",101)=="주문 #15 · 입금완료 · 배송준비"
    assert store.lookup(CUSTOMER,"15",PHONE,PHONE)["payment"]["state"]=="PAID"
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    assert store.lookup(CUSTOMER,"15",PHONE,PHONE)["fulfillment"]["state"]=="SHIPPED"
def config(tmp_path):
    p=tmp_path/"sms.json";p.write_text(json.dumps({"environment":"DEV","enabled":True,"bank":{"name":"TEST BANK","account":"TEST ACCOUNT","holder":"TEST HOLDER"},"credentials":{"account_sid":"AC"+"a"*32,"auth_token":"TEST","messaging_service_sid":"MG"+"b"*32}}));p.chmod(0o600);return p
def sms_fixture(tmp_path,transport):
    store,_=fixture(tmp_path,[1000.0])
    original=store.ledger.customer_orders
    rows=original(CUSTOMER);store.ledger.customer_orders=lambda customer: rows if customer==CUSTOMER else []
    sms=DevOrderSMS(tmp_path/"sms.sqlite3",aftersales=store,phone_cfg={"guest_customer_id":CUSTOMER,"test_phone":PHONE},config_path=config(tmp_path),transport=transport)
    return sms,store,rows
def test_historical_orders_never_backfill_and_new_confirmation_sends_once(tmp_path):
    sent=[];sms,store,rows=sms_fixture(tmp_path,lambda cfg,to,text:sent.append((to,text)))
    assert sms.dispatch_one()=="IDLE" and not sent and sms.state(ORDER)=="HISTORICAL"
    with sqlite3.connect(sms.path) as c:c.execute("DELETE FROM notices WHERE order_id=?",(ORDER,))
    rows[0]["review_state"]="PENDING_REVIEW"
    assert sms.dispatch_one()=="IDLE" and not sent
    rows[0]["review_state"]="CONFIRMED"
    assert sms.dispatch_one()=="ACCEPTED" and len(sent)==1
    assert "주문번호: 15" in sent[0][1] and "TEST ACCOUNT" in sent[0][1] and sent[0][0]==PHONE
    assert sms.dispatch_one()=="IDLE" and len(sent)==1
def test_ambiguous_sms_is_not_retried_after_restart(tmp_path):
    def failing(*args):raise TimeoutError()
    sms,store,rows=sms_fixture(tmp_path,failing)
    with sqlite3.connect(sms.path) as c:c.execute("DELETE FROM notices WHERE order_id=?",(ORDER,))
    assert sms.dispatch_one()=="UNKNOWN"
    assert sms.dispatch_one()=="IDLE"
    restarted=DevOrderSMS(sms.path,aftersales=store,phone_cfg=sms.phone_cfg,config_path=sms.config_path,transport=lambda *a:pytest.fail("duplicate"))
    assert restarted.dispatch_one()=="IDLE" and restarted.state(ORDER)=="UNKNOWN"
def test_missing_private_bank_config_does_not_claim_or_send(tmp_path):
    sms,store,rows=sms_fixture(tmp_path,lambda *a:pytest.fail("not configured"))
    with sqlite3.connect(sms.path) as c:c.execute("DELETE FROM notices WHERE order_id=?",(ORDER,))
    cfg=json.loads(sms.config_path.read_text());cfg["bank"]["account"]="";sms.config_path.write_text(json.dumps(cfg))
    assert sms.dispatch_one()=="CONFIGURATION_REQUIRED" and sms.state(ORDER)=="PENDING"
