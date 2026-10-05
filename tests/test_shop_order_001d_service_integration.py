from __future__ import annotations

from datetime import datetime,timedelta,timezone
from decimal import Decimal

import pytest

from core.shopping.adapters.woocommerce_order_write import (
    ORDER_DIGEST_META_KEY,OrderWriteCredential,OrderWriteDisposition,
    OrderWriteTransportResponse,OrderWriteTransportUnknownOutcome,
    WooCommerceOrderCreateAdapter,
)
from core.shopping.models import Product
from core.shopping.order_core import (
    OrderCreateAuthority,OrderCreateCommand,OrderCreateDefinitiveFailure,
    OrderCreateLine,OrderCreateOperationTerminalFailure,
    OrderCreateOperationUnknownOutcome,OrderCreateService,SQLiteOrderCreateLedger,
    ShoppingServiceOrderCatalogResolver,
)
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy

NOW=datetime(2026,10,5,14,0,tzinfo=timezone.utc)
CUSTOMER="AG-CUS-"+"1"*12+"4"+"1"*3+"8"+"1"*15
SESSION="AG-SES-"+"2"*12+"4"+"2"*3+"8"+"2"*15

class Clock:
    def __init__(self):self.value=NOW
    def __call__(self):return self.value
    def tick(self):self.value+=timedelta(seconds=1)

class Catalog:
    def __init__(self):self.calls=[]
    def get_product(self,product_id):
        self.calls.append(product_id)
        value=Product(id="123",name="P",slug="p",description="d",price=Decimal("10000"),
                      currency="KRW",category="C",in_stock=True,source="woocommerce").__dict__.copy()
        value["variants"]=[]
        return value

class Credentials:
    def get_credentials(self):return OrderWriteCredential("consumer","secret")

class Transport:
    def __init__(self,mode="success"):self.mode=mode;self.calls=[]
    def send(self,request,credential,*,timeout_seconds):
        self.calls.append(request)
        if self.mode=="unknown":raise OrderWriteTransportUnknownOutcome()
        if self.mode=="not-applied":
            return OrderWriteTransportResponse(400,{},OrderWriteDisposition.NOT_APPLIED)
        body=__import__("json").loads(request.canonical_body)
        digest=body["meta_data"][0]["value"]
        payload={
            "id":501,"number":"501","status":"pending","currency":"KRW","customer_id":0,
            "line_items":[{"id":7001,"product_id":123,"variation_id":0,"sku":None,
                           "name":"P","quantity":1,"subtotal":"10000","total":"10000","total_tax":"0"}],
            "total":"10000","total_tax":"0","date_created_gmt":"2026-10-05T14:00:00Z",
            "date_modified_gmt":"2026-10-05T14:00:00Z","version":"10.0.0",
            "meta_data":[{"id":1,"key":ORDER_DIGEST_META_KEY,"value":digest}],
        }
        if self.mode=="malformed":payload.pop("number")
        return OrderWriteTransportResponse(201,payload,OrderWriteDisposition.APPLIED)

def command():
    return OrderCreateCommand(
        customer_id=CUSTOMER,line_items=(OrderCreateLine("123",None,1),),
        idempotency_key="order-001",correlation_id="corr-001",
        audit_reference="audit-001",requested_at=NOW)

def authority():
    return OrderCreateAuthority(CUSTOMER,SESSION,"auth-001",NOW,NOW+timedelta(minutes=10))

def build(tmp_path,mode="success"):
    clock=Clock();catalog=Catalog();transport=Transport(mode)
    ledger=SQLiteOrderCreateLedger(tmp_path/"orders.sqlite3",clock=clock,
        path_policy=IsolatedTestDatabasePathPolicy(tmp_path));ledger.initialize()
    adapter=WooCommerceOrderCreateAdapter(
        credential_provider=Credentials(),transport=transport)
    service=OrderCreateService(
        catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),
        order_creator=adapter,coordinator=ledger)
    return service,ledger,catalog,transport,clock

def test_success_completes_durable_ledger_and_replays_without_second_transport(tmp_path):
    service,ledger,catalog,transport,clock=build(tmp_path)
    first=service.execute(command(),authority())
    assert first.snapshot.provider_order_id==501
    assert ledger.inspect_operation("order-001")["state"]=="COMPLETED"
    assert len(catalog.calls)==1 and len(transport.calls)==1
    clock.tick()
    fresh=OrderCreateAuthority(CUSTOMER,SESSION,"auth-002",clock(),NOW+timedelta(minutes=10))
    retry=OrderCreateCommand(
        customer_id=CUSTOMER,line_items=(OrderCreateLine("123",None,1),),
        idempotency_key="order-001",correlation_id="corr-002",
        audit_reference="audit-002",requested_at=clock())
    replay=service.execute(retry,fresh)
    assert replay.idempotent_replay is True and replay.snapshot==first.snapshot
    assert len(catalog.calls)==1 and len(transport.calls)==1

def test_unknown_transport_quarantines_and_blocks_second_provider_attempt(tmp_path):
    service,ledger,catalog,transport,clock=build(tmp_path,"unknown")
    with pytest.raises(Exception,match="WRITE_TRANSPORT_UNKNOWN"):
        service.execute(command(),authority())
    assert ledger.inspect_operation("order-001")["state"]=="UNKNOWN_OUTCOME"
    with pytest.raises(OrderCreateOperationUnknownOutcome):
        service.execute(command(),authority())
    assert len(transport.calls)==1

def test_provider_not_applied_is_terminal_and_never_retried(tmp_path):
    service,ledger,catalog,transport,clock=build(tmp_path,"not-applied")
    with pytest.raises(OrderCreateDefinitiveFailure,match="PROVIDER_NOT_APPLIED"):
        service.execute(command(),authority())
    assert ledger.inspect_operation("order-001")["state"]=="TERMINAL_FAILED"
    with pytest.raises(OrderCreateOperationTerminalFailure):
        service.execute(command(),authority())
    assert len(transport.calls)==1

def test_applied_but_malformed_response_is_unknown_outcome(tmp_path):
    service,ledger,catalog,transport,clock=build(tmp_path,"malformed")
    with pytest.raises(Exception,match="PROVIDER_RESPONSE_INVALID"):
        service.execute(command(),authority())
    assert ledger.inspect_operation("order-001")["state"]=="UNKNOWN_OUTCOME"
    assert len(transport.calls)==1

def test_default_unconfigured_adapter_is_definitive_before_any_network(tmp_path):
    clock=Clock();catalog=Catalog()
    ledger=SQLiteOrderCreateLedger(tmp_path/"orders.sqlite3",clock=clock,
        path_policy=IsolatedTestDatabasePathPolicy(tmp_path));ledger.initialize()
    service=OrderCreateService(
        catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),
        order_creator=WooCommerceOrderCreateAdapter(),coordinator=ledger)
    with pytest.raises(OrderCreateDefinitiveFailure,match="WRITE_CREDENTIAL_UNAVAILABLE"):
        service.execute(command(),authority())
    assert ledger.inspect_operation("order-001")["state"]=="TERMINAL_FAILED"
