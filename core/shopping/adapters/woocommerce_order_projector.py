"""Explicit projection from the canonical Woo order summary to Order Core."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from core.shopping.contracts.provisional import OrderSummary
from core.shopping.order_core.domain import OrderSnapshot


class WooCommerceOrderSummaryProjectionError(ValueError):
    """Raised when a canonical summary cannot safely become an order snapshot."""


_SUMMARY_FIELDS = frozenset(
    {
        "created_at",
        "item_count",
        "order_id",
        "status",
        "total",
        "updated_at",
    }
)


def _required_text(summary: Mapping[str, Any], field: str) -> str:
    value = summary.get(field)
    if type(value) is not str or not value.strip():
        raise WooCommerceOrderSummaryProjectionError(
            f"order_summary_{field}_invalid"
        )
    return value.strip()


def _provider_order_id(summary: OrderSummary) -> int:
    raw = _required_text(summary, "order_id")
    if not raw.isascii() or not raw.isdecimal() or raw.startswith("0"):
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_order_id_invalid"
        )
    value = int(raw)
    if value <= 0 or str(value) != raw:
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_order_id_invalid"
        )
    return value


def _utc_datetime(summary: OrderSummary, field: str) -> datetime:
    raw = _required_text(summary, field)
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise WooCommerceOrderSummaryProjectionError(
            f"order_summary_{field}_invalid"
        ) from None
    if value.tzinfo is None:
        raise WooCommerceOrderSummaryProjectionError(
            f"order_summary_{field}_timezone_required"
        )
    return value.astimezone(timezone.utc)


def _total(summary: OrderSummary, currency_minor_unit: int) -> tuple[Decimal, str]:
    value = summary.get("total")
    if not isinstance(value, Mapping) or set(value) != {"amount_minor", "currency"}:
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_total_invalid"
        )
    amount_minor = value.get("amount_minor")
    currency = value.get("currency")
    if (
        type(amount_minor) is not int
        or amount_minor < 0
        or type(currency) is not str
        or len(currency) != 3
        or not currency.isascii()
        or not currency.isalpha()
        or currency.upper() != currency
    ):
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_total_invalid"
        )
    if type(currency_minor_unit) is not int or not 0 <= currency_minor_unit <= 6:
        raise WooCommerceOrderSummaryProjectionError(
            "currency_minor_unit_invalid"
        )
    return Decimal(amount_minor).scaleb(-currency_minor_unit), currency


def project_woocommerce_order_summary(
    summary: OrderSummary,
    *,
    currency_minor_unit: int = 0,
) -> OrderSnapshot:
    """Project only canonical fields; provider payloads never cross this boundary.

    The canonical contract is a summary, so the Order Core snapshot deliberately
    has no line items and no customer contact data. The exact provider order ID is
    retained as both the binding and the bounded order number.
    """

    if not isinstance(summary, Mapping) or set(summary) != _SUMMARY_FIELDS:
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_incomplete"
        )

    provider_order_id = _provider_order_id(summary)
    item_count = summary.get("item_count")
    if type(item_count) is not int or item_count < 0:
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_item_count_invalid"
        )
    total, currency = _total(summary, currency_minor_unit)
    status = _required_text(summary, "status")
    created_at = _utc_datetime(summary, "created_at")
    updated_at = _utc_datetime(summary, "updated_at")
    if updated_at < created_at:
        raise WooCommerceOrderSummaryProjectionError(
            "order_summary_timestamp_order_invalid"
        )

    return OrderSnapshot(
        provider="woocommerce",
        provider_order_id=provider_order_id,
        provider_reference=f"woocommerce:order:{provider_order_id}",
        order_number=str(provider_order_id),
        status=status,
        currency=currency,
        customer_reference=None,
        line_items=(),
        total=total,
        total_tax=Decimal("0"),
        created_at=created_at,
        updated_at=updated_at,
        provider_version="order-summary-v1",
    )


__all__ = (
    "WooCommerceOrderSummaryProjectionError",
    "project_woocommerce_order_summary",
)
