"""Deterministic eligibility -> authorization -> fake-write orchestration."""
from __future__ import annotations

from datetime import datetime

from ..models import ProductDraftRevision
from ..values import require_utc
from .authorization import (AuthorizationDecisionValue,
                            CommerceWriteAuthorizationPort)
from .eligibility import evaluate_eligibility
from .idempotency import IdempotencyConflict, InMemoryWriteIdempotencyStore
from .models import (CommerceOperation, ControlledDeploymentIntent,
                     ControlledWritePlan, SourceFreshnessPolicy, WriteMode)
from .results import ControlledWriteServiceResult, DeploymentOutcome
from .write_port import CommerceProductWritePort


class ControlledCommerceWriteService:
    def __init__(self, authorization: CommerceWriteAuthorizationPort,
                 writer: CommerceProductWritePort,
                 idempotency: InMemoryWriteIdempotencyStore[ControlledWriteServiceResult],
                 *, mode: WriteMode = WriteMode.FAKE) -> None:
        self._authorization = authorization
        self._writer = writer
        self._idempotency = idempotency
        self._mode = mode

    def execute(self, revision: ProductDraftRevision,
                intent: ControlledDeploymentIntent, *,
                freshness_policy: SourceFreshnessPolicy,
                evaluated_at: datetime,
                completed_at: datetime) -> ControlledWriteServiceResult:
        require_utc(evaluated_at, "evaluated_at"); require_utc(completed_at, "completed_at")
        eligibility = evaluate_eligibility(revision, intent,
                                           freshness_policy=freshness_policy,
                                           evaluated_at=evaluated_at)
        base = dict(mode=self._mode, operation=intent.operation.value,
                    draft_id=intent.draft_id, revision_id=intent.revision_id,
                    deployment_intent_id=intent.deployment_intent_id,
                    expected_source_digest=intent.expected_source_snapshot_digest,
                    audit_reference=intent.audit_reference,
                    correlation_id=intent.correlation_id, completed_at=completed_at,
                    live_write_performed=False)
        if not eligibility.eligible:
            return ControlledWriteServiceResult(
                **base, eligibility=eligibility.outcome,
                rejection_reasons=eligibility.reasons,
                authorization_decision=AuthorizationDecisionValue.DENY,
                plan_digest=None, idempotency_status="NOT_BOUND",
                outcome=DeploymentOutcome(eligibility.outcome))
        decision = self._authorization.authorize(
            action=intent.operation.value, actor=intent.requested_actor_reference,
            draft_id=intent.draft_id, revision_id=intent.revision_id,
            deployment_intent_id=intent.deployment_intent_id,
            authorization_reference=intent.authorization_reference,
            evaluated_at=evaluated_at)
        exact = (decision.action, decision.actor, decision.draft_id,
                 decision.revision_id, decision.deployment_intent_id,
                 decision.authorization_reference, decision.evaluated_at) == (
                    intent.operation.value, intent.requested_actor_reference,
                    intent.draft_id, intent.revision_id,
                    intent.deployment_intent_id, intent.authorization_reference,
                    evaluated_at)
        if decision.decision is not AuthorizationDecisionValue.ALLOW or not exact:
            return ControlledWriteServiceResult(
                **base, eligibility="ELIGIBLE", rejection_reasons=(),
                authorization_decision=AuthorizationDecisionValue.DENY,
                plan_digest=None, idempotency_status="NOT_BOUND",
                outcome=DeploymentOutcome.REJECTED_AUTHORIZATION)
        plan = ControlledWritePlan.create(intent, mode=self._mode,
                                          policy_reference=decision.policy_reference,
                                          evaluated_at=evaluated_at)
        try:
            replay = self._idempotency.lookup(intent.idempotency_key, plan.plan_digest)
        except IdempotencyConflict:
            return ControlledWriteServiceResult(
                **base, eligibility="ELIGIBLE", rejection_reasons=(),
                authorization_decision=decision.decision,
                plan_digest=plan.plan_digest, idempotency_status="CONFLICT",
                outcome=DeploymentOutcome.IDEMPOTENCY_CONFLICT)
        if replay is not None:
            return replay.as_replay()
        written = self._writer.apply(plan, completed_at=completed_at)
        result = ControlledWriteServiceResult(
            **base, eligibility="ELIGIBLE", rejection_reasons=(),
            authorization_decision=decision.decision,
            plan_digest=plan.plan_digest, idempotency_status="BOUND",
            outcome=DeploymentOutcome.FAKE_APPLIED,
            adapter_identifier=written.adapter_identifier,
            result_digest=written.result_digest)
        self._idempotency.bind(intent.idempotency_key, plan.plan_digest, result)
        return result
