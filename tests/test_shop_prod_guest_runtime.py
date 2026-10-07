from datetime import datetime,timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from core.shopping.guest_runtime import create_guest_commerce_app
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy
from core.shopping.guest_aftersales import GuestAftersalesStore
from core.shopping.order_core import OrderSnapshot,OrderLineItem,OrderCreateAmbiguousFailure
from test_shop_prod_customer_isolation import FakePort
from test_shop_guest_checkout import LiveCatalog

ORIGIN="https://bokstory.duckdns.org"
BODY={"cart":{"line_items":[{"product_id":"10","variation_id":"11","quantity":1}]},"delivery":{"recipient":"테스트 수령인","postcode":"12345","address1":"테스트 배송 주소 123","address2":""}}
@pytest.fixture
def runtime(tmp_path):
    now=datetime.now(timezone.utc);calls=[];phone_calls=[];amount=[Decimal("29000")];fail=[False]
    class Writer:
        def create_order(self,command):
            calls.append(command)
            if fail[0]:raise OrderCreateAmbiguousFailure("TEST_LOST_RESPONSE")
            line=command.line_items[0];number=500+len(calls)
            return OrderSnapshot(provider="woocommerce",provider_order_id=number,provider_reference="woocommerce:order:"+str(number),order_number=str(number),status="pending",currency="KRW",customer_reference=None,line_items=(OrderLineItem(number,line.provider_product_id,line.provider_variation_id,None,"테스트 상품",line.quantity,amount[0],amount[0],Decimal("0")),),total=amount[0],total_tax=Decimal("0"),created_at=now,updated_at=now,provider_version="fake")
    def quote(catalog,cart):
        return {"line_items":[{"product_id":"10","variation_id":"11","quantity":1,"name":"테스트 상품","option":"S","unit_price":str(amount[0]),"subtotal":str(amount[0])}],"items_total":str(amount[0]),"shipping_fee":"0","total_tax":"0","final_total":str(amount[0]),"currency":"KRW","shipping_policy":"EXPLICIT_TEST_POLICY"}
    app=create_guest_commerce_app(path_policy=IsolatedTestDatabasePathPolicy(tmp_path),private_root=tmp_path/"prod",origin=ORIGIN,phone_cfg={"environment":"PROD","enabled":True},binding_key=b"b"*32,csrf_key=b"c"*32,catalog=LiveCatalog(),quote=quote,writer_factory=lambda *args:Writer(),lookup_store_factory=lambda ledger,checkout,catalog:GuestAftersalesStore(tmp_path/"prod"/"fulfillment.sqlite3",tmp_path/"prod"/"attachments",ledger=ledger,checkout=checkout,catalog=catalog,clock=lambda:now.timestamp()),clock=lambda:now,port_factory=lambda phone:FakePort(phone,lambda:now,phone_calls,set()))
    return app,calls,amount,fail

def login(app,phone):
    client=TestClient(app,base_url=ORIGIN);headers={"Origin":ORIGIN}
    assert client.post("/shopping/phone/start",json={"phone":phone,"consent":True},headers=headers).status_code==200
    assert client.post("/shopping/phone/check",json={"code":"123456"},headers=headers).status_code==201
    session=client.get("/shopping/auth/session");assert session.status_code==200
    headers["X-CSRF-Token"]=session.headers["X-CSRF-Token"]
    return client,headers

def test_multi_customer_orders_replay_lookup_and_foreign_drafts(runtime):
    app,calls,_,_=runtime;a,ha=login(app,"01012345678");b,hb=login(app,"01087654321")
    draft_a=a.post("/shopping/checkout/prepare",json=BODY,headers=ha).json()
    forbidden=b.post("/shopping/checkout/confirm",json={"draft_id":draft_a["draft_id"]},headers=hb)
    assert forbidden.status_code==409 and not calls
    result=a.post("/shopping/checkout/confirm",json={"draft_id":draft_a["draft_id"]},headers=ha)
    assert result.status_code==201
    assert a.post("/shopping/checkout/confirm",json={"draft_id":draft_a["draft_id"]},headers=ha).status_code==200
    assert len(calls)==1
    lookup={"order_number":result.json()["order_number"],"phone":"01012345678"}
    owned=a.post("/shopping/orders/lookup",json=lookup,headers=ha)
    assert owned.status_code==200 and owned.json()["order"]["delivery"]["address_1"]=="테스트 배송 주소 123"
    assert b.post("/shopping/orders/lookup",json=lookup,headers=hb).status_code==403
    status_path="/shopping/orders/operations/"+draft_a["operation_key"]
    assert a.get(status_path,headers=ha).status_code==200
    assert b.get(status_path,headers=hb).status_code==403
    draft_b=b.post("/shopping/checkout/prepare",json=BODY,headers=hb).json()
    assert b.post("/shopping/checkout/confirm",json={"draft_id":draft_b["draft_id"]},headers=hb).status_code==201
    assert len(calls)==2 and calls[0].customer_id!=calls[1].customer_id
    assert a.post("/shopping/orders",json={},headers=ha).status_code==404
    assert a.get("/__order-dev/chat/capabilities").status_code==404
    assert a.get("/shopping/chat/capabilities").json()["transaction_sms"] is False

def test_changed_quote_and_missing_csrf_cannot_write(runtime):
    app,calls,amount,_=runtime;client,h=login(app,"01012345678")
    assert client.post("/shopping/checkout/prepare",json=BODY,headers={"Origin":ORIGIN}).status_code==422
    draft=client.post("/shopping/checkout/prepare",json=BODY,headers=h).json();amount[0]=Decimal("30000")
    assert client.post("/shopping/checkout/confirm",json={"draft_id":draft["draft_id"]},headers=h).status_code==409
    assert not calls

def test_unknown_provider_response_never_reposts(runtime):
    app,calls,_,fail=runtime;client,h=login(app,"01012345678")
    draft=client.post("/shopping/checkout/prepare",json=BODY,headers=h).json();fail[0]=True
    payload={"draft_id":draft["draft_id"]}
    assert client.post("/shopping/checkout/confirm",json=payload,headers=h).status_code==409
    assert client.post("/shopping/checkout/confirm",json=payload,headers=h).status_code==409
    assert len(calls)==1

def test_inquiries_are_anonymous_but_origin_bound(runtime):
    app,calls,_,_=runtime;client=TestClient(app,base_url=ORIGIN)
    body={"product_id":"10","message":"재고 있나요"}
    assert client.post("/shopping/chat/inquiry",json=body).status_code==422
    assert client.post("/shopping/chat/inquiry",json=body,headers={"Origin":ORIGIN}).status_code==200
    assert not calls

def test_production_composition_rejects_dev_origin_and_storage(tmp_path):
    base=dict(private_root=tmp_path/"prod",origin=ORIGIN,phone_cfg={"environment":"PROD","enabled":True},binding_key=b"b"*32,csrf_key=b"c"*32,catalog=None,quote=lambda *a:None,writer_factory=lambda *a:None,lookup_store_factory=lambda *a:None,clock=lambda:datetime.now(timezone.utc))
    for change in ({"origin":"https://dev.bokstory.duckdns.org"},{"private_root":tmp_path/"dev-order"},{"phone_cfg":{"environment":"DEV","enabled":True}}):
        with pytest.raises(ValueError):create_guest_commerce_app(**{**base,**change})
