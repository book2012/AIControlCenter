from pathlib import Path

import pytest

from core.governance.audit_repository import (
    SQLiteAuditRepository,
)
from core.governance.audit_service import (
    AuditServiceError,
    AuditSnapshotService,
    build_governance_summary,
    calculate_severity,
    derive_governance_counts,
    validate_governance_payload,
)
from core.governance.audit_snapshot import (
    GovernanceSummary,
)


SOURCE_COMMIT = "756e78d4293f108f0790d9e9b60591f5456aaffc"
RUNTIME_RELEASE = "39fe04e3330e"
MIGRATED_AT = "2026-07-21T15:00:00Z"


def model(
    name: str,
    status: str,
) -> dict:
    return {
        "name": name,
        "compliance_status": status,
    }


def payload(
    *,
    models: list[dict] | None = None,
    approved_count: int = 0,
    observed_count: int = 0,
    compliant_count: int = 0,
    violation_count: int = 0,
    write_operations_allowed: bool = False,
) -> dict:
    return {
        "service": "model-governance",
        "mode": "read-only",
        "default_policy": "DENY",
        "approved_count": approved_count,
        "observed_count": observed_count,
        "compliant_count": compliant_count,
        "violation_count": violation_count,
        "models": [] if models is None else models,
        "write_operations_allowed": (
            write_operations_allowed
        ),
    }


def repository(
    path: Path,
) -> SQLiteAuditRepository:
    repo = SQLiteAuditRepository(
        path,
        application_commit=SOURCE_COMMIT,
        migrated_at=MIGRATED_AT,
    )
    repo.initialize()
    return repo


def test_empty_governance_builds_info_summary() -> None:
    summary = build_governance_summary(payload())

    assert summary == GovernanceSummary(
        severity="INFO",
        approved_count=0,
        observed_count=0,
        compliant_count=0,
        violation_count=0,
        unapproved_count=0,
        missing_count=0,
        digest_mismatch_count=0,
        resource_policy_violation_count=0,
    )


@pytest.mark.parametrize(
    ("status", "expected_severity"),
    [
        ("COMPLIANT", "INFO"),
        ("MISSING", "WARNING"),
        ("UNAPPROVED", "CRITICAL"),
        ("DIGEST_MISMATCH", "CRITICAL"),
        (
            "RESOURCE_POLICY_VIOLATION",
            "CRITICAL",
        ),
    ],
)
def test_severity_mapping(
    status: str,
    expected_severity: str,
) -> None:
    item = model("example", status)

    approved_count = (
        0
        if status == "UNAPPROVED"
        else 1
    )
    observed_count = (
        0
        if status == "MISSING"
        else 1
    )
    compliant_count = (
        1
        if status == "COMPLIANT"
        else 0
    )
    violation_count = (
        0
        if status == "COMPLIANT"
        else 1
    )

    result = build_governance_summary(
        payload(
            models=[item],
            approved_count=approved_count,
            observed_count=observed_count,
            compliant_count=compliant_count,
            violation_count=violation_count,
        )
    )

    assert result.severity == expected_severity


def test_write_allowed_is_critical() -> None:
    summary = build_governance_summary(
        payload(
            write_operations_allowed=True,
        )
    )

    assert summary.severity == "CRITICAL"


def test_counts_are_derived_from_models() -> None:
    governance = payload(
        models=[
            model("a", "COMPLIANT"),
            model("b", "UNAPPROVED"),
            model("c", "MISSING"),
            model("d", "DIGEST_MISMATCH"),
            model(
                "e",
                "RESOURCE_POLICY_VIOLATION",
            ),
        ],
        approved_count=4,
        observed_count=4,
        compliant_count=1,
        violation_count=4,
    )

    counts = derive_governance_counts(governance)

    assert counts.compliant_count == 1
    assert counts.unapproved_count == 1
    assert counts.missing_count == 1
    assert counts.digest_mismatch_count == 1
    assert (
        counts.resource_policy_violation_count
        == 1
    )
    assert counts.violation_count == 4


def test_count_mismatch_fails_closed() -> None:
    governance = payload(
        models=[
            model("a", "UNAPPROVED"),
        ],
        approved_count=0,
        observed_count=1,
        compliant_count=0,
        violation_count=0,
    )

    with pytest.raises(
        AuditServiceError,
        match="violation_count",
    ):
        validate_governance_payload(governance)


def test_unknown_status_fails_closed() -> None:
    governance = payload(
        models=[
            model("a", "UNKNOWN"),
        ],
        approved_count=0,
        observed_count=1,
        compliant_count=0,
        violation_count=1,
    )

    with pytest.raises(
        AuditServiceError,
        match="unknown compliance status",
    ):
        validate_governance_payload(governance)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("approved_count", -1),
        ("observed_count", True),
        ("compliant_count", "0"),
        ("violation_count", 1.5),
    ],
)
def test_invalid_counts_fail_closed(
    field: str,
    value: object,
) -> None:
    governance = payload()
    governance[field] = value

    with pytest.raises(AuditServiceError):
        validate_governance_payload(governance)


def test_non_read_only_mode_fails_closed() -> None:
    governance = payload()
    governance["mode"] = "write"

    with pytest.raises(
        AuditServiceError,
        match="read-only",
    ):
        validate_governance_payload(governance)


def test_non_deny_policy_fails_closed() -> None:
    governance = payload()
    governance["default_policy"] = "ALLOW"

    with pytest.raises(
        AuditServiceError,
        match="DENY",
    ):
        validate_governance_payload(governance)


def test_service_captures_and_deduplicates(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    service = AuditSnapshotService(repo)

    governance = payload()

    first = service.capture_snapshot(
        governance=governance,
        captured_at="2026-07-21T15:01:00Z",
        created_at="2026-07-21T15:01:01Z",
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
    )

    second = service.capture_snapshot(
        governance=governance,
        captured_at="2026-07-21T15:01:00Z",
        created_at="2026-07-21T15:02:00Z",
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
    )

    latest = repo.get_latest_snapshot()

    assert first.created is True
    assert second.created is False
    assert first.snapshot == second.snapshot
    assert latest == first.snapshot


def test_service_snapshot_contains_summary(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    service = AuditSnapshotService(repo)

    governance = payload(
        models=[
            model("missing-model", "MISSING"),
        ],
        approved_count=1,
        observed_count=0,
        compliant_count=0,
        violation_count=1,
    )

    snapshot = service.build_snapshot(
        governance=governance,
        captured_at="2026-07-21T15:01:00Z",
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
    )

    assert snapshot.summary.severity == "WARNING"
    assert snapshot.summary.missing_count == 1
    assert snapshot.governance == governance


def test_invalid_created_at_is_rejected(
    tmp_path: Path,
) -> None:
    repo = repository(
        tmp_path / "audit.sqlite3"
    )
    service = AuditSnapshotService(repo)

    with pytest.raises(ValueError):
        service.capture_snapshot(
            governance=payload(),
            captured_at="2026-07-21T15:01:00Z",
            created_at="2026-07-21T15:01:01+00:00",
            source_commit=SOURCE_COMMIT,
            runtime_release=RUNTIME_RELEASE,
        )
