"""Test the same app factory used by the real dev preview, without network I/O."""
import hashlib
import json
import re
from html import unescape

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from core.api.dependencies.shopping import get_shopping_service
from core.api.routes import homepage, shopping
from core.homepage import storefront
from core.homepage.preview import PRESENTATION_VERSION, create_app
from test_shop_ui_001_storefront import ROOT, UI, Elements, fixture_client


def assert_hashtag_token(tag):
    assert isinstance(tag, str) and tag.startswith("#") and len(tag) > 1
    assert not any(character.isspace() for character in tag), repr(tag)


def assert_hashtag_row(row):
    # Split only the renderer's literal separator. Generic split()/strip()
    # would discard tabs, newlines and other whitespace before validation.
    tags = row.split(" ")
    assert len(tags) == 3
    for tag in tags:
        assert_hashtag_token(tag)


def rendered_cards(html):
    # Inert JS templates intentionally have empty fields; validate actual
    # server-rendered cards, including any incorrectly empty live tag rows.
    html = re.sub(r"<template\b[^>]*>.*?</template>", "", html, flags=re.S)
    cards = re.findall(r'<li class="product-card"[^>]*>.*?</li>', html, flags=re.S)
    assert cards
    return cards


@pytest.mark.parametrize("tag", ["#티셔츠", "#데일리", "#내추럴", "#와이드핏", "#daily", "#2026"])
def test_hashtag_contract_accepts_nonempty_tokens_without_whitespace(tag):
    assert_hashtag_token(tag)


@pytest.mark.parametrize("tag", [
    "", "#", "티셔츠", "#티 셔 츠", "#데 일 리", "#와이드 핏",
    " #티셔츠", "#티셔츠 ", "# 티셔츠", "#티\t셔츠", "#티\n셔츠",
    "#티\r셔츠", "#티\u00a0셔츠", "#티\u3000셔츠", "#티셔츠\t",
])
def test_hashtag_contract_rejects_invalid_raw_tokens_and_rendered_rows(tag):
    with pytest.raises(AssertionError):
        assert_hashtag_token(tag)
    with pytest.raises(AssertionError):
        assert_hashtag_row(f"{tag} #데일리 #내추럴")


def test_hashtag_row_accepts_only_complete_tokens():
    assert_hashtag_row("#티셔츠 #데일리 #내추럴")
    with pytest.raises(AssertionError):
        assert_hashtag_row("#티셔츠\t#데일리 #내추럴")


@pytest.fixture
def client():
    with fixture_client() as client:
        yield client


@pytest.mark.parametrize("path,status,meaningful", [
    ("/homepage/storefront", 200, "상품 92개"),
    ("/homepage/storefront/search", 200, "상품 92개"),
    ("/homepage/storefront/search?category=women-tops", 200, "상품 20개"),
    ("/homepage/storefront/search?category=women-tops&page=2", 200, "2 / 2 페이지"),
    ("/homepage/storefront/product/oc-demo-top-0001", 200, "소프트 린넨 블라우스"),
    ("/homepage/storefront/product/no-such-product", 404, "상품을 찾을 수 없습니다"),
])
def test_preview_serves_rendered_meaningful_html(client, path, status, meaningful):
    response = client.get(path)
    assert response.status_code == status
    assert "{{" not in response.text and "}}" not in response.text
    assert meaningful in response.text
    assert response.headers["x-shop-presentation"] == PRESENTATION_VERSION
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("filename", ["storefront.html", "storefront-search.html", "storefront-product.html", "storefront-card.html"])
def test_static_helper_cannot_bypass_server_presentation(filename):
    # The stale preview did exactly this static read before templates were added.
    assert "{{" in (UI / filename).read_text()
    with pytest.raises(ValueError, match="presentation renderer"):
        homepage._ui_asset(filename)
    with pytest.raises(KeyError):
        storefront.template(filename)


def test_preview_launcher_is_repository_owned_and_reloads_python_changes():
    source = (ROOT / "scripts/preview_orange_coco.py").read_text()
    assert '"core.homepage.preview:create_app"' in source
    assert "factory=True" in source and "reload=True" in source
    assert 'host="127.0.0.1"' in source
    assert "ConfigLoader.load = lambda" in source
    assert "test_shop_ui" not in source and "core.api.app" not in source


@pytest.mark.parametrize("path", ["/homepage", "/homepage/status", "/runtime/status", "/shopping/product-drafts",
                                  "/homepage/assets/storefront.html", "/homepage/assets/storefront/unknown.jpg"])
