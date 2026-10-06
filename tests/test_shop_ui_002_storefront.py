"""SHOP_UI_002: Korean storefront, canonical detail and source safety contracts.

Browser interaction assertions live in shop_ui_001_browser.cjs. Static/API
checks here do not claim to execute browser history or responsive layout.
"""
from pathlib import Path
import re
from html import escape, unescape
from urllib.parse import parse_qs, urlsplit
from unittest.mock import Mock

from core.api.dependencies.shopping import get_shopping_service
from core.homepage import storefront
from core.shopping.ports import CatalogReadUnavailable

import pytest

from test_shop_ui_001_storefront import Elements, UI, fixture_client


@pytest.fixture
def client():
    with fixture_client() as client:
        yield client


@pytest.mark.parametrize("filename", ["storefront.html", "storefront-search.html", "storefront-product.html"])
def test_korean_accessible_storefront_with_shared_order_navigation(filename):
    source = (UI / filename).read_text()
    elements = Elements(source).elements
    assert ('html', {'lang': 'ko'}) in elements
    assert "상품 미리보기 · 현재 구매는 지원하지 않습니다." in source
    assert "본문 바로가기" in source
    assert sum(tag == "h1" for tag, _ in elements) == (2 if filename == "storefront.html" else 1)
    ids = [attrs["id"] for _, attrs in elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    for tag, attrs in elements:
        assert not any(key.startswith("on") for key in attrs)
        if tag == "img":
            assert all(key in attrs for key in ("alt", "width", "height"))
    assert not re.search(r'\b(cart|checkout|account|wishlist)\b', source, re.I)
    assert '/homepage/storefront/my-orders' in source
    assert "HOT" not in source


def test_pdp_is_server_rendered_without_listing_and_hero(client):
    response = client.get("/homepage/storefront/product/oc-demo-top-0001")
    assert response.status_code == 200
    assert 'id="detail-view"' in response.text
    assert 'id="listing-view"' not in response.text
    assert 'class="hero"' not in response.text
    assert "소프트 린넨 블라우스" in response.text
    assert "상품을 불러오는 중" not in response.text
    for identifier in ("missing-product", "42"):
        response = client.get(f"/homepage/storefront/product/{identifier}")
        assert response.status_code == 404
        assert "상품을 찾을 수 없습니다" in response.text


def test_legacy_fixture_integrates_existing_five_orderable_products(client):
    home=client.get("/homepage/storefront")
    assert home.status_code==200 and "/homepage/storefront/my-orders" in home.text
    for product_id in ("oc-demo-top-0001","oc-demo-bottom-0001","oc-demo-outer-0001","oc-demo-dress-0001","oc-demo-bag-0001"):
        page=client.get("/homepage/storefront/product/"+product_id)
        assert 'id="commerce-panel"' in page.text
        assert 'data-demo-product="'+product_id+'"' in page.text
        assert '/homepage/assets/storefront-commerce.js' in page.text
        assert "DEV 주문 테스트" in page.text
    other=client.get("/homepage/storefront/product/oc-demo-acc-0001")
    assert other.status_code==200 and 'id="commerce-panel"' not in other.text
    orders=client.get("/homepage/storefront/my-orders")
    assert orders.status_code==200 and "내 주문" in orders.text and "/homepage/assets/storefront-orders.js" in orders.text

def test_pdp_valid_and_not_found_canonical_api(client):
    product = client.get("/shopping/products/oc-demo-top-0001")
    assert product.status_code == 200
    assert product.json()["id"] == "oc-demo-top-0001"
    assert isinstance(product.json()["price"], str)
    assert isinstance(product.json()["in_stock"], bool)
    missing = client.get("/shopping/products/no-such-product")
    assert missing.status_code == 404
    assert missing.json() == {"detail": {"code": "shopping_product_not_found", "product_id": "no-such-product"}}
    assert set(product.json()) == {"id", "name", "slug", "description", "price", "currency", "category", "in_stock", "source", "image_url", "variants"}


def test_cards_are_real_links_and_pdp_reads_only_canonical_detail():
    html = (UI / "storefront.html").read_text()
    js = (UI / "storefront.js").read_text()
    assert '<a class="product-link">' in html
    assert 'link.href = productURL(product.id)' in js
    assert 'encodeURIComponent(productId)' in js
    assert 'return_to: isHome ? homeURL(state) : listingURL(state)' in js
    detail = js[js.index('  async function loadProduct()'):js.index('  function restoreListing()')]
    assert detail.count("readJSON(") == 1
    assert '`/shopping/products/${encodeURIComponent(id)}`' in detail
    assert "loadProducts(" not in detail and "loadCategories(" not in detail
    assert "product.id !== id" in detail
    assert 'textContent = product.name' in detail
    assert 'textContent = priceLabel(product)' in detail
    assert 'product.in_stock ? "재고 있음" : "품절"' in detail
    assert 'textContent = product.description' in detail
    assert 'setPhoto(byId("detail-photo"), product)' in detail
    for unsupported in ("gallery", "material", "fit", "color"):
        assert f"product.{unsupported}" not in js


def test_url_state_and_navigation_are_explicit_and_nonpersistent():
    js = (UI / "storefront.js").read_text()
    for text in ('params.get("category")', 'params.get("q")', 'params.get("page")',
                 'window.history.pushState', 'window.history.replaceState',
                 'window.addEventListener("popstate"', 'window.addEventListener("pageshow"',
                 'window.addEventListener("pagehide"', 'event.persisted', 'returnURL()',
                 'url.origin !== window.location.origin', '![HOME_PATH, LIST_PATH].includes(url.pathname)'):
        assert text in js
    assert 'select({ category: button.dataset.category, page: 1 })' in js
    assert 'select({ query: byId("search-input").value.trim(), page: 1 })' in js
    for forbidden in ("localStorage", "sessionStorage", "indexedDB", "document.cookie", "caches.", "serviceWorker", "wishes"):
        assert forbidden not in js


def test_category_query_composition_is_supported_by_canonical_demo(client):
    all_tops = client.get("/shopping/search", params={"category": "women-tops", "page_size": 100}).json()
    combined = client.get("/shopping/search", params={"category": "women-tops", "q": "블라우스", "page_size": 100}).json()
    assert combined["total"] > 0
    assert {item["id"] for item in combined["items"]} <= {item["id"] for item in all_tops["items"]}
    assert combined["filters"]["category"] == "women-tops"
    assert combined["filters"]["query"] == "블라우스"
    second = client.get("/shopping/search", params={"category": "women-tops", "page": 2, "page_size": 12}).json()
    assert second["page"] == 2 and second["total"] == 20 and len(second["items"]) == 8


def test_mood_suggestions_and_badges_do_not_invent_facets_or_popularity():
    html = (UI / "storefront-search.html").read_text()
    js = (UI / "storefront.js").read_text()
    assert "검색어 예시이며, 상품 속성 필터가 아닙니다." in html
    assert 'select({ query: button.dataset.query, page: 1 })' in js
    assert 'data-tag=' not in html
    assert '["best", "new"].map' in js
    assert 'category: category.id, page: "1", page_size: "100"' in js
    assert 'result.value.items' in js and 'badges.set(item.id' in js
    assert '["best", "hot", "new"]' not in js
    assert 'data-badge="HOT"' not in (UI / "storefront.css").read_text()


def test_canonical_only_gets_approved_existing_photos_and_exact_safe_text():
    js = (UI / "storefront.js").read_text()
    assert js.count("fetch(") == 2
    assert 'method: "GET"' in js and 'redirect: "error"' in js
    assert 'AbortController' in js and 'version !== requestVersion' in js
    assert 'typeof product.price !== "string"' in js
    assert 'const [whole, fraction] = product.price.split(".")' in js
    assert 'media.has(product.id)' in js
    assert 'PHOTO_PREFIX' not in js and 'wp-content/plugins' not in js
    for forbidden in ("innerHTML", "outerHTML", "insertAdjacentHTML", "DOMParser", "parseFloat", "toFixed", "Number(product.price)",
                      "PUT", "PATCH", "DELETE", "sendBeacon", "XMLHttpRequest", "WebSocket", "EventSource",
                      "wc/v3", "wp-json", "consumer_key", "consumer_secret"):
        assert forbidden not in js
    assert not re.search(r"https?://", js)


def test_mobile_tablet_desktop_layout_and_reduced_motion_contract():
    css = (UI / "storefront.css").read_text()
    for count in (2, 3, 4):
        assert f"repeat({count}, minmax(0, 1fr))" in css
    assert "prefers-reduced-motion" in css
    assert ":focus-visible" in css
    assert "height: 180px" in css and "height: 260px" in css


def test_editorial_home_and_search_have_separate_information_architecture(client):
    home = client.get("/homepage/storefront").text
    search = client.get("/homepage/storefront/search?category=women-tops&q=블라우스&page=1").text
    assert "{{" not in home + search
    assert "자바스크립트 없이도" in home + search
    home_elements, search_elements = Elements(home).elements, Elements(search).elements
    home_ids = {attrs["id"] for _, attrs in home_elements if "id" in attrs}
    search_ids = {attrs["id"] for _, attrs in search_elements if "id" in attrs}
    assert {"home-view", "home-filter-nav", "home-feed", "browse-all", "hero-title", "feed-title"} <= home_ids
    assert not {"search-input", "product-count", "category-nav", "active-conditions", "next-page"} & home_ids
    assert "new-grid" not in home and "best-grid" not in home and "category-lookbook" not in home
    assert home.count('id="shop-chat-form"') == 1
    assert {"listing-view", "search-input", "category-nav", "active-conditions", "product-count", "next-page"} <= search_ids
    assert "hero-title" not in search_ids
    assert any(tag == "a" and attrs.get("href") == "/homepage/storefront/search" for tag, attrs in home_elements)
    assert "추천" not in home + search


def test_home_uses_one_mixed_feed_without_collection_sections(client):
    js = (UI / "storefront.js").read_text()
    assert 'homeURL(value)' in js and 'collection' in js
    assert 'home-feed' in js and 'new-grid' not in js and 'best-grid' not in js
    assert 'featured' not in js and '추천' not in js
    home = client.get(storefront.HOME).text
    assert len(re.findall(r'data-product-id="([^"]+)"', home)) == 24
    assert {x.split("-")[2] for x in re.findall(r'data-product-id="([^"]+)"', home)} >= {"top", "bottom", "outer", "dress", "bag", "acc"}


def test_search_history_and_return_urls_preserve_the_home_search_split():
    js = (UI / "storefront.js").read_text()
    assert 'const HOME_PATH = "/homepage/storefront"' in js
    assert 'const LIST_PATH = `${HOME_PATH}/search`' in js
    assert 'const DETAIL_PREFIX = `${HOME_PATH}/product/`' in js
    assert 'return_to: isHome ? homeURL(state) : listingURL(state)' in js
    assert 'back === HOME_PATH ? "← 홈으로" : "← 상품 목록으로"' in js
    assert 'homeURL(value)' in js
    assert 'else if (!isHome && listingURL(parseState(window.location.search)) !== listingURL(state)) restoreListing()' in js
    assert 'byId("active-conditions").textContent' in js


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", ["/homepage/storefront", "/homepage/storefront/search", "/homepage/storefront/product/oc-demo-top-0001",
                                  "/shopping/products", "/shopping/products/oc-demo-top-0001"])
