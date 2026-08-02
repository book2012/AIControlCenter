"""Safe immutable orchestration result."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from .authorization import AuthorizationDecisionValue
from .eligibility import RejectionReason
from .models import WriteMode


class DeploymentOutcome(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    REJECTED_NOT_APPROVED = "REJECTED_NOT_APPROVED"
    REJECTED_INVALID_VALIDATION = "REJECTED_INVALID_VALIDATION"
    REJECTED_APPROVAL_BINDING = "REJECTED_APPROVAL_BINDING"
    REJECTED_STALE_SOURCE = "REJECTED_STALE_SOURCE"
    REJECTED_SOURCE_DIGEST = "REJECTED_SOURCE_DIGEST"
    REJECTED_INTENT_BINDING = "REJECTED_INTENT_BINDING"
    REJECTED_AUTHORIZATION = "REJECTED_AUTHORIZATION"
    FAKE_APPLIED = "FAKE_APPLIED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"


@dataclass(frozen=True, slots=True)
class ControlledWriteServiceResult:
    mode: WriteMode
    operation: str
    draft_id: str
    revision_id: str
    deployment_intent_id: str
    eligibility: str
    rejection_reasons: tuple[RejectionReason, ...]
    authorization_decision: AuthorizationDecisionValue
    expected_source_digest: str
    plan_digest: str | None
    idempotency_status: str
    outcome: DeploymentOutcome
    audit_reference: str
    correlation_id: str
    completed_at: datetime
    adapter_identifier: str | None = None
    result_digest: str | None = None
    live_write_performed: bool = False

    def as_replay(self) -> "ControlledWriteServiceResult":
        return replace(self, outcome=DeploymentOutcome.IDEMPOTENT_REPLAY,
                       idempotency_status="REPLAY")
