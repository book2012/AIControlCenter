from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

from core.shopping.product_drafts import *

NOW=datetime(2026,8,1,12,0,tzinfo=timezone.utc)
DIG="sha256:"+"a"*64

def actor(kind=ActorType.HUMAN): return ActorReference("actor-1",kind)
def identity(n=1,rid="r1",previous=None): return RevisionIdentity("d1",rid,n,previous,NOW,actor(),"corr","audit")
def source(): return SourceSnapshotReference("42",NOW,snapshot_reference="snapshot:42",snapshot_digest=DIG)
def fields(): return ProposedFields(name="Orange",regular_price=Decimal("12.340"),categories=(Reference("7","Fruit"),))
def revision(state=LifecycleState.DRAFT): return ProductDraftRevision(identity(),source(),state,fields())
def command(frm,to,key="key",digest=DIG,expected_id="r1",expected_number=1):
    return TransitionCommand("d1","r1",expected_id,expected_number,frm,to,actor(),"corr","audit",key,digest,NOW)

def test_values_are_immutable_and_validate_utc_digest_and_source():
    with pytest.raises(FrozenInstanceError): actor().actor_id="x"
    with pytest.raises(ValueError): SourceSnapshotReference("42",NOW.replace(tzinfo=None),snapshot_reference="x")
    with pytest.raises(ValueError): SourceSnapshotReference("42",NOW,snapshot_reference="x",source_system="OTHER")
    with pytest.raises(ValueError): SourceSnapshotReference("42",NOW)
    with pytest.raises(ValueError): SourceSnapshotReference("42",NOW,snapshot_digest="bad")
    assert SourceSnapshotReference("42",NOW+timedelta(hours=0),snapshot_digest=DIG).observed_at.tzinfo is timezone.utc

def test_validation_approval_and_intent_are_exact_revision_bound_and_human_only():
    validation=ValidationResult("r1",ValidationStatus.VALID,(),("note",),"v1",NOW,DIG,DIG,"audit")
    with pytest.raises(ValueError): ApprovalDecision("x","d1","r1",actor(ActorType.SERVICE),ApprovalDecisionType.APPROVE,NOW,"ok","c","a","k")
    approval=ApprovalDecision("x","d1","r1",actor(),ApprovalDecisionType.APPROVE,NOW,"ok","c","a","k")
    intent=DeploymentIntent("i","d1","r1","woocommerce-adapter",DIG,"k","auth","audit",ReadinessStatus.READY,actor(ActorType.SERVICE),"c",NOW)
    aggregate=ProductDraftRevision(identity(),source(),LifecycleState.APPROVED,fields(),validation=validation,human_decision=approval,deployment_intent=intent)
    assert aggregate.human_decision.reviewer.actor_type is ActorType.HUMAN
    with pytest.raises(ValueError): ProductDraftRevision(identity(),source(),LifecycleState.DRAFT,fields(),validation=ValidationResult("other",ValidationStatus.VALID,(),(),"v",NOW,DIG,DIG,"a"))


def test_rejected_or_revoked_decision_cannot_back_deployment_intent():
    intent=DeploymentIntent("i","d1","r1","adapter",DIG,"k","auth","audit",ReadinessStatus.READY,actor(ActorType.SERVICE),"c",NOW)
    for decision in (ApprovalDecisionType.REJECT, ApprovalDecisionType.REVOKE):
        inactive=ApprovalDecision("x","d1","r1",actor(),decision,NOW,"reason","c","a","k")
        with pytest.raises(ValueError, match="active exact-revision approval"):
            ProductDraftRevision(identity(),source(),LifecycleState.REVOKED,fields(),human_decision=inactive,deployment_intent=intent)

def test_new_revision_preserves_chain_and_does_not_inherit_approval():
    approval=ApprovalDecision("x","d1","r1",actor(),ApprovalDecisionType.APPROVE,NOW,"ok","c","a","k")
    old=ProductDraftRevision(identity(),source(),LifecycleState.APPROVED,fields(),human_decision=approval)
    new=old.new_revision(identity(2,"r2","r1"),ProposedFields(name="New"))
    assert (new.state,new.human_decision,new.identity.previous_revision_id)==(LifecycleState.DRAFT,None,"r1")
    with pytest.raises(ValueError): old.new_revision(identity(2,"r2","wrong"),fields())

def test_exact_manifest_transitions_and_every_unspecified_pair():
    assert "DEPLOYED" not in LifecycleState.__members__
    for frm in LifecycleState:
        for to in LifecycleState:
            result=evaluate_transition(revision(frm),command(frm,to),NOW)
            expected=TransitionOutcome.APPLIED if (frm,to) in PERMITTED_TRANSITIONS else TransitionOutcome.REJECTED_INVALID_TRANSITION
            assert result.outcome is expected
    assert evaluate_transition(revision(LifecycleState.REJECTED),command(LifecycleState.REJECTED,LifecycleState.APPROVED),NOW).outcome is TransitionOutcome.REJECTED_INVALID_TRANSITION

