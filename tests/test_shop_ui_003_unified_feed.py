"""SHOP_UI_003 unified agachichi Home feed contracts."""
import re
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient

from core.homepage.preview import create_app


class Elements(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.elements = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def cards(html):
    html = re.sub(r"<template\b[^>]*>.*?</template>", "", html, flags=re.S)
    return re.findall(r'<li class="product-card"[^>]*>.*?</li>', html, flags=re.S)


def ids(html):
    return re.findall(r'data-product-id="([^"]+)"', html)


def test_default_home_is_one_mixed_feed_and_filters_are_shareable():
    with TestClient(create_app()) as client:
        response = client.get("/homepage/storefront")
        assert response.status_code == 200
        html = response.text
        assert len(cards(html)) == 24
        assert 'id="feed-count">상품 120개<' in html
        assert {value.split("-")[2] for value in ids(html)} == {"top", "bottom", "outer", "dress", "bag", "acc"}
        assert [value.split("-")[2] for value in ids(html)[:6]] == ["top", "bottom", "outer", "dress", "bag", "acc"]
        assert 'id="new-grid"' not in html and 'id="best-grid"' not in html
        assert 'category-lookbook' not in html and 'data-lookbook-category' not in html
        assert [a[1]["data-feed-filter"] for a in Elements(html).elements if a[0] == "a" and "data-feed-filter" in a[1]] == [
            "all", "hot", "sale", "update", "top", "bottom", "outer", "dress", "bag", "acc", "men"
        ]
        for slug, prefix in (("women-tops", "top"), ("women-bottoms", "bottom"), ("women-outer", "outer"),
                             ("women-dresses", "dress"), ("women-bags", "bag"), ("women-accessories", "acc")):
            filtered = client.get("/homepage/storefront", params={"category": slug})
            assert filtered.status_code == 200
            assert ids(filtered.text) and {value.split("-")[2] for value in ids(filtered.text)} == {prefix}
        page_two = client.get("/homepage/storefront?page=2")
        assert page_two.status_code == 200 and ids(page_two.text) != ids(html)


def test_collection_filters_stay_separate_and_use_truthful_empty_states():
    with TestClient(create_app()) as client:
        for collection in ("hot", "sale"):
            response = client.get("/homepage/storefront", params={"collection": collection})
            assert response.status_code == 200
            assert not ids(response.text)
            assert collection.upper() in response.text
        update = client.get("/homepage/storefront?collection=update")
        assert update.status_code == 200 and ids(update.text)
        assert {value.split("-")[2] for value in ids(update.text)} <= {"top", "bottom", "outer", "dress", "bag", "acc"}
        both = client.get("/homepage/storefront?category=women-tops&collection=update")
        assert both.status_code == 200
        # V1 has one primary filter; collection takes precedence in the rendered state.
        assert 'data-feed-filter="update"' in both.text and 'aria-current="page"' in both.text.split('data-feed-filter="update"', 1)[1].split(">", 1)[0]
        assert 'data-feed-filter="top"' in both.text and 'aria-current="page"' not in both.text.split('data-feed-filter="top"', 1)[1].split(">", 1)[0]


def test_men_is_forward_compatible_and_has_a_valid_empty_state():
    with TestClient(create_app()) as client:
        response = client.get("/homepage/storefront?category=men")
        assert response.status_code == 200
        assert 'data-feed-filter="men"' in response.text
        assert 'data-feed-filter="men"' in response.text and 'aria-current="page"' in response.text.split('data-feed-filter="men"', 1)[1].split(">", 1)[0]
        assert not ids(response.text)
        assert "조건에 맞는 상품이 없습니다." in response.text


def test_cards_are_image_and_hashtags_only_and_search_remains_dedicated():
    with TestClient(create_app()) as client:
        home = client.get("/homepage/storefront").text
        rendered = re.sub(r"<template\b[^>]*>.*?</template>", "", home, flags=re.S)
        assert "product-name" not in rendered and "product-price" not in rendered and "product-category" not in rendered
        assert "data-badge=" not in rendered and "product-badge" not in rendered and "재고 있음" not in rendered
        assert all(re.fullmatch(r"#[^\s]+ #[^\s]+ #[^\s]+", row)
                   for row in re.findall(r'<p class="product-tags">([^<]*)</p>', rendered))
        assert client.get("/homepage/storefront/search?q=블라우스&page=1").status_code == 200
        assert 'id="search-panel"' in client.get("/homepage/storefront/search").text
        assert client.get("/homepage/storefront/product/oc-demo-top-0001").status_code == 200
        assert client.get("/homepage/storefront/product/no-such-product").status_code == 404


def test_filter_hrefs_encode_distinct_semantics_and_back_urls():
    with TestClient(create_app()) as client:
        html = client.get("/homepage/storefront").text
        elements = Elements(html).elements
        links = {a[1]["data-feed-filter"]: a[1]["href"] for a in elements if a[0] == "a" and "data-feed-filter" in a[1]}
        assert links["all"] == "/homepage/storefront"
        assert parse_qs(urlsplit(links["top"]).query) == {"category": ["women-tops"]}
        assert parse_qs(urlsplit(links["hot"]).query) == {"collection": ["hot"]}
        assert parse_qs(urlsplit(links["sale"]).query) == {"collection": ["sale"]}
        assert parse_qs(urlsplit(links["update"]).query) == {"collection": ["update"]}
        card = re.search(r'href="([^"]+return_to=%2Fhomepage%2Fstorefront%3Fcategory%3Dwomen-tops)"', client.get("/homepage/storefront?category=women-tops").text)
        assert card
        detail = client.get(card.group(1).replace("&amp;", "&"))
        assert detail.status_code == 200 and 'href="/homepage/storefront?category=women-tops"' in detail.text


def test_pdp_variants_are_read_model_data_with_disabled_and_free_options():
    with TestClient(create_app()) as client:
        sized = client.get("/homepage/storefront/product/oc-demo-top-0001")
        assert sized.status_code == 200
        assert '<h2 id="variant-title">SIZE</h2>' in sized.text
        assert 'data-variant-id="oc-demo-top-0001-s"' in sized.text
        assert 'data-variant-id="oc-demo-top-0001-m"' in sized.text
        assert 'data-variant-id="oc-demo-top-0001-l"' in sized.text and 'disabled' in sized.text.split('data-variant-id="oc-demo-top-0001-l"', 1)[1].split('>', 1)[0]
        free = client.get("/homepage/storefront/product/oc-demo-top-0002")
        assert 'data-variant-id="oc-demo-top-0002-free"' in free.text and ">FREE<" in free.text
        empty = client.get("/homepage/storefront/product/oc-demo-top-0003")
        assert "판매 옵션 준비 중입니다." in empty.text


def test_variant_payload_is_canonical_and_not_hardcoded_in_pdp_template():
    with TestClient(create_app()) as client:
        payload = client.get("/shopping/products/oc-demo-top-0001").json()
        assert [(item["label"], item["available"]) for item in payload["variants"]] == [("S", True), ("M", True), ("L", False)]
        template = open("core/homepage/ui/storefront-product.html", encoding="utf-8").read()
        assert "data-variant-id" not in template and "<button class=\"variant-option\"" not in template
