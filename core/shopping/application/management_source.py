from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from decimal import Decimal
from typing import Any, Protocol


class ShoppingManagementSourceAdapterError(ValueError):
    """Raised when the Shopping service violates the adapter contract."""


class LegacyShoppingService(Protocol):
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


def _mapping(
    name: str,
    value: Any,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ShoppingManagementSourceAdapterError(
            f"shopping.management_source.{name}_mapping_required"
        )

    if not all(isinstance(key, str) for key in value):
        raise ShoppingManagementSourceAdapterError(
            f"shopping.management_source.{name}_string_keys_required"
        )

    return value


def _optional_string(
    name: str,
    value: Any,
) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise ShoppingManagementSourceAdapterError(
            f"shopping.management_source.{name}_string_required"
        )

    value = value.strip()

    return value or None


def _required_string(
    name: str,
    value: Any,
) -> str:
    normalized = _optional_string(name, value)

    if normalized is None:
        raise ShoppingManagementSourceAdapterError(
            f"shopping.management_source.{name}_required"
        )

    return normalized


def _inventory_quantity(
    value: Any,
) -> int | None:
    if value is None:
        return None

    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or value < 0
    ):
        raise ShoppingManagementSourceAdapterError(
            "shopping.management_source."
            "inventory_quantity_non_negative_integer_required"
        )

    return value


def _json_price(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, bool):
        raise ShoppingManagementSourceAdapterError(
            "shopping.management_source.price_number_required"
        )

    if value is None or isinstance(
        value,
        (int, float, str),
    ):
        return value

    raise ShoppingManagementSourceAdapterError(
        "shopping.management_source.price_json_value_required"
    )


def _image_urls(product: Mapping[str, Any]) -> list[str]:
    value = product.get("image_urls")

    if value is not None:
        if not isinstance(value, Sequence) or isinstance(
            value,
            (str, bytes, bytearray),
        ):
            raise ShoppingManagementSourceAdapterError(
                "shopping.management_source."
                "image_urls_sequence_required"
            )

        if not all(isinstance(item, str) for item in value):
            raise ShoppingManagementSourceAdapterError(
                "shopping.management_source."
                "image_url_string_required"
            )

        return [
            item.strip()
            for item in value
            if item.strip()
        ]

    legacy = product.get("image_url")

    if legacy is None:
        return []

    if not isinstance(legacy, str):
        raise ShoppingManagementSourceAdapterError(
            "shopping.management_source."
            "legacy_image_url_string_required"
        )

    legacy = legacy.strip()

    return [legacy] if legacy else []


def normalize_management_product(
    value: Any,
) -> dict[str, Any]:
    product = _mapping("product", value)

    product_id = product.get("product_id")

    if product_id is None:
        product_id = product.get("id")

    in_stock = product.get("in_stock")

    if not isinstance(in_stock, bool):
        raise ShoppingManagementSourceAdapterError(
            "shopping.management_source."
            "product_in_stock_boolean_required"
        )

    description = product.get("description", "")

    if description is None:
        description = ""

    if not isinstance(description, str):
        raise ShoppingManagementSourceAdapterError(
            "shopping.management_source."
            "product_description_string_required"
        )

    return {
        "product_id": _required_string(
            "product_id",
            product_id,
        ),
        "sku": _optional_string(
            "product_sku",
            product.get("sku"),
        ),
        "name": _required_string(
            "product_name",
            product.get("name"),
        ),
        "description": description,
        "price": _json_price(product.get("price")),
        "inventory_quantity": _inventory_quantity(
            product.get("inventory_quantity")
        ),
        "in_stock": in_stock,
        "image_urls": _image_urls(product),
        "url": _optional_string(
            "product_url",
            product.get("url"),
        ),
        "updated_at": _optional_string(
            "product_updated_at",
            product.get("updated_at"),
        ),
    }


class ShoppingServiceManagementSourceAdapter:
    """Adapts the current ShoppingService to the canonical read model."""

    def __init__(
        self,
        service: LegacyShoppingService,
    ) -> None:
        self._service = service

    def health(self) -> Mapping[str, Any]:
        return deepcopy(
            dict(
                _mapping(
                    "health",
                    self._service.health(),
                )
            )
        )

    def readiness(self) -> Mapping[str, Any]:
        return deepcopy(
            dict(
                _mapping(
                    "readiness",
                    self._service.readiness(),
                )
            )
        )

    def capabilities(self) -> Mapping[str, Any]:
        return deepcopy(
            dict(
                _mapping(
                    "capabilities",
                    self._service.capabilities(),
                )
            )
        )

    def integration_status(self) -> Mapping[str, Any]:
        return deepcopy(
            dict(
                _mapping(
                    "integration",
                    self._service.integration_status(),
                )
            )
        )

    def list_products(
        self,
        page: int,
        page_size: int,
    ) -> Mapping[str, Any]:
        catalog = _mapping(
            "catalog",
            self._service.list_products(
                page=page,
                page_size=page_size,
            ),
        )

        items = catalog.get("items")

        if not isinstance(items, Sequence) or isinstance(
            items,
            (str, bytes, bytearray),
        ):
            raise ShoppingManagementSourceAdapterError(
                "shopping.management_source."
                "catalog_items_sequence_required"
            )

        total = catalog.get("total", len(items))

        if (
            not isinstance(total, int)
            or isinstance(total, bool)
            or total < 0
        ):
            raise ShoppingManagementSourceAdapterError(
                "shopping.management_source."
                "catalog_total_non_negative_integer_required"
            )

        return {
            "items": [
                normalize_management_product(item)
                for item in items
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        }


def management_source_adapter_contract_manifest(
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "adapter_role": (
            "legacy_shopping_service_to_management_contract"
        ),
        "canonical_contract_weakened": False,
        "direct_woocommerce_dependency": False,
        "external_network_client": False,
        "external_read_delegated_to_service": True,
        "legacy_id_mapping": "id_to_product_id",
        "legacy_image_mapping": (
            "image_url_to_image_urls"
        ),
        "local_product_truth": False,
        "persistence": False,
        "price_decimal_mapping": (
            "decimal_to_json_number"
        ),
        "read_only": True,
        "synthetic_inventory_allowed": False,
        "synthetic_sku_allowed": False,
        "synthetic_updated_at_allowed": False,
        "synthetic_url_allowed": False,
        "write_methods_allowed": False,
    }


__all__ = (
    "LegacyShoppingService",
    "ShoppingManagementSourceAdapterError",
    "ShoppingServiceManagementSourceAdapter",
    "management_source_adapter_contract_manifest",
    "normalize_management_product",
)
