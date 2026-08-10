"""Pure read-only SEC-02A9 Governance API projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from ..domain import (
    AuthorizationState,
    ExecutionStatus,
    MutationBudgetStatus,
    PostconditionDecision,
    PreconditionComparisonStatus,
)


_CONTRACT_NAMES = frozenset({
    "GovernanceAuthorizationRequest", "GovernancePreconditionSnapshot",
    "GovernanceAuthorizationDecision", "GovernanceAuthorizationReceipt",
    "GovernanceAuthorizationStateRecord", "GovernanceMutationBudget",
    "GovernanceAuthorizationConsumptionReceipt", "GovernanceExecutionRequest",
    "GovernanceExecutionReceipt", "GovernancePostconditionReport",
    "GovernanceFailureEvidence", "GovernanceEvidenceManifest",
    "GovernanceEvidenceBundle", "GovernanceAuditEvent",
    "GovernanceGitDocumentationGateReport", "GovernanceApiEnvelope",
})


def _text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty canonical text")
    return value


def _utc(value: datetime, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be timezone-aware UTC")
    return value.astimezone(timezone.utc)


def _count(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")
    return value


@dataclass(frozen=True, slots=True, order=True)
class GovernanceApiReference:
    contract_name: str
    resource_id: str
    digest: str

    def __post_init__(self) -> None:
        if self.contract_name not in _CONTRACT_NAMES:
            raise ValueError("contract_name must belong to the Governance v1 contract family")
        _text(self.resource_id, "resource_id")
        _text(self.digest, "digest")

    def to_dict(self) -> dict[str, str]:
        return {
            "contract_name": self.contract_name,
            "resource_id": self.resource_id,
            "digest": self.digest,
        }


@dataclass(frozen=True, slots=True)
class GovernanceReadModel:
    """Typed, value-free current-state observation supplied by Governance."""

    lifecycle_id: str
    authorization_state: AuthorizationState
    precondition_status: PreconditionComparisonStatus | None
    mutation_budget_status: MutationBudgetStatus
    allowed_invocation_count: int
    actual_invocation_count: int
    completed_count: int
    uncertain_count: int
    execution_status: ExecutionStatus | None
    postcondition_decision: PostconditionDecision | None
    failure_present: bool
    manual_action_required: bool
    data_reference: GovernanceApiReference
    evidence_manifest_reference: GovernanceApiReference | None
    evidence_bundle_reference: GovernanceApiReference | None
    git_documentation_gate_status: str | None
    git_documentation_gate_reference: GovernanceApiReference | None
    projected_at: datetime

    def __post_init__(self) -> None:
        _text(self.lifecycle_id, "lifecycle_id")
        if not isinstance(self.authorization_state, AuthorizationState):
            raise TypeError("authorization_state must be AuthorizationState")
        if self.precondition_status is not None and not isinstance(
            self.precondition_status, PreconditionComparisonStatus
        ):
            raise TypeError("precondition_status must be PreconditionComparisonStatus or None")
        if not isinstance(self.mutation_budget_status, MutationBudgetStatus):
            raise TypeError("mutation_budget_status must be MutationBudgetStatus")
        for name in (
            "allowed_invocation_count", "actual_invocation_count", "completed_count",
            "uncertain_count",
        ):
            _count(getattr(self, name), name)
        if self.actual_invocation_count > self.allowed_invocation_count:
            raise ValueError("actual_invocation_count exceeds allowed_invocation_count")
        if self.completed_count > self.actual_invocation_count:
            raise ValueError("completed_count exceeds actual_invocation_count")
        if self.uncertain_count > self.actual_invocation_count:
            raise ValueError("uncertain_count exceeds actual_invocation_count")
        if self.completed_count + self.uncertain_count > self.actual_invocation_count:
            raise ValueError("completed_count plus uncertain_count exceeds actual_invocation_count")
        if self.execution_status is not None and not isinstance(self.execution_status, ExecutionStatus):
            raise TypeError("execution_status must be ExecutionStatus or None")
        if self.postcondition_decision is not None and not isinstance(
            self.postcondition_decision, PostconditionDecision
        ):
            raise TypeError("postcondition_decision must be PostconditionDecision or None")
        if self.postcondition_decision is not None and self.execution_status is None:
            raise ValueError("postcondition_decision requires execution_status")
        for name in ("failure_present", "manual_action_required"):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be boolean")
        if not isinstance(self.data_reference, GovernanceApiReference):
            raise TypeError("data_reference must be GovernanceApiReference")
        for name in (
            "evidence_manifest_reference", "evidence_bundle_reference",
            "git_documentation_gate_reference",
        ):
            value = getattr(self, name)
            if value is not None and not isinstance(value, GovernanceApiReference):
                raise TypeError(f"{name} must be GovernanceApiReference or None")
        if self.evidence_manifest_reference is not None and (
            self.evidence_manifest_reference.contract_name != "GovernanceEvidenceManifest"
        ):
            raise ValueError("evidence_manifest_reference has the wrong contract")
        if self.evidence_bundle_reference is not None and (
            self.evidence_bundle_reference.contract_name != "GovernanceEvidenceBundle"
        ):
            raise ValueError("evidence_bundle_reference has the wrong contract")
        if self.git_documentation_gate_status is not None:
            _text(self.git_documentation_gate_status, "git_documentation_gate_status")
        if self.git_documentation_gate_reference is not None and (
            self.git_documentation_gate_reference.contract_name
            != "GovernanceGitDocumentationGateReport"
        ):
            raise ValueError("git_documentation_gate_reference has the wrong contract")
        object.__setattr__(self, "projected_at", _utc(self.projected_at, "projected_at"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "lifecycle_id": self.lifecycle_id,
            "authorization_state": self.authorization_state.value,
            "precondition_status": (
                self.precondition_status.value if self.precondition_status else None
            ),
            "mutation_budget_status": self.mutation_budget_status.value,
            "allowed_invocation_count": self.allowed_invocation_count,
            "actual_invocation_count": self.actual_invocation_count,
            "completed_count": self.completed_count,
            "uncertain_count": self.uncertain_count,
            "execution_status": self.execution_status.value if self.execution_status else None,
            "postcondition_decision": (
                self.postcondition_decision.value if self.postcondition_decision else None
            ),
            "failure_present": self.failure_present,
            "manual_action_required": self.manual_action_required,
            "data_reference": self.data_reference.to_dict(),
            "evidence_manifest_reference": (
                self.evidence_manifest_reference.to_dict()
                if self.evidence_manifest_reference else None
            ),
            "evidence_bundle_reference": (
                self.evidence_bundle_reference.to_dict() if self.evidence_bundle_reference else None
            ),
            "git_documentation_gate_status": self.git_documentation_gate_status,
            "git_documentation_gate_reference": (
                self.git_documentation_gate_reference.to_dict()
                if self.git_documentation_gate_reference else None
            ),
            "projected_at": self.projected_at.isoformat(),
        }


def project_governance_api_envelope(read_model: GovernanceReadModel) -> dict[str, Any]:
    """Project the existing GovernanceApiEnvelope schema without side effects."""
    if not isinstance(read_model, GovernanceReadModel):
        raise TypeError("read_model must be GovernanceReadModel")
    evidence = tuple(sorted(filter(None, (
        read_model.evidence_manifest_reference,
        read_model.evidence_bundle_reference,
        read_model.git_documentation_gate_reference,
    ))))
    return {
        "schema_version": "governance/v1",
        "generated_at": read_model.projected_at.isoformat(),
        "status": "OK",
        "data_reference": read_model.data_reference.to_dict(),
        "error": None,
        "evidence_references": [reference.to_dict() for reference in evidence],
    }


__all__ = (
    "GovernanceApiReference", "GovernanceReadModel", "project_governance_api_envelope",
)
