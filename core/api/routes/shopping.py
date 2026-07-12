"""AI Shopping Platform API routes."""

from fastapi import APIRouter

from core.shopping.schemas import (
    ShoppingCapabilitiesResponse,
    ShoppingHealthResponse,
    ShoppingReadinessResponse,
)
from core.shopping.service import ShoppingService


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
