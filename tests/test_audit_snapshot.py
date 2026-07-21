from dataclasses import FrozenInstanceError

import pytest

from core.governance.audit_snapshot import (
    AuditSnapshot,
    AuditSnapshotError,
    GovernanceSummary,
    canonical_json,
    validate_rfc3339_utc,
)


SOURCE_COMMIT = "a" * 40
RUNTIME_RELEASE = "b" * 12
CAPTURED_AT = "2026-07-21T12:34:56Z"


def summary(
    *,
    severity: str = "INFO",
    violation_count: int = 0,
    unapproved_count: int = 0,
    missing_count: int = 0,
    digest_mismatch_count: int = 0,
    resource_policy_violation_count: int = 0,
) -> GovernanceSummary:
    return GovernanceSummary(
        severity=severity,
        approved_count=0,
        observed_count=0,
        compliant_count=0,
        violation_count=violation_count,
        unapproved_count=unapproved_count,
        missing_count=missing_count,
        digest_mismatch_count=digest_mismatch_count,
        resource_policy_violation_count=(
            resource_policy_violation_count
        ),
    )


def governance_payload() -> dict:
    return {
        "service": "model-governance",
        "mode": "read-only",
        "default_policy": "DENY",
        "approved_count": 0,
        "observed_count": 0,
        "compliant_count": 0,
        "violation_count": 0,
        "models": [],
        "write_operations_allowed": False,
    }


def test_canonical_json_is_deterministic() -> None:
    first = {
        "z": 1,
        "a": {
            "y": False,
            "x": ["한글", None],
        },
    }
    second = {
        "a": {
            "x": ["한글", None],
            "y": False,
        },
        "z": 1,
    }

    assert canonical_json(first) == canonical_json(second)
    assert canonical_json(first) == (
        '{"a":{"x":["한글",null],"y":false},"z":1}'
    )


def test_canonical_json_rejects_nested_float() -> None:
    with pytest.raises(AuditSnapshotError):
        canonical_json(
            {
                "models": [
                    {
                        "size_ratio": 1.5,
                    }
                ]
            }
        )


def test_validate_rfc3339_utc_accepts_z_timestamp() -> None:
    assert validate_rfc3339_utc(CAPTURED_AT) == CAPTURED_AT
    assert (
        validate_rfc3339_utc(
            "2026-07-21T12:34:56.123456Z"
        )
        == "2026-07-21T12:34:56.123456Z"
    )


@pytest.mark.parametrize(
    "value",
    [
        "2026-07-21T12:34:56",
        "2026-07-21T12:34:56+00:00",
        "2026-07-21 12:34:56Z",
        "2026-02-30T12:34:56Z",
    ],
)
def test_validate_rfc3339_utc_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(AuditSnapshotError):
        validate_rfc3339_utc(value)


def test_snapshot_id_is_deterministic() -> None:
    first_payload = governance_payload()
    second_payload = {
        key: first_payload[key]
        for key in reversed(tuple(first_payload))
    }

    first = AuditSnapshot.create(
        captured_at=CAPTURED_AT,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=first_payload,
        summary=summary(),
    )

    second = AuditSnapshot.create(
        captured_at=CAPTURED_AT,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=second_payload,
        summary=summary(),
    )

    assert first.snapshot_id == second.snapshot_id
    assert len(first.snapshot_id) == 64


def test_snapshot_copies_governance_input() -> None:
    payload = governance_payload()

    snapshot = AuditSnapshot.create(
        captured_at=CAPTURED_AT,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=payload,
        summary=summary(),
    )

    payload["mode"] = "write"

    assert snapshot.governance["mode"] == "read-only"


def test_snapshot_round_trip() -> None:
    original = AuditSnapshot.create(
        captured_at=CAPTURED_AT,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=governance_payload(),
        summary=summary(),
    )

    restored = AuditSnapshot.from_dict(
        original.to_dict()
    )

    assert restored == original


def test_snapshot_rejects_tampered_identity() -> None:
    snapshot = AuditSnapshot.create(
        captured_at=CAPTURED_AT,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=governance_payload(),
        summary=summary(),
    )

    payload = snapshot.to_dict()
    payload["governance"]["mode"] = "write"

    with pytest.raises(AuditSnapshotError):
        AuditSnapshot.from_dict(payload)


def test_snapshot_dataclass_is_frozen() -> None:
    snapshot = AuditSnapshot.create(
        captured_at=CAPTURED_AT,
        source_commit=SOURCE_COMMIT,
        runtime_release=RUNTIME_RELEASE,
        governance=governance_payload(),
        summary=summary(),
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.captured_at = "2026-07-21T00:00:00Z"


@pytest.mark.parametrize(
    ("source_commit", "runtime_release"),
    [
        ("A" * 40, RUNTIME_RELEASE),
        ("a" * 39, RUNTIME_RELEASE),
        (SOURCE_COMMIT, "B" * 12),
        (SOURCE_COMMIT, "b" * 11),
    ],
)
def test_snapshot_rejects_invalid_release_identity(
    source_commit: str,
    runtime_release: str,
) -> None:
    with pytest.raises(AuditSnapshotError):
        AuditSnapshot.create(
            captured_at=CAPTURED_AT,
            source_commit=source_commit,
            runtime_release=runtime_release,
            governance=governance_payload(),
            summary=summary(),
        )


def test_summary_requires_consistent_violation_count() -> None:
    with pytest.raises(AuditSnapshotError):
        summary(
            severity="CRITICAL",
            violation_count=1,
            unapproved_count=0,
        )


def test_summary_rejects_negative_count() -> None:
    with pytest.raises(AuditSnapshotError):
        GovernanceSummary(
            severity="WARNING",
            approved_count=0,
            observed_count=0,
            compliant_count=0,
            violation_count=-1,
            unapproved_count=0,
            missing_count=0,
            digest_mismatch_count=0,
            resource_policy_violation_count=0,
        )
