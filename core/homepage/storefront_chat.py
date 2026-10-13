"""Shared, page-aware DEV shopping chat presentation."""
from html import escape as html_escape, unescape
import json
import re

PAGE_GUIDES = {
    "product": ("상품 상세", "현재 상품 정보를 확인하고 궁금한 점을 물어보세요.", [
        ("사이즈·옵션", "사이즈와 옵션을 알려주세요", "product"),
        ("소재·설명", "소재와 상품 설명이 궁금해요", "product"),
        ("주문 방법", "이 상품은 어떻게 주문하나요?", "product"),
    ]),
    "home": ("쇼핑 홈", "원하시는 분위기나 찾는 상품을 알려주세요.", [
        ("상품 추천", "원하는 스타일에 어울리는 상품을 추천해 주세요", "product"),
        ("인기 상품", "요즘 인기 있는 상품을 알려주세요", "product"),
        ("신상품", "새로 나온 상품이 궁금해요", "product"),
    ]),
    "search": ("상품 검색", "검색 결과와 카테고리를 살펴보고 계세요.", [
        ("사이즈·옵션", "사이즈와 옵션을 알려주세요", "product"),
        ("상품 정보", "소재와 상품 설명이 궁금해요", "product"),
        ("비슷한 상품", "비슷한 스타일의 상품을 찾고 있어요", "product"),
    ]),
    "cart": ("장바구니", "담은 상품의 옵션·수량·주문 방법을 도와드릴게요.", [
        ("옵션 확인", "장바구니 상품의 옵션을 확인하고 싶어요", "product"),
        ("주문 방법", "장바구니 상품은 어떻게 주문하나요?", "product"),
        ("배송 안내", "주문과 배송 방법이 궁금해요", "page_help"),
    ]),
    "orders": ("주문 내역", "주문번호를 입력하면 배송 상태를 확인할 수 있어요.", [
        ("배송 조회", "", "order_status"),
        ("주문 상태", "", "order_status"),
        ("교환·환불", "교환이나 환불 방법을 알고 싶어요", "product"),
    ]),
    "checkout": ("주문하기", "주문 상품과 배송정보를 확인하는 단계예요.", [
        ("상품·옵션", "주문 상품과 옵션을 다시 확인하고 싶어요", "product"),
        ("최종 금액", "배송비와 최종 금액은 언제 확인하나요?", "product"),
        ("주소 입력", "배송 주소 입력 방법이 궁금해요", "product"),
    ]),
    "guest-order": ("비회원 주문", "휴대폰 인증과 배송정보를 입력하는 단계예요.", [
        ("인증 안내", "비회원 휴대폰 인증은 어떻게 하나요?", "page_help"),
        ("주소 입력", "배송 주소는 어떻게 입력하나요?", "page_help"),
        ("주문 확인", "최종 주문 금액은 어디서 확인하나요?", "page_help"),
    ]),
}


def escape(value, quote=True):
    return html_escape(str(value), quote=quote).replace("{", "&#123;").replace("}", "&#125;")


def _summary(product, service):
    from core.homepage.storefront import LABELS, price_label
    catalog = getattr(service, "catalog", None)
    pending = callable(getattr(catalog, "dev_upload_inventory_pending", None)) and catalog.dev_upload_inventory_pending(product["id"]) is True
    test_stock = callable(getattr(catalog, "dev_upload_test_inventory", None)) and catalog.dev_upload_test_inventory(product["id"]) is True
    price_note = callable(getattr(catalog, "dev_upload_price_note", None)) and bool(catalog.dev_upload_price_note(product["id"]))
    description = unescape(re.sub(r"<[^>]*>", " ", product.get("description", "")))
    description = " ".join(description.split())[:220]
    variants = [item["label"] for item in product.get("variants", [])[:6]]
    return {
        "name": product["name"][:120],
        "category": LABELS.get(product["category"].lower(), product["category"])[:60],
        "price": (price_label(product) + (" · 임시 가격" if pending or test_stock or price_note else ""))[:100],
        "options": variants,
        "description": description,
        "questions": [
            {"label": "사이즈·옵션", "text": "사이즈와 옵션을 알려주세요", "action": "product"},
            {"label": "소재·설명", "text": "소재와 상품 설명이 궁금해요", "action": "product"},
            {"label": "주문 방법", "text": "이 상품은 어떻게 주문하나요?", "action": "product"},
        ],
    }


