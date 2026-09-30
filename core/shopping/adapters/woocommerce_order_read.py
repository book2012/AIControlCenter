from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from core.shopping.order_core.domain import (
    OrderContractError,
    OrderLineItem,
    OrderSnapshot,
)


class WooCommerceOrderNormalizationError(
    OrderContractError
):
    pass


def _require_int(
    payload: Mapping[str, object],
    key: str,
    *,
    minimum: int = 0,
) -> int:
    value = payload.get(key)

    if (
        type(value) is not int
        or value < minimum
    ):
        raise WooCommerceOrderNormalizationError(
            f"{key}:INVALID"
        )

    return value


def _require_text(
    payload: Mapping[str, object],
    key: str,
) -> str:
    value = payload.get(key)

    if type(value) is not str:
        raise WooCommerceOrderNormalizationError(
            f"{key}:TYPE"
        )

    value = value.strip()

    if not value:
        raise WooCommerceOrderNormalizationError(
            f"{key}:EMPTY"
        )

    return value


def _decimal(
    payload: Mapping[str, object],
    key: str,
) -> Decimal:
    value = payload.get(key)

    if type(value) not in {
        str,
        int,
        float,
    }:
        raise WooCommerceOrderNormalizationError(
            f"{key}:TYPE"
        )

    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise WooCommerceOrderNormalizationError(
            f"{key}:DECIMAL"
        ) from exc

    if (
        not result.is_finite()
        or result < Decimal("0")
    ):
        raise WooCommerceOrderNormalizationError(
            f"{key}:INVALID"
        )

    return result


def _utc_datetime(
    payload: Mapping[str, object],
    key: str,
) -> datetime:
    raw = _require_text(
        payload,
        key,
    )

    normalized = (
        raw[:-1] + "+00:00"
        if raw.endswith("Z")
        else raw
    )

    try:
        value = datetime.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise WooCommerceOrderNormalizationError(
            f"{key}:DATETIME"
        ) from exc

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def _line_item(
    raw: object,
) -> OrderLineItem:
    if not isinstance(raw, Mapping):
        raise WooCommerceOrderNormalizationError(
            "line_item:TYPE"
        )

    sku = raw.get("sku")

    if sku is not None and type(sku) is not str:
        raise WooCommerceOrderNormalizationError(
            "sku:TYPE"
        )

    return OrderLineItem(
        provider_line_item_id=_require_int(
            raw,
            "id",
            minimum=1,
        ),
        product_id=_require_int(
            raw,
            "product_id",
        ),
        variation_id=_require_int(
            raw,
            "variation_id",
        ),
        sku=sku,
        name=_require_text(
            raw,
            "name",
        ),
        quantity=_require_int(
            raw,
            "quantity",
            minimum=1,
        ),
        subtotal=_decimal(
            raw,
            "subtotal",
        ),
        total=_decimal(
            raw,
            "total",
        ),
        total_tax=_decimal(
            raw,
            "total_tax",
        ),
    )


def normalize_woocommerce_order(
    payload: Mapping[str, object],
) -> OrderSnapshot:
    if not isinstance(payload, Mapping):
        raise WooCommerceOrderNormalizationError(
            "payload:TYPE"
        )

    provider_order_id = _require_int(
        payload,
        "id",
        minimum=1,
    )

    line_items_raw = payload.get(
        "line_items"
    )

    if type(line_items_raw) is not list:
        raise WooCommerceOrderNormalizationError(
            "line_items:TYPE"
        )

    customer_id = _require_int(
        payload,
        "customer_id",
    )

    customer_reference = (
        None
        if customer_id == 0
        else f"woocommerce:customer:{customer_id}"
    )

    return OrderSnapshot(
        provider="woocommerce",
        provider_order_id=provider_order_id,
        provider_reference=(
            f"woocommerce:order:{provider_order_id}"
        ),
        order_number=_require_text(
            payload,
            "number",
        ),
        status=_require_text(
            payload,
            "status",
        ),
        currency=_require_text(
            payload,
            "currency",
        ),
        customer_reference=customer_reference,
        line_items=tuple(
            _line_item(item)
            for item in line_items_raw
        ),
        total=_decimal(
            payload,
            "total",
        ),
        total_tax=_decimal(
            payload,
            "total_tax",
        ),
        created_at=_utc_datetime(
            payload,
            "date_created_gmt",
        ),
        updated_at=_utc_datetime(
            payload,
            "date_modified_gmt",
        ),
        provider_version=_require_text(
            payload,
            "version",
        ),
    )


def normalize_woocommerce_orders(
    payload: object,
) -> tuple[OrderSnapshot, ...]:
    if type(payload) is not list:
        raise WooCommerceOrderNormalizationError(
            "orders:TYPE"
        )

    return tuple(
        normalize_woocommerce_order(
            item
        )
        for item in payload
    )
