from __future__ import annotations

import warnings

from pathlib import Path

from core.api.routes import dashboard, shopping
from core.dashboard.api import DashboardAPI
from core.shopping.product_drafts.read import unavailable_dashboard_projection


def test_homepage_shopping_dashboard_exact_keys_and_shapes_are_consumed() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=(
                r"datetime\.datetime\.utcnow\(\) "
                r"is deprecated.*"
            ),
            category=DeprecationWarning,
        )
        payload = DashboardAPI(
            shopping_management=lambda: {
                "status": "READY",
                "mode": "READ_ONLY",
            },
            product_drafts=lambda: {
                "status": "AVAILABLE",
                "mode": "READ_ONLY",
            },
        ).status([], include_datacenter=False)

    assert payload["shopping_management"] == {
        "status": "READY",
        "mode": "READ_ONLY",
    }
    assert payload["product_draft_review"] == {
        "status": "AVAILABLE",
        "mode": "READ_ONLY",
    }

    route = next(
        route
        for route in dashboard.router.routes
        if route.path == "/dashboard"
    )

    assert route.methods == {"GET"}

def test_homepage_shopping_dashboard_existing_get_routes_remain_unchanged() -> None:
    routes = {route.path: route.methods for route in shopping.router.routes}
    assert routes == {
        "/shopping/product-drafts": {"GET"},
        "/shopping/product-drafts/{draft_id}": {"GET"},
        "/shopping/product-drafts/{draft_id}/revisions/{revision_id}": {"GET"},
        "/shopping/health": {"GET"},
        "/shopping/readiness": {"GET"},
        "/shopping/capabilities": {"GET"},
        "/shopping/integrations": {"GET"},
        "/shopping/search": {"GET"},
        "/shopping/featured-products": {"GET"},
        "/shopping/categories": {"GET"},
        "/shopping/products": {"GET"},
        "/shopping/products/{product_id}": {"GET"},
    }


def test_homepage_shopping_dashboard_product_draft_contract_is_unchanged() -> None:
    projection = unavailable_dashboard_projection()
    assert projection["status"] == "UNAVAILABLE"
    assert projection["mode"] == "READ_ONLY"
    assert projection["mutation_capabilities"] is False
    assert projection["summary"] == {
        "draft_count": 0, "revision_count": 0, "lifecycle_counts": {},
    }


def test_homepage_shopping_dashboard_is_presentation_only() -> None:
    ui = Path(__file__).parents[1] / "core" / "homepage" / "ui"
    source = "\n".join(path.read_text(encoding="utf-8") for path in ui.iterdir() if path.is_file())
    assert "woocommerce.com" not in source.lower()
    assert "wc-api" not in source.lower()
    assert "fetch(DASHBOARD_ENDPOINT" in source
    assert "FAKE_APPLIED" in source and "NOT_AUTHORIZED" in source
    assert "mutation control is exposed" in source
