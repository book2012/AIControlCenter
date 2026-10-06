"""Escaped, read-only storefront HTML over the canonical Shopping service.

No adapter construction, self-HTTP requests or CMS access belongs in this view.
Slots are substituted once; all source/query values are escaped at the boundary.
"""
from html import escape as html_escape
from importlib.resources import files
from functools import lru_cache
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlencode, urlsplit
from core.homepage import storefront_media

from core.shopping.ports import CatalogReadUnavailable, CatalogReadQueryError
from core.shopping.schemas import ProductResponse, ShoppingCategoryListResponse
from core.shopping.service import ProductNotFoundError, ShoppingService

HOME = "/homepage/storefront"
LIST = HOME + "/search"
PAGE_SIZE = 12
FEED_PAGE_SIZE = 24
HOME_FILTERS = (
    ("all", "전체", ""), ("hot", "HOT", ""), ("sale", "SALE", ""), ("update", "UPDATE", ""),
    ("top", "TOP", "women-tops"), ("bottom", "BOTTOM", "women-bottoms"),
    ("outer", "OUTER", "women-outer"), ("dress", "DRESS", "women-dresses"),
    ("bag", "BAG", "women-bags"), ("acc", "ACC", "women-accessories"),
    # Forward-compatible category filter; no canonical MEN catalog exists yet.
    ("men", "MEN", "men"),
)
COLLECTION_SOURCE = Path(__file__).resolve().parents[2] / "brands/orange-coco/catalog/lookbook-preview/collections.json"
LABELS = {
    "new": "신상품", "best": "인기 상품", "sale": "할인 상품",
    "top": "상의", "bottom": "하의", "outer": "아우터", "dress": "원피스",
    "bag": "가방", "acc": "액세서리", "women-tops": "상의", "women-bottoms": "하의",
    "women-outer": "아우터", "women-dresses": "원피스", "women-bags": "가방",
    "women-accessories": "액세서리",
}
UNAVAILABLE = "상품을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요."


def escape(value: str) -> str:
    # Preserve literal canonical braces as visible text, without template tokens
    # in the HTML source (including deliberately hostile names/query strings).
    return html_escape(value).replace("{", "&#123;").replace("}", "&#125;")


def template(filename: str, **values: str) -> str:
    source = files("core.homepage.ui").joinpath(filename).read_text(encoding="utf-8")
    result = re.sub(r"\{\{([^{}]+)\}\}", lambda match: values[match[1]], source)
    if "{{" in result or "}}" in result:
        raise ValueError("Unresolved storefront template")
    return result


def rendered(filename: str, values: dict, code: int, retry_id: str, service=None) -> tuple[str, int]:
    values["media"] = storefront_media.browser_mapping()
    if service is not None and getattr(service, "_dev_uploaded_only", False) is True:
        values["media"] = json.dumps({key: value for key, value in json.loads(values["media"]).items() if key.startswith("ag-upload-")}, ensure_ascii=False)
    html = template(filename, **values)
    if service is not None:
        from core.homepage.storefront_chat import widget
        chat_html = widget(service, values.get("product_id", ""))
        if chat_html:
            html = re.sub(r'<section id="inquiry-section".*?</section>', "", html, flags=re.S)
        html = html.replace("</body>", chat_html + "</body>")
    if code == 503:
        html = re.sub(rf'(<button id="{retry_id}"[^>]*?) hidden', r"\1", html, count=1)
    return html, code


def browse_state(category: str = "", q: str = "", page: str = "1", collection: str = "") -> dict:
    number = int(page) if re.fullmatch(r"[0-9]{1,16}", page) else 1
    return {"category": category.strip()[:100], "q": q.strip()[:200], "collection": collection.strip().lower()[:40],
            "page": number if 0 < number <= 9007199254740991 else 1}


def listing_url(state: dict) -> str:
    params = {key: state[key] for key in ("category", "q") if state.get(key)}
    if state.get("page", 1) != 1:
        params["page"] = str(state["page"])
    return LIST + ("?" + urlencode(params) if params else "")


