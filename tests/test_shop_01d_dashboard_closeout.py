from __future__ import annotations

import ast
from pathlib import Path

from core.api.routes import dashboard as dashboard_route
from core.dashboard.api import DashboardAPI


class FakeShoppingService:
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
            "generate_ai_content": False,
            "execute_automation": False,
            "approval_required": True,
        }

    def integration_status(self):
        return {
            "catalog_adapter": "woocommerce",
            "configured": True,
            "read_only": True,
            "source": "FakeShoppingService",
        }

    def list_products(
        self,
        page: int,
        page_size: int,
    ):
        return {
            "items": [
                {
                    "product_id": "product-1",
                    "sku": "SKU-1",
                    "name": "Orange Bag",
                    "description": "Operator projection test",
                    "price": 100.0,
                    "inventory_quantity": 3,
                    "in_stock": True,
                    "image_urls": [
                        "https://example.test/product-1.jpg"
                    ],
                    "url": (
                        "https://example.test/products/product-1"
                    ),
                    "updated_at": "2026-07-31T00:00:00Z",
                },
                {
                    "product_id": "product-2",
                    "sku": "SKU-2",
                    "name": "Orange Dress",
                    "description": "Operator projection test",
                    "price": 200.0,
                    "inventory_quantity": 0,
                    "in_stock": False,
                    "image_urls": [
                        "https://example.test/product-2.jpg"
                    ],
                    "url": (
                        "https://example.test/products/product-2"
                    ),
                    "updated_at": "2026-07-31T00:00:00Z",
                },
            ],
            "total": 2,
            "page": page,
            "page_size": page_size,
        }


def test_default_dashboard_projection_contract(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        dashboard_route,
        "ShoppingService",
        FakeShoppingService,
    )

    payload = (
        dashboard_route
        .build_default_shopping_management_dashboard_payload()
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "READ_ONLY"
    assert payload["status"] == "READY"

    assert payload["summary"] == {
        "catalog_total": 2,
        "page": 1,
        "page_size": 25,
        "page_items": 2,
        "in_stock": 1,
        "out_of_stock": 1,
        "inventory_quantity_total": 3,
    }

    assert [
        item["product_id"]
        for item in payload["products"]
    ] == [
        "product-1",
        "product-2",
    ]

    assert payload["capabilities"]["write_catalog"] is False
    assert payload["integration"]["read_only"] is True


def test_dashboard_json_contains_injected_management_section(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        dashboard_route,
        "ShoppingService",
        FakeShoppingService,
    )

    payload = DashboardAPI(
        shopping_management=(
            dashboard_route
            .build_default_shopping_management_dashboard_payload
        )
    ).status(include_datacenter=False)

    assert "shopping_management" in payload
    assert payload["shopping_management"]["status"] == "READY"
    assert payload["shopping_management"]["mode"] == (
        "READ_ONLY"
    )
    assert payload["shopping_management"]["summary"][
        "catalog_total"
    ] == 2


def test_existing_dashboard_shape_remains_compatible() -> None:
    payload = DashboardAPI().status(
        include_datacenter=False
    )

    assert set(payload) == {
        "brain",
        "control_plane",
        "storage",
        "backup",
        "workers",
    }


def test_shopping_and_dashboard_routes_remain_get_only() -> None:
    paths = [
        Path("core/api/routes/dashboard.py"),
        Path("core/api/routes/shopping.py"),
    ]

    methods = []

    for path in paths:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                continue

            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(
                        decorator.func,
                        ast.Attribute,
                    )
                    and decorator.func.attr.lower()
                    in {
                        "get",
                        "post",
                        "put",
                        "patch",
                        "delete",
                    }
                ):
                    methods.append(
                        (
                            str(path),
                            decorator.func.attr.lower(),
                        )
                    )

    assert methods
    assert all(method == "get" for _, method in methods)


def test_dashboard_has_no_direct_woocommerce_dependency() -> None:
    paths = [
        Path("core/dashboard/api.py"),
        Path("core/dashboard/shopping_management.py"),
        Path("core/api/routes/dashboard.py"),
    ]

    for path in paths:
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )

        for node in ast.walk(tree):
            modules = []

            if isinstance(node, ast.Import):
                modules.extend(
                    alias.name
                    for alias in node.names
                )

            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
            ):
                modules.append(node.module)

            assert all(
                "woocommerce" not in module.lower()
                for module in modules
            )


def test_shop_01_closeout_keeps_write_authority_disabled() -> None:
    source = FakeShoppingService()

    capabilities = source.capabilities()
    integration = source.integration_status()

    assert capabilities["write_catalog"] is False
    assert capabilities["generate_ai_content"] is False
    assert capabilities["execute_automation"] is False
    assert capabilities["approval_required"] is True
    assert integration["read_only"] is True
