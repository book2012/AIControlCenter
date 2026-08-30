from __future__ import annotations

import inspect

import pytest

from core.continuity_witness.contracts import HistoryCoverage, ImmutableHistoryObservation, TransitionIntent
from core.continuity_witness.domain import (ApprovalClaimState, ContinuityHostId, IdentityEvaluationId,
    LifecycleApprovalId, LifecycleOperation, LifecycleOperationId)
from core.continuity_witness.fakes import (ClaimUnavailable, FakeImmutableHistoryStore,
    FakeTransactionStore, MutationRetryProhibited)
from core.continuity_witness.json_contracts import encode_base64url
from core.continuity_witness.state_machine import (DatabaseStatus, EffectiveStatus, LifecycleDenied,
    LifecycleRecord, LifecycleState, ReconciliationResult, reconcile_effective_status)


def uid(n): return f"01890f3c-4b2a-7cc1-8c00-{n:012x}"
DIGEST = encode_base64url(b"m" * 32)
ABSENT = ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, True)


def intent(kind, n=1, current=None):
    values = dict(operation_id=LifecycleOperationId(uid(100+n)), evaluation_id=IdentityEvaluationId(uid(200+n)),
        operation_type=kind, expected_continuity_host_id=None, expected_predecessor_continuity_host_id=None,
        expected_record_generation=None, validated_hardware_evidence_binding_digest=DIGEST)
    if kind in {LifecycleOperation.RECOVERY, LifecycleOperation.DECOMMISSION}:
        values.update(expected_continuity_host_id=current.continuity_host_id,
                      expected_record_generation=current.record_generation)
    elif kind is LifecycleOperation.MIGRATION:
        values.update(expected_predecessor_continuity_host_id=current.continuity_host_id,
                      expected_record_generation=current.record_generation)
    if kind is LifecycleOperation.DECOMMISSION:
        values["validated_hardware_evidence_binding_digest"] = None
    return TransitionIntent(**values)


def claimed(store, request, n):
    approval = LifecycleApprovalId(uid(300+n))
    store.durably_claim_approval(approval, operation_id=request.operation_id,
                                 evaluation_id=request.evaluation_id,
                                 expected_transition_intent_digest=request.expected_transition_intent_digest)
    return approval


def genesis(store, n=1, **kwargs):
    request = intent(LifecycleOperation.GENESIS_ENROLLMENT, n)
    return store.commit_lifecycle_transition(request, approval_id=claimed(store, request, n), history=ABSENT, **kwargs)


def test_genesis_success_assigns_identity_and_single_active_transition():
    result = genesis(FakeTransactionStore())
    assert len(result.transitions) == 1
    assert result.transitions[0].after.state is LifecycleState.ACTIVE
    assert result.transitions[0].after.enrollment_generation == 1


@pytest.mark.parametrize("observation", [
    ImmutableHistoryObservation(HistoryCoverage.COMPLETE_PRESENT, True),
    ImmutableHistoryObservation(HistoryCoverage.INCOMPLETE, True),
    ImmutableHistoryObservation(HistoryCoverage.CONFLICTING, True),
    ImmutableHistoryObservation(HistoryCoverage.UNAVAILABLE, True),
    ImmutableHistoryObservation(HistoryCoverage.UNVERIFIABLE, True),
    ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, False),
    ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, True, delete_marker_observed=True),
    ImmutableHistoryObservation(HistoryCoverage.COMPLETE_ABSENT, True, latest_key_not_found=True),
])
def test_genesis_denied_without_complete_historical_absence(observation):
    store = FakeTransactionStore(); request = intent(LifecycleOperation.GENESIS_ENROLLMENT)
    with pytest.raises(LifecycleDenied):
        store.commit_lifecycle_transition(request, approval_id=claimed(store, request, 1), history=observation)


def test_history_evidence_alone_has_no_authority_and_cannot_execute():
    assert ABSENT.proves_historical_absence and not hasattr(ABSENT, "genesis_eligible")
    store = FakeTransactionStore(); request = intent(LifecycleOperation.GENESIS_ENROLLMENT)
    with pytest.raises(ClaimUnavailable):
        store.commit_lifecycle_transition(request, approval_id=LifecycleApprovalId(uid(999)), history=ABSENT)


