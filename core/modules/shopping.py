"""A real ShoppingService adapter, limited to local mock catalog reads.

No legacy app import, inquiry repository, credentials, jobs or DB creation.
The preview does not switch the existing DEV/PROD runtime or replace checkout.
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse


def create_shopping_preview() -> FastAPI:
    from core.shopping.config import ShoppingSettings
    from core.shopping.service import ShoppingService, ProductNotFoundError
    from core.shopping.ports import CatalogReadQueryError, CatalogReadUnavailable

    service = ShoppingService(settings=ShoppingSettings(
        enabled=True, environment="isolated_preview", runtime="virtual",
        deployment_target="mac-mini-m4", write_mode="read_only",
        approval_required=True, automation_enabled=False, ai_enabled=False,
        catalog_adapter="mock",
    ))
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health():
        return service.health()

    @app.get("/products")
    def products(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        try:
            return service.list_products(page=page, page_size=page_size)
        except (CatalogReadQueryError, CatalogReadUnavailable):
            return JSONResponse({"detail": "catalog_unavailable"}, status_code=503)

    @app.get("/products/{product_id}")
    def product(product_id: str):
        try:
            return service.get_product(product_id)
        except ProductNotFoundError:
            return JSONResponse({"detail": "product_not_found"}, status_code=404)
        except (CatalogReadQueryError, CatalogReadUnavailable):
            return JSONResponse({"detail": "catalog_unavailable"}, status_code=503)

    return app
