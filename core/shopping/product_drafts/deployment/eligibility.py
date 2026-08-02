"""Pure exact-revision controlled-write eligibility."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..models import (ApprovalDecisionType, LifecycleState, ProductDraftRevision,
                      ValidationStatus)
from ..serialization import sha256_digest
from ..values import ActorType, require_utc
from .models import ControlledDeploymentIntent, SourceFreshnessPolicy


class RejectionReason(str, Enum):
    REJECTED_NOT_APPROVED = "REJECTED_NOT_APPROVED"
    REJECTED_INVALID_VALIDATION = "REJECTED_INVALID_VALIDATION"
    REJECTED_APPROVAL_BINDING = "REJECTED_APPROVAL_BINDING"
    REJECTED_INTENT_BINDING = "REJECTED_INTENT_BINDING"
    REJECTED_SOURCE_DIGEST = "REJECTED_SOURCE_DIGEST"
    REJECTED_STALE_SOURCE = "REJECTED_STALE_SOURCE"


@dataclass(frozen=True, slots=True)
class EligibilityResult:
    outcome: str
    reasons: tuple[RejectionReason, ...]

    @property
    def eligible(self) -> bool:
        return not self.reasons


def evaluate_eligibility(revision: ProductDraftRevision,
                         intent: ControlledDeploymentIntent, *,
                         freshness_policy: SourceFreshnessPolicy,
                         evaluated_at: datetime) -> EligibilityResult:
    require_utc(evaluated_at, "evaluated_at")
    reasons: list[RejectionReason] = []
    if revision.state is not LifecycleState.APPROVED:
        reasons.append(RejectionReason.REJECTED_NOT_APPROVED)
    if revision.validation is None or revision.validation.status is not ValidationStatus.VALID:
        reasons.append(RejectionReason.REJECTED_INVALID_VALIDATION)
    decision = revision.human_decision
    if (decision is None or decision.reviewer.actor_type is not ActorType.HUMAN
            or decision.decision is not ApprovalDecisionType.APPROVE
            or (decision.draft_id, decision.revision_id) != (revision.draft_id, revision.revision_id)):
        reasons.append(RejectionReason.REJECTED_APPROVAL_BINDING)
    embedded = revision.deployment_intent
    if ((intent.draft_id, intent.revision_id, intent.expected_revision_number)
            != (revision.draft_id, revision.revision_id, revision.revision_number)
            or intent.target_product_identifier != revision.source.source_product_identifier
            or embedded is None
            or (embedded.intent_id, embedded.draft_id, embedded.revision_id,
                embedded.expected_source_digest, embedded.idempotency_key,
                embedded.authorization_reference, embedded.audit_reference,
                embedded.correlation_id)
            != (intent.deployment_intent_id, intent.draft_id, intent.revision_id,
                intent.expected_source_snapshot_digest, intent.idempotency_key,
                intent.authorization_reference, intent.audit_reference,
                intent.correlation_id)
            or embedded.created_by != intent.requested_actor_reference
            or embedded.created_at != intent.requested_at):
        reasons.append(RejectionReason.REJECTED_INTENT_BINDING)
    source_digest = revision.source.snapshot_digest
    if source_digest is None or intent.expected_source_snapshot_digest != source_digest:
        reasons.append(RejectionReason.REJECTED_SOURCE_DIGEST)
    observed_at = revision.source.observed_at
    if observed_at > evaluated_at or evaluated_at - observed_at > freshness_policy.max_age:
        reasons.append(RejectionReason.REJECTED_STALE_SOURCE)
    # The payload is the exact immutable proposed-field projection.
    if intent.payload_digest != sha256_digest(revision.proposed_fields):
        if RejectionReason.REJECTED_INTENT_BINDING not in reasons:
            reasons.append(RejectionReason.REJECTED_INTENT_BINDING)
    ordered = tuple(reason for reason in RejectionReason if reason in reasons)
    return EligibilityResult("ELIGIBLE" if not ordered else ordered[0].value, ordered)