def test_recovery_preserves_identity_generation_and_maxima():
    store = FakeTransactionStore(); original = genesis(store).transitions[0].after
    request = intent(LifecycleOperation.RECOVERY, 2, original)
    recovered = store.commit_lifecycle_transition(request, approval_id=claimed(store, request, 2),
                                                  version_maxima={"policy": 4}).transitions[0].after
    assert recovered.continuity_host_id == original.continuity_host_id
    assert recovered.enrollment_generation == original.enrollment_generation
    assert recovered.version_maxima["policy"] == 4


def test_lifecycle_record_defensively_copies_and_freezes_version_maxima():
    source = {"policy": 4}
    record = LifecycleRecord(ContinuityHostId(uid(701)), 1, 1, LifecycleState.ACTIVE, source)
    source["policy"] = 99
    assert record.version_maxima["policy"] == 4
    with pytest.raises(TypeError):
        record.version_maxima["policy"] = 5


@pytest.mark.parametrize("version_maxima", [
    {"policy": True}, {"policy": -1}, {"policy": 1.0}, {"policy": "1"},
    {"": 1}, {1: 1},
])
def test_lifecycle_record_rejects_invalid_version_maxima(version_maxima):
    with pytest.raises(ValueError, match="version maxima"):
        LifecycleRecord(ContinuityHostId(uid(702)), 1, 1, LifecycleState.ACTIVE, version_maxima)


def test_recovery_and_migration_preserve_nondecreasing_version_maxima():
    store = FakeTransactionStore()
    original = genesis(store, version_maxima={"policy": 4}).transitions[0].after
    recovery_request = intent(LifecycleOperation.RECOVERY, 2, original)
    recovered = store.commit_lifecycle_transition(
        recovery_request, approval_id=claimed(store, recovery_request, 2),
        version_maxima={"policy": 5},
    ).transitions[0].after
    migration_request = intent(LifecycleOperation.MIGRATION, 3, recovered)
    migrated = store.commit_lifecycle_transition(
        migration_request, approval_id=claimed(store, migration_request, 3),
        version_maxima={"policy": 5},
    )
    assert [transition.after.version_maxima["policy"] for transition in migrated.transitions] == [5, 5]
    lower_request = intent(LifecycleOperation.RECOVERY, 4, migrated.transitions[1].after)
    with pytest.raises(LifecycleDenied, match="cannot decrease"):
        store.commit_lifecycle_transition(
            lower_request, approval_id=claimed(store, lower_request, 4),
            version_maxima={"policy": 4},
        )


def test_decommission_needs_no_mda_and_is_terminal():
    store = FakeTransactionStore(); current = genesis(store).transitions[0].after
    request = intent(LifecycleOperation.DECOMMISSION, 2, current)
    assert request.validated_hardware_evidence_binding_digest is None
    final = store.commit_lifecycle_transition(request, approval_id=claimed(store, request, 2)).transitions[0].after
    retry = intent(LifecycleOperation.RECOVERY, 3, final)
    with pytest.raises(LifecycleDenied, match="terminal"):
        store.commit_lifecycle_transition(retry, approval_id=claimed(store, retry, 3))


def test_migration_is_two_ordered_transitions_in_one_atomic_result():
    store = FakeTransactionStore(); predecessor = genesis(store).transitions[0].after
    request = intent(LifecycleOperation.MIGRATION, 2, predecessor)
    result = store.commit_lifecycle_transition(request, approval_id=claimed(store, request, 2))
    assert [(t.ordinal, t.role, t.operation_id) for t in result.transitions] == [
        (1, "PREDECESSOR", request.operation_id), (2, "SUCCESSOR", request.operation_id)]
    assert result.transitions[0].after.state is LifecycleState.DECOMMISSIONED
    successor = result.transitions[1].after
    assert successor.state is LifecycleState.ACTIVE and successor.continuity_host_id != predecessor.continuity_host_id
    assert successor.predecessor_continuity_host_id == predecessor.continuity_host_id


def test_durable_and_stranded_claims_cannot_be_reused_or_stolen():
    store = FakeTransactionStore(); approval = LifecycleApprovalId(uid(501))
    store.durably_claim_approval(approval, operation_id=LifecycleOperationId(uid(601)),
                                 expected_transition_intent_digest=DIGEST)
    assert store.get_claim(approval).state is ApprovalClaimState.DURABLY_CLAIMED
    with pytest.raises(ClaimUnavailable):
        store.durably_claim_approval(approval, operation_id=LifecycleOperationId(uid(602)),
                                     expected_transition_intent_digest=DIGEST)