def test_conflict_idempotency_and_repository_semantics():
    repo=InMemoryProductDraftRepository(); repo.store(revision())
    conflict=repo.transition(command(LifecycleState.DRAFT,LifecycleState.VALIDATED,expected_number=2),NOW)
    assert conflict.outcome is TransitionOutcome.REJECTED_CONFLICT
    first=repo.transition(command(LifecycleState.DRAFT,LifecycleState.VALIDATED,key="apply"),NOW)
    assert first.outcome is TransitionOutcome.APPLIED and repo.fetch_current("d1").state is LifecycleState.VALIDATED
    assert repo.transition(command(LifecycleState.DRAFT,LifecycleState.VALIDATED,key="apply"),NOW).outcome is TransitionOutcome.IDEMPOTENT_REPLAY
    assert repo.transition(command(LifecycleState.DRAFT,LifecycleState.VALIDATED,key="apply",digest="sha256:"+"b"*64),NOW).outcome is TransitionOutcome.REJECTED_IDEMPOTENCY_KEY_REUSE
    with pytest.raises(DuplicateRevisionError): repo.store(revision())
    repo.store(revision().new_revision(identity(2,"r2","r1"),ProposedFields(sku="S")))
    assert repo.fetch("d1","r1").revision_id=="r1" and repo.fetch_current("d1").revision_id=="r2"
    with pytest.raises(RevisionSequenceError): repo.store(ProductDraftRevision(identity(4,"r4","r2"),source(),LifecycleState.DRAFT,fields()))


def test_repository_chain_rejection_and_instance_isolation():
    first=InMemoryProductDraftRepository(); second=InMemoryProductDraftRepository()
    first.store(revision())
    assert second.fetch_current("d1") is None
    with pytest.raises(RevisionSequenceError):
        second.store(ProductDraftRevision(identity(2,"r2","r1"),source(),LifecycleState.DRAFT,fields()))
    with pytest.raises(RevisionChainError):
        first.store(ProductDraftRevision(identity(2,"r2","other"),source(),LifecycleState.DRAFT,fields()))


def test_transition_contract_values_are_immutable_and_validate_utc():
    item=command(LifecycleState.DRAFT,LifecycleState.VALIDATED)
    with pytest.raises(FrozenInstanceError): item.to_state=LifecycleState.APPROVED
    with pytest.raises(ValueError):
        command(LifecycleState.DRAFT,LifecycleState.VALIDATED).__class__(
            "d1","r1","r1",1,LifecycleState.DRAFT,LifecycleState.VALIDATED,
            actor(),"corr","audit","key",DIG,NOW.replace(tzinfo=None),
        )
    result=evaluate_transition(revision(),item,NOW)
    with pytest.raises(FrozenInstanceError): result.state=LifecycleState.APPROVED


def test_sha256_helper_uses_canonical_json_not_process_hash():
    left={"decimal":Decimal("1.230"),"nested":{"b":2,"a":1}}
    right={"nested":{"a":1,"b":2},"decimal":Decimal("1.230")}
    assert canonical_json(left)==canonical_json(right)
    assert sha256_digest(left)==sha256_digest(right)
    assert sha256_digest(left).startswith("sha256:") and len(sha256_digest(left))==71

def test_canonical_json_decimal_round_trip_and_no_credentials():
    item=revision()
    encoded=canonical_json(item)
    assert encoded==canonical_json(item) and '"regular_price":"12.340"' in encoded
    assert json.loads(encoded)["schema_version"]=="1.0.0"
    restored=product_draft_from_json(encoded)
    assert restored==item
    assert sha256_digest(item)==sha256_digest(restored)
    lowered=encoded.lower()
    assert all(word not in lowered for word in ("password","consumer_secret","consumer_key","credential"))


def test_serialized_draft_omits_unproposed_nullable_incompatible_fields():
    payload=json.loads(canonical_json(ProductDraftRevision(identity(),source(),LifecycleState.DRAFT,ProposedFields(sku="S"))))
    assert payload["proposed_fields"] == {
        "categories": [], "image_references": [], "sku": "S", "tags": []
    }
    assert product_draft_from_dict(payload).proposed_fields.sku == "S"


def test_nested_domain_types_and_idempotency_records_are_guarded():
    with pytest.raises(ValueError, match="created_by"):
        RevisionIdentity("d1","r1",1,None,NOW,"not-an-actor","c","a")
    with pytest.raises(ValueError, match="suggestions"):
        ProductDraftRevision(identity(),source(),LifecycleState.DRAFT,fields(),suggestions=("bad",))
    repo=InMemoryProductDraftRepository()
    result=evaluate_transition(revision(),command(LifecycleState.DRAFT,LifecycleState.VALIDATED),NOW)
    repo.bind_idempotency("d1","key",DIG,result)
    with pytest.raises(ValueError, match="immutable"):
        repo.bind_idempotency("d1","key","sha256:"+"b"*64,result)

def test_no_io_or_route_dependencies_in_public_package():
    import pathlib
    root=pathlib.Path(__file__).parents[1]/"core/shopping/product_drafts"
    text="\n".join(p.read_text() for p in root.glob("*.py")).lower()
    assert all(token not in text for token in ("fastapi","requests","httpx","subprocess","@router","woocommerce_rest"))
