from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from core.api.dependencies.audit import (
    get_audit_query_service,
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
from core.shopping.secure_runtime import (
    build_default_shopping_service,
)
from core.shopping.service import ShoppingService


router = APIRouter()


def build_default_shopping_management_dashboard_payload(
) -> dict[str, Any]:
    try:
        source = build_default_shopping_service()
    except Exception:
        return (
            unavailable_shopping_management_dashboard_payload()
        )

    return build_shopping_management_dashboard_payload(
        ShoppingServiceManagementSourceAdapter(
            source
        )
    )


@router.get("/dashboard")
def dashboard(
    audit_service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
):
    payload = DashboardAPI(
        shopping_management=(
            build_default_shopping_management_dashboard_payload
        ),
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