def home_url(state: dict) -> str:
    """Shareable Home feed state; collection and category remain distinct."""
    params = {}
    if state.get("collection") in {"hot", "sale", "update"}:
        params["collection"] = state["collection"]
    elif state.get("category"):
        params["category"] = state["category"]
    if state.get("page", 1) != 1:
        params["page"] = str(state["page"])
    return HOME + (("?" + urlencode(params)) if params else "")


def return_url(raw: str) -> str:
    try:
        url = urlsplit(raw)
        if url.scheme or url.netloc or url.fragment or url.path not in (HOME, LIST):
            return LIST
        params = parse_qs(url.query)
        if url.path == HOME:
            return home_url(browse_state(params.get("category", [""])[0], "", params.get("page", ["1"])[0], params.get("collection", [""])[0]))
        return listing_url(browse_state(*(params.get(key, [default])[0]
                                         for key, default in (("category", ""), ("q", ""), ("page", "1")))))
    except ValueError:
        return LIST


def product_data(raw: dict) -> dict:
    product = ProductResponse.model_validate(raw).model_dump(mode="json")
    if (not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", product["id"])
            or not product["name"].strip() or not re.fullmatch(r"[A-Z]{3}", product["currency"])):
        raise ValueError("Invalid product presentation")
    for value in product.values():
        if isinstance(value, str):
            value.encode("utf-8")
    return product


def price_label(product: dict) -> str:
    # Zero is a sentinel only for DEV upload records awaiting operator price input.
    from decimal import Decimal
    if product.get("source") == "dev_upload" and Decimal(product["price"]) == 0:
        return "가격 준비 중"
    whole, dot, fraction = format(Decimal(product["price"]), "f").partition(".")
    grouped = re.sub(r"\B(?=(\d{3})+(?!\d))", ",", whole)
    amount = grouped + dot + fraction
    return amount + "원" if product["currency"] == "KRW" else product["currency"] + " " + amount


def photo_url(product: dict) -> str | None:
    mapped = storefront_media.photo(product)
    if mapped:
        return mapped
    return None


def presentation_tags(product: dict) -> str:
    """Deterministic editorial hashtags; never asserts commerce facts."""
    name = product["name"].lower()
    category = product["category"].lower()
    tags = {
        "top": ["#상의", "#데일리", "#미니멀"], "bottom": ["#팬츠", "#클래식", "#심플"],
        "outer": ["#아우터", "#소프트", "#가을무드"], "dress": ["#원피스", "#페미닌", "#데일리룩"],
        "bag": ["#가방", "#미니멀", "#데일리백"], "acc": ["#액세서리", "#포인트", "#데일리"],
    }.get(category, ["#아가치치", "#데일리"])
    if any(word in name for word in ("블라우스", "셔츠")): tags[0] = "#블라우스" if "블라우스" in name else "#셔츠"
    if any(word in name for word in ("오버핏", "와이드")): tags[1] = "#오버핏"
    if any(word in name for word in ("니트", "가디건")): tags[1] = "#니트"
    if product["source"] == "dev_upload" and "코트" in name:
        tags = ["#롱코트" if "롱" in name else "#코트", "#벨티드" if "벨티드" in name else "#아우터", "#카멜브라운" if "카멜" in name else "#오트밀베이지" if "오트밀" in name else "#가을무드"]
    return " ".join(tags[:3])


def _categories(service: ShoppingService) -> list[dict]:
    if not service.settings.enabled:
        raise CatalogReadUnavailable("shopping_catalog_unavailable")
    items = ShoppingCategoryListResponse.model_validate(service.list_categories()).model_dump()["items"]
    if (any(not item["id"] or not item["slug"] or len(item["id"]) > 100 or len(item["slug"]) > 100 for item in items)
            or len({item["slug"] for item in items}) != len(items)
            or len({item["id"] for item in items}) != len(items)):
        raise ValueError("Invalid categories")
    return [{**item, "label": LABELS.get(item["slug"].lower(), LABELS.get(item["name"].lower(), item["name"]))}
            for item in items if not any(item[key].strip().lower() == "hot" for key in ("slug", "name"))]