def test_no_commerce_writes(client, method, path):
    assert client.request(method, path).status_code == 405


def links(html, *, class_name=None):
    return [attrs for tag, attrs in Elements(html).elements if tag == "a" and attrs.get("href")
            and (class_name is None or class_name in attrs.get("class", "").split())]


def test_native_home_category_links_follow_canonical_slugs(client):
    response = client.get(storefront.HOME)
    assert response.status_code == 200
    anchors = links(response.text)
    for category in client.get("/shopping/categories").json()["items"]:
        if category["slug"] in ("new", "best", "sale"):
            continue
        target = storefront.HOME + "?category=" + category["slug"]
        assert any(item["href"] == target for item in anchors)
        listing = client.get(target)
        assert listing.status_code == 200
        assert links(listing.text, class_name="product-link")
    assert any(item["href"] == storefront.LIST for item in anchors)


@pytest.mark.parametrize("path", [storefront.HOME, storefront.LIST, storefront.LIST + "?category=women-tops&page=2"])
def test_native_card_to_detail_to_origin_round_trip_without_scripts(client, path):
    response = client.get(path)
    assert response.status_code == 200
    anchors = links(response.text, class_name="product-link")
    assert len(anchors) == (12 if path == storefront.LIST else 8 if "page=2" in path else 24)
    for anchor in anchors:
        target = urlsplit(anchor["href"])
        assert re.fullmatch(r"/homepage/storefront/product/oc-demo-[a-z]+-[0-9]{4}", target.path)
        assert parse_qs(target.query)["return_to"] == [path]
        detail = client.get(anchor["href"])
        assert detail.status_code == 200
        back = next(item for item in links(detail.text) if item.get("id") == "back-to-list")
        assert back["href"] == path
        assert client.get(back["href"]).status_code == 200


