from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from core.shopping.product_drafts import (
    ActorReference, ActorType, LifecycleState, ProductDraftRevision,
    ProposedFields, RevisionIdentity, SourceSnapshotReference,
)
from core.shopping.product_drafts.application import (
    AuthorizationDecision, AuthorizationDecisionValue, ContractValidationRules,
    FindingSeverity, IdempotencyKeyReuseConflict, InMemoryAuditAdapter,
    InMemoryIdempotencyStore, ProductDraftReviewService,
    ProductDraftValidationService, ReviewCommand, ReviewOperation,
    StaticAuthorizationAdapter, ValidationFinding,
)
from core.shopping.product_drafts.serialization import sha256_digest

NOW = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)
DONE = NOW + timedelta(minutes=1)
DIGEST = "sha256:" + "a" * 64
HUMAN = ActorReference("reviewer-1", ActorType.HUMAN)
SERVICE = ActorReference("service-1", ActorType.SERVICE)


def revision(state=LifecycleState.VALIDATED, number=1, rid="revision-1", previous=None):
    identity = RevisionIdentity("draft-1", rid, number, previous, NOW, SERVICE, "corr-create", "audit-create")
    source = SourceSnapshotReference("product-42", NOW, snapshot_digest=DIGEST)
    return ProductDraftRevision(identity, source, state, ProposedFields(name="Orange", regular_price=Decimal("12.30")))


class Findings:
    def evaluate(self, item):
        return (
            ValidationFinding(FindingSeverity.WARNING, "W_ZETA"),
            ValidationFinding(FindingSeverity.ERROR, "E_BETA"),
            ValidationFinding(FindingSeverity.ERROR, "E_ALPHA"),
            ValidationFinding(FindingSeverity.ERROR, "E_ALPHA"),
        )


def decision(operation, actor=HUMAN, rid="revision-1", reference="auth-1", at=NOW):
    return AuthorizationDecision(operation.value, actor, "draft-1", rid, reference,
                                 AuthorizationDecisionValue.ALLOW, at, "policy:test")


def command(operation, *, actor=HUMAN, rid="revision-1", number=1, key="key-1", reference="auth-1", reason="reviewed"):
    return ReviewCommand(operation, "draft-1", rid, number, actor, reason, reference,
                         "audit-1", "corr-1", key, NOW)


def service(*allowed):
    audit = InMemoryAuditAdapter()
    return ProductDraftReviewService(StaticAuthorizationAdapter(tuple(allowed)), audit,
                                     InMemoryIdempotencyStore()), audit


def test_validation_is_deterministic_stable_digest_bound_and_non_mutating():
    original = revision(LifecycleState.DRAFT)
    audit = InMemoryAuditAdapter()
    validator = ProductDraftValidationService(Findings(), audit)
    first = validator.validate(original, validator_version="contract-v1", validated_at=NOW,
                               actor=SERVICE, audit_reference="audit-v", correlation_id="corr-v")
    second = ProductDraftValidationService(Findings(), InMemoryAuditAdapter()).validate(
        original, validator_version="contract-v1", validated_at=NOW, actor=SERVICE,
        audit_reference="audit-v", correlation_id="corr-v")
    assert first.validation == second.validation
    assert first.validation.revision_id == original.revision_id
    assert first.validation.errors == ("E_ALPHA", "E_BETA")
    assert first.validation.warnings == ("W_ZETA",)
    assert first.validation.validation_input_digest == sha256_digest(original)
    assert first.validation.result_digest == second.validation.result_digest
    assert original.validation is None and first.revision is not original
    assert len(audit.events) == 1
    assert audit.events[0].payload_digest.startswith("sha256:")


def test_validation_default_contract_rules_and_utc_enforcement():
    audit = InMemoryAuditAdapter()
    validator = ProductDraftValidationService(ContractValidationRules(), audit)
    result = validator.validate(revision(LifecycleState.DRAFT), validator_version="1.0.0",
                                validated_at=NOW, actor=SERVICE,
                                audit_reference="audit", correlation_id="corr")
    assert result.validation.status.value == "VALID"
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        validator.validate(revision(), validator_version="v", validated_at=NOW.replace(tzinfo=None),
                           actor=SERVICE, audit_reference="a", correlation_id="c")


