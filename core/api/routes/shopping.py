from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.shopping.schemas import (
    ProductSearchResponse,
    FeaturedProductListResponse,
    ShoppingCategoryListResponse,
    ProductListResponse,
    ProductResponse,
    ShoppingCapabilitiesResponse,
    ShoppingHealthResponse,
    ShoppingIntegrationResponse,
    ShoppingReadinessResponse,
)
from core.shopping.service import (
    ProductNotFoundError,
    ShoppingService,
)
from core.shopping.secure_runtime import (
    build_default_shopping_service,
)
from core.shopping.product_drafts.read import (
    ProductDraftQueryService,
    ProductDraftReadUnavailable,
    ProductDraftRevisionNotFound,
    UnavailableProductDraftReadSource,
)


router = APIRouter(
    prefix="/shopping",
    tags=["shopping"],
)

shopping = build_default_shopping_service()


def get_product_draft_query_service() -> ProductDraftQueryService:
    """Safe default: unavailable until a production read source is configured."""
    return ProductDraftQueryService(UnavailableProductDraftReadSource())


ProductDraftQuery = Annotated[ProductDraftQueryService, Depends(get_product_draft_query_service)]


def _product_draft_error(error: Exception) -> HTTPException:
    if isinstance(error, ProductDraftReadUnavailable):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                             detail={"code": "product_draft_read_unavailable", "retryable": True})
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                         detail={"code": "product_draft_revision_not_found"})


@router.get("/product-drafts")
def product_draft_collection(
    service: ProductDraftQuery,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    lifecycle_state: str | None = Query(default=None),
):
    try:
        return service.list_revisions(page=page, page_size=page_size, lifecycle_state=lifecycle_state)
    except ProductDraftReadUnavailable as error:
        raise _product_draft_error(error) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail={"code": "product_draft_invalid_query"}) from error


@router.get("/product-drafts/{draft_id}")
def product_draft_current(draft_id: str, service: ProductDraftQuery):
    try:
        return service.current_revision(draft_id)
    except (ProductDraftReadUnavailable, ProductDraftRevisionNotFound) as error:
        raise _product_draft_error(error) from error


@router.get("/product-drafts/{draft_id}/revisions/{revision_id}")
def product_draft_revision(draft_id: str, revision_id: str, service: ProductDraftQuery):
    try:
        return service.exact_revision(draft_id, revision_id)
    except (ProductDraftReadUnavailable, ProductDraftRevisionNotFound) as error:
        raise _product_draft_error(error) from error


@router.get(
    "/health",
    response_model=ShoppingHealthResponse,
)
def shopping_health():
    return shopping.health()


@router.get(
    "/readiness",
    response_model=ShoppingReadinessResponse,
)
def shopping_readiness():
    return shopping.readiness()


@router.get(
    "/capabilities",
    response_model=ShoppingCapabilitiesResponse,
)
def shopping_capabilities():
    return shopping.capabilities()



@router.get(
    "/integrations",
    response_model=ShoppingIntegrationResponse,
)
def shopping_integrations():
    return shopping.integration_status()





@router.get(
    "/search",
    response_model=ProductSearchResponse,
)
def shopping_search(
    q: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    category: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    minimum_price: float | None = Query(
        default=None,
        ge=0,
    ),
    maximum_price: float | None = Query(
        default=None,
        ge=0,
    ),
    in_stock: bool | None = Query(
        default=None,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
):
    if (
        minimum_price is not None
        and maximum_price is not None
        and minimum_price > maximum_price
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "shopping_invalid_price_range",
                "minimum_price": minimum_price,
                "maximum_price": maximum_price,
            },
        )

    return shopping.search_products(
        query=q,
        category=category,
        minimum_price=minimum_price,
        maximum_price=maximum_price,
        in_stock=in_stock,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/featured-products",
    response_model=FeaturedProductListResponse,
)
def shopping_featured_products(
    limit: int = Query(
        default=4,
        ge=1,
        le=20,
    ),
):
    return shopping.list_featured_products(
        limit=limit,
    )


@router.get(
    "/categories",
    response_model=ShoppingCategoryListResponse,
)
def shopping_categories():
    return shopping.list_categories()


@router.get(
    "/products",
    response_model=ProductListResponse,
)
def shopping_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    return shopping.list_products(
        page=page,
        page_size=page_size,
    )


@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
)
def shopping_product(product_id: str):
    try:
        return shopping.get_product(product_id)
    except ProductNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "shopping_product_not_found",
                "product_id": str(error),
            },
        ) from error
