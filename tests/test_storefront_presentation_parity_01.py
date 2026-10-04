"""Offline source contract for STOREFRONT-PRESENTATION-PARITY-01."""

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "deploy/shopping/wordpress/plugins/ai-shopping-storefront"
MAIN = (PLUGIN / "ai-shopping-storefront.php").read_text()
RENDERER = (PLUGIN / "includes/class-renderer.php").read_text()
SHORTCODES = (PLUGIN / "includes/class-shortcodes.php").read_text()
DETAIL = (PLUGIN / "includes/renderers/class-product-detail-renderer.php").read_text()
FRONT = (PLUGIN / "templates/storefront-front-page.php").read_text()
PRODUCT = (PLUGIN / "templates/product-detail.php").read_text()
CSS = (PLUGIN / "assets/agachichi-v1.css").read_text()
JS = (PLUGIN / "assets/storefront-ui.js").read_text()
MEDIA = json.loads((PLUGIN / "assets/agachichi-v1/deployment-manifest.json").read_text())


def test_candidate_identity_and_dev_reference_contract():
    assert "Version: 0.19.0" in MAIN
    assert "'0.19.0'" in MAIN
    assert "SHOP_MEDIA_003_AGACHICHI" in MAIN
    assert "core/homepage" not in FRONT + PRODUCT
    assert "dev.bokstory.duckdns.org" not in MAIN + RENDERER + SHORTCODES + DETAIL + JS


def test_homepage_contract_matches_dev_structure_and_order():
    assert RENDERER.index('class="hero"') < RENDERER.index('class="filter-rail"')
    assert RENDERER.index('class="filter-rail"') < RENDERER.index('id="feed-title"')
    assert RENDERER.index('id="feed-title"') < RENDERER.index('id="home-feed"')
    for text in ("매일 편하게,", "조금 더 사랑스럽게.", "피드", "전체 상품 둘러보기 · 검색"):
        assert text in RENDERER
    for key in ("all", "hot", "sale", "update", "top", "bottom", "outer", "dress", "bag", "acc", "men"):
        assert f"['{key}'," in RENDERER
    assert "agachichi-hero" not in RENDERER + FRONT
    assert "ACCOUNT" not in RENDERER + FRONT
    assert "BAG" not in FRONT


def test_search_contract_persists_query_category_and_empty_state():
    for text in (
        'name="ai_shop_q"',
        'name="ai_shop_category"',
        'id="search-input"',
        'id="category-nav"',
        '이런 검색어는 어때요?',
        '검색어 예시이며, 상품 속성 필터가 아닙니다.',
        '조건에 맞는 상품이 없습니다. 검색어나 페이지를 바꿔 보세요.',
        '검색·카테고리 초기화',
    ):
        assert text in RENDERER
    assert "category_slug" in SHORTCODES
    assert "'page' => $search_filters['page']" in SHORTCODES
    assert "'page_size' => 12" in SHORTCODES


def test_pagination_page_two_and_back_navigation_contract():
    assert "ai_shop_page" in RENDERER
    assert "max(1, $page - 1)" in RENDERER
    assert "['page' => $page + 1]" in RENDERER
    assert "return_to" in RENDERER
    assert "← 이전" in RENDERER
    assert "다음 →" in RENDERER
    assert 'id="back-to-list"' in DETAIL
    assert "← 홈으로" in DETAIL
    assert "← 상품 목록으로" in DETAIL


def test_product_detail_contract_has_dev_metadata_and_behavior():
    for text in (
        'id="detail-view"',
        'class="detail-layout"',
        'detail-photo',
        'id="detail-category"',
        'id="detail-name"',
        'id="detail-price"',
        'id="detail-availability"',
        'id="detail-variants"',
        '상품 문의',
        '상품 미리보기 · 현재 구매는 지원하지 않습니다.',
        'id="detail-description"',
        '상품 설명',
        '재고 있음',
        '품절',
    ):
        assert text in DETAIL
    assert "AI_Shopping_Agachichi_Presentation_Adapter::image_url" in DETAIL
    assert "static IVORY" not in DETAIL
    assert "카카오 구매 문의" not in DETAIL
    assert "You May Also Like" not in DETAIL


def test_responsive_contract_matches_dev_breakpoints_and_media_ratio():
    assert "@media (max-width: 900px)" in CSS
    assert "@media (max-width: 600px)" in CSS
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in CSS
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in CSS
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in CSS
    assert "aspect-ratio: 2 / 3" in CSS
    assert "filter-rail a[data-feed-filter=\"hot\"]" in CSS
    assert "filter-rail a[data-feed-filter=\"men\"]" in CSS


def test_media_contract_remains_pass_and_identifier_unchanged():
    assert MEDIA["presentation_identifier"] == "SHOP_MEDIA_003_AGACHICHI"
    assert MEDIA["source_manifest"] == "brands/agachichi/assets/media/SHOP_MEDIA_003.json"
    assert MEDIA["media_count"] == len(MEDIA["assets"])
    assert MEDIA["product_media_count"] == 120
    assert "hero_url" in RENDERER
    assert "image_url" in RENDERER and "image_url" in DETAIL


def test_browser_and_wordpress_boundaries_remain_safe():
    assert "host.docker.internal" not in JS
    assert "58081" not in JS
    assert "consumer_key" not in JS
    assert "consumer_secret" not in JS
    assert "Authorization" not in JS
    assert "wp_remote_get" not in RENDERER + SHORTCODES + DETAIL
    assert "woocommerce" not in RENDERER.lower() + SHORTCODES.lower() + DETAIL.lower()
    assert "/homepage/assets/" not in MAIN + RENDERER + SHORTCODES + DETAIL + FRONT + PRODUCT + JS
    migration = (ROOT / "tests/test_public_storefront_migration_02.py").read_text()
    assert "reverse_proxy 127.0.0.1:58081" in migration
