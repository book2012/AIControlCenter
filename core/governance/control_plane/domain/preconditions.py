"""Pure immutable SEC-02 precondition snapshots and stale evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any

from .authorization import (
    AuthorizationState,
    AuthorizationTransitionResult,
    GovernanceAuthorization,
    GovernanceAuthorizationStateRecord,
    transition_authorization,
)
from .failures import (
    AuthorizationSnapshotBindingMismatch,
    DuplicatePreconditionBinding,
    InvalidPreconditionComparisonInput,
    InvalidPreconditionModel,
    InvalidStaleEvaluationState,
)
from .identity import GovernanceIdentity


class PreconditionComparisonStatus(StrEnum):
    MATCH = "MATCH"
    DRIFT = "DRIFT"


class PreconditionDriftReason(StrEnum):
    LIFECYCLE_BINDING_DRIFT = "LIFECYCLE_BINDING_DRIFT"
    REQUEST_BINDING_DRIFT = "REQUEST_BINDING_DRIFT"
    TARGET_IDENTITY_DRIFT = "TARGET_IDENTITY_DRIFT"
    GIT_STATE_DRIFT = "GIT_STATE_DRIFT"
    RUNTIME_IDENTITY_DRIFT = "RUNTIME_IDENTITY_DRIFT"
    SECURITY_STATE_DRIFT = "SECURITY_STATE_DRIFT"
    MANIFEST_BINDING_DRIFT = "MANIFEST_BINDING_DRIFT"
    OPERATIONAL_STATE_DRIFT = "OPERATIONAL_STATE_DRIFT"
    POLICY_VERSION_DRIFT = "POLICY_VERSION_DRIFT"
    SNAPSHOT_DIGEST_DRIFT = "SNAPSHOT_DIGEST_DRIFT"


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidPreconditionModel(f"{field_name} must not be empty")
    return value


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise InvalidPreconditionModel(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise InvalidPreconditionModel(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True, order=True)
class PreconditionBinding:
    """A named, value-free reference to one authorization-bound observation."""

    name: str
    value: str

    def __post_init__(self) -> None:
        _text(self.name, "binding name")
        _text(self.value, "binding value")

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "value": self.value}


def _bindings(
    value: tuple[PreconditionBinding, ...], field_name: str
) -> tuple[PreconditionBinding, ...]:
    if not isinstance(value, tuple):
        raise InvalidPreconditionModel(f"{field_name} must be a tuple")
    if any(not isinstance(item, PreconditionBinding) for item in value):
        raise InvalidPreconditionModel(f"{field_name} must contain PreconditionBinding values")
    names = tuple(item.name for item in value)
    if len(names) != len(set(names)):
        raise DuplicatePreconditionBinding(f"{field_name} contains a duplicate binding name")
    return tuple(sorted(value, key=lambda item: item.name))


def _collectors(value: tuple[GovernanceIdentity, ...]) -> tuple[GovernanceIdentity, ...]:
    if not isinstance(value, tuple) or not value:
        raise InvalidPreconditionModel("collector_identities must not be empty")
    if any(not isinstance(item, GovernanceIdentity) for item in value):
        raise InvalidPreconditionModel("collector_identities must contain GovernanceIdentity values")
    keys = tuple((item.identity_type, item.identity_id) for item in value)
    if len(keys) != len(set(keys)):
        raise DuplicatePreconditionBinding("collector_identities contains a duplicate identity")
    return tuple(sorted(value, key=lambda item: (item.identity_type, item.identity_id)))


@dataclass(frozen=True, slots=True)
class GovernancePreconditionSnapshot:
    schema_version: str
    snapshot_id: str
    lifecycle_id: str
    request_id: str
    collected_at: datetime
    collector_identities: tuple[GovernanceIdentity, ...]
    target_identity: GovernanceIdentity
    git_state_binding: PreconditionBinding
    runtime_identity_binding: PreconditionBinding
    security_state_bindings: tuple[PreconditionBinding, ...]
    manifest_bindings: tuple[PreconditionBinding, ...]
    operational_state_bindings: tuple[PreconditionBinding, ...]
    policy_version: str
    snapshot_digest: str

    def __post_init__(self) -> None:
        for name in (
            "schema_version", "snapshot_id", "lifecycle_id", "request_id",
            "policy_version", "snapshot_digest",
        ):
            _text(getattr(self, name), name)
        object.__setattr__(self, "collected_at", _utc(self.collected_at, "collected_at"))
        object.__setattr__(self, "collector_identities", _collectors(self.collector_identities))
        if not isinstance(self.target_identity, GovernanceIdentity):
            raise InvalidPreconditionModel("target_identity must be GovernanceIdentity")
        for name in ("git_state_binding", "runtime_identity_binding"):
            if not isinstance(getattr(self, name), PreconditionBinding):
                raise InvalidPreconditionModel(f"{name} must be PreconditionBinding")
        for name in (
            "security_state_bindings", "manifest_bindings", "operational_state_bindings",
        ):
            object.__setattr__(self, name, _bindings(getattr(self, name), name))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "snapshot_id": self.snapshot_id,
            "lifecycle_id": self.lifecycle_id,
            "request_id": self.request_id,
            "collected_at": self.collected_at.isoformat(),
            "collector_identities": [item.to_dict() for item in self.collector_identities],
            "target_identity": self.target_identity.to_dict(),
            "git_state_binding": self.git_state_binding.to_dict(),
            "runtime_identity_binding": self.runtime_identity_binding.to_dict(),
            "security_state_bindings": [item.to_dict() for item in self.security_state_bindings],
            "manifest_bindings": [item.to_dict() for item in self.manifest_bindings],
            "operational_state_bindings": [
                item.to_dict() for item in self.operational_state_bindings
            ],
            "policy_version": self.policy_version,
            "snapshot_digest": self.snapshot_digest,
        }


@dataclass(frozen=True, slots=True)
class PreconditionComparisonResult:
    status: PreconditionComparisonStatus
    expected_snapshot_id: str
    observed_snapshot_id: str
    reason_codes: tuple[PreconditionDriftReason, ...]
    expected_snapshot_digest: str
    observed_snapshot_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "expected_snapshot_id": self.expected_snapshot_id,
            "observed_snapshot_id": self.observed_snapshot_id,
            "reason_codes": [reason.value for reason in self.reason_codes],
            "expected_snapshot_digest": self.expected_snapshot_digest,
            "observed_snapshot_digest": self.observed_snapshot_digest,
        }


_BOUND_COMPARISONS = (
    ("lifecycle_id", PreconditionDriftReason.LIFECYCLE_BINDING_DRIFT),
    ("request_id", PreconditionDriftReason.REQUEST_BINDING_DRIFT),
    ("target_identity", PreconditionDriftReason.TARGET_IDENTITY_DRIFT),
    ("git_state_binding", PreconditionDriftReason.GIT_STATE_DRIFT),
    ("runtime_identity_binding", PreconditionDriftReason.RUNTIME_IDENTITY_DRIFT),
    ("security_state_bindings", PreconditionDriftReason.SECURITY_STATE_DRIFT),
    ("manifest_bindings", PreconditionDriftReason.MANIFEST_BINDING_DRIFT),
    ("operational_state_bindings", PreconditionDriftReason.OPERATIONAL_STATE_DRIFT),
    ("policy_version", PreconditionDriftReason.POLICY_VERSION_DRIFT),
    ("snapshot_digest", PreconditionDriftReason.SNAPSHOT_DIGEST_DRIFT),
)


def compare_precondition_snapshots(
    expected: GovernancePreconditionSnapshot,
    observed: GovernancePreconditionSnapshot,
) -> PreconditionComparisonResult:
    """Compare authorization-bound content without mutating either snapshot."""
    if not isinstance(expected, GovernancePreconditionSnapshot) or not isinstance(
        observed, GovernancePreconditionSnapshot
    ):
        raise InvalidPreconditionComparisonInput("expected and observed must be snapshots")
    reasons = tuple(
        reason for field_name, reason in _BOUND_COMPARISONS
        if getattr(expected, field_name) != getattr(observed, field_name)
    )
    return PreconditionComparisonResult(
        status=(PreconditionComparisonStatus.DRIFT if reasons else PreconditionComparisonStatus.MATCH),
        expected_snapshot_id=expected.snapshot_id,
        observed_snapshot_id=observed.snapshot_id,
        reason_codes=reasons,
        expected_snapshot_digest=expected.snapshot_digest,
        observed_snapshot_digest=observed.snapshot_digest,
    )


def validate_authorization_snapshot_binding(
    authorization: GovernanceAuthorization,
    expected_snapshot: GovernancePreconditionSnapshot,
) -> None:
    """Fail closed unless issued authority binds exactly to the expected snapshot."""
    if not isinstance(authorization, GovernanceAuthorization) or not isinstance(
        expected_snapshot, GovernancePreconditionSnapshot
    ):
        raise InvalidPreconditionComparisonInput("authorization and expected snapshot are required")
    if authorization.state is not AuthorizationState.AUTHORIZED or authorization.receipt is None:
        raise InvalidStaleEvaluationState("precondition evaluation requires AUTHORIZED state")
    receipt = authorization.receipt
    if (
        receipt.lifecycle_id != expected_snapshot.lifecycle_id
        or receipt.request_id != expected_snapshot.request_id
        or receipt.precondition_snapshot_digest != expected_snapshot.snapshot_digest
    ):
        raise AuthorizationSnapshotBindingMismatch("authorization does not bind expected snapshot")


@dataclass(frozen=True, slots=True)
class PreconditionEvaluationResult:
    authorization: GovernanceAuthorization
    comparison: PreconditionComparisonResult
    state_record: GovernanceAuthorizationStateRecord | None


def evaluate_authorization_preconditions(
    authorization: GovernanceAuthorization,
    expected_snapshot: GovernancePreconditionSnapshot,
    observed_snapshot: GovernancePreconditionSnapshot,
    evaluated_at: datetime,
    *,
    comparison_digest: str | None = None,
    audit_event_id: str | None = None,
) -> PreconditionEvaluationResult:
    """Keep matching authority unchanged or return a terminal stale transition."""
    validate_authorization_snapshot_binding(authorization, expected_snapshot)
    try:
        evaluation_time = _utc(evaluated_at, "evaluated_at")
    except InvalidPreconditionModel as error:
        raise InvalidPreconditionComparisonInput(
            "evaluated_at must be timezone-aware UTC"
        ) from error
    comparison = compare_precondition_snapshots(expected_snapshot, observed_snapshot)
    if comparison.status is PreconditionComparisonStatus.MATCH:
        return PreconditionEvaluationResult(authorization, comparison, None)
    reason = "PRECONDITION_DRIFT:" + ",".join(item.value for item in comparison.reason_codes)
    transitioned = transition_authorization(
        authorization,
        AuthorizationState.STALE,
        reason,
        evaluation_time,
        precondition_comparison_digest=comparison_digest,
        audit_event_id=audit_event_id,
    )
    return PreconditionEvaluationResult(
        transitioned.authorization, comparison, transitioned.state_record
    )


def evaluate_authorization_expiry(
    authorization: GovernanceAuthorization,
    evaluated_at: datetime,
    *,
    audit_event_id: str | None = None,
) -> AuthorizationTransitionResult | None:
    """Expire only after expires_at; the exact boundary remains authorized."""
    if not isinstance(authorization, GovernanceAuthorization):
        raise InvalidPreconditionComparisonInput("authorization is required")
    if authorization.state is not AuthorizationState.AUTHORIZED or authorization.receipt is None:
        raise InvalidStaleEvaluationState("expiry evaluation requires AUTHORIZED state")
    try:
        evaluation_time = _utc(evaluated_at, "evaluated_at")
    except InvalidPreconditionModel as error:
        raise InvalidPreconditionComparisonInput("evaluated_at must be timezone-aware UTC") from error
    if evaluation_time <= authorization.receipt.expires_at:
        return None
    return transition_authorization(
        authorization,
        AuthorizationState.STALE,
        "AUTHORIZATION_EXPIRED",
        evaluation_time,
        audit_event_id=audit_event_id,
    )