def test_authorization_is_deny_by_default_and_exact_resource_bound():
    adapter = StaticAuthorizationAdapter((decision(ReviewOperation.APPROVE),))
    assert adapter.authorize(action="APPROVE", actor=HUMAN, draft_id="draft-1",
                             revision_id="revision-1", authorization_reference="auth-1",
                             evaluated_at=NOW).decision is AuthorizationDecisionValue.ALLOW
    for changed in ({"action": "REJECT"}, {"revision_id": "revision-2"},
                    {"authorization_reference": "other"}, {"actor": SERVICE}):
        args = dict(action="APPROVE", actor=HUMAN, draft_id="draft-1", revision_id="revision-1",
                    authorization_reference="auth-1", evaluated_at=NOW)
        args.update(changed)
        assert adapter.authorize(**args).decision is AuthorizationDecisionValue.DENY


def test_review_service_rejects_misbound_allow_decision_from_port():
    class MisboundAuthorization:
        def authorize(self, **request):
            return decision(ReviewOperation.APPROVE, rid="revision-other")

    audit = InMemoryAuditAdapter()
    svc = ProductDraftReviewService(
        MisboundAuthorization(), audit, InMemoryIdempotencyStore()
    )
    result = svc.execute(
        revision(LifecycleState.REVIEW_REQUIRED),
        command(ReviewOperation.APPROVE),
        completed_at=DONE,
    )
    assert result.outcome == "REJECTED_AUTHORIZATION"
    assert result.revision.state is LifecycleState.REVIEW_REQUIRED
    assert audit.events[0].outcome == "REJECTED_AUTHORIZATION"


def test_request_review_approve_reject_and_revoke_flows_use_domain_lifecycle():
    cases = (
        (ReviewOperation.REQUEST_REVIEW, LifecycleState.VALIDATED, LifecycleState.REVIEW_REQUIRED),
        (ReviewOperation.APPROVE, LifecycleState.REVIEW_REQUIRED, LifecycleState.APPROVED),
        (ReviewOperation.REJECT, LifecycleState.REVIEW_REQUIRED, LifecycleState.REJECTED),
        (ReviewOperation.REVOKE, LifecycleState.APPROVED, LifecycleState.REVOKED),
    )
    for index, (operation, before, after) in enumerate(cases):
        cmd = command(operation, key=f"key-{index}")
        svc, audit = service(decision(operation))
        result = svc.execute(revision(before), cmd, completed_at=DONE)
        assert result.outcome == "ACCEPTED" and result.revision.state is after
        assert (result.review_decision is None) is (operation is ReviewOperation.REQUEST_REVIEW)
        assert len(audit.events) == 1 and audit.events[0].outcome == "ACCEPTED"


def test_human_only_decisions_and_denied_authorization_do_not_apply():
    for operation in (ReviewOperation.APPROVE, ReviewOperation.REJECT, ReviewOperation.REVOKE):
        before = LifecycleState.APPROVED if operation is ReviewOperation.REVOKE else LifecycleState.REVIEW_REQUIRED
        cmd = command(operation, actor=SERVICE, key=f"service-{operation.value}")
        svc, _ = service(decision(operation, SERVICE))
        result = svc.execute(revision(before), cmd, completed_at=DONE)
        assert result.outcome == "REJECTED_NON_HUMAN_ACTOR" and result.revision.state is before
    svc, _ = service()
    denied = svc.execute(revision(LifecycleState.REVIEW_REQUIRED), command(ReviewOperation.APPROVE), completed_at=DONE)
    assert denied.outcome == "REJECTED_AUTHORIZATION"
    assert denied.review_decision is None and denied.revision.state is LifecycleState.REVIEW_REQUIRED


