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
REFUND_ACCOUNT={"bank_name":"국민은행","account_holder":"홍길동","account_number":"123456789012"}
class Ledger:
    def __init__(self,key):self.key=key;self.review_state="CONFIRMED"
    def customer_orders(self,customer):
        if customer!=CUSTOMER:return []
        return [{"operation_key":self.key,"reference":"a"*24,"review_state":self.review_state,"provider_order_id":ORDER,"requested_at":"2026-10-06T00:00:00Z"}]
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
    store=DevAftersalesStore(tmp_path/"after.sqlite3",tmp_path/"files",ledger=ledger,checkout=checkout,catalog=Catalog(),clock=lambda:clock[0],refund_account_key=b"r"*32)
    return store,d

def test_delivery_completion_starts_14_day_customer_window(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    first=store.customer_orders(CUSTOMER)[0]
    assert first["fulfillment"]["state"]=="NOT_SHIPPED" and not first["return_available"]
    with pytest.raises(ValueError):store.mark_delivered(ORDER)
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    assert not store.customer_orders(CUSTOMER)[0]["return_available"]
    store.mark_delivered(ORDER)
    current=store.customer_orders(CUSTOMER)[0]
    assert current["return_available"] and current["exchange_available"]
    clock[0]+=14*86400
    assert not store.customer_orders(CUSTOMER)[0]["return_available"]

def test_exchange_case_attachment_and_approval(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.confirm_payment(ORDER);store.mark_shipped(ORDER,"한진택배","1234567890");store.mark_delivered(ORDER)
    assert store.exchange_options(CUSTOMER,ORDER)==[{"variation_id":"12","option":"M"}]
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"SIZE_EXCHANGE","reason":"M 사이즈로 교환하고 싶어요","reason_type":"CHANGE_OF_MIND","target_variation_id":"12"})
    assert case["state"]=="REQUESTED" and case["target_option"]=="M"
    assert not store.customer_orders(CUSTOMER)[0]["exchange_available"]
    png=b"\x89PNG\r\n\x1a\n"+b"x"*64
    receipt=store.attach(CUSTOMER,case["id"],"image/png",png)
    assert receipt["size"]==len(png) and store.case(CUSTOMER,case["id"])["attachments"]==1
    decided=store.decide(case["id"],True);assert decided["state"]=="EXCHANGE_APPROVED"

def test_return_case_and_operator_commands_are_idempotent(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    store.confirm_payment(ORDER)
    reply=store.operator_command("주문발송 #15 CJ대한통운 1234567890",1)
    assert "발송 등록" in reply and store.operator_command("주문발송 #15 CJ대한통운 9999999999",1)==reply
    assert "14일" in store.operator_command("배송완료 #15",2)
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"단순 변심","reason_type":"CHANGE_OF_MIND","target_variation_id":None})
    listing=store.operator_command("환불목록",3);assert case["id"] in listing
    approved=store.operator_command("환불승인 #"+case["id"],4);assert "RETURN_APPROVED" in approved
    assert store.operator_command("환불승인 #"+case["id"],4)==approved

def test_customer_routes_require_session_csrf_and_keep_attachments_private(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890");store.mark_delivered(ORDER)
    boundary=Boundary();app=FastAPI();mount_aftersales(app,store=store,boundary=boundary,phone_cfg={"guest_customer_id":CUSTOMER})
    with TestClient(app,base_url="https://dev.bokstory.duckdns.org") as client:
        portal=client.get("/dev-order/my-orders",follow_redirects=False)
        assert portal.status_code==302 and portal.headers["location"]=="/homepage/storefront/my-orders"
        assert client.get("/__order-dev/aftersales/orders").status_code==401
        client.cookies.set("__Host-aicc_customer","secret")
        orders=client.get("/__order-dev/aftersales/orders").json()["orders"];assert orders[0]["return_available"]
        assert client.post("/__order-dev/aftersales/cases",json={"order_id":ORDER,"kind":"RETURN","reason":"변심","reason_type":"CHANGE_OF_MIND","target_variation_id":None}).status_code==422
        h={"Origin":"https://dev.bokstory.duckdns.org","X-CSRF-Token":"csrf"}
        created=client.post("/__order-dev/aftersales/cases",json={"order_id":ORDER,"kind":"RETURN","reason":"변심","reason_type":"CHANGE_OF_MIND","target_variation_id":None},headers=h)
        assert created.status_code==201;case_id=created.json()["case"]["id"]
        png=b"\x89PNG\r\n\x1a\n"+b"x"*64
        attached=client.post("/__order-dev/aftersales/cases/"+case_id+"/attachments",content=png,headers={**h,"Content-Type":"image/png"})
        assert attached.status_code==201 and boundary.csrf_checked>=2
        assert list((tmp_path/"files").iterdir()) and all(p.stat().st_mode&0o077==0 for p in (tmp_path/"files").iterdir())


def test_customer_pre_shipment_cancel_and_order_change_are_review_requests(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    order=store.customer_orders(CUSTOMER)[0]
    assert order["cancel_request_available"] and order["order_change_available"]
    assert not order["return_available"] and not order["exchange_available"]
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"ORDER_CHANGE","reason":"배송지 주소를 변경해 주세요","target_variation_id":None})
    assert case["state"]=="REQUESTED" and case["shipping_fee_payer"] is None
    assert not store.customer_orders(CUSTOMER)[0]["order_change_available"]
    assert store.decide(case["id"],True)["state"]=="ORDER_CHANGE_APPROVED"
    # Approval records review only; the checkout address is not silently mutated.
    _,draft=store._customer_order(CUSTOMER,ORDER)
    assert draft["body"]["shipping"]["address_1"]=="DEV 테스트 배송 주소"


