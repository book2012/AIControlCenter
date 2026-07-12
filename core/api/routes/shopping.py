from fastapi import APIRouter, HTTPException, Query, status

from core.shopping.schemas import (
    ProductListResponse,
    ProductResponse,
    ShoppingCapabilitiesResponse,
    ShoppingHealthResponse,
    ShoppingReadinessResponse,
)
from core.shopping.service import (
    ProductNotFoundError,
    ShoppingService,
)


router = APIRouter(
    prefix="/shopping",
    tags=["shopping"],
)

shopping = ShoppingService()


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
