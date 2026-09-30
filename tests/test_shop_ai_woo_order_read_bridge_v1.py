from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import inspect

import pytest

from core.shopping.adapters.woocommerce_order_core_bridge import (
    WooCommerceExistingStackOrderReadBridge,
    WooCommerceOrderCoreBridgeError,
)
from core.shopping.order_core.domain import (
    OrderContractError,
    OrderLineItem,
    OrderListQuery,
    OrderSnapshot,
)


def _snapshot(
    order_id: int = 101,
) -> OrderSnapshot:
    return OrderSnapshot(
        provider="woocommerce",
        provider_order_id=order_id,
        provider_reference=(
            f"woocommerce:order:{order_id}"
        ),
        order_number=str(order_id),
        status="processing",
        currency="USD",
        customer_reference=(
            "woocommerce:customer:55"
        ),
        line_items=(
            OrderLineItem(
                provider_line_item_id=501,
                product_id=901,
                variation_id=0,
                sku="SKU-901",
                name="Test Product",
                quantity=1,
                subtotal=Decimal("12.00"),
                total=Decimal("12.00"),
                total_tax=Decimal("1.00"),
            ),
        ),
        total=Decimal("13.00"),
        total_tax=Decimal("1.00"),
        created_at=datetime(
            2026,
            10,
            1,
            tzinfo=timezone.utc,
        ),
        updated_at=datetime(
            2026,
            10,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        provider_version="test",
    )


class FakeExistingWooReadStack:
    def __init__(
        self,
        summary=None,
    ):
        self.summary = summary
        self.calls = []

    def get_order_summary(
        self,
        context,
        order_id,
    ):
        self.calls.append(
            (context, order_id)
        )

        return self.summary


def test_read_order_reuses_existing_stack():
    marker = object()

    existing = (
        FakeExistingWooReadStack(
            summary={
                "provider_id": 101,
            }
        )
    )

    projected = []

    def projector(summary):
        projected.append(summary)
        return _snapshot(101)

    bridge = (
        WooCommerceExistingStackOrderReadBridge(
            existing_read_stack=existing,
            read_context_provider=(
                lambda: marker
            ),
            order_summary_projector=projector,
        )
    )

    result = bridge.read_order(101)

    assert result == _snapshot(101)

    assert existing.calls == [
        (
            marker,
            "101",
        )
    ]

    assert projected == [
        {
            "provider_id": 101,
        }
    ]


def test_missing_order_returns_none():
    existing = (
        FakeExistingWooReadStack(
            summary=None
        )
    )

    bridge = (
        WooCommerceExistingStackOrderReadBridge(
            existing_read_stack=existing,
            read_context_provider=(
                lambda: object()
            ),
            order_summary_projector=(
                lambda value: _snapshot()
            ),
        )
    )

    assert bridge.read_order(999) is None

    assert len(existing.calls) == 1


def test_invalid_order_id_is_denied_before_existing_stack():
    existing = FakeExistingWooReadStack()

    context_calls = []

    bridge = (
        WooCommerceExistingStackOrderReadBridge(
            existing_read_stack=existing,
            read_context_provider=(
                lambda: context_calls.append(
                    True
                )
            ),
            order_summary_projector=(
                lambda value: _snapshot()
            ),
        )
    )

    with pytest.raises(
        OrderContractError
    ):
        bridge.read_order(0)

    assert existing.calls == []
    assert context_calls == []


def test_projector_order_id_mismatch_fails_closed():
    existing = (
        FakeExistingWooReadStack(
            summary={"id": 101}
        )
    )

    bridge = (
        WooCommerceExistingStackOrderReadBridge(
            existing_read_stack=existing,
            read_context_provider=(
                lambda: object()
            ),
            order_summary_projector=(
                lambda value: _snapshot(102)
            ),
        )
    )

    with pytest.raises(
        WooCommerceOrderCoreBridgeError
    ) as exc:
        bridge.read_order(101)

    assert (
        exc.value.reason_code
        == "PROJECTOR_ORDER_ID_MISMATCH"
    )


def test_list_orders_is_fail_closed_without_existing_contract():
    existing = FakeExistingWooReadStack()

    bridge = (
        WooCommerceExistingStackOrderReadBridge(
            existing_read_stack=existing,
            read_context_provider=(
                lambda: object()
            ),
            order_summary_projector=(
                lambda value: _snapshot()
            ),
        )
    )

    with pytest.raises(
        WooCommerceOrderCoreBridgeError
    ) as exc:
        bridge.list_orders(
            OrderListQuery()
        )

    assert (
        exc.value.reason_code
        == "LIST_ORDERS_NOT_SUPPORTED_BY_"
        "EXISTING_WOO_READ_STACK"
    )

    assert existing.calls == []


def test_bridge_owns_no_network_credentials_or_writes():
    import core.shopping.adapters.woocommerce_order_core_bridge as module

    source = inspect.getsource(
        module
    )

    forbidden = (
        "requests.",
        "httpx.",
        "HTTPSConnection",
        "consumer_key",
        "consumer_secret",
        '"POST"',
        '"PUT"',
        '"PATCH"',
        '"DELETE"',
    )

    for token in forbidden:
        assert token not in source

    bridge = (
        WooCommerceExistingStackOrderReadBridge(
            existing_read_stack=(
                FakeExistingWooReadStack()
            ),
            read_context_provider=(
                lambda: object()
            ),
            order_summary_projector=(
                lambda value: _snapshot()
            ),
        )
    )

    assert bridge.provider == "woocommerce"
    assert bridge.read_order_enabled is True
    assert bridge.list_orders_enabled is False
    assert bridge.owns_network_transport is False
    assert bridge.owns_credentials is False
    assert bridge.writes_enabled is False
