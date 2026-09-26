"""Demo-only dev composition; shares the real Homepage and Shopping GET routes.

This does not import core.api.app, build a production runtime, or use a test
fixture as an application. The launcher isolates ambient configuration first.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import re
from pathlib import Path

from core.api.dependencies.shopping import get_shopping_service
from core.api.routes import homepage, shopping
from core.shopping.adapters.demo_commerce import DemoCommerceCatalogAdapter
from core.shopping.config import ShoppingSettings
from core.shopping.service import ShoppingService
from core.shopping.inquiries import InMemoryInquiryRepository

PRESENTATION_VERSION = "SHOP_MEDIA_003_AGACHICHI"


def create_app(*, lookbook: bool = True) -> FastAPI:
    service = ShoppingService(settings=ShoppingSettings(
        enabled=True, environment="test", runtime="virtual", deployment_target="mac-mini-m4",
        write_mode="read_only", approval_required=True, automation_enabled=False,
        ai_enabled=False, catalog_adapter="demo",
    ), catalog=DemoCommerceCatalogAdapter(catalog_root=(
        Path(__file__).resolve().parents[2] / "brands/orange-coco/catalog" / "lookbook-preview"
        if lookbook else Path(__file__).resolve().parents[2] / "brands/orange-coco/catalog")))
    service._lookbook_enabled = lookbook
    app = FastAPI(title="agachichi local read-only preview", docs_url=None, redoc_url=None)
    app.state.inquiry_repository = InMemoryInquiryRepository()
    app.include_router(homepage.router)
    app.include_router(shopping.router)
    app.dependency_overrides[get_shopping_service] = lambda: service

    @app.middleware("http")
    async def preview_boundary(request: Request, call_next):
        # Do not expose inquiry, operator, or runtime routes from the
        # included routers. Preview is storefront/catalog only.
        path = request.url.path
        allowed = (path == "/openapi.json" or path == "/homepage/storefront"
                   or path.startswith("/homepage/storefront/")
                   or path.startswith("/homepage/assets/storefront")
                   or bool(re.fullmatch(r"/shopping/(products(?:/[^/]+)?|categories|search|contact-channels)", path)))
        if request.method not in {"GET", "POST"}:
            return JSONResponse({"detail": "Method not allowed"}, status_code=405, headers={"Allow": "GET, POST"})
        if request.method == "POST" and not (path == "/shopping/inquiries" or path.endswith("/messages")):
            return JSONResponse({"detail": "Method not allowed"}, status_code=405, headers={"Allow": "GET"})
        if not allowed:
            return JSONResponse({"detail": "Not found"}, status_code=404)
        response = await call_next(request)
        response.headers["X-Shop-Presentation"] = PRESENTATION_VERSION
        response.headers["Cache-Control"] = "no-store"
        return response

    return app
