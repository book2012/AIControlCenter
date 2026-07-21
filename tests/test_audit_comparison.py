import pytest

from core.governance.audit_comparison import (
    AuditComparisonError,
    compare_snapshots,
)
from core.governance.audit_snapshot import (
    AuditSnapshot,
    GovernanceSummary,
)


SOURCE_COMMIT = "0188a2b10c3aa498e7a58a1583eb7e4eb8d549bc"
RUNTIME_RELEASE = "39fe04e3330e"


def snapshot(
    captured_at: str,
    *,
    models: list[dict] | None = None,
    severity: str = "INFO",
    approved_count: int = 0,
    observed_count: int = 0,
    compliant_count: int = 0,
    violation_count: int = 0,
    unapproved_count: int = 0,
    missing_count: int = 0,
    digest_mismatch_count: int = 0,
    resource_policy_violation_count: int = 0,
) -> AuditSnapshot:
    models = [] if models is None else models

    governance = {
        "service": "model-governance",
        "mode": "read-only",
        "default_policy": "DENY",
        "approved_count": approved_count,
        "observed_count": observed_count,
        "compliant_count": compliant_count,
        "violation_count": violation_count,
        "models": models,
        "write_operations_allowed": False,
    }

    summary = GovernanceSummary(
        severity=severity,
        approved_count=approved_count,
        observed_count=observed_count,
        compliant_count=compliant_count,
        violation_count=violation_count,
        unapproved_count=unapproved_count,
        missing_count=missing_count,
        digest_mismatch_count=digest_mismatch_count,
        resource_policy_violation_count=(
            resource_policy_violation_count
        ),
    )

    return AuditSnapshot.create(
        captured_at=captured_at,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=governance,
        summary=summary,
    )


def model(
    name: str,
    status: str,
) -> dict:
    return {
        "name": name,
        "compliance_status": status,
    }


def test_identical_state_is_unchanged() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z"
    )
    current = snapshot(
        "2026-07-21T16:01:00Z"
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "UNCHANGED"
    assert result.severity_delta == 0
    assert result.model_transitions == ()


def test_new_unapproved_model_is_new_violation() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z"
    )
    current = snapshot(
        "2026-07-21T16:01:00Z",
        models=[
            model("unknown-model", "UNAPPROVED"),
        ],
        severity="CRITICAL",
        observed_count=1,
        violation_count=1,
        unapproved_count=1,
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "NEW_VIOLATION"
    assert result.new_violation_count == 1
    assert result.count_delta.violation_count == 1


def test_all_violations_resolved() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z",
        models=[
            model("approved-model", "MISSING"),
        ],
        severity="WARNING",
        approved_count=1,
        violation_count=1,
        missing_count=1,
    )
    current = snapshot(
        "2026-07-21T16:01:00Z",
        models=[
            model("approved-model", "COMPLIANT"),
        ],
        severity="INFO",
        approved_count=1,
        observed_count=1,
        compliant_count=1,
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "RESOLVED_VIOLATION"
    assert result.resolved_violation_count == 1
    assert result.count_delta.violation_count == -1


def test_violation_count_increase_is_degraded() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z",
        models=[
            model("model-a", "MISSING"),
        ],
        severity="WARNING",
        approved_count=1,
        violation_count=1,
        missing_count=1,
    )
    current = snapshot(
        "2026-07-21T16:01:00Z",
        models=[
            model("model-a", "MISSING"),
            model("model-b", "MISSING"),
        ],
        severity="WARNING",
        approved_count=2,
        violation_count=2,
        missing_count=2,
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "NEW_VIOLATION"
    assert result.count_delta.violation_count == 1


def test_missing_to_digest_mismatch_is_degraded() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z",
        models=[
            model("model-a", "MISSING"),
        ],
        severity="WARNING",
        approved_count=1,
        violation_count=1,
        missing_count=1,
    )
    current = snapshot(
        "2026-07-21T16:01:00Z",
        models=[
            model("model-a", "DIGEST_MISMATCH"),
        ],
        severity="CRITICAL",
        approved_count=1,
        observed_count=1,
        violation_count=1,
        digest_mismatch_count=1,
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "DEGRADED"
    assert result.severity_delta == 1


def test_digest_mismatch_to_missing_is_improved() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z",
        models=[
            model("model-a", "DIGEST_MISMATCH"),
        ],
        severity="CRITICAL",
        approved_count=1,
        observed_count=1,
        violation_count=1,
        digest_mismatch_count=1,
    )
    current = snapshot(
        "2026-07-21T16:01:00Z",
        models=[
            model("model-a", "MISSING"),
        ],
        severity="WARNING",
        approved_count=1,
        violation_count=1,
        missing_count=1,
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "IMPROVED"
    assert result.severity_delta == -1


def test_mixed_transition_prefers_degraded() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z",
        models=[
            model("model-a", "MISSING"),
            model("model-b", "COMPLIANT"),
        ],
        severity="WARNING",
        approved_count=2,
        observed_count=1,
        compliant_count=1,
        violation_count=1,
        missing_count=1,
    )
    current = snapshot(
        "2026-07-21T16:01:00Z",
        models=[
            model("model-a", "COMPLIANT"),
            model("model-b", "DIGEST_MISMATCH"),
        ],
        severity="CRITICAL",
        approved_count=2,
        observed_count=2,
        compliant_count=1,
        violation_count=1,
        digest_mismatch_count=1,
    )

    result = compare_snapshots(
        previous,
        current,
    )

    assert result.status == "NEW_VIOLATION"
    assert result.new_violation_count == 1
    assert result.resolved_violation_count == 1


def test_comparison_is_json_ready() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z"
    )
    current = snapshot(
        "2026-07-21T16:01:00Z"
    )

    payload = compare_snapshots(
        previous,
        current,
    ).to_dict()

    assert payload["status"] == "UNCHANGED"
    assert payload["count_delta"]["violation_count"] == 0
    assert payload["model_transitions"] == []


def test_duplicate_model_identity_fails_closed() -> None:
    previous = snapshot(
        "2026-07-21T16:00:00Z",
        models=[
            model("duplicate", "COMPLIANT"),
            model("duplicate", "COMPLIANT"),
        ],
        approved_count=2,
        observed_count=2,
        compliant_count=2,
    )
    current = snapshot(
        "2026-07-21T16:01:00Z"
    )

    with pytest.raises(
        AuditComparisonError,
        match="duplicate model identity",
    ):
        compare_snapshots(
            previous,
            current,
        )


def test_older_current_snapshot_is_rejected() -> None:
    previous = snapshot(
        "2026-07-21T16:01:00Z"
    )
    current = snapshot(
        "2026-07-21T16:00:00Z"
    )

    with pytest.raises(
        AuditComparisonError,
        match="older",
    ):
        compare_snapshots(
            previous,
            current,
        )
