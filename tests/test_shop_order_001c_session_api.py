from __future__ import annotations

from datetime import datetime,timedelta,timezone
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretBytes

from core.api.dependencies.customer_session import (
    COOKIE_NAME,CSRF_HEADER,SessionAPIDenied,get_customer_session_boundary,
)
from core.api.dependencies.order_create import get_order_create_service
from core.api.routes.order_create import router
from core.api.schemas.customer_sessions import SessionAPIError
from core.shopping.customer_sessions import SafeSessionProjection
from core.shopping.models import Product
from core.shopping.order_core import (
    OrderCreateService,OrderLineItem,OrderSnapshot,SQLiteOrderCreateLedger,
    ShoppingServiceOrderCatalogResolver,
)
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy

NOW=datetime(2026,10,5,12,0,tzinfo=timezone.utc)
CUSTOMER="AG-CUS-"+"1"*12+"4"+"1"*3+"8"+"1"*15
SESSION="AG-SES-"+"2"*12+"4"+"2"*3+"8"+"2"*15
SESSION2="AG-SES-"+"3"*12+"4"+"3"*3+"8"+"3"*15
SECRET="a"*43
CSRF="b"*64
ORIGIN="https://shop.example.test"

class Clock:
    def __init__(self):self.value=NOW
    def __call__(self):return self.value
    def tick(self,seconds=1):self.value+=timedelta(seconds=seconds)

class Boundary:
    def __init__(self,clock):
        self.clock=clock;self.session_id=SESSION;self.calls=[]
    def now(self):return self.clock()
    def check_origin(self,request,*,required):
        self.calls.append("origin")
        if required and request.headers.get("origin")!=ORIGIN:
            raise SessionAPIDenied(SessionAPIError.ORIGIN_DENIED)
    def cookie_secret(self,request):
        self.calls.append("cookie")
        raw=request.headers.get("cookie","")
        if raw!=f"{COOKIE_NAME}={SECRET}":
            raise SessionAPIDenied(SessionAPIError.DENIED,clear_cookie=True)
        return SECRET
    def authenticate(self,secret,*,now):
        self.calls.append("authenticate")
        if secret!=SECRET:raise SessionAPIDenied(SessionAPIError.DENIED)
        return SafeSessionProjection(
            id=self.session_id,customer_id=CUSTOMER,created_at=NOW-timedelta(minutes=1),
            last_activity_at=NOW,idle_expires_at=NOW+timedelta(minutes=30),
            absolute_expires_at=NOW+timedelta(hours=23,minutes=59),revoked_at=None)
    def check_csrf(self,request,secret,projection):
        self.calls.append("csrf")
        if request.headers.get(CSRF_HEADER)!=CSRF:
            raise SessionAPIDenied(SessionAPIError.CSRF_DENIED)

class Catalog:
    def get_product(self,product_id):
        value=Product(id="123",name="P",slug="p",description="d",price=Decimal("10000"),
                      currency="KRW",category="C",in_stock=True,source="woocommerce").__dict__.copy()
        value["variants"]=[]
        return value

class Writer:
    def __init__(self):self.calls=[]
    def create_order(self,resolved):
        self.calls.append(resolved)
        line=resolved.line_items[0]
        return OrderSnapshot(
            provider="woocommerce",provider_order_id=501,provider_reference="woocommerce:order:501",
            order_number="501",status="pending",currency="KRW",customer_reference=None,
            line_items=(OrderLineItem(1,line.provider_product_id,line.provider_variation_id,None,"P",
                                      line.quantity,Decimal("10000"),Decimal("10000"),Decimal("0")),),
            total=Decimal("10000"),total_tax=Decimal("0"),created_at=NOW,updated_at=NOW,
            provider_version="test")

