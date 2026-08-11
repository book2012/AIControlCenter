"""Application-owned Shopping runtime composition."""
from __future__ import annotations

from dataclasses import dataclass

from .product_drafts.read import ProductDraftQueryService
from .product_drafts.runtime import ProductDraftCapability, build_product_draft_read_runtime
from .secure_runtime import build_default_shopping_service
from .service import ShoppingService


@dataclass(frozen=True, slots=True)
class ShoppingRuntime:
    catalog_service: ShoppingService
    product_draft_query_service: ProductDraftQueryService
    product_draft_capability: ProductDraftCapability
    product_draft_mutation_available: bool = False


def build_shopping_runtime() -> ShoppingRuntime:
    product_drafts = build_product_draft_read_runtime()
    return ShoppingRuntime(
        catalog_service=build_default_shopping_service(),
        product_draft_query_service=product_drafts.query_service,
        product_draft_capability=product_drafts.capability,
    )


__all__ = ("ShoppingRuntime", "build_shopping_runtime")