def test_native_search_form_and_pagination_preserve_composed_state(client):
    path = storefront.LIST + "?category=women-tops&q=블라우스&page=1"
    html = client.get(path).text
    elements = Elements(html).elements
    form = next(attrs for tag, attrs in elements if tag == "form")
    assert form["method"] == "get" and form["action"] == storefront.LIST
    values = {attrs.get("name"): attrs.get("value") for tag, attrs in elements if tag == "input" and attrs.get("name")}
    assert values == {"category": "women-tops", "q": "블라우스"}
    for anchor in links(html):
        if "data-category" in anchor:
            assert parse_qs(urlsplit(anchor["href"]).query)["q"] == ["블라우스"]
    first = client.get(storefront.LIST + "?category=women-tops").text
    next_link = next(item for item in links(first) if item.get("id") == "next-page")
    second = client.get(next_link["href"])
    assert second.status_code == 200 and "2 / 2 페이지" in second.text
    previous = next(item for item in links(second.text) if item.get("id") == "previous-page")
    assert previous["href"] == storefront.LIST + "?category=women-tops"
    unknown = client.get(storefront.LIST + "?category=no-such-category")
    assert unknown.status_code == 200 and "상품 0개" in unknown.text
    assert not links(unknown.text, class_name="product-link")
    filtered_home = client.get(storefront.HOME + "?category=women-tops")
    assert filtered_home.status_code == 200
    assert {value.split("-")[2] for value in re.findall(r'data-product-id="([^"]+)"', filtered_home.text)} == {"top"}


