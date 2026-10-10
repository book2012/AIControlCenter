"""Public product presentation for the customer-bound guest commerce API."""
from html import escape
import re
from fastapi.responses import HTMLResponse,JSONResponse

PANEL = '<div class="commerce-panel-content" data-guest-shop-product="PRODUCT">\n<h2>주문하기</h2>\n<p class="commerce-note">궁금한 내용은 챗봇에게 물어보고, 여기에서 주문을 진행하세요.</p>\n<div class="commerce-choice"><label>옵션<select id="variation">OPTIONS</select></label><label>수량<input id="quantity" type="number" min="1" max="10" value="1"></label></div>\n<div class="commerce-actions"><button id="add" type="button">장바구니 담기</button><button id="single" type="button">이 상품 주문하기</button></div>\n\n<section class="commerce-subsection commerce-cart-section"><h3>장바구니</h3><div id="cart"></div><button id="checkout" type="button">장바구니 주문하기</button><button id="clear" type="button">비우기</button></section>\n<section id="order" class="commerce-subsection" hidden><h3>주문</h3><div id="summary"></div><p id="auth-note" role="status"></p><div id="phone-form" hidden><label>휴대폰 번호<input id="phone-number" type="tel" autocomplete="tel" maxlength="32" placeholder="01012345678"></label><label class="commerce-consent"><input id="phone-consent" type="checkbox">주문 진행을 위한 인증 문자 수신 동의</label><button id="phone" type="button" disabled>인증 문자 받기</button><label>인증번호<input id="phone-code" inputmode="numeric" autocomplete="one-time-code" maxlength="10"></label><button id="phone-check" type="button" disabled>휴대폰 인증 확인</button></div><p>휴대폰 인증 후 배송정보를 확인하고 마지막에 주문을 확정합니다.</p><div id="delivery-form" hidden><h4>배송정보</h4><label>수령인<input id="recipient" maxlength="64" autocomplete="name"></label><div><label>우편번호<input id="postcode" inputmode="numeric" maxlength="5" autocomplete="postal-code" readonly></label><button id="address-search" type="button">한국 주소 검색</button></div><div id="address-search-layer" hidden><div id="address-search-frame"></div><button id="address-search-close" type="button">주소 검색 닫기</button></div><label>주소<input id="address1" maxlength="200" autocomplete="address-line1" readonly></label><label>상세주소<input id="address2" maxlength="100" autocomplete="address-line2" placeholder="동·호수 등 상세주소"></label><button id="prepare" type="button">배송정보와 주문 내용 확인</button></div><div id="final-review"></div><button id="confirm" type="button" disabled>이 내용으로 주문 확정</button><button id="guest-status" type="button" disabled>주문 상태 확인</button><button id="guest-new" type="button" hidden>새 주문 시작</button></section>\n<p class="commerce-links"><a href="/homepage/storefront/cart">장바구니 보기</a></p><p id="error" role="alert"></p><p class="commerce-links"><a href="/homepage/storefront/my-orders">내 주문 · 환불 · 사이즈교환 보기</a></p>\n</div>'
HEADERS={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"}

def mount_storefront_routes(app,*,catalog,bindings):
    # The caller supplies an explicit CMS slug -> commerce ID mapping.
    mapping=dict(bindings)
    if any(not re.fullmatch(r"ag-upload-(?:top|bottom|outer|dress|bag|acc)-[0-9]{4}",slug) or not isinstance(pid,str) or not re.fullmatch(r"[0-9]{1,10}",pid) for slug,pid in mapping.items()):
        raise ValueError("STOREFRONT_BINDING_REQUIRED")
    if len(set(mapping.values()))!=len(mapping):raise ValueError("UNIQUE_STOREFRONT_BINDING_REQUIRED")
    def panel(product=None):
        options="" if product is None else "".join('<option value="'+escape(v.id,quote=True)+'"'+('' if v.available else ' disabled')+'>'+escape(v.label)+('' if v.available else ' · 품절')+'</option>' for v in product['variants'])
        html=PANEL.replace('PRODUCT',escape(product['id'],quote=True) if product else '').replace('OPTIONS',options or '<option value="">옵션을 확인해 주세요</option>')
        if product is None:
            html=html.replace('data-guest-shop-product="','data-cart-page="true" data-guest-shop-product="',1).replace('<h2>주문하기</h2>','<h2>담은 상품</h2>',1)
        elif not any(v.available for v in product['variants']):
            html=html.replace('id="add" type="button"','id="add" type="button" disabled').replace('id="single" type="button"','id="single" type="button" disabled')
        return HTMLResponse(html,headers=HEADERS)
    @app.get('/shopping/chat/embed/{slug}',include_in_schema=False)
    def embed(slug:str):
        if slug not in mapping:return HTMLResponse('상품 주문 기능을 확인할 수 없습니다.',status_code=404,headers=HEADERS)
        try:return panel(catalog.get_product(mapping[slug]))
        except Exception:return HTMLResponse('상품 주문 기능을 확인할 수 없습니다.',status_code=503,headers=HEADERS)
    @app.get('/shopping/chat/cart',include_in_schema=False)
    def cart():return panel()
    @app.get('/shopping/chat/cart/product/{product_id}',include_in_schema=False)
    def metadata(product_id:str):
        slug=next((key for key,value in mapping.items() if value==product_id),None)
        if slug is None:return JSONResponse({'message':'상품 정보를 확인하지 못했습니다.'},status_code=404,headers=HEADERS)
        try:
            p=catalog.get_product(product_id)
            return JSONResponse({'id':p['id'],'name':p['name'],'price':str(p['price']),'currency':p['currency'],
                'product_url':'/homepage/storefront/product/'+slug,
                'variants':[{'id':v.id,'label':v.label,'available':v.available} for v in p['variants']]},headers=HEADERS)
        except Exception:return JSONResponse({'message':'상품 정보를 확인하지 못했습니다.'},status_code=503,headers=HEADERS)
