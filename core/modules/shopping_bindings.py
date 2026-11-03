"""Trusted Shopping runtime injection, without ambient production defaults.

Bindings supply existing authenticated authorities; module attachment creates no
new customer/session/notification authority. All exposed operations are read-only.
"""
from dataclasses import asdict, dataclass
from decimal import Decimal
from typing import Callable

from fastapi import FastAPI, APIRouter, Request, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


@dataclass(frozen=True)
class ShoppingBindings:
    runtime: object
    authorize: Callable[[Request, str], bool] | None = None
    session_boundary: object | None = None
    order_service: object | None = None
    notifications: object | None = None


def create_bound_shopping(bindings: ShoppingBindings):
    from core.api.routes import shopping
    from core.api.routes import customer_sessions
    from core.api.dependencies.customer_session import get_customer_session_boundary, CustomerSessionBoundary
    from core.shopping.runtime_composition import ShoppingRuntime
    from core.shopping.order_core.domain import OrderListQuery
    from core.shopping.order_core.service import OrderService, OrderNotFoundError
    from core.notifications import NotificationPlatform

    if not isinstance(bindings.runtime, ShoppingRuntime):
        raise TypeError("explicit ShoppingRuntime required")
    if bindings.session_boundary is not None and not isinstance(bindings.session_boundary, CustomerSessionBoundary):
        raise TypeError("explicit CustomerSessionBoundary required")
    if bindings.order_service is not None and not isinstance(bindings.order_service, OrderService):
        raise TypeError("explicit OrderService required")
    if bindings.notifications is not None and not isinstance(bindings.notifications, NotificationPlatform):
        raise TypeError("explicit NotificationPlatform required")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.shopping_runtime = bindings.runtime

    def allow(request, scope):
        try:
            allowed = bindings.authorize is not None and bindings.authorize(request, scope) is True
        except Exception:
            allowed = False
        if not allowed:
            raise HTTPException(403, "module_access_denied")

    # Reuse only existing catalog read endpoints. Legacy inquiry/token endpoints
    # and product-draft operator reads are not exposed by wholesale router import.
    permitted = {"/shopping/health", "/shopping/health/read-path", "/shopping/readiness",
                 "/shopping/capabilities", "/shopping/integrations", "/shopping/search",
                 "/shopping/featured-products", "/shopping/categories", "/shopping/products",
                 "/shopping/products/{product_id}"}
    catalog_router = APIRouter()
    catalog_router.routes.extend(route for route in shopping.router.routes
                                 if getattr(route, "path", None) in permitted)
    app.include_router(catalog_router)
    if bindings.session_boundary is not None:
        app.dependency_overrides[get_customer_session_boundary] = lambda: bindings.session_boundary
        session_router = APIRouter()
        session_router.routes.extend(route for route in customer_sessions.router.routes
                                     if route.path == "/shopping/auth/session" and route.methods == {"GET"})
        app.include_router(session_router)

    @app.middleware("http")
    async def private_response_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health")
    def health():
        return {"service": "shopping", "profile": "explicit_bindings", "read_only": True,
                "orders_bound": bindings.order_service is not None,
                "sessions_bound": bindings.session_boundary is not None,
                "notifications_bound": bindings.notifications is not None}

    @app.get("/orders")
    def orders(request: Request, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        allow(request, "orders.read")
        if bindings.order_service is None:
            raise HTTPException(503, "order_reader_unavailable")
        try:
            values = bindings.order_service.list_orders(OrderListQuery(page, page_size))
            return JSONResponse({"orders": jsonable_encoder([asdict(x) for x in values], custom_encoder={Decimal: str})})
        except Exception:
            raise HTTPException(503, "order_reader_unavailable") from None

    @app.get("/orders/{order_id}")
    def order(request: Request, order_id: int):
        allow(request, "orders.read")
        if bindings.order_service is None:
            raise HTTPException(503, "order_reader_unavailable")
        try:
            value = bindings.order_service.read_order(order_id)
            return JSONResponse(jsonable_encoder(asdict(value), custom_encoder={Decimal: str}))
        except OrderNotFoundError:
            raise HTTPException(404, "order_not_found") from None
        except Exception:
            raise HTTPException(503, "order_reader_unavailable") from None

    @app.get("/notifications")
    def notifications(request: Request):
        allow(request, "notifications.status.read")
        if bindings.notifications is None:
            raise HTTPException(503, "notification_status_unavailable")
        return bindings.notifications.platform()

    return app
