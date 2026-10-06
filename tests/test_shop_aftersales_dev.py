from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.shopping.models import ProductVariant
from core.shopping.order_core.guest_checkout import PrivateCheckoutStore
from ops.macos.shopping.dev_aftersales import DevAftersalesStore,mount_aftersales
from test_shop_guest_checkout import draft

CUSTOMER="customer"
ORDER=15
class Ledger:
    def __init__(self,key):self.key=key
    def customer_orders(self,customer):
        if customer!=CUSTOMER:return []
        return [{"operation_key":self.key,"reference":"a"*24,"review_state":"CONFIRMED","provider_order_id":ORDER,"requested_at":"2026-10-06T00:00:00Z"}]
    def operator_orders(self):
        return [{"operation_key":self.key,"reference":"a"*24,"state":"CONFIRMED","provider_order_id":ORDER,"requested_at":"2026-10-06T00:00:00Z","customer_id":CUSTOMER}]
class Catalog:
    def get_product(self,key):
        return {"id":key,"name":"블라우스","source":"woocommerce","variants":(
            ProductVariant("11","S","size",True),ProductVariant("12","M","size",True),ProductVariant("13","L","size",False))}
class Boundary:
    def __init__(self):self.csrf_checked=0
    def now(self):return None
    def cookie_secret(self,request):
        if request.cookies.get("__Host-aicc_customer")!="secret":raise ValueError()
        return "secret"
    def authenticate(self,secret,now):return SimpleNamespace(customer_id=CUSTOMER,id="session")
    def check_origin(self,request,required):
        if required and request.headers.get("origin")!="https://dev.bokstory.duckdns.org":raise ValueError()
    def check_csrf(self,request,secret,projection):
        if request.headers.get("X-CSRF-Token")!="csrf":raise ValueError()
        self.csrf_checked+=1

def fixture(tmp_path,clock):
    checkout=PrivateCheckoutStore(tmp_path/"checkout.sqlite3",clock=lambda:clock[0]);d=draft(checkout);checkout.confirm(d["draft_id"],CUSTOMER,"session")
    ledger=Ledger(d["operation_key"])
    store=DevAftersalesStore(tmp_path/"after.sqlite3",tmp_path/"files",ledger=ledger,checkout=checkout,catalog=Catalog(),clock=lambda:clock[0])
    return store,d

def test_delivery_completion_starts_14_day_customer_window(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    first=store.customer_orders(CUSTOMER)[0]
    assert first["fulfillment"]["state"]=="NOT_SHIPPED" and not first["return_available"]
    with pytest.raises(ValueError):store.mark_delivered(ORDER)
    store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    assert not store.customer_orders(CUSTOMER)[0]["return_available"]
    store.mark_delivered(ORDER)
    current=store.customer_orders(CUSTOMER)[0]
    assert current["return_available"] and current["exchange_available"]
    clock[0]+=14*86400
    assert not store.customer_orders(CUSTOMER)[0]["return_available"]

def test_exchange_case_attachment_and_approval(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.mark_shipped(ORDER,"한진택배","1234567890");store.mark_delivered(ORDER)
    assert store.exchange_options(CUSTOMER,ORDER)==[{"variation_id":"12","option":"M"}]
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"SIZE_EXCHANGE","reason":"M 사이즈로 교환하고 싶어요","target_variation_id":"12"})
    assert case["state"]=="REQUESTED" and case["target_option"]=="M"
    assert not store.customer_orders(CUSTOMER)[0]["exchange_available"]
    png=b"\x89PNG\r\n\x1a\n"+b"x"*64
    receipt=store.attach(CUSTOMER,case["id"],"image/png",png)
    assert receipt["size"]==len(png) and store.case(CUSTOMER,case["id"])["attachments"]==1
    decided=store.decide(case["id"],True);assert decided["state"]=="EXCHANGE_APPROVED"

def test_return_case_and_operator_commands_are_idempotent(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    reply=store.operator_command("주문발송 #15 CJ대한통운 1234567890",1)
    assert "발송 등록" in reply and store.operator_command("주문발송 #15 CJ대한통운 9999999999",1)==reply
    assert "14일" in store.operator_command("배송완료 #15",2)
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"단순 변심","target_variation_id":None})
    listing=store.operator_command("환불목록",3);assert case["id"] in listing
    approved=store.operator_command("환불승인 #"+case["id"],4);assert "RETURN_APPROVED" in approved
    assert store.operator_command("환불승인 #"+case["id"],4)==approved

def test_customer_routes_require_session_csrf_and_keep_attachments_private(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.mark_shipped(ORDER,"CJ대한통운","1234567890");store.mark_delivered(ORDER)
    boundary=Boundary();app=FastAPI();mount_aftersales(app,store=store,boundary=boundary,phone_cfg={"guest_customer_id":CUSTOMER})
    with TestClient(app,base_url="https://dev.bokstory.duckdns.org") as client:
        portal=client.get("/dev-order/my-orders",follow_redirects=False)
        assert portal.status_code==302 and portal.headers["location"]=="/homepage/storefront/my-orders"
        assert client.get("/__order-dev/aftersales/orders").status_code==401
        client.cookies.set("__Host-aicc_customer","secret")
        orders=client.get("/__order-dev/aftersales/orders").json()["orders"];assert orders[0]["return_available"]
        assert client.post("/__order-dev/aftersales/cases",json={"order_id":ORDER,"kind":"RETURN","reason":"변심","target_variation_id":None}).status_code==422
        h={"Origin":"https://dev.bokstory.duckdns.org","X-CSRF-Token":"csrf"}
        created=client.post("/__order-dev/aftersales/cases",json={"order_id":ORDER,"kind":"RETURN","reason":"변심","target_variation_id":None},headers=h)
        assert created.status_code==201;case_id=created.json()["case"]["id"]
        png=b"\x89PNG\r\n\x1a\n"+b"x"*64
        attached=client.post("/__order-dev/aftersales/cases/"+case_id+"/attachments",content=png,headers={**h,"Content-Type":"image/png"})
        assert attached.status_code==201 and boundary.csrf_checked>=2
        assert list((tmp_path/"files").iterdir()) and all(p.stat().st_mode&0o077==0 for p in (tmp_path/"files").iterdir())