def test_html_read_uses_the_composed_service_and_canonical_category_id(client):
    service = client.app.dependency_overrides[get_shopping_service]()
    original = service.list_categories()
    categories = [{**item, "id": "101"} if item["slug"] == "women-tops" else item for item in original["items"]]
    products = service.search_products(query=None, category="women-tops", minimum_price=None,
                                      maximum_price=None, in_stock=None, page=1, page_size=12)
    service.list_categories = Mock(return_value={"items": categories, "total": len(categories)})
    service.search_products = Mock(return_value=products)
    response = client.get(storefront.LIST + "?category=women-tops")
    assert response.status_code == 200
    assert service.search_products.call_args.kwargs["category"] == "101"
    assert 'data-category="women-tops" data-category-id="101"' in response.text
    product = service.get_product("oc-demo-top-0001")
    detail_service = Mock(spec=["get_product"])
    detail_service.get_product.return_value = product
    client.app.dependency_overrides[get_shopping_service] = lambda: detail_service
    assert client.get(storefront.HOME + "/product/oc-demo-top-0001").status_code == 200
    detail_service.get_product.assert_called_once_with("oc-demo-top-0001")


@pytest.mark.parametrize("raw", ["https://untrusted.invalid", "//untrusted.invalid", "/homepage", "/shopping/products", "/homepage/storefront/search#bad"])
def test_server_return_destinations_are_bounded(client, raw):
    html = client.get(storefront.HOME + "/product/oc-demo-top-0001", params={"return_to": raw}).text
    assert next(item for item in links(html) if item.get("id") == "back-to-list")["href"] == storefront.LIST


