from fastapi import APIRouter

from core.dashboard.api import DashboardAPI
from typing import Annotated
from fastapi import Depends
from core.api.dependencies.audit import get_audit_query_service
from core.dashboard.governance_audit import build_governance_audit_dashboard_read_model
from core.governance.audit_query import AuditQueryService

router = APIRouter()


@router.get("/dashboard")
def dashboard(
    audit_service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
):
    payload = DashboardAPI().status(["ubuntu-main"])
    payload["model_governance_audit"] = (
        build_governance_audit_dashboard_read_model(
            audit_service
        ).to_dict()
    )
    return payload
