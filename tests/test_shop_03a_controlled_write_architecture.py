from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path

import pytest

from core.shopping.product_drafts.models import (
    ApprovalDecision, ApprovalDecisionType, DeploymentIntent, LifecycleState,
    ProductDraftRevision, ProposedFields, ReadinessStatus, RevisionIdentity,
    SourceSnapshotReference, ValidationResult, ValidationStatus,
)
from core.shopping.product_drafts.serialization import sha256_digest
from core.shopping.product_drafts.values import ActorReference, ActorType
from core.shopping.product_drafts.deployment import (
    AuthorizationDecisionValue, CommerceOperation, ControlledCommerceWriteService,
    ControlledDeploymentIntent, ControlledWritePlan, DeploymentOutcome,
    FakeCommerceProductWriteAdapter, InMemoryWriteIdempotencyStore,
    SourceFreshnessPolicy, StaticWriteAuthorizationAdapter,
    WriteAuthorizationDecision, WriteMode, evaluate_eligibility,
    preview_projection,
)

UTC = timezone.utc
NOW = datetime(2026, 8, 3, 3, 0, tzinfo=UTC)
DIGEST = "sha256:" + "a" * 64


def approved_pair(*, state=LifecycleState.APPROVED, validation_status=ValidationStatus.VALID,
                  observed_at=NOW - timedelta(minutes=5), expected_revision=2,
                  expected_digest=DIGEST):
    human = ActorReference("human-1", ActorType.HUMAN)
    service = ActorReference("service-1", ActorType.SERVICE)
    identity = RevisionIdentity("draft-1", "revision-2", 2, "revision-1", NOW - timedelta(days=1), service, "correlation-1", "audit-revision")
    source = SourceSnapshotReference("product-9", observed_at, "snapshot-9", DIGEST)
    fields = ProposedFields(name="Updated", regular_price=Decimal("12.50"))
    validation = ValidationResult("revision-2", validation_status, () if validation_status is ValidationStatus.VALID else ("BAD",), (), "rules-v1", NOW - timedelta(minutes=4), DIGEST, "sha256:" + "b" * 64, "audit-validation")
    approval = ApprovalDecision("decision-1", "draft-1", "revision-2", human, ApprovalDecisionType.APPROVE, NOW - timedelta(minutes=3), "approved", "correlation-1", "audit-approval", "approval-key")
    embedded = DeploymentIntent("intent-1", "draft-1", "revision-2", "commerce-product-write", expected_digest, "write-key", "auth-1", "audit-write", ReadinessStatus.READY, human, "correlation-1", NOW - timedelta(minutes=2))
    revision = ProductDraftRevision(identity, source, state, fields, validation=validation, human_decision=approval, deployment_intent=embedded)
    intent = ControlledDeploymentIntent("intent-1", "draft-1", "revision-2", expected_revision, expected_digest, "product-9", CommerceOperation.UPDATE_PRODUCT, human, "auth-1", "audit-write", "correlation-1", "write-key", NOW - timedelta(minutes=2), sha256_digest(fields))
    return revision, intent


def allow(intent, *, evaluated_at=NOW):
    return WriteAuthorizationDecision(intent.operation.value, intent.requested_actor_reference,
        intent.draft_id, intent.revision_id, intent.deployment_intent_id,
        intent.authorization_reference, evaluated_at, "policy-test-1",
        AuthorizationDecisionValue.ALLOW)


def service(intent, decisions=()):
    writer = FakeCommerceProductWriteAdapter()
    return ControlledCommerceWriteService(StaticWriteAuthorizationAdapter(decisions), writer,
        InMemoryWriteIdempotencyStore()), writer


def test_shop_03a_exact_approved_revision_is_eligible_and_fake_applied():
    revision, intent = approved_pair()
    eligibility = evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW)
    assert eligibility.outcome == "ELIGIBLE"
    app, writer = service(intent, (allow(intent),))
    result = app.execute(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW, completed_at=NOW)
    assert result.outcome is DeploymentOutcome.FAKE_APPLIED
    assert result.live_write_performed is False
    assert len(writer.calls) == 1


@pytest.mark.parametrize("state", [LifecycleState.DRAFT, LifecycleState.VALIDATED,
    LifecycleState.REVIEW_REQUIRED, LifecycleState.REJECTED, LifecycleState.REVOKED,
    LifecycleState.SUPERSEDED])
def test_shop_03a_non_approved_lifecycle_states_rejected(state):
    revision, intent = approved_pair(state=state)
    result = evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW)
    assert "REJECTED_NOT_APPROVED" in [item.value for item in result.reasons]


def test_shop_03a_missing_and_invalid_validation_rejected():
    revision, intent = approved_pair(validation_status=ValidationStatus.INVALID)
    assert evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).outcome == "REJECTED_INVALID_VALIDATION"
    revision = replace(revision, validation=None)
    assert "REJECTED_INVALID_VALIDATION" in [r.value for r in evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).reasons]