def _page(service: ShoppingService, state: dict, category_id: str | None = None, size: int = PAGE_SIZE) -> dict:
    if not service.settings.enabled:
        raise CatalogReadUnavailable("shopping_catalog_unavailable")
    page = state.get("page", 1)
    if category_id or state.get("q"):
        raw = service.search_products(query=state.get("q") or None, category=category_id,
                                      minimum_price=None, maximum_price=None, in_stock=None,
                                      page=page, page_size=size)
    else:
        raw = service.list_products(page=page, page_size=size)
    if (type(raw["total"]) is not int or raw["total"] < 0 or raw["page"] != page or raw["page_size"] != size
            or len(raw["items"]) != min(size, max(0, raw["total"] - (page - 1) * size))):
        raise ValueError("Invalid collection")
    items = [product_data(item) for item in raw["items"]]
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("Duplicate product")
    return {"items": items, "total": raw["total"]}


def category_links(items: list[dict], state: dict, *, home: bool = False) -> str:
    links = []
    for item in [{"id": "", "slug": "", "label": "전체 상품"}, *items]:
        if home and item["slug"] in ("new", "best", "sale"):
            continue
        href = listing_url({"category": item["slug"], "q": "" if home else state.get("q", "")})
        current = ' aria-current="page"' if item["slug"] == state.get("category", "") else ""
        links.append(f'<a href="{escape(href)}" data-category="{escape(item["slug"])}" '
                     f'data-category-id="{escape(item["id"])}"{current}>{escape(item["label"])}</a>')
    return "\n".join(links)


def home_filters(state: dict) -> str:
    links = []
    active = state.get("collection") if state.get("collection") in {"hot", "sale", "update"} else (
        next((key for key, _, slug in HOME_FILTERS if slug and slug == state.get("category")), "all")
    )
    for key, label, slug in HOME_FILTERS:
        params = {"collection": key} if key in {"hot", "sale", "update"} else {"category": slug} if slug else {}
        href = HOME + ("?" + urlencode(params) if params else "")
        current = ' aria-current="page"' if key == active else ""
        kind = "collection" if key in {"hot", "sale", "update"} else "category"
        links.append(f'<a href="{escape(href)}" data-feed-filter="{key}" data-feed-kind="{kind}"{current}>{escape(label)}</a>')
    return "\n".join(links)


@lru_cache(maxsize=1)
def _presentation_collections() -> dict[str, set[str]]:
    try:
        data = json.loads(COLLECTION_SOURCE.read_text(encoding="utf-8"))["collections"]
        return {key: set(value.get("product_ids", [])) for key, value in data.items()}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def _home_collection_ids(collection: str) -> set[str] | None:
    memberships = _presentation_collections()
    if collection == "hot":
        # No explicit HOT membership exists in the current canonical/presentation data.
        return set()
    if collection == "sale":
        # The demo has no canonical sale/discount field; never infer SALE from a list.
        return set()
    if collection == "update":
        # UPDATE is the deterministic explicit NEW collection policy.
        return memberships.get("new", set())
    return None


def _home_page(service: ShoppingService, state: dict, available: list[dict]) -> tuple[list[dict], int]:
    """Read one bounded Home page through the canonical Shopping pagination model."""
    page = state.get("page", 1)
    primary_collection = state.get("collection") in {"hot", "sale", "update"}
    if state.get("collection") == "hot":
        ids=getattr(service,"_dev_hot_product_ids",())
        if type(ids) is not tuple or any(type(v) is not str or re.fullmatch(r"[A-Za-z0-9_-]{1,128}",v) is None for v in ids):raise ValueError("Invalid editorial collection")
        products=[product_data(service.get_product(v)) for v in ids]
        start=(page-1)*FEED_PAGE_SIZE
        return products[start:start+FEED_PAGE_SIZE],len(products)
    if state.get("collection") == "sale":
        return [], 0
    if state.get("collection") == "update":
        payload = _page(service, {"page": page}, "new", size=FEED_PAGE_SIZE)
        return payload["items"], payload["total"]
    if state.get("category") and not primary_collection:
        category = next((item for item in available if item["slug"] == state["category"]), None)
        if not category:
            return [], 0
        payload = _page(service, {"page": page}, category["id"], size=FEED_PAGE_SIZE)
        return payload["items"], payload["total"]
    # One small page per canonical category gives a mixed feed without loading
    # the entire catalog into one server response.
    products, total = [], 0
    for slug in storefront_media.CATEGORIES.values():
        category = next((item for item in available if item["slug"] == slug), None)
        if not category:
            continue
        payload = _page(service, {"page": page}, category["id"], size=4)
        products.extend(payload["items"])
        total += payload["total"]
    return _interleave_products(products), total


