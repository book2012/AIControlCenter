from __future__ import annotations

from dataclasses import fields
from datetime import datetime, timezone
from decimal import Decimal
import inspect

import pytest

from core.shopping.order_core import (
    InMemoryOrderCreateOperationCoordinator,
    OrderCreateAuthority,
    OrderCreateAmbiguousFailure,
    OrderCreateCommand,
    OrderCreateDefinitiveFailure,
    OrderCreateContractError,
    OrderCreateLine,
    OrderCreateOperationConflict,
    OrderCreateOperationTerminalFailure,
    OrderCreateOperationUnknownOutcome,
    OrderCreateService,
    OrderLineItem,
    OrderSnapshot,
)


CUSTOMER = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
SESSION = "AG-SES-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
NOW = datetime(2026, 10, 5, 6, 0, tzinfo=timezone.utc)


def command(*, quantity: int = 1, key: str = "order-create-001") -> OrderCreateCommand:
    return OrderCreateCommand(
        customer_id=CUSTOMER,
        line_items=(OrderCreateLine(product_id="mock-001", quantity=quantity),),
        idempotency_key=key,
        correlation_id="corr-order-001",
        audit_reference="audit-order-001",
        requested_at=NOW,
    )


def authority() -> OrderCreateAuthority:
    return OrderCreateAuthority(
        customer_id=CUSTOMER, session_id=SESSION, authorization_reference="auth-order-001",
        authorized_at=NOW, expires_at=NOW.replace(hour=7),
    )



def test_command_digest_is_customer_intent_not_server_observability_evidence():
    first=command(key="stable-key")
    second=OrderCreateCommand(
        customer_id=CUSTOMER,line_items=first.line_items,idempotency_key="stable-key",
        correlation_id="corr-order-002",audit_reference="audit-order-002",
        requested_at=NOW.replace(minute=1),
    )
    assert first.command_digest==second.command_digest

def snapshot(order_id: int = 101, *, product_id: int = 901, quantity: int = 1) -> OrderSnapshot:
    return OrderSnapshot(
        provider="woocommerce",
        provider_order_id=order_id,
        provider_reference=f"woocommerce:order:{order_id}",
        order_number=str(order_id),
        status="pending",
        currency="KRW",
        customer_reference=None,
        line_items=(
            OrderLineItem(
                provider_line_item_id=501,
                product_id=product_id,
                variation_id=0,
                sku=None,
                name="Canonical Product",
                quantity=quantity,
                subtotal=Decimal("10000"),
                total=Decimal("10000"),
                total_tax=Decimal("0"),
            ),
        ),
        total=Decimal("10000"),
        total_tax=Decimal("0"),
        created_at=NOW,
        updated_at=NOW,
        provider_version="test",
    )


class FakeResolved:
    def __init__(self, quantity=1):
        self.customer_id=CUSTOMER
        self.line_items=(type("Line",(),{
            "product_id":"mock-001","variation_id":None,
            "provider_product_id":901,"provider_variation_id":0,"quantity":quantity,
        })(),)


class FakeResolver:
    def __init__(self): self.calls=[]
    def resolve(self,value):
        self.calls.append(value)
        return FakeResolved(value.line_items[0].quantity)


class FakeCreator:
    def __init__(self, *, result=None, error=None):
        self.result = result if result is not None else snapshot()
        self.error = error
        self.calls = []

    def create_order(self, value):
        self.calls.append(value)
        if self.error is not None:
            raise self.error
        return self.result


def test_create_command_is_closed_and_has_no_client_commerce_authority():
    names = {field.name for field in fields(OrderCreateCommand)}
    assert names == {
        "customer_id",
        "line_items",
        "idempotency_key",
        "correlation_id",
        "audit_reference",
        "requested_at",
    }
    line_names = {field.name for field in fields(OrderCreateLine)}
    assert line_names == {"product_id", "variation_id", "quantity"}
    forbidden = {
        "price", "subtotal", "total", "currency", "coupon", "discount",
        "email", "phone", "billing", "shipping", "address", "payment",
    }
    assert forbidden.isdisjoint(names | line_names)


def test_create_command_validates_customer_lines_and_utc_time():
    valid = command()
    assert valid.customer_id == CUSTOMER
    assert len(valid.command_digest) == 64
    with pytest.raises(OrderCreateContractError, match="customer_id:INVALID"):
        OrderCreateCommand(
            customer_id="customer-1", line_items=valid.line_items,
            idempotency_key="key", correlation_id="corr",
            audit_reference="audit", requested_at=NOW,
        )
    with pytest.raises(OrderCreateContractError, match="line_items:BOUNDS"):
        OrderCreateCommand(
            customer_id=CUSTOMER, line_items=(), idempotency_key="key",
            correlation_id="corr", audit_reference="audit", requested_at=NOW,
        )
    with pytest.raises(OrderCreateContractError, match="requested_at:UTC_REQUIRED"):
        OrderCreateCommand(
            customer_id=CUSTOMER, line_items=valid.line_items, idempotency_key="key",
            correlation_id="corr", audit_reference="audit",
            requested_at=datetime(2026, 10, 5, 6, 0),
        )


