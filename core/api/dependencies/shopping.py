"""FastAPI dependencies for the application-composed Shopping runtime."""
from fastapi import Request

from core.shopping.product_drafts.read import ProductDraftQueryService
from core.shopping.runtime_composition import ShoppingRuntime
from core.shopping.service import ShoppingService


def get_shopping_runtime(request: Request) -> ShoppingRuntime:
    runtime = getattr(request.app.state, "shopping_runtime", None)
    if not isinstance(runtime, ShoppingRuntime):
        raise RuntimeError("Shopping runtime is not composed")
    return runtime


def get_shopping_service(request: Request) -> ShoppingService:
    return get_shopping_runtime(request).catalog_service


def get_product_draft_query_service(request: Request) -> ProductDraftQueryService:
    return get_shopping_runtime(request).product_draft_query_service


__all__ = ("get_product_draft_query_service", "get_shopping_runtime", "get_shopping_service")