def test_preview_does_not_expose_operator_or_raw_template_routes(client, path):
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("method,path", [
    ("get", "/shopping/inquiries"),
    ("post", "/shopping/inquiries"),
    ("get", "/shopping/inquiries/AG-INQ-000001"),
    ("get", "/shopping/inquiries/AG-INQ-000001/messages"),
    ("post", "/shopping/inquiries/AG-INQ-000001/messages"),
    ("get", "/shopping/operator/inquiries"),
    ("get", "/shopping/operator/inquiries/AG-INQ-000001"),
    ("post", "/shopping/operator/inquiries/AG-INQ-000001/messages"),
])
def test_preview_excludes_legacy_inquiry_and_operator_http_apis(client, method, path):
    if method == "post":
        response = client.post(path, json={"body": "Preview must not expose inquiry APIs"})
    else:
        response = client.get(path)
    assert response.status_code == 404


def test_preview_keeps_storefront_and_catalog_surface_available(client):
    assert client.get("/homepage/storefront").status_code == 200
    assert client.get("/shopping/products").status_code == 200
    assert client.get("/shopping/categories").status_code == 200


def test_hero_is_a_brand_owned_local_jpeg_and_visible_copy_is_fixed(client):
    path = ROOT / "brands/agachichi/assets/media/storefront/hero-agachichi.jpg"
    response = client.get("/homepage/assets/storefront/hero-boutique.jpg")
    assert response.status_code == 200 and response.headers["content-type"] == "image/jpeg"
    assert response.content == path.read_bytes() and response.content.startswith(b"\xff\xd8\xff")
    html = client.get("/homepage/storefront").text
    assert 'src="/homepage/assets/storefront/hero-boutique.jpg"' in html
    assert "매일 편하게," in html and "조금 더 사랑스럽게." in html
    assert "agachichi" in html and "Everyday Comfort, Playful Touch" in html
    assert 'data-feed-filter="all"' in html
    assert "HOT" in html and "추천" not in html
    assert html.count('id="shop-chat-form"') == 1
    assert 'id="shop-chat-product"' in html
    assert len([attrs for _, attrs in Elements(html).elements if attrs.get("class") == "header-search"]) == 1


def test_lookbook_plan_is_deterministic_and_completed_assets_have_matching_checksums():
    from collections import Counter
    import hashlib
    manifest = json.loads((ROOT / "brands/agachichi/assets/media/SHOP_MEDIA_003.json").read_text())
    assert len(manifest["assets"]) == 120
    assert manifest["target_count"] == 120
    completed = sum(item["status"] == "GENERATED" for item in manifest["assets"])
    planned = sum(item["status"] == "PLANNED" for item in manifest["assets"])
    assert completed == 120 and planned == 0
    assert manifest["completed_count"] == completed and manifest["planned_count"] == planned
    assert manifest["source_distribution"] == {"ai_generated": completed, "stock": 0, "unverified_planned": planned}
    assert all(item["source"] is None and item["preferred_sources"] == ["ai_generated"]
               for item in manifest["assets"] if item["status"] == "PLANNED")
    assert Counter(item["category"] for item in manifest["assets"]) == {key: 20 for key in ("TOP", "BOTTOM", "OUTER", "DRESS", "BAG", "ACC")}
    assert len({item["target_path"] for item in manifest["assets"]}) == 120
    completed_hashes = [item["sha256"] for item in manifest["assets"] if item["status"] == "GENERATED"]
    assert len(set(completed_hashes)) == completed
    catalog = ROOT / "brands/agachichi/assets/media/catalog"
    assert {path for path in catalog.rglob("*") if path.is_file()} == {
        ROOT / item["target_path"] for item in manifest["assets"] if item["status"] == "GENERATED"
    }
    for item in manifest["assets"]:
        # Validate raw values before joining/splitting: spaced Korean syllables
        # must never be accepted as individual hashtag fragments.
        assert len(item["presentation_tags"]) == 3
        for tag in item["presentation_tags"]:
            assert_hashtag_token(tag)
        target = ROOT / item["target_path"]
        if item["status"] == "GENERATED":
            assert target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"]
            assert item["source"]["type"] == "ai_generated"
            assert item["generation_tool"] and item["generation_prompt"]
            assert item["source"]["provider"] and item["source"]["generation_date"]
            assert item["source"]["generation_artifact"] and item["source"]["review"]
        else:
            assert item["status"] == "PLANNED" and item["sha256"] is None
            assert not target.exists()