def test_pre_shipment_cancel_refund_request_is_separate_from_actual_cancellation(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    store.confirm_payment(ORDER)
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"입금한 주문 취소 요청","target_variation_id":None},refund_account=REFUND_ACCOUNT,refund_account_consent=True)
    assert case["state"]=="REQUESTED" and case["shipping_fee_payer"] is None
    assert store.cancellation(ORDER)["state"]=="NONE"
    assert not store.customer_orders(CUSTOMER)[0]["cancel_request_available"]
    assert store.decide(case["id"],True)["state"]=="RETURN_APPROVED"
    assert store.cancellation(ORDER)["state"]=="NONE"


def test_delivery_reason_persists_correct_shipping_fee_owner_and_must_be_selected(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890");store.mark_delivered(ORDER)
    with pytest.raises(ValueError,match="REASON_TYPE_REQUIRED"):
        store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"상품 반품"})
    seller_case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"상품에 하자가 있습니다","reason_type":"DEFECT_OR_WRONG"})
    assert seller_case["shipping_fee_payer"]=="SELLER"
    assert seller_case["reason_type"]=="DEFECT_OR_WRONG"
    assert store.customer_orders(CUSTOMER)[0]["cases"][0]["shipping_fee_payer"]=="SELLER"


def test_customer_change_request_is_denied_after_shipment_starts(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    order=store.customer_orders(CUSTOMER)[0]
    assert not order["cancel_request_available"] and not order["order_change_available"]
    with pytest.raises(ValueError,match="ORDER_CHANGE_CLOSED"):
        store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"ORDER_CHANGE","reason":"주소 변경","target_variation_id":None})


def test_existing_case_database_adds_nullable_fee_fields_without_losing_cases(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"ORDER_CHANGE","reason":"주소 수정 요청","target_variation_id":None})
    import sqlite3
    with sqlite3.connect(store.path) as db:
        db.execute("ALTER TABLE cases DROP COLUMN shipping_fee_payer")
        db.execute("ALTER TABLE cases DROP COLUMN reason_type")
    migrated=DevAftersalesStore(store.path,store.attachments,ledger=store.ledger,checkout=store.checkout,catalog=store.catalog,clock=lambda:clock[0])
    restored=migrated.case(CUSTOMER,case["id"])
    assert restored["kind"]=="ORDER_CHANGE" and restored["shipping_fee_payer"] is None and restored["reason_type"] is None


def test_delivery_replay_after_restart_preserves_original_receipt(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock)
    store.confirm_payment(ORDER);store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    first=store.mark_delivered(ORDER)
    clock[0]+=300
    restarted=DevAftersalesStore(store.path,store.attachments,ledger=store.ledger,
        checkout=store.checkout,catalog=store.catalog,clock=lambda:clock[0])
    assert restarted.mark_delivered(ORDER)==first
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts=list(pool.map(lambda _:restarted.mark_delivered(ORDER),range(8)))
    assert all(receipt==first for receipt in receipts)
    assert restarted.customer_orders("another-customer")==[]
    assert restarted.payment(ORDER)["state"]=="PAID"
    from core.shopping.customer_order_notices import order_notices
    messages=order_notices(restarted.customer_orders(CUSTOMER)[0],None)
    assert messages[-1]["kind"]=="DELIVERED"


