"""Read-only comparison of immutable governance audit snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from core.governance.audit_snapshot import AuditSnapshot


_COMPARISON_STATUSES = frozenset(
    {
        "UNCHANGED",
        "IMPROVED",
        "DEGRADED",
        "NEW_VIOLATION",
        "RESOLVED_VIOLATION",
    }
)

_SEVERITY_RANK = {
    "INFO": 0,
    "WARNING": 1,
    "CRITICAL": 2,
}

_MODEL_STATUS_RANK = {
    "COMPLIANT": 0,
    "MISSING": 1,
    "UNAPPROVED": 2,
    "DIGEST_MISMATCH": 3,
    "RESOURCE_POLICY_VIOLATION": 3,
}

_VIOLATING_STATUSES = frozenset(
    {
        "MISSING",
        "UNAPPROVED",
        "DIGEST_MISMATCH",
        "RESOURCE_POLICY_VIOLATION",
    }
)


class AuditComparisonError(ValueError):
    """Raised when audit snapshots cannot be compared safely."""


@dataclass(frozen=True)
class CountDelta:
    approved_count: int
    observed_count: int
    compliant_count: int
    violation_count: int
    unapproved_count: int
    missing_count: int
    digest_mismatch_count: int
    resource_policy_violation_count: int

    def to_dict(self) -> dict[str, int]:
        return {
            "approved_count": self.approved_count,
            "observed_count": self.observed_count,
            "compliant_count": self.compliant_count,
            "violation_count": self.violation_count,
            "unapproved_count": self.unapproved_count,
            "missing_count": self.missing_count,
            "digest_mismatch_count":
                self.digest_mismatch_count,
            "resource_policy_violation_count":
                self.resource_policy_violation_count,
        }


@dataclass(frozen=True)
class ModelTransition:
    model_key: str
    previous_status: str | None
    current_status: str | None
    direction: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "model_key": self.model_key,
            "previous_status": self.previous_status,
            "current_status": self.current_status,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class AuditComparison:
    previous_snapshot_id: str
    current_snapshot_id: str
    status: str
    previous_severity: str
    current_severity: str
    severity_delta: int
    count_delta: CountDelta
    model_transitions: tuple[ModelTransition, ...]
    new_violation_count: int
    resolved_violation_count: int

    def __post_init__(self) -> None:
        if self.status not in _COMPARISON_STATUSES:
            raise AuditComparisonError(
                "unsupported comparison status"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "previous_snapshot_id":
                self.previous_snapshot_id,
            "current_snapshot_id":
                self.current_snapshot_id,
            "status": self.status,
            "previous_severity":
                self.previous_severity,
            "current_severity":
                self.current_severity,
            "severity_delta": self.severity_delta,
            "count_delta": self.count_delta.to_dict(),
            "model_transitions": [
                transition.to_dict()
                for transition in self.model_transitions
            ],
            "new_violation_count":
                self.new_violation_count,
            "resolved_violation_count":
                self.resolved_violation_count,
        }


def _model_key(
    model: Mapping[str, Any],
    index: int,
) -> str:
    for field in (
        "approved_model_id",
        "name",
        "model",
        "id",
    ):
        value = model.get(field)

        if isinstance(value, str) and value:
            return value

    raise AuditComparisonError(
        f"models[{index}] has no stable identity"
    )


def _model_status(
    model: Mapping[str, Any],
    index: int,
) -> str:
    status = model.get("compliance_status")

    if status is None:
        status = model.get("status")

    if (
        not isinstance(status, str)
        or status not in _MODEL_STATUS_RANK
    ):
        raise AuditComparisonError(
            f"models[{index}] has invalid compliance status"
        )

    return status


def _model_status_map(
    snapshot: AuditSnapshot,
) -> dict[str, str]:
    models = snapshot.governance.get("models")

    if not isinstance(models, list):
        raise AuditComparisonError(
            "snapshot governance models must be a list"
        )

    result: dict[str, str] = {}

    for index, model in enumerate(models):
        if not isinstance(model, Mapping):
            raise AuditComparisonError(
                f"models[{index}] must be an object"
            )

        key = _model_key(model, index)

        if key in result:
            raise AuditComparisonError(
                f"duplicate model identity: {key}"
            )

        result[key] = _model_status(model, index)

    return result


def _transition_direction(
    previous_status: str | None,
    current_status: str | None,
) -> str:
    if previous_status == current_status:
        return "UNCHANGED"

    if previous_status is None:
        if current_status in _VIOLATING_STATUSES:
            return "DEGRADED"

        return "ADDED"

    if current_status is None:
        if previous_status in _VIOLATING_STATUSES:
            return "IMPROVED"

        return "REMOVED"

    previous_rank = _MODEL_STATUS_RANK[previous_status]
    current_rank = _MODEL_STATUS_RANK[current_status]

    if current_rank > previous_rank:
        return "DEGRADED"

    if current_rank < previous_rank:
        return "IMPROVED"

    return "CHANGED"


def _count_delta(
    previous: AuditSnapshot,
    current: AuditSnapshot,
) -> CountDelta:
    previous_summary = previous.summary
    current_summary = current.summary

    return CountDelta(
        approved_count=(
            current_summary.approved_count
            - previous_summary.approved_count
        ),
        observed_count=(
            current_summary.observed_count
            - previous_summary.observed_count
        ),
        compliant_count=(
            current_summary.compliant_count
            - previous_summary.compliant_count
        ),
        violation_count=(
            current_summary.violation_count
            - previous_summary.violation_count
        ),
        unapproved_count=(
            current_summary.unapproved_count
            - previous_summary.unapproved_count
        ),
        missing_count=(
            current_summary.missing_count
            - previous_summary.missing_count
        ),
        digest_mismatch_count=(
            current_summary.digest_mismatch_count
            - previous_summary.digest_mismatch_count
        ),
        resource_policy_violation_count=(
            current_summary.resource_policy_violation_count
            - previous_summary.resource_policy_violation_count
        ),
    )


def compare_snapshots(
    previous: AuditSnapshot,
    current: AuditSnapshot,
) -> AuditComparison:
    """Compare two snapshots without mutating either snapshot."""

    if not isinstance(previous, AuditSnapshot):
        raise AuditComparisonError(
            "previous must be an AuditSnapshot"
        )

    if not isinstance(current, AuditSnapshot):
        raise AuditComparisonError(
            "current must be an AuditSnapshot"
        )

    if current.captured_at < previous.captured_at:
        raise AuditComparisonError(
            "current snapshot cannot be older than previous"
        )

    previous_models = _model_status_map(previous)
    current_models = _model_status_map(current)

    transitions: list[ModelTransition] = []

    for key in sorted(
        set(previous_models) | set(current_models)
    ):
        previous_status = previous_models.get(key)
        current_status = current_models.get(key)

        direction = _transition_direction(
            previous_status,
            current_status,
        )

        if direction == "UNCHANGED":
            continue

        transitions.append(
            ModelTransition(
                model_key=key,
                previous_status=previous_status,
                current_status=current_status,
                direction=direction,
            )
        )

    new_violation_count = sum(
        transition.current_status in _VIOLATING_STATUSES
        and transition.previous_status
            not in _VIOLATING_STATUSES
        for transition in transitions
    )

    resolved_violation_count = sum(
        transition.previous_status in _VIOLATING_STATUSES
        and transition.current_status
            not in _VIOLATING_STATUSES
        for transition in transitions
    )

    severity_delta = (
        _SEVERITY_RANK[current.summary.severity]
        - _SEVERITY_RANK[previous.summary.severity]
    )

    count_delta = _count_delta(
        previous,
        current,
    )

    degraded_transition = any(
        transition.direction == "DEGRADED"
        for transition in transitions
    )

    improved_transition = any(
        transition.direction == "IMPROVED"
        for transition in transitions
    )

    if (
        previous.summary.violation_count == 0
        and current.summary.violation_count > 0
    ) or new_violation_count > 0:
        status = "NEW_VIOLATION"
    elif (
        previous.summary.violation_count > 0
        and current.summary.violation_count == 0
    ) or (
        resolved_violation_count > 0
        and new_violation_count == 0
        and not degraded_transition
        and count_delta.violation_count < 0
    ):
        status = "RESOLVED_VIOLATION"
    elif (
        severity_delta > 0
        or count_delta.violation_count > 0
        or degraded_transition
    ):
        status = "DEGRADED"
    elif (
        severity_delta < 0
        or count_delta.violation_count < 0
        or improved_transition
    ):
        status = "IMPROVED"
    elif (
        previous.to_dict() == current.to_dict()
        or (
            previous.governance == current.governance
            and previous.summary == current.summary
        )
    ):
        status = "UNCHANGED"
    else:
        status = "UNCHANGED"

    return AuditComparison(
        previous_snapshot_id=previous.snapshot_id,
        current_snapshot_id=current.snapshot_id,
        status=status,
        previous_severity=previous.summary.severity,
        current_severity=current.summary.severity,
        severity_delta=severity_delta,
        count_delta=count_delta,
        model_transitions=tuple(transitions),
        new_violation_count=new_violation_count,
        resolved_violation_count=resolved_violation_count,
    )
