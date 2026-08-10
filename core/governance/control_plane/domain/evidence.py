"""Pure immutable SEC-02 failure and value-free evidence reference models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import re
from typing import Any

from .authorization import AuthorizationState
from .failures import (
    DuplicateEvidenceReference,
    InvalidEvidenceBundle,
    InvalidEvidenceManifest,
    InvalidEvidenceReference,
    InvalidFailureEvidence,
    InvalidReceiptCounts,
    RetryProhibitionViolation,
    RollbackProhibitionViolation,
)


class FailurePhase(StrEnum):
    PRECONDITION = "PRECONDITION"
    AUTHORIZATION_CONSUMPTION = "AUTHORIZATION_CONSUMPTION"
    EXECUTION = "EXECUTION"
    POSTCONDITION = "POSTCONDITION"
    EVIDENCE_PERSISTENCE = "EVIDENCE_PERSISTENCE"
    CLOSEOUT = "CLOSEOUT"


class FailureClass(StrEnum):
    PRECONDITION_FAILED = "PRECONDITION_FAILED"
    AUTHORIZATION_CONSUMPTION_FAILED = "AUTHORIZATION_CONSUMPTION_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    EXECUTION_UNCERTAIN = "EXECUTION_UNCERTAIN"
    POSTCONDITION_FAILED = "POSTCONDITION_FAILED"
    EVIDENCE_PERSISTENCE_FAILED = "EVIDENCE_PERSISTENCE_FAILED"
    CLOSEOUT_FAILED = "CLOSEOUT_FAILED"


_CODE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
_MANUAL_CLASSES = frozenset({
    FailureClass.EXECUTION_FAILED,
    FailureClass.EXECUTION_UNCERTAIN,
    FailureClass.POSTCONDITION_FAILED,
    FailureClass.EVIDENCE_PERSISTENCE_FAILED,
    FailureClass.CLOSEOUT_FAILED,
})


def _text(value: str, field_name: str, error_type: type[ValueError]) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise error_type(f"{field_name} must be non-empty canonical text")
    return value


def _utc(value: datetime, field_name: str, error_type: type[ValueError]) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise error_type(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def _count(value: int, field_name: str, error_type: type[ValueError]) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise error_type(f"{field_name} must be a non-negative integer")
    return value


def _reasons(value: tuple[str, ...], error_type: type[ValueError]) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise error_type("reason_codes must be a tuple")
    for reason in value:
        _text(reason, "reason_code", error_type)
        if _CODE.fullmatch(reason) is None:
            raise error_type("reason_code must be a stable code")
    if len(value) != len(set(value)):
        raise error_type("reason_codes must not contain duplicates")
    return tuple(sorted(value))


@dataclass(frozen=True, slots=True)
class GovernanceFailureEvidence:
    schema_version: str
    failure_id: str
    lifecycle_id: str
    phase: FailurePhase
    failure_class: FailureClass
    reason_codes: tuple[str, ...]
    authorization_state: AuthorizationState
    claim_consumed: bool
    actual_invocation_count: int
    completed_count: int
    uncertain_count: int
    retry_prohibited: bool
    rollback_prohibited: bool
    manual_action_required: bool
    occurred_at: datetime

    def __post_init__(self) -> None:
        for name in ("schema_version", "failure_id", "lifecycle_id"):
            _text(getattr(self, name), name, InvalidFailureEvidence)
        if not isinstance(self.phase, FailurePhase):
            raise InvalidFailureEvidence("phase must be FailurePhase")
        if not isinstance(self.failure_class, FailureClass):
            raise InvalidFailureEvidence("failure_class must be FailureClass")
        if not isinstance(self.authorization_state, AuthorizationState):
            raise InvalidFailureEvidence("authorization_state must be AuthorizationState")
        if not isinstance(self.claim_consumed, bool):
            raise InvalidFailureEvidence("claim_consumed must be boolean")
        for name in ("actual_invocation_count", "completed_count", "uncertain_count"):
            _count(getattr(self, name), name, InvalidReceiptCounts)
        if self.completed_count > self.actual_invocation_count:
            raise InvalidReceiptCounts("completed_count exceeds actual_invocation_count")
        if self.uncertain_count > self.actual_invocation_count:
            raise InvalidReceiptCounts("uncertain_count exceeds actual_invocation_count")
        if self.completed_count + self.uncertain_count > self.actual_invocation_count:
            raise InvalidReceiptCounts("completed_count plus uncertain_count exceeds actual_invocation_count")
        if self.claim_consumed and self.authorization_state is not AuthorizationState.CONSUMED:
            raise InvalidFailureEvidence("consumed claim requires CONSUMED authorization state")
        if not self.retry_prohibited:
            raise RetryProhibitionViolation("retry_prohibited must be true")
        if not self.rollback_prohibited:
            raise RollbackProhibitionViolation("rollback_prohibited must be true")
        if not isinstance(self.manual_action_required, bool):
            raise InvalidFailureEvidence("manual_action_required must be boolean")
        if (self.claim_consumed or self.failure_class in _MANUAL_CLASSES) and not self.manual_action_required:
            raise InvalidFailureEvidence("failure class requires manual action")
        object.__setattr__(self, "reason_codes", _reasons(self.reason_codes, InvalidFailureEvidence))
        object.__setattr__(self, "occurred_at", _utc(self.occurred_at, "occurred_at", InvalidFailureEvidence))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "failure_id": self.failure_id,
            "lifecycle_id": self.lifecycle_id, "phase": self.phase.value,
            "failure_class": self.failure_class.value, "reason_codes": list(self.reason_codes),
            "authorization_state": self.authorization_state.value,
            "claim_consumed": self.claim_consumed,
            "actual_invocation_count": self.actual_invocation_count,
            "completed_count": self.completed_count, "uncertain_count": self.uncertain_count,
            "retry_prohibited": self.retry_prohibited,
            "rollback_prohibited": self.rollback_prohibited,
            "manual_action_required": self.manual_action_required,
            "occurred_at": self.occurred_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class EvidenceArtifactReference:
    artifact_type: str
    artifact_id: str
    digest: str
    size_bytes: int | None = None
    created_at: datetime | None = None
    lifecycle_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("artifact_type", "artifact_id", "digest"):
            _text(getattr(self, name), name, InvalidEvidenceReference)
        if _CODE.fullmatch(self.artifact_type) is None:
            raise InvalidEvidenceReference("artifact_type must be a stable code")
        if self.size_bytes is not None:
            _count(self.size_bytes, "size_bytes", InvalidEvidenceReference)
        if self.created_at is not None:
            object.__setattr__(self, "created_at", _utc(self.created_at, "created_at", InvalidEvidenceReference))
        if self.lifecycle_id is not None:
            _text(self.lifecycle_id, "lifecycle_id", InvalidEvidenceReference)

    @property
    def identity(self) -> tuple[str, str]:
        return self.artifact_type, self.artifact_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_type": self.artifact_type, "artifact_id": self.artifact_id,
            "digest": self.digest, "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "lifecycle_id": self.lifecycle_id,
        }


def _references(
    value: tuple[EvidenceArtifactReference, ...], field_name: str,
    error_type: type[ValueError], *, lifecycle_id: str | None = None,
) -> tuple[EvidenceArtifactReference, ...]:
    if not isinstance(value, tuple):
        raise error_type(f"{field_name} must be a tuple")
    if any(not isinstance(item, EvidenceArtifactReference) for item in value):
        raise error_type(f"{field_name} must contain EvidenceArtifactReference values")
    identities = tuple(item.identity for item in value)
    if len(identities) != len(set(identities)):
        raise DuplicateEvidenceReference(f"{field_name} contains duplicate artifact identity")
    if lifecycle_id is not None and any(item.lifecycle_id != lifecycle_id for item in value):
        raise error_type(f"{field_name} lifecycle binding mismatch")
    return tuple(sorted(value, key=lambda item: item.identity))


@dataclass(frozen=True, slots=True)
class GovernanceEvidenceManifest:
    schema_version: str
    manifest_id: str
    lifecycle_id: str
    artifact_references: tuple[EvidenceArtifactReference, ...]
    storage_identity: str
    manifest_digest: str
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("schema_version", "manifest_id", "lifecycle_id", "storage_identity", "manifest_digest"):
            _text(getattr(self, name), name, InvalidEvidenceManifest)
        if not self.artifact_references:
            raise InvalidEvidenceManifest("artifact_references must not be empty")
        object.__setattr__(self, "artifact_references", _references(
            self.artifact_references, "artifact_references", InvalidEvidenceManifest,
            lifecycle_id=self.lifecycle_id,
        ))
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at", InvalidEvidenceManifest))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "manifest_id": self.manifest_id,
            "lifecycle_id": self.lifecycle_id,
            "artifact_references": [item.to_dict() for item in self.artifact_references],
            "storage_identity": self.storage_identity, "manifest_digest": self.manifest_digest,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class GovernanceEvidenceBundle:
    schema_version: str
    bundle_id: str
    lifecycle_id: str
    authorization_request_reference: EvidenceArtifactReference
    precondition_snapshot_reference: EvidenceArtifactReference
    authorization_receipt_reference: EvidenceArtifactReference
    mutation_budget_reference: EvidenceArtifactReference
    consumption_receipt_reference: EvidenceArtifactReference
    execution_request_reference: EvidenceArtifactReference
    evidence_manifest_reference: EvidenceArtifactReference
    audit_references: tuple[EvidenceArtifactReference, ...]
    bundle_digest: str
    created_at: datetime
    execution_receipt_reference: EvidenceArtifactReference | None = None
    postcondition_report_reference: EvidenceArtifactReference | None = None
    failure_evidence_reference: EvidenceArtifactReference | None = None
    git_documentation_gate_reference: EvidenceArtifactReference | None = None

    def __post_init__(self) -> None:
        for name in ("schema_version", "bundle_id", "lifecycle_id", "bundle_digest"):
            _text(getattr(self, name), name, InvalidEvidenceBundle)
        required_names = (
            "authorization_request_reference", "precondition_snapshot_reference",
            "authorization_receipt_reference", "mutation_budget_reference",
            "consumption_receipt_reference", "execution_request_reference",
            "evidence_manifest_reference",
        )
        optional_names = (
            "execution_receipt_reference", "postcondition_report_reference",
            "failure_evidence_reference", "git_documentation_gate_reference",
        )
        refs: list[EvidenceArtifactReference] = []
        for name in required_names:
            value = getattr(self, name)
            if not isinstance(value, EvidenceArtifactReference):
                raise InvalidEvidenceBundle(f"{name} must be EvidenceArtifactReference")
            refs.append(value)
        for name in optional_names:
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, EvidenceArtifactReference):
                    raise InvalidEvidenceBundle(f"{name} must be EvidenceArtifactReference")
                refs.append(value)
        audits = _references(self.audit_references, "audit_references", InvalidEvidenceBundle,
                             lifecycle_id=self.lifecycle_id)
        object.__setattr__(self, "audit_references", audits)
        refs.extend(audits)
        if any(item.lifecycle_id != self.lifecycle_id for item in refs):
            raise InvalidEvidenceBundle("reference lifecycle binding mismatch")
        identities = tuple(item.identity for item in refs)
        if len(identities) != len(set(identities)):
            raise DuplicateEvidenceReference("bundle contains duplicate artifact identity")
        object.__setattr__(self, "created_at", _utc(self.created_at, "created_at", InvalidEvidenceBundle))

    def to_dict(self) -> dict[str, Any]:
        def project(value: EvidenceArtifactReference | None) -> dict[str, Any] | None:
            return value.to_dict() if value else None

        return {
            "schema_version": self.schema_version, "bundle_id": self.bundle_id,
            "lifecycle_id": self.lifecycle_id,
            "authorization_request_reference": project(self.authorization_request_reference),
            "precondition_snapshot_reference": project(self.precondition_snapshot_reference),
            "authorization_receipt_reference": project(self.authorization_receipt_reference),
            "mutation_budget_reference": project(self.mutation_budget_reference),
            "consumption_receipt_reference": project(self.consumption_receipt_reference),
            "execution_request_reference": project(self.execution_request_reference),
            "execution_receipt_reference": project(self.execution_receipt_reference),
            "postcondition_report_reference": project(self.postcondition_report_reference),
            "failure_evidence_reference": project(self.failure_evidence_reference),
            "evidence_manifest_reference": project(self.evidence_manifest_reference),
            "audit_references": [item.to_dict() for item in self.audit_references],
            "git_documentation_gate_reference": project(self.git_documentation_gate_reference),
            "bundle_digest": self.bundle_digest, "created_at": self.created_at.isoformat(),
        }
