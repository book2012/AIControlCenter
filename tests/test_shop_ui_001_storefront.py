"""Fixture/static storefront checks; no application runtime or external I/O."""
from html.parser import HTMLParser
from pathlib import Path
import re

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.api.dependencies.shopping import get_shopping_service
from core.api.routes import homepage
from core.homepage.preview import create_app as create_preview_app

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "core/homepage/ui"
PHOTO_ROOT = ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/demo/orange-coco-v1/products"


def fixture_client():
    # Existing SHOP_UI regression fixtures retain the original 92-item demo
    # catalog; the real launcher opts into the 120-item lookbook preview.
    return TestClient(create_preview_app(lookbook=False))


@pytest.fixture
def client():
    with fixture_client() as client:
        yield client


@pytest.mark.parametrize("path,media", [
    ("/homepage/storefront", "text/html"),
    ("/homepage/storefront/search", "text/html"),
    ("/homepage/storefront/product/oc-demo-top-0001", "text/html"),
    ("/homepage/assets/storefront.css", "text/css"),
    ("/homepage/assets/storefront.js", "application/javascript"),
    ("/homepage/assets/storefront/hero-boutique.jpg", "image/jpeg"),
    ("/homepage/assets/storefront/photos/top/oc-demo-top-0001.jpg", "image/jpeg"),
])
def test_local_presentation_routes_are_get_only_and_not_api_schema(client, path, media):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(media)
    assert response.content
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert client.request(method, path).status_code == 405
    assert "storefront" not in str(client.get("/openapi.json").json()["paths"])


@pytest.mark.parametrize("suffix", [
    "top/oc-demo-top-0000.jpg", "top/oc-demo-dress-0001.jpg",
    "top/oc-demo-top-0001.svg", "top/catalog.json", "unknown/oc-demo-top-0001.jpg",
    "top/%2e%2e%2f%2e%2e%2fAGENTS.md", "top/%2fetc%2fpasswd",
])
def test_photo_route_rejects_unknown_files_and_traversal(client, suffix):
    response = client.get(f"/homepage/assets/storefront/photos/{suffix}")
    assert response.status_code == 404


def test_demo_images_are_served_from_repository_bytes_and_contract_is_unchanged(client):
    response = client.get("/shopping/products?page=1&page_size=100")
    payload = response.json()
    assert set(payload) == {"items", "page", "page_size", "total"}
    assert payload["total"] == 92
    for item in payload["items"]:
        assert set(item) == {"id", "name", "slug", "description", "price", "currency", "category", "in_stock", "source", "image_url", "variants"}
        assert isinstance(item["variants"], list)
        for variant in item["variants"]:
            assert set(variant) == {"id", "label", "option_type", "available"}
        assert isinstance(item["price"], str)
        category = item["category"].lower()
        filename = f"{item['id']}.jpg"
        photo = client.get(f"/homepage/assets/storefront/photos/{category}/{filename}")
        assert photo.content == (PHOTO_ROOT / category / filename).read_bytes()
    assert client.get("/shopping/products/oc-demo-top-0001").json() == payload["items"][0]


def test_source_collections_supply_badges_without_hot_inference(client):
    categories = client.get("/shopping/categories").json()["items"]
    slugs = {item["slug"] for item in categories}
    assert {"new", "best"} <= slugs
    assert "hot" not in slugs
    for category, expected in (("new", 24), ("best", 23), ("top", 20), ("dress", 20), ("bag", 12), ("acc", 10)):
        data = client.get("/shopping/search", params={"category": category, "page": 1, "page_size": 100}).json()
        assert data["total"] == expected
        assert len(data["items"]) == expected
    assert client.get("/shopping/search?q=no-such-coco-piece").json()["total"] == 0


def test_operator_pages_still_do_not_resolve_shopping_dependency(client):
    def unavailable():
        raise AssertionError("Page serving must not resolve Commerce")
    app = FastAPI()
    app.include_router(homepage.router)
    app.dependency_overrides[get_shopping_service] = unavailable
    with TestClient(app) as internal:
        assert "Platform overview" in internal.get("/homepage").text
        assert "Product" in internal.get("/homepage/product-management").text


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def test_accessible_shell_local_assets_and_safe_dom_rendering(client):
    html = client.get("/homepage/storefront/search").text
    css = (UI / "storefront.css").read_text()
    js = (UI / "storefront.js").read_text()
    elements = Elements(html).elements
    ids = [attrs["id"] for _, attrs in elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    # Actual category controls are composed from canonical /shopping/categories.
    assert {attrs["data-category"] for _, attrs in elements if "data-category" in attrs} >= {"", "women-tops", "new", "best"}
    assert sum(tag == "h1" for tag, _ in elements) == 1
    assert any(tag == "a" and attrs.get("href") == "#main-content" for tag, attrs in elements)
    assert any(tag == "noscript" for tag, _ in elements)
    for tag, attrs in elements:
        if tag == "img":
            assert "alt" in attrs and "width" in attrs and "height" in attrs
        if "aria-controls" in attrs:
            assert attrs["aria-controls"] in ids
    assert 'aria-live="polite"' in html and 'aria-busy="false"' in html
    assert "repeat(2, minmax(0, 1fr))" in css and "overflow-x: auto" in css
    assert "prefers-reduced-motion" in css and ":focus-visible" in css
    assert 'method: "GET"' in js and 'redirect: "error"' in js
    assert "FETCH_TIMEOUT_MS = 8000" in js and "AbortController" in js
    assert "version !== requestVersion" in js
    assert set(re.findall(r'"(/shopping/[^"?]+)"', js)) == {"/shopping/products", "/shopping/search", "/shopping/categories", "/shopping/inquiries"}
    assert "`/shopping/products/${encodeURIComponent(id)}`" in js
    for forbidden in ("innerHTML", "localStorage", "sessionStorage", "document.cookie", "XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource", "PUT", "PATCH", "DELETE", "consumer_key", "consumer_secret"):
        assert forbidden not in js
    assert not re.search(r"https?://", html + css + js)
