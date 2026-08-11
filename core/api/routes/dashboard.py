from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from core.api.dependencies.audit import (
    get_audit_query_service,
)
from core.api.dependencies.shopping import (
    get_product_draft_query_service,
    get_shopping_service,
)
from core.api.services.governance_audit_operations import (
    build_governance_audit_operations_dashboard_payload,
)
from core.dashboard.api import DashboardAPI
from core.dashboard.governance_audit import (
    build_governance_audit_dashboard_read_model,
)
from core.dashboard.shopping_management import (
    build_shopping_management_dashboard_payload,
    unavailable_shopping_management_dashboard_payload,
)
from core.governance.audit_query import AuditQueryService
from core.shopping.application.management_source import (
    ShoppingServiceManagementSourceAdapter,
)
from core.shopping.service import ShoppingService
from core.shopping.product_drafts.read import ProductDraftQueryService
from core.shopping.product_drafts.read import ProductDraftReadUnavailable, unavailable_dashboard_projection


router = APIRouter()


def build_product_draft_dashboard_payload(service: ProductDraftQueryService) -> dict[str, Any]:
    try:
        return service.dashboard_projection()
    except ProductDraftReadUnavailable:
        return unavailable_dashboard_projection()


def build_default_shopping_management_dashboard_payload(
    service: ShoppingService,
) -> dict[str, Any]:
    try:
        return build_shopping_management_dashboard_payload(
            ShoppingServiceManagementSourceAdapter(service)
        )
    except Exception:
        return unavailable_shopping_management_dashboard_payload()


@router.get("/dashboard")
def dashboard(
    audit_service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
    product_draft_service: Annotated[
        ProductDraftQueryService,
        Depends(get_product_draft_query_service),
    ],
    shopping_service: Annotated[
        ShoppingService,
        Depends(get_shopping_service),
    ],
):
    payload = DashboardAPI(
        shopping_management=(
            lambda: build_default_shopping_management_dashboard_payload(shopping_service)
        ),
        product_drafts=lambda: build_product_draft_dashboard_payload(product_draft_service),
    ).status(["ubuntu-main"])

    payload["model_governance_audit"] = (
        build_governance_audit_dashboard_read_model(
            audit_service
        ).to_dict()
    )

    payload["governance_audit_operations"] = (
        build_governance_audit_operations_dashboard_payload()
    )

    return payload
