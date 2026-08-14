"""GET-only AIControlCenter projection of WooCommerce engine readiness."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/shopping/providers", tags=["shopping"])


@router.get("/woocommerce")
def woocommerce_status(request: Request) -> dict[str, object]:
    return request.app.state.woocommerce_status_service.status()
