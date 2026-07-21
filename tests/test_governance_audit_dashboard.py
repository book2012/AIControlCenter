from __future__ import annotations

from dataclasses import dataclass

from core.dashboard.governance_audit import (
    build_governance_audit_dashboard_read_model,
    unavailable_read_model,
)
from core.governance.audit_query import AuditQueryError
from core.governance.audit_snapshot import (
    AuditSnapshot,
    GovernanceSummary,
)


SOURCE_COMMIT = "ab69cbd665f6bc788eb573275f00ec71fca7762c"
RUNTIME_RELEASE = "39fe04e3330e"


@dataclass(frozen=True)
class LatestResult:
    snapshot: AuditSnapshot | None


@dataclass(frozen=True)
class ComparisonResult:
    status: str


def snapshot(
    *,
    severity: str = "INFO",
    violation_count: int = 0,
) -> AuditSnapshot:
    observed_count = 1 if violation_count else 0

    models = (
        [
            {
                "name": "unapproved-model",
                "compliance_status": "UNAPPROVED",
            }
        ]
        if violation_count
        else []
    )

    return AuditSnapshot.create(
        captured_at="2026-07-21T18:00:00Z",
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance={
            "service": "model-governance",
            "mode": "read-only",
            "default_policy": "DENY",
            "approved_count": 0,
            "observed_count": observed_count,
            "compliant_count": 0,
            "violation_count": violation_count,
            "models": models,
            "write_operations_allowed": False,
        },
        summary=GovernanceSummary(
            severity=severity,
            approved_count=0,
            observed_count=observed_count,
            compliant_count=0,
            violation_count=violation_count,
            unapproved_count=violation_count,
            missing_count=0,
            digest_mismatch_count=0,
            resource_policy_violation_count=0,
        ),
    )


class EmptyService:
    def get_latest(self) -> LatestResult:
        return LatestResult(snapshot=None)

    def compare_latest(self) -> ComparisonResult:
        return ComparisonResult(status="NO_DATA")


class NoBaselineService:
    def __init__(self) -> None:
        self.item = snapshot()

    def get_latest(self) -> LatestResult:
        return LatestResult(snapshot=self.item)

    def compare_latest(self) -> ComparisonResult:
        return ComparisonResult(status="NO_BASELINE")


class ViolationService:
    def __init__(self) -> None:
        self.item = snapshot(
            severity="CRITICAL",
            violation_count=1,
        )

    def get_latest(self) -> LatestResult:
        return LatestResult(snapshot=self.item)

    def compare_latest(self) -> ComparisonResult:
        return ComparisonResult(status="NEW_VIOLATION")


class FailingLatestService:
    def get_latest(self) -> LatestResult:
        raise AuditQueryError(
            "/private/audit/database.sqlite3"
        )

    def compare_latest(self) -> ComparisonResult:
        raise AssertionError(
            "comparison must not run after latest failure"
        )


class FailingComparisonService:
    def __init__(self) -> None:
        self.item = snapshot()

    def get_latest(self) -> LatestResult:
        return LatestResult(snapshot=self.item)

    def compare_latest(self) -> ComparisonResult:
        raise AuditQueryError(
            "hidden repository failure"
        )


def test_no_data_read_model() -> None:
    result = build_governance_audit_dashboard_read_model(
        EmptyService()
    )

    assert result.to_dict() == {
        "available": True,
        "read_only": True,
        "status": "NO_DATA",
        "severity": None,
        "violation_count": 0,
        "comparison_status": "NO_DATA",
        "latest_snapshot_id": None,
    }


def test_no_baseline_read_model() -> None:
    service = NoBaselineService()

    result = build_governance_audit_dashboard_read_model(
        service
    )

    assert result.available is True
    assert result.read_only is True
    assert result.status == "READY"
    assert result.severity == "INFO"
    assert result.violation_count == 0
    assert result.comparison_status == "NO_BASELINE"
    assert (
        result.latest_snapshot_id
        == service.item.snapshot_id
    )


def test_violation_read_model() -> None:
    service = ViolationService()

    result = build_governance_audit_dashboard_read_model(
        service
    )

    assert result.available is True
    assert result.status == "READY"
    assert result.severity == "CRITICAL"
    assert result.violation_count == 1
    assert result.comparison_status == "NEW_VIOLATION"
    assert (
        result.latest_snapshot_id
        == service.item.snapshot_id
    )


def test_latest_failure_is_fail_soft() -> None:
    result = build_governance_audit_dashboard_read_model(
        FailingLatestService()
    )

    assert result == unavailable_read_model()
    assert "database" not in str(result.to_dict())
    assert "private" not in str(result.to_dict())


def test_comparison_failure_is_fail_soft() -> None:
    result = build_governance_audit_dashboard_read_model(
        FailingComparisonService()
    )

    assert result == unavailable_read_model()


def test_read_model_has_no_write_controls() -> None:
    payload = build_governance_audit_dashboard_read_model(
        EmptyService()
    ).to_dict()

    forbidden = {
        "capture",
        "pull",
        "create",
        "copy",
        "delete",
        "remediate",
        "write_operations_allowed",
    }

    assert forbidden.isdisjoint(payload)