def test_claim_must_match_current_identity_evaluation():
    store = FakeTransactionStore(); request = intent(LifecycleOperation.GENESIS_ENROLLMENT)
    approval = LifecycleApprovalId(uid(503))
    store.durably_claim_approval(approval, operation_id=request.operation_id,
                                 evaluation_id=IdentityEvaluationId(uid(998)),
                                 expected_transition_intent_digest=request.expected_transition_intent_digest)
    with pytest.raises(ClaimUnavailable, match="identity evaluation"):
        store.commit_lifecycle_transition(request, approval_id=approval, history=ABSENT)


def test_definitive_stage_a_precommit_failure_creates_no_claim():
    store = FakeTransactionStore(); approval = LifecycleApprovalId(uid(502))
    with pytest.raises(RuntimeError):
        store.durably_claim_approval(approval, expected_transition_intent_digest=DIGEST,
                                     fail_before_commit=True)
    assert store.get_claim(approval) is None


def test_durable_claim_rejects_same_operation_and_evaluation_with_substituted_intent():
    store = FakeTransactionStore()
    intent_a = intent(LifecycleOperation.GENESIS_ENROLLMENT)
    intent_b = TransitionIntent(
        operation_id=intent_a.operation_id,
        evaluation_id=intent_a.evaluation_id,
        operation_type=LifecycleOperation.GENESIS_ENROLLMENT,
        expected_continuity_host_id=None,
        expected_predecessor_continuity_host_id=None,
        expected_record_generation=None,
        validated_hardware_evidence_binding_digest=encode_base64url(b"n" * 32),
    )
    assert intent_b.expected_transition_intent_digest != intent_a.expected_transition_intent_digest
    approval = claimed(store, intent_a, 1)
    with pytest.raises(ClaimUnavailable, match="transition intent"):
        store.commit_lifecycle_transition(intent_b, approval_id=approval, history=ABSENT)
    assert store.get_operation(intent_a.operation_id) is None
    assert store._records == {}
    assert store.get_claim(approval).state is ApprovalClaimState.DURABLY_CLAIMED
    with pytest.raises(ClaimUnavailable):
        store.durably_claim_approval(
            approval, operation_id=intent_a.operation_id, evaluation_id=intent_a.evaluation_id,
            expected_transition_intent_digest=intent_a.expected_transition_intent_digest,
        )


def test_ambiguous_mutation_cannot_be_post_retried():
    store = FakeTransactionStore(); request = intent(LifecycleOperation.GENESIS_ENROLLMENT)
    approval = claimed(store, request, 1)
    result = store.commit_lifecycle_transition(request, approval_id=approval, history=ABSENT,
                                               checkpoint_result=ReconciliationResult.MISSING)
    assert result.effective_status is EffectiveStatus.UNCERTAIN_CONSUMED
    with pytest.raises(MutationRetryProhibited):
        store.commit_lifecycle_transition(request, approval_id=approval, history=ABSENT)


def test_external_success_requires_exact_database_checkpoint_and_bindings():
    exact = dict(database_status=DatabaseStatus.COMMITTED, database_result=ReconciliationResult.EXACT,
                 checkpoint_result=ReconciliationResult.EXACT)
    assert reconcile_effective_status(**exact) is EffectiveStatus.PROVEN_SUCCESS
    assert reconcile_effective_status(**exact, digests_match=False) is EffectiveStatus.UNCERTAIN_CONSUMED
    assert reconcile_effective_status(**{**exact, "checkpoint_result": ReconciliationResult.MISSING}) is EffectiveStatus.UNCERTAIN_CONSUMED


def test_fake_history_exact_version_lookup_and_closed_coverage():
    history = FakeImmutableHistoryStore()
    history.set_coverage("hardware", HistoryCoverage.CONFLICTING)
    assert history.prove_coverage("hardware").coverage is HistoryCoverage.CONFLICTING
    assert history.get_checkpoint("missing", "v7") is None


def test_fakes_have_no_concrete_infrastructure_dependencies():
    import core.continuity_witness.fakes as fakes
    source = inspect.getsource(fakes)
    for prohibited in ("boto3", "botocore", "psycopg", "asyncpg", "ControlledExecutionPort", "UbuntuWorkerClient"):
        assert prohibited not in source
