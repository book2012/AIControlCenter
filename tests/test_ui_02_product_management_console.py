from pathlib import Path

from fastapi.testclient import TestClient

from core.api.app import app
from core.api.routes import homepage, shopping
from core.shopping.product_drafts.read import unavailable_dashboard_projection


ROOT = Path(__file__).parents[1]
UI = ROOT / "core" / "homepage" / "ui"
client = TestClient(app)


def source(name: str) -> str:
    return (UI / name).read_text(encoding="utf-8")


def test_ui_02_route_and_assets_are_available() -> None:
    expected = {
        "/homepage/product-management": "text/html",
        "/homepage/assets/product-management.css": "text/css",
        "/homepage/assets/product-management.js": "application/javascript",
    }
    for path, media_type in expected.items():
        response = client.get(path)
        assert response.status_code == 200
        assert media_type in response.headers["content-type"]


def test_ui_02_homepage_presentation_is_get_head_only_and_schema_safe() -> None:
    for route in homepage.router.routes:
        assert route.methods == {"GET"}
    schema_paths = app.openapi()["paths"]
    assert "/homepage/status" in schema_paths
    assert "/homepage" not in schema_paths
    assert "/homepage/product-management" not in schema_paths
    assert not any(path.startswith("/homepage/assets/") for path in schema_paths)


def test_ui_02_uses_exact_same_origin_get_boundaries_only() -> None:
    js = source("product-management.js")
    assert '"/shopping/product-drafts?page=1&page_size=100"' in js
    assert '`/shopping/product-drafts/${encodeURIComponent(draftId)}`' in js
    assert '/revisions/${encodeURIComponent(revisionId)}' in js
    assert 'method: "GET"' in js
    for token in ("POST", "PUT", "PATCH", "DELETE", "woocommerce.com", "wc-api", "http://", "https://"):
        assert token not in js
    routes = {route.path: route.methods for route in shopping.router.routes if "product-drafts" in route.path}
    assert routes == {
        "/shopping/product-drafts": {"GET"},
        "/shopping/product-drafts/{draft_id}": {"GET"},
        "/shopping/product-drafts/{draft_id}/revisions/{revision_id}": {"GET"},
    }


def test_ui_02_safe_rendering_timeout_retry_and_no_persistence() -> None:
    all_ui = "\n".join(source(name) for name in ("product-management.html", "product-management.css", "product-management.js"))
    js = source("product-management.js")
    assert "innerHTML" not in all_ui
    assert "localStorage" not in all_ui and "sessionStorage" not in all_ui and "indexedDB" not in all_ui
    assert "document.cookie" not in all_ui
    assert "textContent" in js and "createElement" in js and "replaceChildren" in js and "appendChild" in js
    assert "AbortController" in js and "FETCH_TIMEOUT_MS = 8000" in js and 'id="retry"' in all_ui
    assert "safe retry is available" in js
    assert "EMPTY · ProductDraft source is AVAILABLE" in js
    assert "UNAVAILABLE — this is not an empty" in js


def test_ui_02_accessibility_responsive_and_state_baseline() -> None:
    html = source("product-management.html")
    css = source("product-management.css")
    js = source("product-management.js")
    assert 'aria-live="polite"' in html and 'role="status"' in html
    assert "skip-link" in html and ":focus-visible" in css and "@media(max-width:" in css
    assert "prefers-reduced-motion" in css
    for state in ("AVAILABLE", "EMPTY", "UNAVAILABLE", "DEGRADED", "READ_ONLY", "REVIEW_REQUIRED", "APPROVED", "REJECTED", "NOT_AUTHORIZED"):
        assert state in html + js


def test_ui_02_contract_and_frozen_implementation_guards() -> None:
    projection = unavailable_dashboard_projection()
    assert projection["schema_version"] == "1.0"
    assert projection["mode"] == "READ_ONLY"
    assert projection["mutation_capabilities"] is False
    js = source("product-management.js")
    assert "deployment_intent" in js and "human_decision" in js and "validation" in js
    assert "schema_version" not in js  # presentation does not reinterpret contracts

def test_ui_02_clears_stale_state_and_normalizes_optional_arrays() -> None:
    js = source("product-management.js")

    assert "function resetSelection" in js
    assert "function clearDraftPanels" in js
    assert "function clearRevisionPanel" in js

    assert "ProductDraft source is unavailable." in js
    assert "ProductDraft detail is unavailable." in js
    assert "Revision detail is unavailable." in js

    assert "listOf(validation.errors)" in js
    assert "listOf(validation.warnings)" in js
    assert "validation.errors.join" not in js
    assert "validation.warnings.join" not in js