def test_stale_revision_conflicts_and_superseding_revision_has_no_approval():
    svc, _ = service(decision(ReviewOperation.APPROVE))
    stale = svc.execute(revision(LifecycleState.REVIEW_REQUIRED),
                        command(ReviewOperation.APPROVE, number=2), completed_at=DONE)
    assert stale.outcome == "REJECTED_CONFLICT"
    approved_svc, _ = service(decision(ReviewOperation.APPROVE))
    approved = approved_svc.execute(revision(LifecycleState.REVIEW_REQUIRED),
                                    command(ReviewOperation.APPROVE, key="approve"), completed_at=DONE).revision
    newer = approved.new_revision(
        RevisionIdentity("draft-1", "revision-2", 2, "revision-1", DONE, SERVICE, "c2", "a2"),
        ProposedFields(name="New"),
    )
    assert newer.human_decision is None and newer.state is LifecycleState.DRAFT


def test_revoked_approval_cannot_be_reused():
    approve_svc, _ = service(decision(ReviewOperation.APPROVE))
    approved = approve_svc.execute(revision(LifecycleState.REVIEW_REQUIRED),
                                   command(ReviewOperation.APPROVE, key="approve"), completed_at=DONE).revision
    revoke_svc, _ = service(decision(ReviewOperation.REVOKE))
    revoked = revoke_svc.execute(approved, command(ReviewOperation.REVOKE, key="revoke"), completed_at=DONE)
    assert revoked.revision.state is LifecycleState.REVOKED
    assert revoked.review_decision.decision.value == "REVOKE"


def test_idempotent_replay_conflict_and_denial_cannot_become_approval():
    svc, audit = service(decision(ReviewOperation.APPROVE))
    cmd = command(ReviewOperation.APPROVE)
    first = svc.execute(revision(LifecycleState.REVIEW_REQUIRED), cmd, completed_at=DONE)
    replay = svc.execute(revision(LifecycleState.REVIEW_REQUIRED), cmd, completed_at=DONE)
    assert first.idempotent_replay is False and replay.idempotent_replay is True
    assert len(audit.events) == 1
    with pytest.raises(IdempotencyKeyReuseConflict):
        svc.execute(revision(LifecycleState.REVIEW_REQUIRED), command(ReviewOperation.APPROVE, reason="different"), completed_at=DONE)
    denied_svc, _ = service()
    denied = denied_svc.execute(revision(LifecycleState.REVIEW_REQUIRED), cmd, completed_at=DONE)
    denied_svc._authorization = StaticAuthorizationAdapter((decision(ReviewOperation.APPROVE),))
    assert denied_svc.execute(revision(LifecycleState.REVIEW_REQUIRED), cmd, completed_at=DONE).outcome == denied.outcome


def test_audit_is_deterministic_isolated_and_projection_read_only_safe():
    first_audit, second_audit = InMemoryAuditAdapter(), InMemoryAuditAdapter()
    svc = ProductDraftReviewService(StaticAuthorizationAdapter((decision(ReviewOperation.APPROVE),)),
                                    first_audit, InMemoryIdempotencyStore())
    result = svc.execute(revision(LifecycleState.REVIEW_REQUIRED), command(ReviewOperation.APPROVE), completed_at=DONE)
    assert second_audit.events == ()
    clone, clone_audit = service(decision(ReviewOperation.APPROVE))
    clone.execute(revision(LifecycleState.REVIEW_REQUIRED), command(ReviewOperation.APPROVE), completed_at=DONE)
    assert first_audit.events == clone_audit.events
    projection = result.projection()
    assert json.loads(json.dumps(projection))["outcome"] == "ACCEPTED"
    assert set(projection) == {"operation", "draft_id", "revision_id", "outcome", "validation_status",
                               "review_decision", "authorization_reference", "audit_reference",
                               "idempotent_replay", "correlation_id", "completed_at"}
    with pytest.raises(TypeError):
        projection["outcome"] = "changed"
    with pytest.raises(FrozenInstanceError):
        first_audit.events[0].outcome = "changed"
    assert not any(word in str(projection).lower() for word in ("password", "credential", "secret"))


def test_application_package_has_no_api_external_io_or_persistence_dependencies():
    root = Path(__file__).parents[1] / "core/shopping/product_drafts/application"
    text = "\n".join(path.read_text() for path in root.glob("*.py")).lower()
    forbidden = ("fastapi", "@router", "requests", "httpx", "aiohttp", "socket",
                 "subprocess", "sqlite", "sqlalchemy", "open(", "pathlib", "woocommerce")
    assert all(token not in text for token in forbidden)