def widget(service, context="", page_context=None):
    from core.homepage.storefront import dev_orderable, product_data
    rows = []
    for product_id in sorted(dev_orderable(service)):
        try:
            product = product_data(service.get_product(product_id))
            if product["id"] == product_id:
                rows.append(product)
        except Exception:
            continue
    if not rows:
        return ""

    allowed = {product["id"] for product in rows}
    context = context if context in allowed else ""
    summaries = {product["id"]: _summary(product, service) for product in rows}
    page_context = page_context or {}
    kind = page_context.get("type", "product" if context else "home")
    if kind not in PAGE_GUIDES:
        kind = "product" if context else "home"
    title, default_summary, question_rows = PAGE_GUIDES[kind]
    page_summary = str(page_context.get("summary") or default_summary)[:240]
    page_key = str(page_context.get("key") or kind)[:180]
    initial_product = summaries.get(context) if context else None
    payload = {"type": kind, "key": page_key, "title": title, "summary": page_summary,
               "questions": [{"label": label, "text": text, "action": action} for label, text, action in question_rows],
               "product": initial_product}
    encoded = escape(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return '''<button id="shop-chat-launcher" class="shop-chat-launcher" type="button" aria-controls="shop-chat" aria-haspopup="dialog"><span class="shop-chat-launcher-icon" aria-hidden="true">✦</span><span class="shop-chat-launcher-copy"><strong>챗봇 상담</strong><small>상품과 주문을 도와드려요</small></span><span class="shop-chat-launcher-arrow" aria-hidden="true">↗</span></button>
<dialog id="shop-chat" aria-labelledby="shop-chat-title" data-context="PRODUCT_CONTEXT_ID" data-page-context="PAGE_CONTEXT_JSON">
<header class="shop-chat-header"><div class="shop-chat-brand"><span class="shop-chat-avatar" aria-hidden="true">a</span><div><p class="shop-chat-eyebrow">AGACHICHI · CUSTOMER CARE</p><h2 id="shop-chat-title">agachichi 챗봇</h2><p id="shop-chat-page-label" class="shop-chat-page-label"></p></div></div><button id="shop-chat-close" type="button" aria-label="챗봇 닫기">×</button></header>
<div class="shop-chat-body"><p id="shop-chat-tag" class="shop-chat-tag"></p><div id="shop-chat-messages" role="log" aria-live="polite" aria-relevant="additions text"></div><div id="shop-chat-suggestions" class="shop-chat-suggestions" aria-label="추천 질문"></div><p class="shop-chat-privacy">문의는 인증 없이 가능해요. 이름·전화번호·주소는 입력하지 마세요.</p></div>
<form id="shop-chat-form"><label class="shop-chat-visually-hidden" for="shop-chat-question">문의 내용을 입력하세요</label><input id="shop-chat-question" maxlength="500" required autocomplete="off" placeholder="궁금한 내용을 입력해 주세요"><button id="shop-chat-send" type="submit">보내기</button></form>
<button id="shop-chat-history" type="button" class="shop-chat-history">휴대폰 인증 후 최근 문의 보기</button><section id="shop-chat-phone" hidden><label>휴대폰 번호<input id="shop-chat-phone-number" type="tel" autocomplete="tel" maxlength="32"></label><label><input id="shop-chat-consent" type="checkbox">인증 문자 수신 동의</label><button id="shop-chat-sms" type="button">인증 문자 받기</button><label>인증번호<input id="shop-chat-code" inputmode="numeric" autocomplete="one-time-code" maxlength="10"></label><button id="shop-chat-verify" type="button">인증 확인</button></section><section id="shop-chat-recent" hidden aria-label="최근 문의 내역"></section><p id="shop-chat-error" role="alert"></p></dialog><script src="/homepage/assets/storefront-chat.js" defer></script>'''.replace("PRODUCT_CONTEXT_ID", escape(context, quote=True)).replace("PAGE_CONTEXT_JSON", encoded)
