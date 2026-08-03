from __future__ import annotations

import warnings

import re
from pathlib import Path

from core.api.routes import homepage


ROOT = Path(__file__).parents[1]
UI = ROOT / "core" / "homepage" / "ui"
HTML = (UI / "index.html").read_text(encoding="utf-8")
CSS = (UI / "homepage.css").read_text(encoding="utf-8")
JS = (UI / "homepage.js").read_text(encoding="utf-8")


def test_ui_01_homepage_returns_package_local_html_and_assets() -> None:
    document = homepage.homepage_browser()
    stylesheet = homepage.homepage_styles()
    script = homepage.homepage_script()

    assert isinstance(document, str)
    assert "AIControlCenter" in document

    assert stylesheet.media_type == "text/css"
    assert b":root" in stylesheet.body

    assert script.media_type == "application/javascript"
    assert b'DASHBOARD_ENDPOINT = "/dashboard"' in script.body


def test_ui_01_status_contract_remains_compatible() -> None:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=(
                r"datetime\.datetime\.utcnow\(\) "
                r"is deprecated.*"
            ),
            category=DeprecationWarning,
        )
        payload = homepage.homepage_status()

    assert {
        "brain",
        "scheduler",
        "memory",
        "knowledge",
    }.issubset(payload)

def test_ui_01_homepage_router_is_get_head_only() -> None:
    routes = [route for route in homepage.router.routes if route.path.startswith("/homepage")]
    assert {route.path for route in routes} == {
        "/homepage", "/homepage/status", "/homepage/assets/homepage.css",
        "/homepage/assets/homepage.js",
    }
    assert all(set(route.methods or ()) <= {"GET", "HEAD"} for route in routes)

    routes_by_path = {
        route.path: route
        for route in routes
    }

    for path in (
        "/homepage",
        "/homepage/assets/homepage.css",
        "/homepage/assets/homepage.js",
    ):
        assert routes_by_path[path].include_in_schema is False

    assert routes_by_path[
        "/homepage/status"
    ].include_in_schema is True


def test_ui_01_uses_discovered_dashboard_endpoint_with_safe_client() -> None:
    assert 'DASHBOARD_ENDPOINT = "/dashboard"' in JS
    assert re.findall(r'fetch\(([^,]+)', JS) == ["DASHBOARD_ENDPOINT"]
    assert 'method: "GET"' in JS
    assert "AbortController" in JS and "FETCH_TIMEOUT_MS = 8000" in JS
    assert 'addEventListener("click", refreshDashboard)' in JS
    assert not re.search(r'https?://|//[^/]', JS)
    assert not re.search(r'method\s*:\s*["\'](?:POST|PUT|PATCH|DELETE)', JS, re.I)


def test_ui_01_core_sections_and_state_semantics_exist() -> None:
    for heading in (
        "Platform overview", "Catalog overview", "ProductDraft review",
        "Controlled deployment status", "AI readiness", "Operational notices",
    ):
        assert heading in HTML
    for state in (
        "AVAILABLE", "READY", "READ_ONLY", "EMPTY", "DEGRADED", "UNAVAILABLE",
        "REVIEW_REQUIRED", "APPROVED", "REJECTED", "FAKE_APPLIED",
        "INTERCEPTED_VALIDATION", "NOT_AUTHORIZED",
    ):
        assert state in HTML + JS
    assert "available with zero products" in JS
    assert "this is not an empty catalog" in JS


def test_ui_01_has_no_mutation_control_credentials_or_external_assets() -> None:
    combined = HTML + CSS + JS
    assert "<form" not in HTML.lower()
    assert not re.search(r'https?://', combined)
    assert ".innerHTML" not in JS
    assert "textContent" in JS and "replaceChildren" in JS
    for forbidden in (
        "consumer_key", "consumer_secret", "api_password", "localStorage",
        "sessionStorage", "eval(", "new Function(",
    ):
        assert forbidden not in combined


def test_ui_01_accessibility_and_responsive_baseline() -> None:
    assert '<main id="main-content">' in HTML
    assert "<header" in HTML and "<footer" in HTML and "<section" in HTML
    assert 'aria-live="polite"' in HTML
    assert 'name="viewport"' in HTML
    assert "prefers-reduced-motion" in CSS
    assert ":focus-visible" in CSS and "@media (max-width:" in CSS
    assert "INTERNAL · READ_ONLY" in HTML
