from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Protocol


class ShoppingManagementReadModelError(ValueError):
    """Raised when a Shopping management source violates its contract."""


class ShoppingManagementSource(Protocol):
    """Read-only application boundary consumed by the management projection."""

    def health(self) -> Mapping[str, Any]:
        ...

    def readiness(self) -> Mapping[str, Any]:
        ...

    def capabilities(self) -> Mapping[str, Any]:
        ...

    def integration_status(self) -> Mapping[str, Any]:
        ...

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> Mapping[str, Any]:
        ...


_PRODUCT_FIELDS = (
    "product_id",
    "sku",
    "name",
    "description",
    "price",
    "inventory_quantity",
    "in_stock",
    "image_urls",
    "url",
    "updated_at",
)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}

        for key, item in value.items():
            if not isinstance(key, str):
                raise ShoppingManagementReadModelError(
                    "shopping.management.mapping_key_string_required"
                )

            frozen[key] = _freeze(item)

        return MappingProxyType(frozen)

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return tuple(_freeze(item) for item in value)

    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _thaw(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [_thaw(item) for item in value]

    return value


def _require_mapping(
    name: str,
    value: Any,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ShoppingManagementReadModelError(
            f"shopping.management.{name}_mapping_required"
        )

    if not all(isinstance(key, str) for key in value):
        raise ShoppingManagementReadModelError(
            f"shopping.management.{name}_string_keys_required"
        )

    return value


def _optional_non_negative_integer(
    name: str,
    value: Any,
) -> int | None:
    if value is None:
        return None

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise ShoppingManagementReadModelError(
            f"shopping.management.{name}_non_negative_integer_required"
        )

    return value


def _project_product(
    value: Any,
) -> Mapping[str, Any]:
    product = _require_mapping("product", value)

    product_id = product.get("product_id")
    name = product.get("name")
    in_stock = product.get("in_stock")
    inventory_quantity = product.get("inventory_quantity")
    image_urls = product.get("image_urls", [])

    if not isinstance(product_id, str) or not product_id.strip():
        raise ShoppingManagementReadModelError(
            "shopping.management.product_id_required"
        )

    if not isinstance(name, str) or not name.strip():
        raise ShoppingManagementReadModelError(
            "shopping.management.product_name_required"
        )

    if not isinstance(in_stock, bool):
        raise ShoppingManagementReadModelError(
            "shopping.management.product_in_stock_boolean_required"
        )

    _optional_non_negative_integer(
        "product_inventory_quantity",
        inventory_quantity,
    )

    if not isinstance(image_urls, Sequence) or isinstance(
        image_urls,
        (str, bytes, bytearray),
    ):
        raise ShoppingManagementReadModelError(
            "shopping.management.product_image_urls_sequence_required"
        )

    if not all(isinstance(item, str) for item in image_urls):
        raise ShoppingManagementReadModelError(
            "shopping.management.product_image_url_string_required"
        )

    projected = {
        field: product.get(field)
        for field in _PRODUCT_FIELDS
    }

    projected["product_id"] = product_id.strip()
    projected["name"] = name.strip()
    projected["image_urls"] = list(image_urls)

    return _freeze(projected)


@dataclass(frozen=True, slots=True)
class ShoppingManagementReadModel:
    status: str
    summary: Mapping[str, Any]
    products: tuple[Mapping[str, Any], ...]
    health: Mapping[str, Any]
    readiness: Mapping[str, Any]
    capabilities: Mapping[str, Any]
    integration: Mapping[str, Any]

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "mode": "READ_ONLY",
            "status": self.status,
            "summary": _thaw(self.summary),
            "products": [
                _thaw(product)
                for product in self.products
            ],
            "health": _thaw(self.health),
            "readiness": _thaw(self.readiness),
            "capabilities": _thaw(self.capabilities),
            "integration": _thaw(self.integration),
        }


def build_shopping_management_read_model(
    source: ShoppingManagementSource,
    *,
    page: int = 1,
    page_size: int = 25,
) -> ShoppingManagementReadModel:
    if (
        not isinstance(page, int)
        or isinstance(page, bool)
        or page < 1
    ):
        raise ShoppingManagementReadModelError(
            "shopping.management.page_positive_integer_required"
        )

    if (
        not isinstance(page_size, int)
        or isinstance(page_size, bool)
        or not 1 <= page_size <= 100
    ):
        raise ShoppingManagementReadModelError(
            "shopping.management.page_size_out_of_range"
        )

    health = _require_mapping(
        "health",
        source.health(),
    )
    readiness = _require_mapping(
        "readiness",
        source.readiness(),
    )
    capabilities = _require_mapping(
        "capabilities",
        source.capabilities(),
    )
    integration = _require_mapping(
        "integration",
        source.integration_status(),
    )
    catalog = _require_mapping(
        "catalog",
        source.list_products(
            page=page,
            page_size=page_size,
        ),
    )

    raw_items = catalog.get("items")

    if not isinstance(raw_items, Sequence) or isinstance(
        raw_items,
        (str, bytes, bytearray),
    ):
        raise ShoppingManagementReadModelError(
            "shopping.management.catalog_items_sequence_required"
        )

    products = tuple(
        sorted(
            (
                _project_product(item)
                for item in raw_items
            ),
            key=lambda item: (
                str(item["name"]).casefold(),
                str(item["product_id"]),
            ),
        )
    )

    total = catalog.get("total", len(products))
    catalog_total = _optional_non_negative_integer(
        "catalog_total",
        total,
    )

    if catalog_total is None:
        catalog_total = len(products)

    in_stock_count = sum(
        1
        for product in products
        if product["in_stock"] is True
    )

    inventory_quantity_total = sum(
        quantity
        for product in products
        if isinstance(
            (
                quantity := product[
                    "inventory_quantity"
                ]
            ),
            int,
        )
        and not isinstance(quantity, bool)
    )

    health_status = str(
        health.get("status", "UNKNOWN")
    ).upper()
    ready = readiness.get("ready") is True

    status = (
        "READY"
        if ready
        and health_status in {"ONLINE", "READY"}
        else "DEGRADED"
    )

    summary = {
        "catalog_total": catalog_total,
        "page": page,
        "page_size": page_size,
        "page_items": len(products),
        "in_stock": in_stock_count,
        "out_of_stock": len(products) - in_stock_count,
        "inventory_quantity_total": inventory_quantity_total,
    }

    return ShoppingManagementReadModel(
        status=status,
        summary=_freeze(summary),
        products=products,
        health=_freeze(health),
        readiness=_freeze(readiness),
        capabilities=_freeze(capabilities),
        integration=_freeze(integration),
    )


def management_read_model_contract_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "application_boundary": "ShoppingManagementSource",
        "dashboard_registration": False,
        "deterministic_product_order": [
            "name_casefold",
            "product_id",
        ],
        "direct_woocommerce_dependency": False,
        "external_network": False,
        "local_product_truth": False,
        "persistence": False,
        "production_registration": False,
        "product_fields": list(_PRODUCT_FIELDS),
        "read_only": True,
        "source_calls": [
            "health",
            "readiness",
            "capabilities",
            "integration_status",
            "list_products",
        ],
        "write_methods_allowed": False,
    }


__all__ = (
    "ShoppingManagementReadModel",
    "ShoppingManagementReadModelError",
    "ShoppingManagementSource",
    "build_shopping_management_read_model",
    "management_read_model_contract_manifest",
)