def test_server_safe_text_exact_price_and_local_image_policy(client):
    service = client.app.dependency_overrides[get_shopping_service]()
    product = service.get_product("oc-demo-top-0001")
    hostile = '<img src=x onerror="alert(1)">{{cards}}'
    product.update(name=hostile, description="<script>alert(1)</script>", price="9007199254740993.0100",
                   currency="USD", image_url="https://untrusted.invalid/photo.jpg")
    service.get_product = Mock(return_value=product)
    html = client.get(storefront.HOME + "/product/oc-demo-top-0001").text
    assert hostile in unescape(html) and escape(product["description"]) in html
    assert "{{" not in html and "}}" not in html
    assert "USD 9,007,199,254,740,993.0100" in html
    assert not any(key.startswith("on") for _, attrs in Elements(html).elements for key in attrs)
    assert not any(attrs.get("src", "").startswith("http") for _, attrs in Elements(html).elements)
    assert storefront.price_label({"price": "0.000000000000000001", "currency": "USD"}) == "USD 0.000000000000000001"
    query = client.get(storefront.LIST, params={"q": hostile}).text
    assert hostile in unescape(query)
    assert "{{" not in query and "}}" not in query


def test_home_badges_prove_membership_and_failures_do_not_become_empty_catalogs(client):
    html = client.get(storefront.HOME).text
    assert 'data-badge=' not in html and 'product-badge' not in html
    service = client.app.dependency_overrides[get_shopping_service]()
    service.get_product = Mock(side_effect=CatalogReadUnavailable("private upstream detail"))
    response = client.get(storefront.HOME + "/product/oc-demo-top-0001")
    assert response.status_code == 503 and "private upstream detail" not in response.text
    service.list_products = Mock(return_value={"items": [], "total": -1, "page": 1, "page_size": 12})
    response = client.get(storefront.LIST)
    assert response.status_code == 503 and "상품 0개" not in response.text
    service.list_categories = Mock(return_value={"items": [], "total": 0})
    service.search_products = Mock(side_effect=AssertionError("No collection means no search"))
    response = client.get(storefront.HOME)
    assert response.status_code == 200 and not links(response.text, class_name="product-link")
    service.search_products.assert_not_called()


def test_media_manifest_covers_every_demo_asset_and_exact_remaining_count():
    import hashlib
    import json
    from test_shop_ui_001_storefront import ROOT
    plan = json.loads((ROOT / "brands/orange-coco/assets/media/SHOP_MEDIA_001.json").read_text())
    catalog = json.loads((ROOT / plan["canonical_catalog"]).read_text())["products"]
    assert plan["status"] == "PARTIAL_REPLACEMENT" and plan["replaced_count"] == 7
    assert plan["pending_count"] == 85
    assert sum(item["status"] == "PENDING" for item in plan["assets"]) == 85
    assert sum(item["status"] == "REPLACED" for item in plan["assets"]) == 7
    assert len(plan["assets"]) == len(catalog) == 92
    assert {item["product_id"] for item in plan["assets"]} == {item["id"] for item in catalog}
    assert len({item["target_path"] for item in plan["assets"]}) == 92
    for item in plan["assets"]:
        assert item["target_path"].endswith("/" + item["product_id"] + ".jpg")
        if item["status"] == "PENDING":
            assert item["candidate_path"].startswith(plan["candidate_root"] + "/products/")
        else:
            assert item["generation"]["tool"] == "image_gen (built-in)"
            assert item["current_sha256"] != item["previous_sha256"]
        assert hashlib.sha256((ROOT / item["target_path"]).read_bytes()).hexdigest() == item["current_sha256"]


def test_server_home_feed_failure_returns_empty_feed_and_retry(client):
    service = client.app.dependency_overrides[get_shopping_service]()
    original = service.search_products

    def partial(**kwargs):
        if kwargs["category"] in {"women-tops", "women-bottoms", "women-outer", "women-dresses", "women-bags", "women-accessories"}:
            raise CatalogReadUnavailable("private upstream failure")
        return original(**kwargs)

    service.search_products = partial
    response = client.get(storefront.HOME)
    assert response.status_code == 503
    assert len(links(response.text, class_name="product-link")) == 0
    retry = next(attrs for _, attrs in Elements(response.text).elements if attrs.get("id") == "home-retry")
    assert "hidden" not in retry
    assert "private upstream failure" not in response.text


def test_disabled_service_never_reaches_adapter_from_storefront(client):
    service = client.app.dependency_overrides[get_shopping_service]()
    from dataclasses import replace
    service.settings = replace(service.settings, enabled=False)
    service.catalog = Mock()
    for path in (storefront.HOME, storefront.LIST, storefront.LIST + "?category=women-tops", storefront.HOME + "/product/oc-demo-top-0001"):
        assert client.get(path).status_code == 503
    assert service.catalog.mock_calls == []
