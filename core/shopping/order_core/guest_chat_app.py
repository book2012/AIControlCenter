"""Explicit DEV guest chat routes. SMS and shipping composition are deliberately gated."""
from pathlib import Path
from html import escape
from fastapi import Request
from fastapi.responses import HTMLResponse,JSONResponse,FileResponse
from core.shopping.order_core.guest_chat import GuestShoppingChat,GuestQuestion,GuestCart

ASSET=Path(__file__).resolve().parents[3]/"deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-guest-chat.js"
def mount_guest_chat(app,*,catalog,session_boundary,phone_available=False):
    chat=GuestShoppingChat(catalog)
    @app.get("/__order-dev/guest-chat.js",include_in_schema=False)
    def asset():return FileResponse(ASSET,media_type="text/javascript",headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/chat/product/{product_id}",include_in_schema=False)
    def page(product_id:str):
        try:p=chat.product(product_id)
        except Exception:return HTMLResponse("상품 정보를 확인할 수 없습니다.",status_code=503,headers={"Cache-Control":"no-store"})
        options="".join('<option value="'+escape(v.id,quote=True)+'"'+("" if v.available else " disabled")+">"+escape(v.label)+("" if v.available else " · 품절")+"</option>" for v in p.variants)
        image=('<img alt="'+escape(p.name,quote=True)+'" src="'+escape(p.image_url,quote=True)+'">' if p.image_url and p.image_url.startswith("/__order-dev/") else "")
        html="""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>상품 문의와 채팅 주문</title>
<style>body{font:16px system-ui;background:#f6f4f1;color:#222;margin:0}main{max-width:650px;margin:auto;padding:24px}img{width:100%;max-height:280px;object-fit:contain}button,input,select{font:inherit;padding:12px;border-radius:10px;border:1px solid #ccc;margin:4px}button{cursor:pointer;background:#fff}button:disabled{opacity:.5}#messages p{padding:14px;border-radius:12px;background:white;white-space:pre-wrap}.customer{border-left:4px solid #79533a}section{padding:16px;background:#eee9e3;border-radius:14px;margin-top:20px}input[type=number]{width:60px}#question{width:calc(100% - 32px)}a{color:#79533a}</style>
<main data-product="PRODUCT"><a href="/homepage/storefront">상품 목록</a>IMAGE<h1>NAME</h1><p>PRICE CURRENCY</p><p>회원가입 없이 문의하고, 휴대폰 인증으로 주문하는 채팅 쇼핑</p>
<label>옵션<select id="variation">OPTIONS</select></label><label>수량<input id="quantity" type="number" min="1" max="10" value="1"></label>
<div><button id="stock">재고 문의</button><button id="add">장바구니 담기</button><button id="single">이 상품 주문하기</button></div>
<section><h2>상품 상담</h2><div id="messages" role="log" aria-live="polite"></div><form id="ask"><label for="question">질문</label><input id="question" maxlength="500" placeholder="S 사이즈 재고가 있나요?" required><button>문의하기</button></form></section>
<section><h2>장바구니</h2><div id="cart"></div><button id="checkout">장바구니 주문하기</button><button id="clear">비우기</button></section>
<section id="order" hidden><h2>주문 대화</h2><div id="summary"></div><p id="auth-note" role="status"></p><div id="phone-form" hidden><label>휴대폰 번호<input id="phone-number" type="tel" autocomplete="tel" maxlength="32" placeholder="01012345678"></label><label><input id="phone-consent" type="checkbox">주문 진행을 위한 인증 문자 수신 동의</label><button id="phone" disabled>인증 문자 받기</button><label>인증번호<input id="phone-code" inputmode="numeric" autocomplete="one-time-code" maxlength="10"></label><button id="phone-check" disabled>휴대폰 인증 확인</button></div><p>인증 후 수령인과 배송지를 입력하고 최종 주문 내용을 확인합니다.</p><button id="confirm" disabled>주문 확정</button></section>
<p id="error" role="alert"></p><script src="/__order-dev/guest-chat.js"></script></main></html>"""
        for key,value in {"PRODUCT":escape(p.id,quote=True),"IMAGE":image,"NAME":escape(p.name),"PRICE":escape(str(p.price)),"CURRENCY":escape(p.currency),"OPTIONS":options or '<option value="">기본 옵션</option>'}.items():html=html.replace(key,value)
        return HTMLResponse(html,headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
    async def body(request,model):
        session_boundary.check_origin(request,required=True)
        raw=bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk)>8192:raise ValueError("BODY_TOO_LARGE")
            raw.extend(chunk)
        return model.model_validate_json(bytes(raw))
    @app.post("/__order-dev/chat/inquiry",include_in_schema=False)
    async def inquiry(request:Request):
        try:payload=await body(request,GuestQuestion);result=chat.answer(payload)
        except ValueError:return JSONResponse({"message":"상품 정보를 확인할 수 없습니다."} ,status_code=422,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"상품 정보를 확인할 수 없습니다."},status_code=503,headers={"Cache-Control":"no-store"})
        return JSONResponse(result,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/chat/quote",include_in_schema=False)
    async def quote(request:Request):
        try:payload=await body(request,GuestCart);result=chat.quote(payload)
        except ValueError:return JSONResponse({"message":"상품·옵션·수량을 확인해 주세요. 품절 또는 잘못된 선택이 포함되어 있습니다."},status_code=422,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"현재 상품 정보를 확인할 수 없습니다."},status_code=503,headers={"Cache-Control":"no-store"})
        return JSONResponse(result,headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/chat/capabilities",include_in_schema=False)
    def capabilities():
        return JSONResponse({"guest_inquiry":True,"cart_quote":True,"phone_verification":phone_available,
            "delivery_capture":False,"order_confirmation":False,
            "message":("휴대폰 인증을 진행해 주세요. DEV에서는 등록된 테스트 번호만 사용할 수 있습니다. 배송정보와 주문 확정은 연결 중입니다." if phone_available else "휴대폰 인증 서비스를 연결 중입니다. 현재 문의와 장바구니 금액 확인이 가능하며 주문은 접수되지 않습니다.")},headers={"Cache-Control":"no-store"})
