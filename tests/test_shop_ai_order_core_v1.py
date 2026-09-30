from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import inspect

import pytest

from core.shopping.adapters.woocommerce_order_read import (
    WooCommerceOrderNormalizationError,
    normalize_woocommerce_order,
    normalize_woocommerce_orders,
)
from core.shopping.order_core.domain import (
    OrderContractError,
    OrderListQuery,
    OrderSnapshot,
)
from core.shopping.order_core.service import (
    OrderNotFoundError,
    OrderService,
)


def _raw_order(
    *,
    order_id=101,
    status="processing",
):
    return {
        "id": order_id,
        "number": str(order_id),
        "status": status,
        "currency": "USD",
        "customer_id": 55,
        "version": "9.0.0",
        "date_created_gmt": (
            "2026-10-01T00:00:00"
        ),
        "date_modified_gmt": (
            "2026-10-01T01:00:00"
        ),
        "total": "25.00",
        "total_tax": "2.00",
        "line_items": [
            {
                "id": 501,
                "product_id": 901,
                "variation_id": 0,
                "sku": "SKU-901",
                "name": "Test Product",
                "quantity": 2,
                "subtotal": "24.00",
                "total": "23.00",
                "total_tax": "2.00",
            }
        ],
    }


@dataclass
class FakeOrderReadAdapter:
    orders: tuple[OrderSnapshot, ...]

    def list_orders(
        self,
        query,
    ):
        result = self.orders

        if query.statuses:
            result = tuple(
                order
                for order in result
                if order.status
                in query.statuses
            )

        start = (
            (query.page - 1)
            * query.page_size
        )

        return result[
            start:
            start + query.page_size
        ]

    def read_order(
        self,
        provider_order_id,
    ):
        for order in self.orders:
            if (
                order.provider_order_id
                == provider_order_id
            ):
                return order

        return None


def test_woocommerce_order_normalization_is_bounded():
    result = normalize_woocommerce_order(
        _raw_order()
    )

    assert result.provider == "woocommerce"
    assert result.provider_order_id == 101
    assert result.status == "processing"
    assert result.currency == "USD"

    assert result.customer_reference == (
        "woocommerce:customer:55"
    )

    assert result.total == Decimal(
        "25.00"
    )

    assert len(result.line_items) == 1

    assert not hasattr(
        result,
        "raw",
    )

    assert not hasattr(
        result,
        "billing",
    )


def test_guest_order_has_no_customer_reference():
    raw = _raw_order()
    raw["customer_id"] = 0

    result = normalize_woocommerce_order(
        raw
    )

    assert result.customer_reference is None


def test_order_list_normalizer_rejects_non_list():
    with pytest.raises(
        WooCommerceOrderNormalizationError
    ):
        normalize_woocommerce_orders(
            {"orders": []}
        )


def test_order_normalizer_rejects_invalid_money():
    raw = _raw_order()
    raw["total"] = "-1"

    with pytest.raises(
        OrderContractError
    ):
        normalize_woocommerce_order(
            raw
        )


def test_order_query_is_bounded():
    with pytest.raises(
        OrderContractError
    ):
        OrderListQuery(
            page_size=101
        )

    query = OrderListQuery(
        statuses=("PROCESSING",),
    )

    assert query.statuses == (
        "processing",
    )


def test_order_service_lists_through_port():
    processing = normalize_woocommerce_order(
        _raw_order(
            order_id=101,
            status="processing",
        )
    )

    completed = normalize_woocommerce_order(
        _raw_order(
            order_id=102,
            status="completed",
        )
    )

    service = OrderService(
        FakeOrderReadAdapter(
            (
                processing,
                completed,
            )
        )
    )

    result = service.list_orders(
        OrderListQuery(
            statuses=("processing",),
        )
    )

    assert result == (
        processing,
    )


def test_order_service_reads_exact_order():
    order = normalize_woocommerce_order(
        _raw_order()
    )

    service = OrderService(
        FakeOrderReadAdapter(
            (order,)
        )
    )

    assert (
        service.read_order(101)
        == order
    )


def test_order_service_missing_order_fails_closed():
    service = OrderService(
        FakeOrderReadAdapter(())
    )

    with pytest.raises(
        OrderNotFoundError
    ):
        service.read_order(999)


def test_order_core_v1_has_no_network_or_write_boundary():
    import core.shopping.adapters.woocommerce_order_read as adapter

    source = inspect.getsource(
        adapter
    )

    forbidden = (
        "requests.",
        "httpx.",
        "HTTPSConnection",
        '"POST"',
        '"PUT"',
        '"PATCH"',
        '"DELETE"',
    )

    for token in forbidden:
        assert token not in source
