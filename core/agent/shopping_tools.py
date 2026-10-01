"""AIControlCenter-owned, read-only structured shopping tools."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal
import math
from types import MappingProxyType
from typing import Any, Protocol

from core.shopping.order_core.domain import OrderSnapshot
from core.shopping.order_core.service import OrderService


class ShoppingToolError(ValueError):
    """A deterministic tool name or argument was rejected."""


class ProductReadService(Protocol):
    def get_product(self, product_id: str) -> dict[str, Any]:
        ...

    def search_products(
        self,
        *,
        query: str | None,
        category: str | None,
        minimum_price: float | None,
        maximum_price: float | None,
        in_stock: bool | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        ...


TOOL_NAMES = (
    "shopping.order.read",
    "shopping.order.status",
    "shopping.product.get",
    "shopping.product.search",
)

WRITE_TOOL_CAPABILITIES = MappingProxyType(
    {
        "shopping.order.create": False,
        "shopping.order.update": False,
        "shopping.payment.*": False,
        "shopping.refund.*": False,
    }
)

_MAX_RESULT_DEPTH = 4
_MAX_RESULT_ITEMS = 100
_MAX_RESULT_STRING_LENGTH = 4096
_MAX_RESULT_KEY_LENGTH = 128

TOOL_CAPABILITY_MANIFEST = MappingProxyType(
    {
        "shopping.order.read": {
            "enabled": True,
            "read_only": True,
            "service": "OrderService",
        },
        "shopping.order.status": {
            "enabled": True,
            "read_only": True,
            "service": "OrderService",
        },
        "shopping.product.get": {
            "enabled": False,
            "read_only": True,
            "service": "ShoppingService",
        },
        "shopping.product.search": {
            "enabled": False,
            "read_only": True,
            "service": "ShoppingService",
        },
    }
)


def _validate_arguments(
    name: str,
    arguments: Mapping[str, Any],
) -> dict[str, Any]:
    if name not in TOOL_NAMES:
        raise ShoppingToolError("shopping_tool_unknown")
    if not isinstance(arguments, Mapping):
        raise ShoppingToolError("shopping_tool_arguments_mapping_required")
    value = dict(arguments)
    schemas = {
        "shopping.order.read": {"order_id"},
        "shopping.order.status": {"order_id"},
        "shopping.product.get": {"product_id"},
        "shopping.product.search": {
            "query",
            "category",
            "minimum_price",
            "maximum_price",
            "in_stock",
            "page",
            "page_size",
        },
    }
    if set(value) - schemas[name]:
        raise ShoppingToolError("shopping_tool_unknown_argument")
    required = {
        "shopping.order.read": {"order_id"},
        "shopping.order.status": {"order_id"},
        "shopping.product.get": {"product_id"},
        "shopping.product.search": set(),
    }[name]
    if required - set(value):
        raise ShoppingToolError("shopping_tool_required_argument_missing")
    if name.startswith("shopping.order"):
        order_id = value.get("order_id")
        if type(order_id) is not int or order_id <= 0:
            raise ShoppingToolError("shopping_tool_order_id_invalid")
    if name == "shopping.product.get":
        product_id = value["product_id"]
        if (
            type(product_id) is not str
            or not product_id
            or len(product_id) > 128
            or not product_id.isascii()
            or not all(char.isalnum() or char in "-_" for char in product_id)
        ):
            raise ShoppingToolError("shopping_tool_product_id_invalid")
    if name == "shopping.product.search":
        defaults = {
            "query": None,
            "category": None,
            "minimum_price": None,
            "maximum_price": None,
            "in_stock": None,
            "page": 1,
            "page_size": 20,
        }
        defaults.update(value)
        value = defaults
        if type(value["page"]) is not int or value["page"] < 1:
            raise ShoppingToolError("shopping_tool_page_invalid")
        if type(value["page_size"]) is not int or not 1 <= value["page_size"] <= 100:
            raise ShoppingToolError("shopping_tool_page_size_invalid")
        for field in ("query", "category"):
            if value[field] is not None:
                if (
                    type(value[field]) is not str
                    or len(value[field]) > 256
                ):
                    raise ShoppingToolError("shopping_tool_filter_invalid")
        for field in ("minimum_price", "maximum_price"):
            if value[field] is not None:
                if (
                    type(value[field]) not in {int, float}
                    or (
                        type(value[field]) is float
                        and not math.isfinite(value[field])
                    )
                    or value[field] < 0
                ):
                    raise ShoppingToolError("shopping_tool_price_invalid")
        if (
            value["minimum_price"] is not None
            and value["maximum_price"] is not None
            and value["minimum_price"] > value["maximum_price"]
        ):
            raise ShoppingToolError("shopping_tool_price_range_invalid")
        if value["in_stock"] is not None and type(value["in_stock"]) is not bool:
            raise ShoppingToolError("shopping_tool_stock_filter_invalid")
    return value


def _json_safe(value: Any, *, depth: int = 0) -> Any:
    if depth > _MAX_RESULT_DEPTH:
        raise ShoppingToolError("shopping_tool_result_too_deep")
    if value is None or type(value) in {int, bool}:
        return value
    if type(value) is str:
        if len(value) > _MAX_RESULT_STRING_LENGTH:
            raise ShoppingToolError("shopping_tool_result_too_large")
        return value
    if type(value) is float:
        if value != value or value in {float("inf"), float("-inf")}:
            raise ShoppingToolError("shopping_tool_result_invalid")
        return value
    if isinstance(value, Decimal):
        result = format(value, "f")
        if len(result) > _MAX_RESULT_STRING_LENGTH:
            raise ShoppingToolError("shopping_tool_result_too_large")
        return result
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ShoppingToolError("shopping_tool_result_timezone_required")
        result = value.isoformat()
        if len(result) > _MAX_RESULT_STRING_LENGTH:
            raise ShoppingToolError("shopping_tool_result_too_large")
        return result
    if isinstance(value, Mapping):
        if len(value) > _MAX_RESULT_ITEMS:
            raise ShoppingToolError("shopping_tool_result_too_large")
        result = {}
        for key, item in value.items():
            if (
                type(key) is not str
                or len(key) > _MAX_RESULT_KEY_LENGTH
            ):
                raise ShoppingToolError("shopping_tool_result_invalid")
            result[key] = _json_safe(item, depth=depth + 1)
        return result
    if isinstance(value, (list, tuple)):
        if len(value) > _MAX_RESULT_ITEMS:
            raise ShoppingToolError("shopping_tool_result_too_large")
        return [_json_safe(item, depth=depth + 1) for item in value]
    raise ShoppingToolError("shopping_tool_raw_result_rejected")


def _order_projection(snapshot: OrderSnapshot) -> dict[str, Any]:
    return _json_safe(
        {
            "provider": snapshot.provider,
            "provider_order_id": snapshot.provider_order_id,
            "provider_reference": snapshot.provider_reference,
            "order_number": snapshot.order_number,
            "status": snapshot.status,
            "currency": snapshot.currency,
            "customer_reference": snapshot.customer_reference,
            "line_items": [asdict(item) for item in snapshot.line_items],
            "total": snapshot.total,
            "total_tax": snapshot.total_tax,
            "created_at": snapshot.created_at,
            "updated_at": snapshot.updated_at,
            "provider_version": snapshot.provider_version,
        }
    )


class ShoppingToolFacade:
    """Structured facade with service-only dependencies and no provider knowledge."""

    def __init__(
        self,
        *,
        order_service: OrderService,
        product_service: ProductReadService | None = None,
    ) -> None:
        self._order_service = order_service
        self._product_service = product_service

    @property
    def registry(self) -> tuple[str, ...]:
        return TOOL_NAMES

    def manifest(self) -> dict[str, Any]:
        tools = {
            name: dict(TOOL_CAPABILITY_MANIFEST[name])
            for name in TOOL_NAMES
        }
        for name in (
            "shopping.product.get",
            "shopping.product.search",
        ):
            tools[name]["enabled"] = self._product_service is not None
        return {
            "tools": tools,
            "write_capabilities": dict(WRITE_TOOL_CAPABILITIES),
            "deterministic_registry": True,
            "unknown_tools_fail_closed": True,
        }

    def invoke(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        value = _validate_arguments(name, arguments)
        if name == "shopping.order.read":
            return {"tool": name, "result": _order_projection(self._order_service.read_order(value["order_id"]))}
        if name == "shopping.order.status":
            snapshot = self._order_service.read_order(value["order_id"])
            return {
                "tool": name,
                "result": {
                    "provider": snapshot.provider,
                    "provider_order_id": snapshot.provider_order_id,
                    "status": snapshot.status,
                },
            }
        if self._product_service is None:
            raise ShoppingToolError("shopping_tool_capability_unavailable")
        if name == "shopping.product.get":
            return {"tool": name, "result": _json_safe(self._product_service.get_product(value["product_id"]))}
        return {
            "tool": name,
            "result": _json_safe(self._product_service.search_products(**value)),
        }


__all__ = (
    "ShoppingToolError",
    "ShoppingToolFacade",
    "TOOL_CAPABILITY_MANIFEST",
    "TOOL_NAMES",
    "WRITE_TOOL_CAPABILITIES",
)
