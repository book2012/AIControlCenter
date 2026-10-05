from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from core.shopping.models import Product, ProductVariant
from core.shopping.order_core import (
    InMemoryOrderCreateOperationCoordinator, OrderCreateAuthority, OrderCreateCommand,
    OrderCreateCatalogResolutionError, OrderCreateLine, OrderCreateService,
    OrderLineItem, OrderSnapshot, ShoppingServiceOrderCatalogResolver,
)

NOW=datetime(2026,10,5,11,0,tzinfo=timezone.utc)
CUSTOMER="AG-CUS-"+"1"*12+"4"+"1"*3+"8"+"1"*15
SESSION="AG-SES-"+"2"*12+"4"+"2"*3+"8"+"2"*15

class Catalog:
    def __init__(self,product): self.product=product;self.calls=[]
    def get_product(self,product_id):
        self.calls.append(product_id)
        if self.product is None: raise LookupError(product_id)
        return self.product.__dict__

class Writer:
    def __init__(self): self.calls=[]
    def create_order(self,resolved):
        self.calls.append(resolved)
        line=resolved.line_items[0]
        return OrderSnapshot(
            provider="woocommerce",provider_order_id=501,provider_reference="woocommerce:order:501",
            order_number="501",status="pending",currency="KRW",customer_reference=None,
            line_items=(OrderLineItem(1,line.provider_product_id,line.provider_variation_id,None,
                                      "Product",line.quantity,Decimal("10000"),Decimal("10000"),Decimal("0")),),
            total=Decimal("10000"),total_tax=Decimal("0"),created_at=NOW,updated_at=NOW,
            provider_version="test",
        )

def product(*,id="123",source="woocommerce",stock=True,variants=()):
    return Product(id=id,name="P",slug="p",description="d",price=Decimal("10000"),currency="KRW",
                   category="C",in_stock=stock,source=source,variants=variants)

def command(product_id="123",variation_id=None):
    return OrderCreateCommand(
        customer_id=CUSTOMER,line_items=(OrderCreateLine(product_id,variation_id,1),),
        idempotency_key="order-001",correlation_id="corr-001",audit_reference="audit-001",requested_at=NOW)

def authority():
    return OrderCreateAuthority(CUSTOMER,SESSION,"auth-001",NOW,NOW+timedelta(minutes=5))

def test_command_uses_canonical_string_product_identity():
    value=command("mock-001")
    assert value.line_items[0].product_id=="mock-001"
    with pytest.raises(Exception,match="product_id"): OrderCreateLine(123)
    with pytest.raises(Exception,match="variation_id"): OrderCreateLine("123","bad variation")

def test_woocommerce_catalog_resolves_numeric_string_provider_identity():
    catalog=Catalog(product())
    resolved=ShoppingServiceOrderCatalogResolver(catalog).resolve(command())
    assert resolved.line_items[0].product_id=="123"
    assert resolved.line_items[0].provider_product_id==123
    assert resolved.line_items[0].provider_variation_id==0
    assert catalog.calls==["123"]

def test_variant_must_exist_be_available_and_provider_numeric():
    ok=ProductVariant("456","M","size",True)
    resolved=ShoppingServiceOrderCatalogResolver(Catalog(product(variants=(ok,)))).resolve(command("123","456"))
    assert resolved.line_items[0].provider_variation_id==456
    for variant in (ProductVariant("456","M","size",False),ProductVariant("sku-m","M","size",True)):
        with pytest.raises(OrderCreateCatalogResolutionError):
            ShoppingServiceOrderCatalogResolver(Catalog(product(variants=(variant,)))).resolve(command("123",variant.id))

@pytest.mark.parametrize(
    "factory,code",
    [
        (lambda: product(id="mock-001", source="mock"), "WRITE_SOURCE_UNAVAILABLE"),
        (lambda: product(id="123", stock=False), "OUT_OF_STOCK"),
    ],
)
def test_unwritable_catalog_product_fails_closed(factory,code):
    item=factory()
    with pytest.raises(OrderCreateCatalogResolutionError,match=code):
        ShoppingServiceOrderCatalogResolver(Catalog(item)).resolve(command(item.id))

def test_resolver_failure_is_prewrite_terminal_and_writer_is_not_called():
    catalog=Catalog(product(id="mock-001",source="mock"));writer=Writer()
    service=OrderCreateService(
        catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),order_creator=writer,
        coordinator=InMemoryOrderCreateOperationCoordinator())
    with pytest.raises(OrderCreateCatalogResolutionError): service.execute(command("mock-001"),authority())
    assert writer.calls==[]

def test_resolved_provider_identity_drives_snapshot_match():
    catalog=Catalog(product());writer=Writer()
    service=OrderCreateService(
        catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),order_creator=writer,
        coordinator=InMemoryOrderCreateOperationCoordinator())
    result=service.execute(command(),authority())
    assert result.snapshot.line_items[0].product_id==123
    assert writer.calls[0].line_items[0].product_id=="123"


def test_variable_product_requires_option_before_provider_write():
    writer=Writer()
    catalog=Catalog(product(variants=(ProductVariant("456","M","size",True),)))
    service=OrderCreateService(catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),
        order_creator=writer,coordinator=InMemoryOrderCreateOperationCoordinator())
    with pytest.raises(OrderCreateCatalogResolutionError,match="VARIATION_REQUIRED"):
        service.execute(command(),authority())
    assert writer.calls==[]
