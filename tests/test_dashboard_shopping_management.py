from __future__ import annotations

import ast
from pathlib import Path

from core.api.routes import dashboard as dashboard_route
from core.dashboard.api import DashboardAPI
from core.dashboard.shopping_management import (
    build_shopping_management_dashboard_payload,
    shopping_management_dashboard_contract_manifest,
    unavailable_shopping_management_dashboard_payload,
)


class FakeShoppingSource:
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
        return {
            "items": [
                {
                    "product_id": "product-1",
                    "sku": "SKU-1",
                    "name": "Orange Bag",
                    "description": "Bag",
                    "price": 10.0,
                    "inventory_quantity": 4,
                    "in_stock": True,
                    "image_urls": [
                        "https://example.test/product-1.jpg"
                    ],
                    "url": (
                        "https://example.test/products/product-1"
                    ),
                    "updated_at": "2026-07-31T00:00:00Z",
                }
            ],
            "total": 1,
            "page": page,
            "page_size": page_size,
        }


class FailingShoppingSource(FakeShoppingSource):
    def health(self):
        raise RuntimeError("secret provider detail")


def test_dashboard_payload_uses_management_read_model() -> None:
    payload = build_shopping_management_dashboard_payload(
        FakeShoppingSource()
    )

    assert payload["schema_version"] == "1.0"
    assert payload["mode"] == "READ_ONLY"
    assert payload["status"] == "READY"
    assert payload["summary"]["catalog_total"] == 1
    assert payload["summary"]["in_stock"] == 1
    assert payload["products"][0]["product_id"] == (
        "product-1"
    )
    assert payload["capabilities"]["write_catalog"] is False
    assert payload["integration"]["read_only"] is True


def test_dashboard_payload_isolates_shopping_failure() -> None:
    payload = build_shopping_management_dashboard_payload(
        FailingShoppingSource()
    )

    assert payload["status"] == "UNAVAILABLE"
    assert payload["mode"] == "READ_ONLY"
    assert payload["products"] == []
    assert payload["error"] == {
        "code": "SHOPPING_MANAGEMENT_UNAVAILABLE",
        "retryable": True,
    }
    assert "secret" not in str(payload)


def test_unavailable_payload_returns_fresh_result() -> None:
    first = (
        unavailable_shopping_management_dashboard_payload()
    )
    second = (
        unavailable_shopping_management_dashboard_payload()
    )

    first["products"].append({"product_id": "changed"})
    first["error"]["code"] = "CHANGED"

    assert second["products"] == []
    assert second["error"]["code"] == (
        "SHOPPING_MANAGEMENT_UNAVAILABLE"
    )


def test_dashboard_without_projection_preserves_existing_shape() -> None:
    payload = DashboardAPI().status(
        include_datacenter=False
    )

    assert "brain" in payload
    assert "control_plane" in payload
    assert "storage" in payload
    assert "backup" in payload
    assert "workers" in payload
    assert "shopping_management" not in payload


def test_dashboard_includes_injected_shopping_projection() -> None:
    payload = DashboardAPI(
        shopping_management=lambda: (
            build_shopping_management_dashboard_payload(
                FakeShoppingSource()
            )
        )
    ).status(include_datacenter=False)

    shopping = payload["shopping_management"]

    assert shopping["status"] == "READY"
    assert shopping["summary"]["catalog_total"] == 1
    assert shopping["products"][0]["name"] == "Orange Bag"


def test_dashboard_isolates_projection_exception() -> None:
    def fail_projection():
        raise RuntimeError("private failure detail")

    payload = DashboardAPI(
        shopping_management=fail_projection
    ).status(include_datacenter=False)

    shopping = payload["shopping_management"]

    assert shopping["status"] == "UNAVAILABLE"
    assert shopping["error"]["code"] == (
        "SHOPPING_MANAGEMENT_UNAVAILABLE"
    )
    assert "private failure detail" not in str(shopping)


def test_dashboard_projection_result_is_mutation_isolated() -> None:
    source_payload = {
        "schema_version": "1.0",
        "mode": "READ_ONLY",
        "status": "READY",
        "summary": {
            "catalog_total": 1,
        },
        "products": [
            {
                "product_id": "product-1",
            }
        ],
    }

    api = DashboardAPI(
        shopping_management=lambda: source_payload
    )

    first = api.status(include_datacenter=False)

    source_payload["summary"]["catalog_total"] = 99
    source_payload["products"].clear()
    first["shopping_management"]["summary"][
        "catalog_total"
    ] = 100

    second = api.status(include_datacenter=False)

    assert second["shopping_management"]["summary"][
        "catalog_total"
    ] == 99


def test_default_route_projection_isolates_service_construction(
    monkeypatch,
) -> None:
    class BrokenShoppingService:
        def __init__(self):
            raise RuntimeError("credential detail")

    monkeypatch.setattr(
        dashboard_route,
        "ShoppingService",
        BrokenShoppingService,
    )

    payload = (
        dashboard_route
        .build_default_shopping_management_dashboard_payload()
    )

    assert payload["status"] == "UNAVAILABLE"
    assert payload["error"]["code"] == (
        "SHOPPING_MANAGEMENT_UNAVAILABLE"
    )
    assert "credential detail" not in str(payload)


def test_contract_manifest_freezes_dashboard_boundary() -> None:
    manifest = (
        shopping_management_dashboard_contract_manifest()
    )

    assert manifest["read_only"] is True
    assert manifest["failure_isolated"] is True
    assert manifest["failure_details_exposed"] is False
    assert manifest["direct_woocommerce_dependency"] is False
    assert manifest["direct_network_client"] is False
    assert (
        manifest["external_read_delegated_to_source"]
        is True
    )
    assert manifest["persistence"] is False
    assert manifest["local_product_truth"] is False
    assert manifest["write_methods_allowed"] is False


def test_dashboard_modules_have_no_direct_woocommerce_dependency(
) -> None:
    paths = [
        Path("core/dashboard/api.py"),
        Path("core/dashboard/shopping_management.py"),
        Path("core/api/routes/dashboard.py"),
    ]

    forbidden_modules = {
        "requests",
        "httpx",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "subprocess",
    }

    for path in paths:
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert (
                        alias.name.split(".", 1)[0]
                        not in forbidden_modules
                    )
                    assert "woocommerce" not in (
                        alias.name.lower()
                    )

            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
            ):
                assert (
                    node.module.split(".", 1)[0]
                    not in forbidden_modules
                )
                assert "woocommerce" not in (
                    node.module.lower()
                )


def test_dashboard_route_remains_get_only_and_wires_projection(
) -> None:
    path = Path("core/api/routes/dashboard.py")
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(path))

    methods = []

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
            ):
                methods.append(
                    decorator.func.attr.lower()
                )

    assert methods == ["get"]

    dashboard_calls = [
        node
        for node in ast.walk(tree)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "DashboardAPI"
        )
    ]

    assert len(dashboard_calls) == 1

    shopping_keywords = [
        keyword
        for keyword in dashboard_calls[0].keywords
        if keyword.arg == "shopping_management"
    ]

    assert len(shopping_keywords) == 1

    projection = shopping_keywords[0].value

    assert isinstance(projection, ast.Name)
    assert projection.id == (
        "build_default_shopping_management_dashboard_payload"
    )
