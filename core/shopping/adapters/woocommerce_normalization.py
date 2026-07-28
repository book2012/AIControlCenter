from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol

from core.shopping.adapters.woocommerce_commerce_read import WooCommerceCommerceReadAdapter, WooCommerceCommerceReadError
from core.shopping.contracts.provisional import OrderSummary, PageRequest, ProductSnapshot, ProductSnapshotPage
from core.shopping.contracts.schema_validation import load_canonical_schema_catalog, validate_instance

PRODUCT_SCHEMA_ID = "urn:aicontrolcenter:shopping:contract:v1:product-snapshot"
PRODUCT_PAGE_SCHEMA_ID = "urn:aicontrolcenter:shopping:contract:v1:product-snapshot-page"
ORDER_SCHEMA_ID = "urn:aicontrolcenter:shopping:contract:v1:order-summary"
CURSOR_PREFIX = "wc-page:"

class WooCommerceRawReadPort(Protocol):
    def get_product_raw(self, product_id: str) -> dict[str, Any] | None:
        ...

    def list_products_raw(self, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
        ...

    def get_order_summary_raw(self, order_id: str) -> dict[str, Any] | None:
        ...

class _RawCatalogFacade:
    def __init__(self, vendor: WooCommerceRawReadPort) -> None:
        self._vendor = vendor

    def get_product(self, product_id: str) -> Any | None:
        return self._vendor.get_product_raw(product_id)

    def list_products(self, page: int, page_size: int) -> tuple[list[Any], int]:
        return self._vendor.list_products_raw(page, page_size)

class _RawOrderFacade:
    def __init__(self, vendor: WooCommerceRawReadPort) -> None:
        self._vendor = vendor

    def get_order_summary(self, order_id: str) -> Any | None:
        return self._vendor.get_order_summary_raw(order_id)

class WooCommerceCanonicalNormalizer:
    def __init__(
        self,
        *,
        currency_code: str,
        currency_minor_unit: int,
        schema_root: Path | None = None,
    ) -> None:
        currency = currency_code.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise WooCommerceCommerceReadError("currency_configuration_invalid")
        if isinstance(currency_minor_unit, bool) or not isinstance(currency_minor_unit, int):
            raise WooCommerceCommerceReadError("currency_configuration_invalid")
        if currency_minor_unit < 0 or currency_minor_unit > 6:
            raise WooCommerceCommerceReadError("currency_configuration_invalid")
        self._currency = currency
        self._minor_unit = currency_minor_unit
        self._catalog = load_canonical_schema_catalog(schema_root=schema_root)

    def _validate(self, schema_id: str, value: Any) -> None:
        result = validate_instance(catalog=self._catalog, schema_id=schema_id, instance=value)
        if result.accepted is not True:
            raise ValueError("canonical validation failed")

    def decode_cursor(self, value: Any) -> int:
        if value is None:
            return 1
        if not isinstance(value, str) or not value.startswith(CURSOR_PREFIX):
            raise ValueError("invalid cursor")
        suffix = value.removeprefix(CURSOR_PREFIX)
        if not suffix.isdigit() or int(suffix) <= 0:
            raise ValueError("invalid cursor")
        return int(suffix)

    def _utc(self, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("invalid timestamp")
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.isoformat(timespec="seconds").replace("+00:00", "Z")

    def _money(self, value: Any, payload_currency: Any = None) -> dict[str, Any]:
        if payload_currency is not None:
            actual = str(payload_currency).strip().upper()
            if actual != self._currency:
                raise ValueError("currency mismatch")
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, ValueError) as error:
            raise ValueError("invalid money") from error
        if not amount.is_finite() or amount < 0:
            raise ValueError("invalid money")
        scaled = amount * (Decimal(10) ** self._minor_unit)
        integral = scaled.to_integral_value()
        if scaled != integral:
            raise ValueError("money precision invalid")
        return {"amount_minor": int(integral), "currency": self._currency}

    def normalize_product(self, payload: Any) -> ProductSnapshot:
        if not isinstance(payload, Mapping):
            raise ValueError("invalid product payload")
        stock_status = payload.get("stock_status")
        if not isinstance(stock_status, str) or not stock_status.strip():
            raise ValueError("invalid stock status")
        quantity = payload.get("stock_quantity")
        if quantity is not None:
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
                raise ValueError("invalid inventory quantity")
        value = {
            "product_id": str(payload["id"]),
            "name": str(payload.get("name", "")).strip(),
            "price": self._money(payload.get("price")),
            "inventory_quantity": quantity,
            "in_stock": stock_status == "instock",
            "updated_at": self._utc(payload.get("date_modified_gmt")),
        }
        self._validate(PRODUCT_SCHEMA_ID, value)
        return value

    def normalize_page(
        self,
        items: Sequence[Any],
        total: int,
        page_request: PageRequest,
        page_number: int,
    ) -> ProductSnapshotPage:
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("invalid total")
        normalized = [self.normalize_product(item) for item in items]
        limit = page_request["limit"]
        has_more = page_number * limit < total
        value = {
            "has_more": has_more,
            "items": normalized,
            "next_cursor": CURSOR_PREFIX + str(page_number + 1) if has_more else None,
        }
        self._validate(PRODUCT_PAGE_SCHEMA_ID, value)
        return value

    def normalize_order(self, payload: Any) -> OrderSummary:
        if not isinstance(payload, Mapping):
            raise ValueError("invalid order payload")
        line_items = payload.get("line_items")
        if not isinstance(line_items, list):
            raise ValueError("invalid line items")
        item_count = 0
        for item in line_items:
            if not isinstance(item, Mapping):
                raise ValueError("invalid line item")
            quantity = item.get("quantity")
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
                raise ValueError("invalid line quantity")
            item_count += quantity
        value = {
            "order_id": str(payload["id"]),
            "status": str(payload.get("status", "")).strip(),
            "total": self._money(payload.get("total"), payload.get("currency")),
            "item_count": item_count,
            "created_at": self._utc(payload.get("date_created_gmt")),
            "updated_at": self._utc(payload.get("date_modified_gmt")),
        }
        self._validate(ORDER_SCHEMA_ID, value)
        return value

def build_woocommerce_commerce_read_adapter(
    *,
    vendor: WooCommerceRawReadPort,
    currency_code: str,
    currency_minor_unit: int,
    schema_root: Path | None = None,
) -> WooCommerceCommerceReadAdapter:
    normalizer = WooCommerceCanonicalNormalizer(
        currency_code=currency_code,
        currency_minor_unit=currency_minor_unit,
        schema_root=schema_root,
    )
    return WooCommerceCommerceReadAdapter(
        catalog=_RawCatalogFacade(vendor),
        order_reader=_RawOrderFacade(vendor),
        cursor_page_decoder=normalizer.decode_cursor,
        product_normalizer=normalizer.normalize_product,
        product_page_normalizer=normalizer.normalize_page,
        order_summary_normalizer=normalizer.normalize_order,
    )