def build(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    clock=Clock();boundary=Boundary(clock);writer=Writer()
    ledger=SQLiteOrderCreateLedger(tmp_path/"orders.sqlite3",clock=clock,
        path_policy=IsolatedTestDatabasePathPolicy(tmp_path));ledger.initialize()
    service=OrderCreateService(
        catalog_resolver=ShoppingServiceOrderCatalogResolver(Catalog()),
        order_creator=writer,coordinator=ledger)
    app=FastAPI();app.include_router(router)
    app.dependency_overrides[get_customer_session_boundary]=lambda:boundary
    app.dependency_overrides[get_order_create_service]=lambda:service
    return TestClient(app),boundary,writer,clock

def headers(*,origin=ORIGIN,csrf=CSRF,cookie=True):
    value={"Origin":origin,"Sec-Fetch-Site":"same-origin",CSRF_HEADER:csrf}
    if cookie:value["Cookie"]=f"{COOKIE_NAME}={SECRET}"
    return value

BODY={"line_items":[{"product_id":"123","quantity":1}],"idempotency_key":"order-001"}

def test_valid_session_create_then_same_session_retry_replays_without_second_write(tmp_path):
    client,boundary,writer,clock=build(tmp_path)
    first=client.post("/shopping/owned-orders",json=BODY,headers=headers())
    assert first.status_code==201 and first.json()["idempotent_replay"] is False
    assert first.json()["order"]=={
        "order_number":"501","status":"pending","currency":"KRW","total":"10000",
        "line_items":[{"product_id":"123","variation_id":None,"quantity":1}]}
    assert writer.calls and len(writer.calls)==1
    clock.tick(1)
    second=client.post("/shopping/owned-orders",json=BODY,headers=headers())
    assert second.status_code==200 and second.json()["idempotent_replay"] is True
    assert len(writer.calls)==1
    assert boundary.calls[:4]==["origin","cookie","authenticate","csrf"]

def test_missing_session_origin_and_csrf_fail_before_writer(tmp_path):
    cases=[
        ({**headers(),"Cookie":""},401,"owned_order_session_denied"),
        (headers(origin="https://evil.example"),403,"owned_order_origin_denied"),
        (headers(csrf="c"*64),403,"owned_order_csrf_denied"),
    ]
    for request_headers,status,code in cases:
        client,boundary,writer,clock=build(tmp_path/f"case-{status}-{code}")
        response=client.post("/shopping/owned-orders",json=BODY,headers=request_headers)
        assert response.status_code==status and response.json()["detail"]["code"]==code
        assert writer.calls==[]

def test_body_cannot_supply_customer_price_payment_or_address_authority(tmp_path):
    for forbidden,value in (
        ("customer_id",CUSTOMER),("price","1"),("total","1"),("payment","x"),("address","x"),
    ):
        client,boundary,writer,clock=build(tmp_path/forbidden)
        body={**BODY,forbidden:value}
        response=client.post("/shopping/owned-orders",json=body,headers=headers())
        assert response.status_code==422
        assert writer.calls==[]

def test_same_key_from_different_session_conflicts_without_second_write(tmp_path):
    client,boundary,writer,clock=build(tmp_path)
    assert client.post("/shopping/owned-orders",json=BODY,headers=headers()).status_code==201
    boundary.session_id=SESSION2;clock.tick(1)
    response=client.post("/shopping/owned-orders",json=BODY,headers=headers())
    assert response.status_code==409
    assert response.json()["detail"]["code"]=="owned_order_idempotency_conflict"
    assert len(writer.calls)==1

def test_route_is_opt_in_and_default_app_source_does_not_register_it():
    source=Path("core/api/app.py").read_text()
    assert "routes.order_create" not in source
    assert "owned_order" not in source

def test_imported_order_route_has_no_live_writer_or_credentials():
    source=Path("core/api/routes/order_create.py").read_text()+Path("core/api/dependencies/order_create.py").read_text()
    for token in ("consumer_key","consumer_secret","requests.","httpx.","/wp-json/wc/v3/orders",'"POST"'):
        assert token not in source