def test_all_agachichi_media_routes_and_raw_rendered_tags_match_local_records():
    manifest = json.loads((ROOT / "brands/agachichi/assets/media/SHOP_MEDIA_003.json").read_text())
    with TestClient(create_app(include_samples=True)) as lookbook:
        for item in manifest["assets"]:
            response = lookbook.get(item["photo_route"])
            if item["status"] == "GENERATED":
                assert response.status_code == 200
                assert response.headers["content-type"] == "image/jpeg"
                assert hashlib.sha256(response.content).hexdigest() == item["sha256"]
            else:
                assert response.status_code == 404
            product = lookbook.get("/shopping/products/" + item["product_id"]).json()
            assert_hashtag_row(storefront.presentation_tags(product))


def test_real_lookbook_composition_prioritizes_editorial_hot_and_update():
    with TestClient(create_app(include_samples=True)) as lookbook:
        html = lookbook.get("/homepage/storefront").text
        assert len(rendered_cards(html)) == 26
        assert 'id="featured-hot-title">HOT' in html and 'id="feed-title">UPDATE' in html
        assert 'id="new-grid"' not in html and 'id="best-grid"' not in html
        for slug in ("women-tops", "women-bottoms", "women-outer", "women-dresses", "women-bags", "women-accessories"):
            response = lookbook.get("/homepage/storefront/search", params={"category": slug, "page_size": 100})
            expected = 22 if slug == "women-outer" else 20
            assert response.status_code == 200 and f"상품 {expected}개" in response.text
        assert lookbook.get("/shopping/products", params={"page_size": 100}).json()["total"] == 122


def test_dev_upload_product_is_classified_priced_and_orderable():
    expected_id = "ag-upload-outer-0001"
    with TestClient(create_app(include_samples=True)) as lookbook:
        service = lookbook.app.dependency_overrides[get_shopping_service]()
        assert expected_id in storefront.dev_orderable(service)
        assert len(storefront.dev_orderable(service)) == 7
        product_response = lookbook.get("/shopping/products/" + expected_id)
        assert product_response.status_code == 200
        product = product_response.json()
        assert product["name"] == "카멜 벨티드 롱 코트"
        assert product["category"] == "OUTER"
        assert product["source"] == "dev_upload"
        assert product["price"] == "300000"
        assert [(v["label"],v["available"]) for v in product["variants"]] == [("S",True),("M",True),("L",True)]
        detail = lookbook.get("/homepage/storefront/product/" + expected_id)
        assert detail.status_code == 200
        assert "300,000원" in detail.text
        assert "DEV 주문 테스트 · 실제 결제·배송 없음" in detail.text
        assert 'id="commerce-panel"' in detail.text
        assert 'data-demo-product="'+expected_id+'"' in detail.text
        assert '/homepage/assets/storefront-commerce.js' in detail.text
        assert detail.text.count('class="variant-option"') == 3
        assert detail.text.count("disabled") == 0
        photo = lookbook.get("/homepage/assets/storefront/catalog/outer/"+expected_id+".jpg")
        assert photo.status_code == 200 and photo.headers["content-type"] == "image/jpeg"
        assert hashlib.sha256(photo.content).hexdigest() == "56d044cf873e0d3c6bd2a21cdd92691791392757c31db0e72799d7c670ede9fc"
        home = lookbook.get("/homepage/storefront")
        assert "카멜 벨티드 롱 코트" in home.text and "#롱코트 #벨티드 #카멜브라운" in home.text
        search = lookbook.get("/homepage/storefront/search",params={"q":"벨티드"})
        assert search.status_code == 200 and expected_id in search.text


def test_media_policy_r1_uses_hashtags_and_disables_legacy_fallback():
    manifest = json.loads((ROOT / "brands/agachichi/assets/media/SHOP_MEDIA_003.json").read_text())
    assert manifest["legacy_fallback_active"] is False
    assert manifest["brand_id"] == "agachichi" and manifest["legacy_fallback_active"] is False
    with TestClient(create_app(include_samples=True)) as lookbook:
        home = lookbook.get("/homepage/storefront").text
        search = lookbook.get("/homepage/storefront/search?category=women-tops").text
        assert home.count("#") >= 72 and search.count("#") >= 3
        assert "/homepage/assets/storefront/photos/" not in home + search
        assert "상품 미리보기 · 현재 구매는 지원하지 않습니다." in home
        pdp = lookbook.get("/homepage/storefront/product/oc-demo-top-0001").text
        assert "소프트 린넨 블라우스" in pdp and "29,000원" in pdp


