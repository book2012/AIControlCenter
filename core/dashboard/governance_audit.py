"""Governance audit projection for the control-plane dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.governance.audit_query import (
    AuditQueryError,
    AuditQueryService,
)


@dataclass(frozen=True)
class GovernanceAuditDashboardReadModel:
    """Stable JSON-ready audit status exposed to Dashboard."""

    available: bool
    read_only: bool
    status: str
    severity: str | None
    violation_count: int
    comparison_status: str
    latest_snapshot_id: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "read_only": self.read_only,
            "status": self.status,
            "severity": self.severity,
            "violation_count": self.violation_count,
            "comparison_status": self.comparison_status,
            "latest_snapshot_id": self.latest_snapshot_id,
        }


def unavailable_read_model() -> GovernanceAuditDashboardReadModel:
    """Return the fail-soft read model used for audit query failures."""

    return GovernanceAuditDashboardReadModel(
        available=False,
        read_only=True,
        status="UNAVAILABLE",
        severity=None,
        violation_count=0,
        comparison_status="UNAVAILABLE",
        latest_snapshot_id=None,
    )


def build_governance_audit_dashboard_read_model(
    service: AuditQueryService,
) -> GovernanceAuditDashboardReadModel:
    """Project audit query state without exposing repository internals."""

    try:
        latest_result = service.get_latest()
        comparison_result = service.compare_latest()
    except AuditQueryError:
        return unavailable_read_model()

    latest = latest_result.snapshot

    if latest is None:
        return GovernanceAuditDashboardReadModel(
            available=True,
            read_only=True,
            status="NO_DATA",
            severity=None,
            violation_count=0,
            comparison_status=comparison_result.status,
            latest_snapshot_id=None,
        )

    return GovernanceAuditDashboardReadModel(
        available=True,
        read_only=True,
        status="READY",
        severity=latest.summary.severity,
        violation_count=latest.summary.violation_count,
        comparison_status=comparison_result.status,
        latest_snapshot_id=latest.snapshot_id,
    )