def _interleave_products(products: list[dict]) -> list[dict]:
    """Round-robin categories so the default editorial feed visibly mixes styles."""
    buckets: dict[str, list[dict]] = {}
    for product in products:
        buckets.setdefault(product["category"].lower(), []).append(product)
    mixed = []
    for index in range(max((len(items) for items in buckets.values()), default=0)):
        for category in ("top", "bottom", "outer", "dress", "bag", "acc"):
            if index < len(buckets.get(category, [])):
                mixed.append(buckets[category][index])
    return mixed


def dev_orderable(service: ShoppingService) -> frozenset[str]:
    value=getattr(service,"_dev_orderable_products",frozenset())
    if type(value) is not frozenset or any(type(v) is not str or re.fullmatch(r"[A-Za-z0-9_-]{1,128}",v) is None for v in value):return frozenset()
    return value


def cards(items: list[dict], back: str, badge: str = "") -> str:
    result = []
    for product in items:
        photo = photo_url(product)
        href = HOME + "/product/" + product["id"] + "?" + urlencode({"return_to": back})
        result.append(template("storefront-card.html", id=escape(product["id"]), href=escape(href),
                               name=escape(product["name"]), price=escape(price_label(product)), tags=escape(presentation_tags(product)),
                               category="", availability="",
                               image_attrs=f'src="{escape(photo)}"' if photo else "hidden",
                               fallback_hidden="hidden" if photo else "", badge=badge,
                               badge_hidden="" if badge else "hidden"))
    return "\n".join(result)


def variant_controls(product: dict) -> str:
    from core.homepage.storefront_gallery import color_fronts
    previews=color_fronts(product["id"]) if product["source"]=="dev_upload" else {}
    variants = product.get("variants") or []
    if not variants:
        return '<p class="variant-empty">판매 옵션 준비 중입니다.</p>'
    controls = []
    for index, variant in enumerate(variants):
        disabled = " disabled" if not variant["available"] and variant["option_type"] != "color" else ""
        pressed = "false"
        color = variant["id"].removeprefix(product["id"]+"-") if variant["option_type"]=="color" else None
        preview = previews.get(color)
        attrs = (' data-color-id="'+escape(color)+'"'+(' data-color-image="'+escape(preview["url"])+'"' if preview else "")) if color else ""
        controls.append(f'<button type="button" class="variant-option" data-variant-id="{escape(variant["id"])}"{attrs} aria-pressed="{pressed}"{disabled}>{escape(variant["label"])}</button>')
    title = "색상 선택 · 재고는 주문 시 확인" if all(v["option_type"] == "color" for v in variants) else "사이즈 선택"
    return '<div class="variant-options" role="group" aria-label="' + title + '">' + "".join(controls) + "</div>"


