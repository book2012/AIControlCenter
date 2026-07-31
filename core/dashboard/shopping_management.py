from __future__ import annotations

from typing import Any

from core.shopping.application.management_read_model import (
    ShoppingManagementSource,
    build_shopping_management_read_model,
)


def unavailable_shopping_management_dashboard_payload(
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "mode": "READ_ONLY",
        "status": "UNAVAILABLE",
        "summary": {
            "catalog_total": 0,
            "page": 1,
            "page_size": 0,
            "page_items": 0,
            "in_stock": 0,
            "out_of_stock": 0,
            "inventory_quantity_total": 0,
        },
        "products": [],
        "health": {
            "status": "UNKNOWN",
        },
        "readiness": {
            "ready": False,
            "status": "UNKNOWN",
        },
        "capabilities": {
            "read_catalog": False,
            "write_catalog": False,
        },
        "integration": {
            "configured": False,
            "read_only": True,
        },
        "error": {
            "code": "SHOPPING_MANAGEMENT_UNAVAILABLE",
            "retryable": True,
        },
    }


def build_shopping_management_dashboard_payload(
    source: ShoppingManagementSource,
    *,
    page: int = 1,
    page_size: int = 25,
) -> dict[str, Any]:
    try:
        return build_shopping_management_read_model(
            source,
            page=page,
            page_size=page_size,
        ).to_json()
    except Exception:
        return unavailable_shopping_management_dashboard_payload()


def shopping_management_dashboard_contract_manifest(
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "dashboard_section": "shopping_management",
        "default_page": 1,
        "default_page_size": 25,
        "direct_woocommerce_dependency": False,
        "direct_network_client": False,
        "external_read_delegated_to_source": True,
        "failure_details_exposed": False,
        "failure_isolated": True,
        "local_product_truth": False,
        "persistence": False,
        "read_only": True,
        "write_methods_allowed": False,
    }


__all__ = (
    "build_shopping_management_dashboard_payload",
    "shopping_management_dashboard_contract_manifest",
    "unavailable_shopping_management_dashboard_payload",
)