def test_admin_can_open_and_approve_exchange_case_while_shipment_is_in_progress(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.confirm_payment(ORDER)
    store.mark_shipped(ORDER,'한진택배','1234567890')
    options=store.admin_exchange_options(ORDER)
    assert options==[{'variation_id':'12','option':'M'}]
    case=store.admin_create_case(ORDER,{'order_id':ORDER,'kind':'SIZE_EXCHANGE','reason':'배송 중 사이즈 교환 요청','target_variation_id':'12'})
    assert case['state']=='REQUESTED' and case['target_option']=='M'
    approved=store.decide(case['id'],True)
    assert approved['state']=='EXCHANGE_APPROVED'
    assert store.admin_fulfillment(ORDER)['state']=='SHIPPED'
    assert store.payment(ORDER)['state']=='PAID'


def test_pending_review_order_allows_customer_cancel_and_change_requests(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.ledger.review_state="PENDING_REVIEW"
    order=store.customer_orders(CUSTOMER)[0]
    assert order["review_state"]=="PENDING_REVIEW" and order["cancel_request_available"] and order["order_change_available"]
    assert order["payment"]["state"]=="AWAITING_DEPOSIT"
    request=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"확인 대기 주문 취소 요청"})
    assert request["state"]=="REQUESTED" and store.cancellation(ORDER)["state"]=="NONE"


def test_paid_pre_shipment_cancel_requires_encrypted_refund_account_and_erases_on_reject(tmp_path):
    import sqlite3
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.confirm_payment(ORDER)
    payload={"order_id":ORDER,"kind":"RETURN","reason":"입금 주문 취소 및 환불 요청"}
    with pytest.raises(ValueError,match="REFUND_ACCOUNT_REQUIRED"):
        store.create_case(CUSTOMER,payload)
    with pytest.raises(ValueError,match="REFUND_ACCOUNT_CONSENT_REQUIRED"):
        store.create_case(CUSTOMER,payload,refund_account=REFUND_ACCOUNT)
    case=store.create_case(CUSTOMER,payload,refund_account=REFUND_ACCOUNT,refund_account_consent=True)
    assert "refund_account" not in case
    with sqlite3.connect(store.path) as db:
        row=db.execute("SELECT ciphertext,notice_version,created FROM refund_destinations WHERE case_id=?",(case["id"],)).fetchone()
        consent=db.execute("SELECT refund_account_consent_version,refund_account_consent_at FROM cases WHERE id=?",(case["id"],)).fetchone()
    encrypted=row[0]
    assert row[1]=="refund-account-dev-001" and consent==("refund-account-dev-001",row[2])
    with pytest.raises(ValueError,match="NOT_AVAILABLE"):
        store.admin_refund_account(case["id"])
    assert REFUND_ACCOUNT["account_number"].encode() not in bytes(encrypted)
    store.decide(case["id"],False)
    with pytest.raises(ValueError,match="NOT_AVAILABLE"):
        store.admin_refund_account(case["id"])
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT 1 FROM refund_destinations WHERE case_id=?",(case["id"],)).fetchone() is None


def test_paid_cancel_request_collects_account_over_customer_route(tmp_path):
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.confirm_payment(ORDER)
    boundary=Boundary();app=FastAPI();mount_aftersales(app,store=store,boundary=boundary,phone_cfg={"guest_customer_id":CUSTOMER})
    with TestClient(app,base_url="https://dev.bokstory.duckdns.org") as client:
        client.cookies.set("__Host-aicc_customer","secret")
        headers={"Origin":"https://dev.bokstory.duckdns.org","X-CSRF-Token":"csrf"}
        created=client.post("/__order-dev/aftersales/cases",json={"order_id":ORDER,"kind":"RETURN","reason":"환불 요청","refund_account":REFUND_ACCOUNT,"refund_account_consent":True},headers=headers)
        assert created.status_code==201
        case=created.json()["case"]
        assert "refund_account" not in case
        with pytest.raises(ValueError,match="NOT_AVAILABLE"):
            store.admin_refund_account(case["id"])
        case_id=case["id"]
    store.decide(case_id,True)
    store.stock_cancellation=lambda row,draft:{"outcome":"STOCK_CANCELLED","order_id":ORDER}
    store.cancel_order(ORDER,refund_case_id=case_id)
    assert store.admin_refund_account(case_id)==REFUND_ACCOUNT


def test_refund_completion_deletes_encrypted_destination(tmp_path):
    import sqlite3
    clock=[1000.0];store,_=fixture(tmp_path,clock);store.confirm_payment(ORDER)
    case=store.create_case(CUSTOMER,{"order_id":ORDER,"kind":"RETURN","reason":"환불 신청"},refund_account=REFUND_ACCOUNT,refund_account_consent=True)
    store.decide(case["id"],True)
    store.stock_cancellation=lambda row,draft:{"outcome":"STOCK_CANCELLED","order_id":ORDER}
    store.cancel_order(ORDER,refund_case_id=case["id"])
    store.manual_refund_records_enabled=True
    _,draft=store._customer_order(CUSTOMER,ORDER);amount=int(draft["body"]["quote"]["final_total"])
    store.record_refund(case["id"],amount,"BANK-001","admin-web-dev",42)
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT 1 FROM refund_destinations WHERE case_id=?",(case["id"],)).fetchone() is None
    with pytest.raises(ValueError,match="NOT_AVAILABLE"):
        store.admin_refund_account(case["id"])
