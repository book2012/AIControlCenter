"""Governance audit snapshot orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from core.governance.audit_repository import (
    AppendResult,
    AuditRepository,
)
from core.governance.audit_snapshot import (
    AuditSnapshot,
    AuditSnapshotError,
    GovernanceSummary,
    validate_rfc3339_utc,
)


_ALLOWED_COMPLIANCE_STATUSES = frozenset(
    {
        "COMPLIANT",
        "UNAPPROVED",
        "MISSING",
        "DIGEST_MISMATCH",
        "RESOURCE_POLICY_VIOLATION",
    }
)

_CRITICAL_STATUSES = frozenset(
    {
        "UNAPPROVED",
        "DIGEST_MISMATCH",
        "RESOURCE_POLICY_VIOLATION",
    }
)


class AuditServiceError(ValueError):
    """Raised when governance audit orchestration fails closed."""


@dataclass(frozen=True)
class GovernanceCounts:
    """Validated compliance counts derived from model records."""

    compliant_count: int
    unapproved_count: int
    missing_count: int
    digest_mismatch_count: int
    resource_policy_violation_count: int

    @property
    def violation_count(self) -> int:
        return (
            self.unapproved_count
            + self.missing_count
            + self.digest_mismatch_count
            + self.resource_policy_violation_count
        )


@dataclass(frozen=True)
class SnapshotCaptureResult:
    """Result returned after snapshot generation and append."""

    snapshot: AuditSnapshot
    created: bool


def _require_non_negative_integer(
    payload: Mapping[str, Any],
    field: str,
) -> int:
    value = payload.get(field)

    if isinstance(value, bool):
        raise AuditServiceError(
            f"{field} must be a non-negative integer"
        )

    if not isinstance(value, int) or value < 0:
        raise AuditServiceError(
            f"{field} must be a non-negative integer"
        )

    return value


def _require_models(
    payload: Mapping[str, Any],
) -> Sequence[Mapping[str, Any]]:
    models = payload.get("models")

    if not isinstance(models, list):
        raise AuditServiceError(
            "models must be a list"
        )

    validated: list[Mapping[str, Any]] = []

    for index, model in enumerate(models):
        if not isinstance(model, Mapping):
            raise AuditServiceError(
                f"models[{index}] must be an object"
            )

        validated.append(model)

    return tuple(validated)


def _model_status(
    model: Mapping[str, Any],
    index: int,
) -> str:
    status = model.get("compliance_status")

    if status is None:
        status = model.get("status")

    if not isinstance(status, str):
        raise AuditServiceError(
            f"models[{index}] compliance status is required"
        )

    if status not in _ALLOWED_COMPLIANCE_STATUSES:
        raise AuditServiceError(
            f"models[{index}] has unknown compliance status"
        )

    return status


def derive_governance_counts(
    payload: Mapping[str, Any],
) -> GovernanceCounts:
    """Derive trusted compliance counts from model records."""

    models = _require_models(payload)

    counts = {
        "COMPLIANT": 0,
        "UNAPPROVED": 0,
        "MISSING": 0,
        "DIGEST_MISMATCH": 0,
        "RESOURCE_POLICY_VIOLATION": 0,
    }

    for index, model in enumerate(models):
        counts[_model_status(model, index)] += 1

    result = GovernanceCounts(
        compliant_count=counts["COMPLIANT"],
        unapproved_count=counts["UNAPPROVED"],
        missing_count=counts["MISSING"],
        digest_mismatch_count=counts["DIGEST_MISMATCH"],
        resource_policy_violation_count=(
            counts["RESOURCE_POLICY_VIOLATION"]
        ),
    )

    supplied_compliant = _require_non_negative_integer(
        payload,
        "compliant_count",
    )
    supplied_violations = _require_non_negative_integer(
        payload,
        "violation_count",
    )

    if supplied_compliant != result.compliant_count:
        raise AuditServiceError(
            "compliant_count does not match model records"
        )

    if supplied_violations != result.violation_count:
        raise AuditServiceError(
            "violation_count does not match model records"
        )

    return result


def calculate_severity(
    *,
    counts: GovernanceCounts,
    write_operations_allowed: bool,
) -> str:
    """Map governance state to an audit severity."""

    if write_operations_allowed:
        return "CRITICAL"

    if (
        counts.unapproved_count > 0
        or counts.digest_mismatch_count > 0
        or counts.resource_policy_violation_count > 0
    ):
        return "CRITICAL"

    if counts.missing_count > 0:
        return "WARNING"

    return "INFO"


def validate_governance_payload(
    payload: Mapping[str, Any],
) -> GovernanceCounts:
    """Validate the read-only model-governance API contract."""

    if not isinstance(payload, Mapping):
        raise AuditServiceError(
            "governance payload must be an object"
        )

    if payload.get("service") != "model-governance":
        raise AuditServiceError(
            "unsupported governance service"
        )

    if payload.get("mode") != "read-only":
        raise AuditServiceError(
            "governance mode must be read-only"
        )

    if payload.get("default_policy") != "DENY":
        raise AuditServiceError(
            "default policy must be DENY"
        )

    write_allowed = payload.get(
        "write_operations_allowed"
    )

    if not isinstance(write_allowed, bool):
        raise AuditServiceError(
            "write_operations_allowed must be boolean"
        )

    approved_count = _require_non_negative_integer(
        payload,
        "approved_count",
    )
    observed_count = _require_non_negative_integer(
        payload,
        "observed_count",
    )

    counts = derive_governance_counts(payload)

    models = _require_models(payload)

    if len(models) != (
        counts.compliant_count
        + counts.violation_count
    ):
        raise AuditServiceError(
            "model count does not match compliance totals"
        )

    if approved_count < (
        counts.compliant_count
        + counts.missing_count
        + counts.digest_mismatch_count
        + counts.resource_policy_violation_count
    ):
        raise AuditServiceError(
            "approved_count is smaller than approved model states"
        )

    if observed_count < (
        counts.compliant_count
        + counts.unapproved_count
        + counts.digest_mismatch_count
        + counts.resource_policy_violation_count
    ):
        raise AuditServiceError(
            "observed_count is smaller than observed model states"
        )

    return counts


def build_governance_summary(
    payload: Mapping[str, Any],
) -> GovernanceSummary:
    """Build an immutable summary from validated governance JSON."""

    counts = validate_governance_payload(payload)

    write_allowed = payload["write_operations_allowed"]

    return GovernanceSummary(
        severity=calculate_severity(
            counts=counts,
            write_operations_allowed=write_allowed,
        ),
        approved_count=payload["approved_count"],
        observed_count=payload["observed_count"],
        compliant_count=counts.compliant_count,
        violation_count=counts.violation_count,
        unapproved_count=counts.unapproved_count,
        missing_count=counts.missing_count,
        digest_mismatch_count=(
            counts.digest_mismatch_count
        ),
        resource_policy_violation_count=(
            counts.resource_policy_violation_count
        ),
    )


class AuditSnapshotService:
    """Create and append canonical governance audit snapshots."""

    def __init__(
        self,
        repository: AuditRepository,
    ) -> None:
        if not isinstance(repository, AuditRepository):
            raise AuditServiceError(
                "repository must implement AuditRepository"
            )

        self._repository = repository

    def build_snapshot(
        self,
        *,
        governance: Mapping[str, Any],
        captured_at: str,
        source_commit: str,
        runtime_release: str,
    ) -> AuditSnapshot:
        summary = build_governance_summary(governance)

        try:
            return AuditSnapshot.create(
                captured_at=captured_at,
                source_commit=source_commit,
                runtime_release=runtime_release,
                governance=governance,
                summary=summary,
            )
        except AuditSnapshotError as error:
            raise AuditServiceError(
                "audit snapshot creation failed"
            ) from error

    def capture_snapshot(
        self,
        *,
        governance: Mapping[str, Any],
        captured_at: str,
        created_at: str,
        source_commit: str,
        runtime_release: str,
    ) -> SnapshotCaptureResult:
        validate_rfc3339_utc(created_at)

        snapshot = self.build_snapshot(
            governance=governance,
            captured_at=captured_at,
            source_commit=source_commit,
            runtime_release=runtime_release,
        )

        append_result: AppendResult = (
            self._repository.append_snapshot(
                snapshot,
                created_at=created_at,
            )
        )

        return SnapshotCaptureResult(
            snapshot=append_result.snapshot,
            created=append_result.created,
        )