def test_shop_03a_approval_mismatch_and_revocation_rejected():
    revision, intent = approved_pair()
    # A legacy/corrupt aggregate can be inspected safely even when construction invariants reject it.
    bad = object.__new__(ApprovalDecision)
    for field, value in (("decision_id", "x"), ("draft_id", "other"), ("revision_id", "other"),
        ("reviewer", ActorReference("svc", ActorType.SERVICE)), ("decision", ApprovalDecisionType.REVOKE),
        ("decided_at", NOW), ("reason", "x"), ("correlation_id", "x"), ("audit_reference", "x"),
        ("idempotency_key", "x"), ("schema_version", "1.0.0")):
        object.__setattr__(bad, field, value)
    object.__setattr__(revision, "human_decision", bad)
    reasons = evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).reasons
    assert any(r.value == "REJECTED_APPROVAL_BINDING" for r in reasons)


def test_shop_03a_intent_revision_payload_and_source_bindings_rejected():
    revision, intent = approved_pair(expected_revision=3)
    reasons = evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).reasons
    assert any(r.value == "REJECTED_INTENT_BINDING" for r in reasons)
    revision, intent = approved_pair(expected_digest="sha256:" + "c" * 64)
    reasons = evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).reasons
    assert any(r.value == "REJECTED_SOURCE_DIGEST" for r in reasons)


def test_shop_03a_freshness_and_timezone_are_explicit():
    revision, intent = approved_pair(observed_at=NOW - timedelta(minutes=59))
    assert evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).eligible
    revision, intent = approved_pair(observed_at=NOW - timedelta(hours=2))
    assert any(r.value == "REJECTED_STALE_SOURCE" for r in evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW).reasons)
    with pytest.raises(ValueError, match="timezone-aware UTC"):
        evaluate_eligibility(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW.replace(tzinfo=None))


def test_shop_03a_deny_default_and_exact_authorization_binding():
    revision, intent = approved_pair()
    denied, writer = service(intent)
    result = denied.execute(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW, completed_at=NOW)
    assert result.outcome is DeploymentOutcome.REJECTED_AUTHORIZATION and not writer.calls
    wrong = replace(allow(intent), deployment_intent_id="other")
    denied, _ = service(intent, (wrong,))
    assert denied.execute(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW, completed_at=NOW).outcome is DeploymentOutcome.REJECTED_AUTHORIZATION


def test_shop_03a_plan_and_fake_adapter_are_deterministic_and_isolated():
    revision, intent = approved_pair()
    plan1 = ControlledWritePlan.create(intent, mode=WriteMode.FAKE, policy_reference="policy", evaluated_at=NOW)
    plan2 = ControlledWritePlan.create(intent, mode=WriteMode.FAKE, policy_reference="policy", evaluated_at=NOW)
    assert plan1 == plan2
    first, second = FakeCommerceProductWriteAdapter(), FakeCommerceProductWriteAdapter()
    assert first.apply(plan1, completed_at=NOW).result_digest == second.apply(plan2, completed_at=NOW + timedelta(seconds=1)).result_digest
    assert len(first.calls) == 1 and len(second.calls) == 1
    different = replace(plan1, target_product_identifier="other", plan_digest=sha256_digest({"different": True}))
    assert first.apply(different, completed_at=NOW).result_digest != first.apply(plan1, completed_at=NOW).result_digest
    assert len(second.calls) == 1


def test_shop_03a_unspecified_operation_rejected():
    _, intent = approved_pair()
    with pytest.raises(ValueError):
        replace(intent, operation="CREATE_PRODUCT")


def test_shop_03a_preview_is_detached_json_safe_and_has_no_credentials():
    revision, intent = approved_pair()
    app, _ = service(intent, (allow(intent),))
    result = app.execute(revision, intent, freshness_policy=SourceFreshnessPolicy(timedelta(hours=1)), evaluated_at=NOW, completed_at=NOW)
    preview = preview_projection(result)
    assert preview["live_write_performed"] is False
    assert json.loads(json.dumps(preview)) == preview
    assert not ({"consumer_key", "consumer_secret", "credentials"} & set(preview))
    mutated = dict(preview); mutated["outcome"] = "ALTERED"
    assert result.outcome is DeploymentOutcome.FAKE_APPLIED


def test_shop_03a_product_draft_contracts_remain_version_1_0_0():
    contract_root = Path("docs/contracts/shopping/v1")
    intent_schema = json.loads((contract_root / "deployment-intent.schema.json").read_text())
    draft_schema = json.loads((contract_root / "product-draft.schema.json").read_text())
    assert intent_schema["properties"]["schema_version"]["const"] == "1.0.0"
    assert draft_schema["properties"]["schema_version"]["const"] == "1.0.0"
    assert "operation" not in intent_schema["properties"]
