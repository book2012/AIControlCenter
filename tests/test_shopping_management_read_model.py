from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.shopping.application.management_read_model import (
    ShoppingManagementReadModelError,
    build_shopping_management_read_model,
    management_read_model_contract_manifest,
)


class FakeShoppingManagementSource:
    def __init__(self) -> None:
        self.catalog = {
            "items": [
                {
                    "product_id": "product-2",
                    "sku": "SKU-2",
                    "name": "Zulu Dress",
                    "description": "Second",
                    "price": 20.0,
                    "inventory_quantity": 0,
                    "in_stock": False,
                    "image_urls": ["https://example.test/2.jpg"],
                    "url": "https://example.test/products/2",
                    "updated_at": "2026-07-31T00:00:00Z",
                    "ignored_vendor_field": "not projected",
                },
                {
                    "product_id": "product-1",
                    "sku": "SKU-1",
                    "name": "Alpha Bag",
                    "description": "First",
                    "price": 10.0,
                    "inventory_quantity": 4,
                    "in_stock": True,
                    "image_urls": ["https://example.test/1.jpg"],
                    "url": "https://example.test/products/1",
                    "updated_at": "2026-07-31T00:00:00Z",
                },
            ],
            "total": 8,
            "page": 1,
            "page_size": 25,
        }

    def health(self):
        return {
            "service": "AIShoppingPlatform",
            "status": "ONLINE",
            "write_mode": "read_only",
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
            "approval_required": True,
        }

    def integration_status(self):
        return {
            "catalog_adapter": "woocommerce",
            "configured": True,
            "read_only": True,
            "source": "FakeAdapter",
        }

    def list_products(
        self,
        page: int,
        page_size: int,
    ):
        assert page == 1
        assert page_size == 25
        return self.catalog


def test_builds_deterministic_read_only_management_projection() -> None:
    result = build_shopping_management_read_model(
        FakeShoppingManagementSource()
    ).to_json()

    assert result["schema_version"] == "1.0"
    assert result["mode"] == "READ_ONLY"
    assert result["status"] == "READY"

    assert result["summary"] == {
        "catalog_total": 8,
        "page": 1,
        "page_size": 25,
        "page_items": 2,
        "in_stock": 1,
        "out_of_stock": 1,
        "inventory_quantity_total": 4,
    }

    assert [
        product["product_id"]
        for product in result["products"]
    ] == [
        "product-1",
        "product-2",
    ]

    assert (
        "ignored_vendor_field"
        not in result["products"][1]
    )

    assert result["capabilities"]["write_catalog"] is False
    assert result["integration"]["read_only"] is True


def test_degraded_status_when_source_is_not_ready() -> None:
    source = FakeShoppingManagementSource()

    source.readiness = lambda: {
        "ready": False,
        "status": "NOT_READY",
    }

    result = build_shopping_management_read_model(
        source
    ).to_json()

    assert result["status"] == "DEGRADED"


def test_result_isolated_from_source_payload_mutation() -> None:
    source = FakeShoppingManagementSource()

    model = build_shopping_management_read_model(source)

    source.catalog["items"][0]["name"] = "Changed"
    source.catalog["items"][0]["image_urls"].append(
        "https://example.test/changed.jpg"
    )
    source.catalog["items"].clear()

    result = model.to_json()

    assert len(result["products"]) == 2
    assert result["products"][1]["name"] == "Zulu Dress"
    assert result["products"][1]["image_urls"] == [
        "https://example.test/2.jpg"
    ]


def test_json_result_mutation_does_not_change_model() -> None:
    model = build_shopping_management_read_model(
        FakeShoppingManagementSource()
    )

    first = model.to_json()

    first["summary"]["catalog_total"] = 999
    first["products"][0]["name"] = "Changed"
    first["products"].clear()

    second = model.to_json()

    assert second["summary"]["catalog_total"] == 8
    assert len(second["products"]) == 2
    assert second["products"][0]["name"] == "Alpha Bag"


@pytest.mark.parametrize(
    ("attribute", "value", "message"),
    [
        (
            "health",
            [],
            "shopping.management.health_mapping_required",
        ),
        (
            "readiness",
            [],
            "shopping.management.readiness_mapping_required",
        ),
        (
            "capabilities",
            [],
            "shopping.management.capabilities_mapping_required",
        ),
        (
            "integration_status",
            [],
            "shopping.management.integration_mapping_required",
        ),
    ],
)
def test_non_mapping_source_payload_is_rejected(
    attribute: str,
    value,
    message: str,
) -> None:
    source = FakeShoppingManagementSource()
    setattr(source, attribute, lambda: value)

    with pytest.raises(
        ShoppingManagementReadModelError,
        match=message,
    ):
        build_shopping_management_read_model(source)


def test_non_sequence_catalog_items_are_rejected() -> None:
    source = FakeShoppingManagementSource()
    source.catalog["items"] = {
        "product_id": "not-a-sequence",
    }

    with pytest.raises(
        ShoppingManagementReadModelError,
        match=(
            "shopping.management."
            "catalog_items_sequence_required"
        ),
    ):
        build_shopping_management_read_model(source)


def test_invalid_product_contract_is_rejected() -> None:
    source = FakeShoppingManagementSource()
    source.catalog["items"][0]["in_stock"] = "yes"

    with pytest.raises(
        ShoppingManagementReadModelError,
        match=(
            "shopping.management."
            "product_in_stock_boolean_required"
        ),
    ):
        build_shopping_management_read_model(source)


@pytest.mark.parametrize(
    ("page", "page_size"),
    [
        (0, 25),
        (True, 25),
        (1, 0),
        (1, 101),
        (1, True),
    ],
)
def test_pagination_contract_is_enforced(
    page,
    page_size,
) -> None:
    with pytest.raises(ShoppingManagementReadModelError):
        build_shopping_management_read_model(
            FakeShoppingManagementSource(),
            page=page,
            page_size=page_size,
        )


def test_contract_manifest_freezes_architecture_boundary() -> None:
    manifest = management_read_model_contract_manifest()

    assert manifest["read_only"] is True
    assert manifest["write_methods_allowed"] is False
    assert manifest["direct_woocommerce_dependency"] is False
    assert manifest["external_network"] is False
    assert manifest["persistence"] is False
    assert manifest["local_product_truth"] is False
    assert manifest["dashboard_registration"] is False
    assert manifest["production_registration"] is False


def test_module_has_no_network_persistence_or_write_imports() -> None:
    path = Path(
        "core/shopping/application/"
        "management_read_model.py"
    )

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    forbidden_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
        "pathlib",
        "woocommerce",
    }

    imported = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(
                alias.name.split(".", 1)[0]
                for alias in node.names
            )

        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])

    assert imported.isdisjoint(forbidden_imports)

    function_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    }

    assert not any(
        token in name
        for name in function_names
        for token in (
            "create_product",
            "update_product",
            "delete_product",
            "publish_product",
            "write_product",
            "save_product",
        )
    )
