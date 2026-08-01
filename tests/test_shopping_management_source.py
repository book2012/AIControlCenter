from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest

from core.shopping.application.management_read_model import (
    build_shopping_management_read_model,
)
from core.shopping.application.management_source import (
    ShoppingManagementSourceAdapterError,
    ShoppingServiceManagementSourceAdapter,
    management_source_adapter_contract_manifest,
    normalize_management_product,
)


class FakeLegacyShoppingService:
    def __init__(self) -> None:
        self.items = [
            {
                "id": "legacy-2",
                "name": "Zulu Dress",
                "slug": "zulu-dress",
                "description": "Dress",
                "price": Decimal("29.90"),
                "currency": "USD",
                "category": "dress",
                "in_stock": False,
                "source": "mock",
                "image_url": None,
            },
            {
                "id": "legacy-1",
                "name": "Alpha Bag",
                "slug": "alpha-bag",
                "description": "Bag",
                "price": Decimal("10.25"),
                "currency": "USD",
                "category": "bag",
                "in_stock": True,
                "source": "mock",
                "image_url": (
                    "https://example.test/alpha.jpg"
                ),
            },
        ]

    def health(self):
        return {
            "status": "ONLINE",
        }

    def readiness(self):
        return {
            "ready": True,
            "status": "READY",
        }

    def capabilities(self):
        return {
            "read_catalog": True,
            "write_catalog": False,
        }

    def integration_status(self):
        return {
            "configured": True,
            "read_only": True,
            "source": "FakeLegacyShoppingService",
        }

    def list_products(
        self,
        page: int,
        page_size: int,
    ):
        return {
            "items": self.items,
            "total": 2,
            "page": page,
            "page_size": page_size,
        }


def test_normalizes_legacy_product_to_canonical_shape() -> None:
    product = normalize_management_product(
        FakeLegacyShoppingService().items[1]
    )

    assert product == {
        "product_id": "legacy-1",
        "sku": None,
        "name": "Alpha Bag",
        "description": "Bag",
        "price": 10.25,
        "inventory_quantity": None,
        "in_stock": True,
        "image_urls": [
            "https://example.test/alpha.jpg"
        ],
        "url": None,
        "updated_at": None,
    }


def test_canonical_product_remains_canonical() -> None:
    product = normalize_management_product(
        {
            "product_id": "canonical-1",
            "sku": "SKU-1",
            "name": "Canonical Product",
            "description": "Canonical",
            "price": 20.0,
            "inventory_quantity": 5,
            "in_stock": True,
            "image_urls": [
                "https://example.test/canonical.jpg"
            ],
            "url": (
                "https://example.test/products/canonical-1"
            ),
            "updated_at": "2026-08-01T00:00:00Z",
        }
    )

    assert product["product_id"] == "canonical-1"
    assert product["sku"] == "SKU-1"
    assert product["inventory_quantity"] == 5
    assert product["image_urls"] == [
        "https://example.test/canonical.jpg"
    ]


def test_adapter_enables_management_read_model() -> None:
    source = ShoppingServiceManagementSourceAdapter(
        FakeLegacyShoppingService()
    )

    result = build_shopping_management_read_model(
        source,
        page=1,
        page_size=25,
    ).to_json()

    assert result["status"] == "READY"
    assert result["summary"]["catalog_total"] == 2
    assert result["summary"]["page_items"] == 2
    assert result["summary"]["in_stock"] == 1
    assert result["summary"]["out_of_stock"] == 1

    assert [
        item["product_id"]
        for item in result["products"]
    ] == [
        "legacy-1",
        "legacy-2",
    ]


def test_adapter_isolates_source_mutation() -> None:
    service = FakeLegacyShoppingService()
    source = ShoppingServiceManagementSourceAdapter(
        service
    )

    catalog = source.list_products(
        page=1,
        page_size=25,
    )

    service.items[0]["id"] = "changed"
    service.items.clear()

    assert len(catalog["items"]) == 2
    assert catalog["items"][0]["product_id"] == "legacy-2"


def test_adapter_does_not_synthesize_unknown_commerce_data() -> None:
    product = normalize_management_product(
        FakeLegacyShoppingService().items[0]
    )

    assert product["sku"] is None
    assert product["inventory_quantity"] is None
    assert product["url"] is None
    assert product["updated_at"] is None
    assert product["image_urls"] == []


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "id",
            None,
            "shopping.management_source.product_id_required",
        ),
        (
            "name",
            None,
            "shopping.management_source.product_name_required",
        ),
        (
            "in_stock",
            "yes",
            "shopping.management_source."
            "product_in_stock_boolean_required",
        ),
    ],
)
def test_invalid_legacy_contract_is_rejected(
    field: str,
    value,
    message: str,
) -> None:
    product = dict(
        FakeLegacyShoppingService().items[0]
    )
    product[field] = value

    with pytest.raises(
        ShoppingManagementSourceAdapterError,
        match=message,
    ):
        normalize_management_product(product)


def test_contract_manifest_freezes_boundary() -> None:
    manifest = management_source_adapter_contract_manifest()

    assert manifest["read_only"] is True
    assert manifest["write_methods_allowed"] is False
    assert manifest["canonical_contract_weakened"] is False
    assert manifest["direct_woocommerce_dependency"] is False
    assert manifest["external_network_client"] is False
    assert (
        manifest["external_read_delegated_to_service"]
        is True
    )
    assert manifest["local_product_truth"] is False
    assert manifest["persistence"] is False
    assert manifest["synthetic_sku_allowed"] is False
    assert (
        manifest["synthetic_inventory_allowed"]
        is False
    )


def test_adapter_module_has_no_network_or_persistence_imports(
) -> None:
    path = Path(
        "core/shopping/application/management_source.py"
    )

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    forbidden = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "woocommerce",
    }

    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name.split(".", 1)[0]
                for alias in node.names
            )

        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert imports.isdisjoint(forbidden)
