"""Revision-bound, authorized human review orchestration without commerce writes."""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from ..lifecycle import TransitionCommand, TransitionOutcome, evaluate_transition
from ..models import (ApprovalDecision, ApprovalDecisionType, LifecycleState,
                      ProductDraftRevision)
from ..serialization import sha256_digest
from ..values import ActorReference, ActorType, require_text, require_utc
from .idempotency import InMemoryIdempotencyStore
from .ports import (AuditEvent, AuditEventPort, AuthorizationDecisionValue,
                    AuthorizationPort)
from .results import ApplicationResult


class ReviewOperation(str, Enum):
    REQUEST_REVIEW = "REQUEST_REVIEW"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVOKE = "REVOKE"


_TARGETS = {
    ReviewOperation.REQUEST_REVIEW: LifecycleState.REVIEW_REQUIRED,
    ReviewOperation.APPROVE: LifecycleState.APPROVED,
    ReviewOperation.REJECT: LifecycleState.REJECTED,
    ReviewOperation.REVOKE: LifecycleState.REVOKED,
}


@dataclass(frozen=True, slots=True)
class ReviewCommand:
    operation: ReviewOperation
    draft_id: str
    revision_id: str
    expected_revision_number: int
    actor: ActorReference
    reason: str
    authorization_reference: str
    audit_reference: str
    correlation_id: str
    idempotency_key: str
    requested_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.operation, ReviewOperation):
            object.__setattr__(self, "operation", ReviewOperation(self.operation))
        for name in ("draft_id", "revision_id", "reason", "authorization_reference",
                     "audit_reference", "correlation_id", "idempotency_key"):
            require_text(getattr(self, name), name)
        if type(self.expected_revision_number) is not int or self.expected_revision_number < 1:
            raise ValueError("expected_revision_number must be >= 1")
        if not isinstance(self.actor, ActorReference):
            raise ValueError("actor must be an ActorReference")
        require_utc(self.requested_at, "requested_at")

    @property
    def digest(self) -> str:
        return sha256_digest(self)


class ProductDraftReviewService:
    def __init__(self, authorization: AuthorizationPort, audit: AuditEventPort,
                 idempotency: InMemoryIdempotencyStore[ApplicationResult]) -> None:
        self._authorization = authorization
        self._audit = audit
        self._idempotency = idempotency

    def execute(self, revision: ProductDraftRevision, command: ReviewCommand,
                *, completed_at: datetime) -> ApplicationResult:
        if not isinstance(revision, ProductDraftRevision):
            raise TypeError("revision must be a ProductDraftRevision")
        if not isinstance(command, ReviewCommand):
            raise TypeError("command must be a ReviewCommand")
        require_utc(completed_at, "completed_at")
        replay = self._idempotency.lookup(command.idempotency_key, command.digest)
        if replay is not None:
            return replay.as_replay()

        if command.operation is not ReviewOperation.REQUEST_REVIEW and command.actor.actor_type is not ActorType.HUMAN:
            result = self._result(revision, command, completed_at, "REJECTED_NON_HUMAN_ACTOR")
        elif (command.draft_id, command.revision_id, command.expected_revision_number) != (
                revision.draft_id, revision.revision_id, revision.revision_number):
            result = self._result(revision, command, completed_at, "REJECTED_CONFLICT")
        else:
            authorization = self._authorization.authorize(
                action=command.operation.value, actor=command.actor,
                draft_id=command.draft_id, revision_id=command.revision_id,
                authorization_reference=command.authorization_reference,
                evaluated_at=command.requested_at,
            )
            authorization_is_exact = (
                authorization.action == command.operation.value
                and authorization.actor == command.actor
                and authorization.draft_id == command.draft_id
                and authorization.revision_id == command.revision_id
                and authorization.authorization_reference
                == command.authorization_reference
                and authorization.evaluated_at == command.requested_at
            )
            if (
                authorization.decision is not AuthorizationDecisionValue.ALLOW
                or not authorization_is_exact
            ):
                result = self._result(revision, command, completed_at, "REJECTED_AUTHORIZATION")
            else:
                result = self._apply(revision, command, completed_at)

        self._idempotency.bind(command.idempotency_key, command.digest, result)
        self._audit.record(AuditEvent.create(
            event_type=f"PRODUCT_DRAFT_{command.operation.value}",
            draft_id=command.draft_id, revision_id=command.revision_id,
            actor=command.actor, correlation_id=command.correlation_id,
            authorization_reference=command.authorization_reference,
            audit_reference=command.audit_reference, outcome=result.outcome,
            occurred_at=completed_at, payload=dict(result.projection()),
        ))
        return result

    def _apply(self, revision: ProductDraftRevision, command: ReviewCommand,
               completed_at: datetime) -> ApplicationResult:
        to_state = _TARGETS[command.operation]
        transition = TransitionCommand(
            command.draft_id, command.revision_id, command.revision_id,
            command.expected_revision_number, revision.state, to_state,
            command.actor, command.correlation_id, command.audit_reference,
            command.idempotency_key, command.digest, command.requested_at,
        )
        evaluated = evaluate_transition(revision, transition, completed_at)
        if evaluated.outcome is not TransitionOutcome.APPLIED:
            return self._result(revision, command, completed_at, evaluated.outcome.value)

        decision = None
        if command.operation is not ReviewOperation.REQUEST_REVIEW:
            decision_type = ApprovalDecisionType(command.operation.value)
            decision_id = sha256_digest({
                "draft_id": revision.draft_id, "revision_id": revision.revision_id,
                "decision": decision_type.value, "reviewer": command.actor,
                "decided_at": completed_at, "idempotency_key": command.idempotency_key,
            })
            decision = ApprovalDecision(
                decision_id, revision.draft_id, revision.revision_id, command.actor,
                decision_type, completed_at, command.reason, command.correlation_id,
                command.audit_reference, command.idempotency_key,
            )
        updated = replace(revision, state=evaluated.state, human_decision=decision)
        return self._result(updated, command, completed_at, "ACCEPTED", decision)

    @staticmethod
    def _result(revision: ProductDraftRevision, command: ReviewCommand,
                completed_at: datetime, outcome: str,
                decision: ApprovalDecision | None = None) -> ApplicationResult:
        return ApplicationResult(
            command.operation.value, command.draft_id, command.revision_id, outcome,
            command.authorization_reference, command.audit_reference,
            command.correlation_id, completed_at, review_decision=decision,
            revision=revision,
        )
