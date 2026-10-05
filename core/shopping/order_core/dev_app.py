"""Explicit DEV application factory; no credential/provider/runtime defaults."""
from html import escape
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse

from core.api.dependencies.customer_session import get_customer_session_boundary
from core.api.dependencies.order_create import SessionBoundOrderCreateApplication
from core.api.routes.customer_sessions import router as sessions
from core.api.routes.order_create import router as orders, get_order_create_application
from core.shopping.models import Product
from .catalog import ShoppingServiceOrderCatalogResolver
from .create import OrderCreateService


_ASSET = Path(__file__).resolve().parents[3] / "deploy/shopping/wordpress/plugins/ai-shopping-storefront/assets/storefront-order.js"


def create_order_dev_app(*, session_boundary, catalog, ledger, writer, telegram_integration):
    """The caller supplies isolated DEV services and trusted synthetic/inert composition.

    No public transport-dispatch or operator mutation HTTP routes are registered.
    This factory does not mount itself into the platform or restart any runtime.
    """
    if telegram_integration._ledger is not ledger:
        raise ValueError("order/Telegram ledger must be identical")
    application = SessionBoundOrderCreateApplication(session_boundary=session_boundary,
        order_service=OrderCreateService(catalog_resolver=ShoppingServiceOrderCatalogResolver(catalog),
                                        order_creator=writer,coordinator=ledger))
    app = FastAPI(title="AIControlCenter isolated DEV order")
    app.include_router(sessions)
    app.include_router(orders)
    app.dependency_overrides[get_customer_session_boundary] = lambda: session_boundary
    app.dependency_overrides[get_order_create_application] = lambda: application
    app.state.order_telegram = telegram_integration

    @app.get("/__order-dev/storefront-order.js", include_in_schema=False)
    def asset():
        return FileResponse(_ASSET,media_type="text/javascript",headers={"Cache-Control":"no-store"})

    @app.get("/order-preview/{product_id}", include_in_schema=False)
    def preview(product_id: str):
        try:
            product = Product(**catalog.get_product(product_id))
            if product.id != product_id: raise ValueError()
        except Exception:
            return HTMLResponse("상품을 찾을 수 없습니다.",status_code=404,headers={"Cache-Control":"no-store"})
        enabled = product.in_stock and product.source == "woocommerce"
        disabled = "" if enabled else " disabled"
        options = "".join('<button class="variant-option" type="button" data-variant-id="'+escape(v.id,quote=True)
            +'" aria-pressed="false"'+('' if v.available else ' disabled')+'>'+escape(v.label)+'</button>'
            for v in product.variants)
        # All HTML content escaped; no caller supplied authority or executable handlers.
        html = ('<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            +'<title>DEV 주문 요청</title><main id="detail-content" data-product-id="'+escape(product.id,quote=True)+'">'
            +'<h1>'+escape(product.name)+'</h1><p>DEV 검증용 · 결제·배송 확정은 별도입니다.</p>'
            +'<div class="variant-options">'+options+'</div><label for="order-quantity">수량</label>'
            +'<input id="order-quantity" type="number" min="1" max="1000" value="1">'
            +'<button id="order-submit" type="button"'+disabled+'>주문하기</button>'
            +'<p id="order-status" role="status" aria-live="polite">운영자 확인이 필요한 주문 요청입니다.</p>'
            +'<button id="order-check" type="button" disabled>주문 상태 확인</button>'
            +'<button id="order-new" type="button" disabled>새 주문 요청</button></main>'
            +'<script src="/__order-dev/storefront-order.js"></script><script src="/__order-dev/variants.js"></script></html>')
        return HTMLResponse(html,headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})

    @app.get("/__order-dev/variants.js",include_in_schema=False)
    def variants():
        from fastapi.responses import Response
        return Response('document.querySelectorAll(".variant-options").forEach(group=>group.addEventListener("click",event=>{const selected=event.target.closest("button.variant-option:not(:disabled)");if(!selected)return;group.querySelectorAll("button").forEach(button=>button.setAttribute("aria-pressed",button===selected?"true":"false"));}));',
                        media_type="text/javascript",headers={"Cache-Control":"no-store"})
    return app