@pytest.mark.parametrize("path", [
    storefront.HOME, storefront.LIST,
    *[storefront.LIST + f"?category={slug}&page={page}"
      for slug in ("women-tops", "women-bottoms", "women-outer", "women-dresses", "women-bags", "women-accessories")
      for page in (1, 2)],
])
def test_r1_cards_are_image_then_hashtag_only(path):
    with TestClient(create_app(include_samples=True)) as lookbook:
        response = lookbook.get(path)
        assert response.status_code == 200
        assert re.search(r'class="wordmark"[^>]*>agachichi</a>', response.text)
        assert "orange coco" not in response.text.lower()
        assert "오렌지 코코" not in response.text
        assert "/homepage/assets/storefront/photos/" not in response.text
        cards = rendered_cards(response.text)
        expected = 26 if path == storefront.HOME else 10 if "women-outer" in path and "page=2" in path else 8 if "page=2" in path else 12
        assert len(cards) == expected
        for card in cards:
            elements = Elements(card).elements
            assert [(tag, attrs.get("class")) for tag, attrs in elements] == [
                ("li", "product-card"), ("a", "product-link"), ("div", "product-photo"),
                ("img", None), ("span", "photo-fallback"), ("div", "product-caption"), ("p", "product-tags"),
            ]
            photo = next(attrs for tag, attrs in elements if tag == "img")
            assert photo["src"].startswith(("/homepage/assets/storefront/catalog/", "/homepage/assets/storefront/gallery/")) and "hidden" not in photo
            fallback = next(attrs for tag, attrs in elements if tag == "span")
            assert "hidden" in fallback
            assert not any("data-badge" in attrs for _, attrs in elements)
            rows = re.findall(r'<p class="product-tags">([^<]*)</p>', card)
            assert len(rows) == 1
            assert_hashtag_row(unescape(rows[0]))
            # No visible name/price/category/badge/stock/metadata outside the row.
            visible = re.sub(r'<span class="photo-fallback"[^>]*>.*?</span>', "", card, flags=re.S)
            assert unescape(re.sub(r"<[^>]*>", "", visible)).strip() == unescape(rows[0])


def test_r1_pdp_keeps_all_canonical_fields_and_unknown_is_404():
    with TestClient(create_app(include_samples=True)) as lookbook:
        response = lookbook.get("/homepage/storefront/product/oc-demo-top-0001")
        assert response.status_code == 200
        pdp = response.text
        product = lookbook.get("/shopping/products/oc-demo-top-0001").json()
        expected = {
            "detail-name": product["name"],
            "detail-price": storefront.price_label(product),
            "detail-category": storefront.LABELS[product["category"].lower()],
            "detail-availability": "재고 있음" if product["in_stock"] else "품절",
            "detail-description": product["description"],
        }
        for identifier, value in expected.items():
            match = re.search(rf'<[^>]+id="{identifier}"[^>]*>([^<]*)</', pdp)
            assert match and unescape(match[1]) == value
        assert "agachichi" in pdp and "orange coco" not in pdp.lower()
        assert "/homepage/assets/storefront/photos/" not in pdp
        assert lookbook.get("/homepage/storefront/product/no-such-product").status_code == 404


def test_every_home_card_uses_a_replaced_photo_with_truthful_provenance(client):
    html = client.get("/homepage/storefront").text
    ids = [attrs["data-product-id"] for _, attrs in Elements(html).elements if "data-product-id" in attrs]
    assert len(ids) == 24 and len(set(ids)) == 24
    assert all("/homepage/assets/storefront/photos/" not in card for card in re.findall(r'<li class="product-card".*?</li>', html, flags=re.S))


@pytest.mark.parametrize("path", ["/shopping/products?page=1&page_size=12", "/shopping/products/oc-demo-top-0001",
                                  "/shopping/products/no-such-product", "/shopping/categories",
                                  "/shopping/search?category=women-tops&q=블라우스&page=1&page_size=12"])
def test_preview_canonical_json_equals_unmodified_shopping_router(client, path):
    app = FastAPI()
    app.include_router(shopping.router)
    app.dependency_overrides[get_shopping_service] = client.app.dependency_overrides[get_shopping_service]
    with TestClient(app) as canonical:
        expected, actual = canonical.get(path), client.get(path)
        assert actual.status_code == expected.status_code
        assert actual.json() == expected.json()
