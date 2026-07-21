from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from core.api.app import create_app
from core.api.dependencies.audit import get_audit_query_service
from core.governance.audit_query import AuditQueryError
from core.governance.audit_snapshot import (
    AuditSnapshot,
    GovernanceSummary,
)


SOURCE_COMMIT = "2cad8ae9e06486cf4e1b86ba5a405a1f04ad26c7"
RUNTIME_RELEASE = "39fe04e3330e"


@dataclass(frozen=True)
class LatestResult:
    snapshot: AuditSnapshot | None


@dataclass(frozen=True)
class ComparisonResult:
    status: str


def snapshot() -> AuditSnapshot:
    return AuditSnapshot.create(
        captured_at="2026-07-21T19:00:00Z",
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance={
            "service": "model-governance",
            "mode": "read-only",
            "default_policy": "DENY",
            "approved_count": 0,
            "observed_count": 1,
            "compliant_count": 0,
            "violation_count": 1,
            "models": [
                {
                    "name": "unapproved-model",
                    "compliance_status": "UNAPPROVED",
                }
            ],
            "write_operations_allowed": False,
        },
        summary=GovernanceSummary(
            severity="CRITICAL",
            approved_count=0,
            observed_count=1,
            compliant_count=0,
            violation_count=1,
            unapproved_count=1,
            missing_count=0,
            digest_mismatch_count=0,
            resource_policy_violation_count=0,
        ),
    )


class EmptyAuditService:
    def get_latest(self) -> LatestResult:
        return LatestResult(snapshot=None)

    def compare_latest(self) -> ComparisonResult:
        return ComparisonResult(status="NO_DATA")


class ViolationAuditService:
    def __init__(self) -> None:
        self.item = snapshot()

    def get_latest(self) -> LatestResult:
        return LatestResult(snapshot=self.item)

    def compare_latest(self) -> ComparisonResult:
        return ComparisonResult(
            status="NEW_VIOLATION"
        )


class FailingAuditService:
    def get_latest(self) -> LatestResult:
        raise AuditQueryError(
            "/private/model-governance-audit.sqlite3"
        )

    def compare_latest(self) -> ComparisonResult:
        raise AssertionError(
            "comparison must not execute"
        )


@pytest.fixture
def application():
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def test_dashboard_contains_no_data_audit_read_model(
    application,
) -> None:
    application.dependency_overrides[
        get_audit_query_service
    ] = lambda: EmptyAuditService()

    with TestClient(application) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200

    payload = response.json()

    assert {
        "backup",
        "brain",
        "control_plane",
        "datacenter",
        "storage",
        "workers",
        "model_governance_audit",
    }.issubset(payload)

    audit = payload["model_governance_audit"]

    assert audit == {
        "available": True,
        "read_only": True,
        "status": "NO_DATA",
        "severity": None,
        "violation_count": 0,
        "comparison_status": "NO_DATA",
        "latest_snapshot_id": None,
    }


def test_dashboard_projects_governance_violation(
    application,
) -> None:
    service = ViolationAuditService()

    application.dependency_overrides[
        get_audit_query_service
    ] = lambda: service

    with TestClient(application) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200

    audit = response.json()[
        "model_governance_audit"
    ]

    assert audit["available"] is True
    assert audit["read_only"] is True
    assert audit["status"] == "READY"
    assert audit["severity"] == "CRITICAL"
    assert audit["violation_count"] == 1
    assert (
        audit["comparison_status"]
        == "NEW_VIOLATION"
    )
    assert (
        audit["latest_snapshot_id"]
        == service.item.snapshot_id
    )


def test_audit_failure_does_not_fail_dashboard(
    application,
) -> None:
    application.dependency_overrides[
        get_audit_query_service
    ] = lambda: FailingAuditService()

    with TestClient(application) as client:
        response = client.get("/dashboard")

    assert response.status_code == 200

    payload = response.json()
    audit = payload["model_governance_audit"]

    assert audit["available"] is False
    assert audit["read_only"] is True
    assert audit["status"] == "UNAVAILABLE"
    assert (
        audit["comparison_status"]
        == "UNAVAILABLE"
    )
    audit_text = repr(audit).lower()
    assert "private" not in audit_text
    assert "sqlite" not in audit_text


def test_dashboard_audit_has_no_write_controls(
    application,
) -> None:
    application.dependency_overrides[
        get_audit_query_service
    ] = lambda: EmptyAuditService()

    with TestClient(application) as client:
        response = client.get("/dashboard")

    audit = response.json()[
        "model_governance_audit"
    ]

    forbidden = {
        "capture",
        "pull",
        "create",
        "copy",
        "delete",
        "remediate",
        "write_operations_allowed",
    }

    assert forbidden.isdisjoint(audit)


def test_dashboard_remains_get_only() -> None:
    schema = create_app().openapi()

    operations = schema["paths"]["/dashboard"]

    methods = {
        method.upper()
        for method in operations
        if method.lower()
        in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }
    }

    assert methods == {"GET"}