def test_create_command_rejects_duplicate_product_identity_and_bad_keys():
    with pytest.raises(OrderCreateContractError, match="line_items:DUPLICATE_PRODUCT"):
        OrderCreateCommand(
            customer_id=CUSTOMER,
            line_items=(
                OrderCreateLine("mock-001", None, 1),
                OrderCreateLine("mock-001", None, 2),
            ),
            idempotency_key="key", correlation_id="corr",
            audit_reference="audit", requested_at=NOW,
        )
    with pytest.raises(OrderCreateContractError, match="idempotency_key:FORMAT"):
        OrderCreateCommand(
            customer_id=CUSTOMER, line_items=(OrderCreateLine("mock-001"),),
            idempotency_key="bad key", correlation_id="corr",
            audit_reference="audit", requested_at=NOW,
        )


@pytest.mark.parametrize("value", [0, -1, 1001, True])
def test_create_line_rejects_invalid_quantity(value):
    with pytest.raises(OrderCreateContractError, match="quantity:INVALID"):
        OrderCreateLine(product_id="mock-001", quantity=value)


def test_service_claims_before_writer_and_replays_without_second_write():
    creator = FakeCreator()
    coordinator = InMemoryOrderCreateOperationCoordinator()
    service = OrderCreateService(catalog_resolver=FakeResolver(), order_creator=creator, coordinator=coordinator)
    first = service.execute(command(), authority())
    second = service.execute(command(), authority())
    assert len(creator.calls) == 1
    assert first.snapshot.provider_order_id == 101
    assert first.idempotent_replay is False
    assert second.idempotent_replay is True
    assert second.command_digest == first.command_digest


def test_same_idempotency_key_with_different_command_fails_before_writer():
    creator = FakeCreator()
    service = OrderCreateService(
        catalog_resolver=FakeResolver(), order_creator=creator,
        coordinator=InMemoryOrderCreateOperationCoordinator(),
    )
    service.execute(command(quantity=1, key="same-key"), authority())
    with pytest.raises(OrderCreateOperationConflict):
        service.execute(command(quantity=2, key="same-key"), authority())
    assert len(creator.calls) == 1


def test_definitive_provider_failure_is_terminal_and_never_auto_retried():
    creator = FakeCreator(error=OrderCreateDefinitiveFailure("PROVIDER_REJECTED"))
    service = OrderCreateService(
        catalog_resolver=FakeResolver(), order_creator=creator, coordinator=InMemoryOrderCreateOperationCoordinator(),
    )
    with pytest.raises(OrderCreateDefinitiveFailure, match="PROVIDER_REJECTED"):
        service.execute(command(), authority())
    with pytest.raises(OrderCreateOperationTerminalFailure):
        service.execute(command(), authority())
    assert len(creator.calls) == 1


def test_ambiguous_provider_failure_is_quarantined_and_never_auto_retried():
    creator = FakeCreator(error=OrderCreateAmbiguousFailure("TIMEOUT_UNKNOWN"))
    service = OrderCreateService(
        catalog_resolver=FakeResolver(), order_creator=creator, coordinator=InMemoryOrderCreateOperationCoordinator(),
    )
    with pytest.raises(OrderCreateAmbiguousFailure, match="TIMEOUT_UNKNOWN"):
        service.execute(command(), authority())
    with pytest.raises(OrderCreateOperationUnknownOutcome):
        service.execute(command(), authority())
    assert len(creator.calls) == 1


def test_provider_snapshot_must_match_requested_line_identity_and_quantity():
    for returned in (
        snapshot(product_id=902),
        snapshot(quantity=2),
    ):
        creator = FakeCreator(result=returned)
        service = OrderCreateService(
            catalog_resolver=FakeResolver(), order_creator=creator,
            coordinator=InMemoryOrderCreateOperationCoordinator(),
        )
        with pytest.raises(OrderCreateContractError, match="order_creator:LINE_ITEMS_MISMATCH"):
            service.execute(command(), authority())
        with pytest.raises(OrderCreateOperationUnknownOutcome):
            service.execute(command(), authority())
        assert len(creator.calls) == 1

def test_invalid_provider_result_fails_terminally():
    creator = FakeCreator(result={"id": 101})
    service = OrderCreateService(
        catalog_resolver=FakeResolver(), order_creator=creator,
        coordinator=InMemoryOrderCreateOperationCoordinator(),
    )
    with pytest.raises(OrderCreateContractError, match="order_creator:INVALID_RESULT"):
        service.execute(command(), authority())
    with pytest.raises(OrderCreateOperationUnknownOutcome):
        service.execute(command(), authority())
    assert len(creator.calls) == 1


def test_001a_has_no_network_credentials_routes_or_provider_writer():
    import core.shopping.order_core.create as module

    source = inspect.getsource(module)
    forbidden = (
        "requests.",
        "httpx.",
        "HTTPSConnection",
        "consumer_key",
        "consumer_secret",
        '"/wp-json/wc/v3/orders"',
        '"POST"',
        '"PUT"',
        '"PATCH"',
        '"DELETE"',
    )
    for token in forbidden:
        assert token not in source
    assert InMemoryOrderCreateOperationCoordinator.production_safe is False