def home(service: ShoppingService, state: dict | None = None) -> tuple[str, int]:
    state = state or browse_state()
    featured=getattr(service,"_dev_featured_home",False) is True
    default_featured=featured and not state.get("category") and not state.get("collection")
    if default_featured:state={**state,"collection":"update"}
    values = {"featured":"","feed_title":"UPDATE" if state.get("collection")=="update" else "HOT" if state.get("collection")=="hot" else "피드","filters": home_filters(state), "feed": "", "feed_status": "", "feed_count": "",
              "feed_more": "", "feed_more_hidden": "hidden"}
    code = 200
    try:
        available = _categories(service)
    except Exception:
        available, code = [], 503
        values["feed_status"] = "카테고리를 불러오지 못했습니다."
    try:
        if default_featured:
            hot,_=_home_page(service,{**state,"collection":"hot","page":1},available)
            if hot:values["featured"]='<section aria-labelledby="featured-hot-title"><div class="feed-heading"><h2 id="featured-hot-title">HOT</h2><p>에디터가 고른 아우터</p></div><ul class="product-grid" aria-label="HOT 추천 상품">'+cards(hot,HOME,badge="HOT")+'</ul></section>'
        products, total = _home_page(service, state, available)
        products = [product for product in products if product["source"] in {"demo", "dev_upload"}]
        values["feed"] = cards(products, home_url(state))
        values["feed_count"] = f"상품 {total}개"
        if len(products) == FEED_PAGE_SIZE and total > state.get("page", 1) * FEED_PAGE_SIZE:
            values["feed_more"] = f'<a id="feed-load-more" class="browse-link" href="{escape(home_url({**state, "page": state.get("page", 1) + 1}))}">더 보기 · 다음 피드 ↗</a>'
            values["feed_more_hidden"] = ""
        if not products:
            values["feed_status"] = ("SALE 상품이 없습니다. 현재 canonical 할인 데이터가 없습니다." if state.get("collection") == "sale"
                                      else "HOT 상품이 없습니다. 명시된 HOT 컬렉션이 없습니다." if state.get("collection") == "hot"
                                      else "조건에 맞는 상품이 없습니다.")
    except Exception:
        values["feed_status"], code = UNAVAILABLE, 503
    return rendered("storefront.html", values, code, "home-retry", service)


def search(service: ShoppingService, state: dict) -> tuple[str, int]:
    code, category_status, available = 200, "", []
    try:
        available = _categories(service)
    except Exception:
        category_status = "카테고리를 불러오지 못했습니다."
    category = next((item for item in available if item["slug"] == state["category"]), None)
    label = category["label"] if category else "선택한 카테고리" if state["category"] else "전체 상품"
    try:
        if state["category"] and category_status:
            raise CatalogReadUnavailable("shopping_catalog_unavailable")
        if state["category"] and not category:
            payload = {"items": [], "total": 0}
        else:
            payload = _page(service, state, category["id"] if category else None)
        status = "" if payload["items"] else "조건에 맞는 상품이 없습니다. 검색어나 페이지를 바꿔 보세요."
    except Exception:
        payload, status, code = {"items": [], "total": 0}, UNAVAILABLE, 503
    total, page = payload["total"], state["page"]
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
    values = {"category": escape(state["category"]), "query": escape(state["q"]),
              "categories": category_links(available, state), "category_status": category_status,
              "search_context": escape(label + " 안에서 검색합니다."),
              "conditions": escape("카테고리: " + label + (" · 검색어: ‘" + state["q"] + "’" if state["q"] else "")),
              "count": f"상품 {total}개" if code == 200 else "상품을 불러오지 못했습니다", "status": status,
              "clear_hidden": "" if state["category"] or state["q"] else "hidden",
              "cards": cards(payload["items"], listing_url(state)),
              "pagination_hidden": "hidden" if code != 200 or (pages <= 1 and page == 1) else "",
              "previous": escape(listing_url({**state, "page": max(1, page - 1)})),
              "next": escape(listing_url({**state, "page": page + 1})),
              "previous_hidden": "hidden" if page <= 1 else "", "next_hidden": "hidden" if page >= pages else "",
              "page_label": f"{page} / {pages} 페이지"}
    for query in ("블라우스", "미니멀", "내추럴", "주말", "출근"):
        values["mood_" + query] = escape(listing_url({**state, "q": query, "page": 1}))
    return rendered("storefront-search.html", values, code, "retry", service)


