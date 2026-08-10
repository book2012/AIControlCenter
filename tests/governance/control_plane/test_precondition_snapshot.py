import json
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from core.governance.control_plane.domain import (
    DuplicatePreconditionBinding,
    GovernanceIdentity,
    GovernancePreconditionSnapshot,
    InvalidPreconditionModel,
    PreconditionBinding,
    PreconditionComparisonStatus,
    PreconditionDriftReason,
    compare_precondition_snapshots,
)

T0 = datetime(2026, 8, 10, 1, tzinfo=timezone.utc)
T1 = datetime(2026, 8, 10, 2, tzinfo=timezone.utc)


def binding(name: str, value: str | None = None) -> PreconditionBinding:
    return PreconditionBinding(name, value or f"ref:{name}")


def snapshot(**changes: object) -> GovernancePreconditionSnapshot:
    values = {
        "schema_version": "1.0.0",
        "snapshot_id": "snapshot-1",
        "lifecycle_id": "lifecycle-1",
        "request_id": "request-1",
        "collected_at": T0,
        "collector_identities": (
            GovernanceIdentity("collector-b", "SERVICE"),
            GovernanceIdentity("collector-a", "SERVICE"),
        ),
        "target_identity": GovernanceIdentity("target-1", "SERVICE"),
        "git_state_binding": binding("git"),
        "runtime_identity_binding": binding("runtime"),
        "security_state_bindings": (binding("z-security"), binding("a-security")),
        "manifest_bindings": (binding("manifest-b"), binding("manifest-a")),
        "operational_state_bindings": (binding("operation-b"), binding("operation-a")),
        "policy_version": "policy-1",
        "snapshot_digest": "sha256:snapshot",
    }
    values.update(changes)
    return GovernancePreconditionSnapshot(**values)  # type: ignore[arg-type]


def test_snapshot_and_bindings_are_immutable() -> None:
    value = snapshot()
    with pytest.raises(FrozenInstanceError):
        value.snapshot_id = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        value.git_state_binding.value = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "change",
    [
        {"snapshot_id": ""},
        {"collector_identities": ()},
        {"target_identity": ""},
        {"policy_version": " "},
        {"snapshot_digest": ""},
    ],
)
def test_non_empty_snapshot_identities(change: dict[str, object]) -> None:
    with pytest.raises(InvalidPreconditionModel):
        snapshot(**change)


@pytest.mark.parametrize(
    "category",
    ["security_state_bindings", "manifest_bindings", "operational_state_bindings"],
)
def test_duplicate_binding_names_are_rejected(category: str) -> None:
    with pytest.raises(DuplicatePreconditionBinding):
        snapshot(**{category: (binding("same", "one"), binding("same", "two"))})


def test_binding_order_and_projection_are_deterministic_and_json_safe() -> None:
    value = snapshot()
    assert [item.name for item in value.security_state_bindings] == [
        "a-security", "z-security"
    ]
    first = value.to_dict()
    assert first == value.to_dict()
    assert json.loads(json.dumps(first)) == first
    assert [item["identity_id"] for item in first["collector_identities"]] == [
        "collector-a", "collector-b"
    ]


def test_observational_metadata_differences_alone_match() -> None:
    expected = snapshot()
    observed = replace(
        expected,
        snapshot_id="snapshot-2",
        collected_at=T1,
        collector_identities=(GovernanceIdentity("other-collector", "SERVICE"),),
    )
    result = compare_precondition_snapshots(expected, observed)
    assert result.status is PreconditionComparisonStatus.MATCH
    assert result.reason_codes == ()
    assert result.expected_snapshot_id == "snapshot-1"
    assert result.observed_snapshot_id == "snapshot-2"


def test_exact_equality_matches() -> None:
    expected = snapshot()
    assert compare_precondition_snapshots(expected, expected).status is PreconditionComparisonStatus.MATCH


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"lifecycle_id": "other"}, PreconditionDriftReason.LIFECYCLE_BINDING_DRIFT),
        ({"request_id": "other"}, PreconditionDriftReason.REQUEST_BINDING_DRIFT),
        ({"target_identity": GovernanceIdentity("other", "SERVICE")}, PreconditionDriftReason.TARGET_IDENTITY_DRIFT),
        ({"git_state_binding": binding("git", "other")}, PreconditionDriftReason.GIT_STATE_DRIFT),
        ({"runtime_identity_binding": binding("runtime", "other")}, PreconditionDriftReason.RUNTIME_IDENTITY_DRIFT),
        ({"security_state_bindings": (binding("security", "other"),)}, PreconditionDriftReason.SECURITY_STATE_DRIFT),
        ({"manifest_bindings": (binding("manifest", "other"),)}, PreconditionDriftReason.MANIFEST_BINDING_DRIFT),
        ({"operational_state_bindings": (binding("operation", "other"),)}, PreconditionDriftReason.OPERATIONAL_STATE_DRIFT),
        ({"policy_version": "other"}, PreconditionDriftReason.POLICY_VERSION_DRIFT),
        ({"snapshot_digest": "sha256:other"}, PreconditionDriftReason.SNAPSHOT_DIGEST_DRIFT),
    ],
)
def test_each_bound_category_independently_drifts(
    change: dict[str, object], reason: PreconditionDriftReason
) -> None:
    result = compare_precondition_snapshots(snapshot(), snapshot(**change))
    assert result.status is PreconditionComparisonStatus.DRIFT
    assert result.reason_codes == (reason,)


def test_reason_order_is_frozen_and_inputs_remain_unchanged() -> None:
    expected = snapshot()
    observed = snapshot(
        lifecycle_id="other-lifecycle",
        git_state_binding=binding("git", "other"),
        policy_version="other-policy",
        snapshot_digest="sha256:other",
    )
    expected_projection = expected.to_dict()
    observed_projection = observed.to_dict()
    result = compare_precondition_snapshots(expected, observed)
    assert result.reason_codes == (
        PreconditionDriftReason.LIFECYCLE_BINDING_DRIFT,
        PreconditionDriftReason.GIT_STATE_DRIFT,
        PreconditionDriftReason.POLICY_VERSION_DRIFT,
        PreconditionDriftReason.SNAPSHOT_DIGEST_DRIFT,
    )
    assert result.to_dict()["reason_codes"] == [item.value for item in result.reason_codes]
    assert expected.to_dict() == expected_projection
    assert observed.to_dict() == observed_projection