def detail(service: ShoppingService, product_id: str, back: str) -> tuple[str, int]:
    back = return_url(back)
    values = {"return_url": escape(back), "return_label": "← 홈으로" if back == HOME else "← 상품 목록으로",
              "name": "상품을 찾을 수 없습니다", "category": "", "price": "", "availability": "", "description": "",
              "variant_title": "SIZE", "dimension_id": "purchase-size", "other_dimension": "", "variants": '<p class="variant-empty">판매 옵션 준비 중입니다.</p>', "inquiry_hidden": "hidden", "product_id": "",
              "photo_hidden": "hidden", "image_attrs": "hidden", "fallback_hidden": "",
              "gallery": "", "hero_caption": "", "description_hidden": "hidden", "status": "상품이 없거나 현재 공개되지 않았습니다.", "dev_order_panel": "", "dev_order_assets": "", "commerce_notice": "상품 미리보기 · 현재 구매는 지원하지 않습니다."}
    code = 200
    try:
        product = product_data(service.get_product(product_id))
        if product["id"] != product_id:
            raise ValueError("Product identity mismatch")
        pending_stock = getattr(service.catalog, "dev_upload_inventory_pending", lambda _: False)(product_id)
        color_options = bool(product.get("variants")) and all(v["option_type"] == "color" for v in product["variants"])
        other_dimension = '<div id="purchase-size" class="purchase-field"><h2>SIZE · 사이즈</h2><p class="purchase-fixed">사이즈 확인 중</p></div>' if color_options else '<div id="purchase-color" class="purchase-field"><h2>COLOR · 컬러</h2><p class="purchase-fixed">'+escape({"ag-upload-outer-0001":"카멜","ag-upload-outer-0002":"오트밀"}.get(product_id,"컬러 확인 중"))+'</p></div>'
        photo = photo_url(product)
        from core.homepage.storefront_gallery import for_product, front
        gallery_rows = for_product(product_id) if product["source"] == "dev_upload" else []
        model = front(product_id) if product["source"] == "dev_upload" else None
        if model:photo = model["url"]
        gallery = '<section class="detail-gallery" aria-label="상품 사진"><h2>상품 사진</h2>' + "".join('<figure><img loading="lazy" src="'+escape(row["url"])+'" alt="'+escape(product["name"]+" · "+row["label"])+'"><figcaption>'+escape(row["label"])+ (" · 원본을 바탕으로 AI 보정한 이미지" if row["kind"] == "garment-cutout" else " · 실제 착용·보이지 않는 각도와 다를 수 있는 AI 예상 이미지")+'</figcaption></figure>' for row in for_product(product_id)) + '</section>' if product["source"] == "dev_upload" else ""
        values.update(hero_caption=('<span class="model-hero-caption">AI 모델 착용 참고 · 정면<br>실제 착용·보이지 않는 각도와 다를 수 있습니다.</span>' if model else ""),gallery=gallery,name=escape(product["name"]), category=escape(LABELS.get(product["category"].lower(), product["category"])), price=escape(price_label(product)+(" · 임시 가격" if pending_stock else "")),
                      availability="사이즈·재고 확인 중" if pending_stock else "재고 있음" if product["in_stock"] else "품절",
                      variant_title="COLOR" if color_options else "SIZE",
                      dimension_id="purchase-color" if color_options else "purchase-size", other_dimension=other_dimension,
                      description=escape(product["description"] or "등록된 상품 설명이 없습니다."),
                      variants=variant_controls(product), product_id=escape(product["id"]),
                      photo_hidden="", image_attrs=f'src="{escape(photo)}"' if photo else "hidden",
                      fallback_hidden="hidden" if photo else "", description_hidden="", status="",
                      inquiry_hidden="hidden" if product["id"] in dev_orderable(service) else "",
                      dev_order_panel=('<section id="commerce-panel" class="commerce-panel" data-demo-product="'+escape(product["id"])+'"><p>주문 기능을 불러오는 중…</p></section>' if product["id"] in dev_orderable(service) else ""),
                      dev_order_assets=('<script src="/homepage/assets/storefront-commerce.js" defer></script>' if product["id"] in dev_orderable(service) else ""),
                      commerce_notice=("DEV 주문 테스트 · 실제 결제·배송 없음" if product["id"] in dev_orderable(service)
                                       else "가격 입력 후 주문 가능 · S/M/L 재고 등록 완료" if product["source"] == "dev_upload" and str(product["price"]) in {"0", "0.0"}
                                       else "상품 미리보기 · 현재 구매는 지원하지 않습니다."))
    except (ProductNotFoundError, CatalogReadQueryError):
        code = 404
    except Exception:
        code = 503
        values.update(name="상품을 불러오지 못했습니다", status=UNAVAILABLE)
    return rendered("storefront-product.html", values, code, "detail-retry", service)
