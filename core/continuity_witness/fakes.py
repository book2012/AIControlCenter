"""Repository-local deterministic fakes for Continuity Witness tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import HistoryCoverage, ImmutableHistoryObservation, StoredCheckpoint, TransitionIntent
from .domain import ApprovalClaimState
from .state_machine import (DatabaseStatus, EffectiveStatus, LifecycleRecord, LifecycleResult,
                            LifecycleStateMachine, ReconciliationResult, reconcile_effective_status)


class ClaimUnavailable(ValueError): pass
class MutationRetryProhibited(ValueError): pass


@dataclass(frozen=True, slots=True)
class FakeClaim:
    approval_id: Any
    claim_id: Any
    operation_id: Any
    evaluation_id: Any
    expected_transition_intent_digest: str
    state: ApprovalClaimState


class FakeTransactionStore:
    """Stage A claim and Stage B lifecycle commit with atomic in-memory writes."""

    def __init__(self, state_machine: LifecycleStateMachine | None = None) -> None:
        self.state_machine = state_machine or LifecycleStateMachine()
        self._claims: dict[Any, FakeClaim] = {}
        self._claim_ids: dict[Any, Any] = {}
        self._operations: dict[Any, LifecycleResult] = {}
        self._records: dict[Any, LifecycleRecord] = {}

    def durably_claim_approval(self, approval_id: Any, claim_id: Any = None,
                               operation_id: Any = None, evaluation_id: Any = None, *,
                               expected_transition_intent_digest: str,
                               fail_before_commit: bool = False) -> FakeClaim:
        if approval_id in self._claims:
            raise ClaimUnavailable("approval is already durably consumed")
        if fail_before_commit:
            raise RuntimeError("definitive Stage-A pre-commit failure")
        claim_id = approval_id if claim_id is None else claim_id
        claim = FakeClaim(approval_id, claim_id, operation_id, evaluation_id,
                          expected_transition_intent_digest,
                          ApprovalClaimState.DURABLY_CLAIMED)
        self._claims[approval_id] = claim
        self._claim_ids[claim_id] = approval_id
        return claim

    def get_claim(self, approval_or_claim_id: Any) -> FakeClaim | None:
        approval_id = self._claim_ids.get(approval_or_claim_id, approval_or_claim_id)
        return self._claims.get(approval_id)

    def get_operation(self, operation_id: Any) -> LifecycleResult | None:
        return self._operations.get(operation_id)

    def get_record(self, host_id: Any) -> LifecycleRecord | None:
        return self._records.get(host_id)

    def commit_lifecycle_transition(self, intent: TransitionIntent, *, approval_id: Any,
                                    history: ImmutableHistoryObservation | None = None,
                                    version_maxima: dict[str, int] | None = None,
                                    checkpoint_result: ReconciliationResult = ReconciliationResult.EXACT,
                                    database_result: ReconciliationResult = ReconciliationResult.EXACT,
                                    identifiers_match: bool = True, digests_match: bool = True) -> LifecycleResult:
        if intent.operation_id in self._operations:
            raise MutationRetryProhibited("mutation POST retry is prohibited")
        claim = self.get_claim(approval_id)
        if claim is None or claim.state is not ApprovalClaimState.DURABLY_CLAIMED:
            raise ClaimUnavailable("a matching durable claim is required")
        if claim.operation_id is not None and claim.operation_id != intent.operation_id:
            raise ClaimUnavailable("claim is bound to another lifecycle operation")
        if claim.evaluation_id is not None and claim.evaluation_id != intent.evaluation_id:
            raise ClaimUnavailable("claim is bound to another identity evaluation")
        if claim.expected_transition_intent_digest != intent.expected_transition_intent_digest:
            raise ClaimUnavailable("claim is bound to another transition intent")
        current_id = intent.expected_continuity_host_id or intent.expected_predecessor_continuity_host_id
        current = self._records.get(current_id)
        transitions = self.state_machine.plan(intent, current=current, history=history,
                                              version_maxima=version_maxima)
        # One assignment publishes the complete operation; migration halves never become operations.
        effective = reconcile_effective_status(database_status=DatabaseStatus.COMMITTED,
            database_result=database_result, checkpoint_result=checkpoint_result,
            identifiers_match=identifiers_match, digests_match=digests_match)
        result = LifecycleResult(intent.operation_id, transitions, DatabaseStatus.COMMITTED,
                                 database_result, checkpoint_result, effective)
        for transition in transitions:
            self._records[transition.after.continuity_host_id] = transition.after
        self._operations[intent.operation_id] = result
        terminal = (ApprovalClaimState.COMMITTED if effective is EffectiveStatus.PROVEN_SUCCESS
                    else ApprovalClaimState.UNCERTAIN_CONSUMED)
        self._claims[claim.approval_id] = FakeClaim(claim.approval_id, claim.claim_id,
                                                   claim.operation_id, claim.evaluation_id,
                                                   claim.expected_transition_intent_digest,
                                                   terminal)
        return result


class FakeImmutableHistoryStore:
    def __init__(self) -> None:
        self._versions: dict[Any, dict[str, StoredCheckpoint]] = {}
        self._coverage: dict[Any, ImmutableHistoryObservation] = {}

    def publish_checkpoint(self, checkpoint: StoredCheckpoint, immutable_version_id: str = "v1") -> None:
        checkpoint_id = checkpoint.payload.as_dict().get("checkpoint_id")
        self._versions.setdefault(checkpoint_id, {})[immutable_version_id] = checkpoint

    def get_checkpoint(self, checkpoint_id: Any, immutable_version_id: str | None = None) -> StoredCheckpoint | None:
        versions = self._versions.get(str(checkpoint_id), self._versions.get(checkpoint_id, {}))
        if immutable_version_id is not None:
            return versions.get(immutable_version_id)
        return versions[sorted(versions)[-1]] if versions else None

    def set_coverage(self, query: Any, coverage: HistoryCoverage,
                     *, version_aware: bool = True, delete_marker_observed: bool = False,
                     latest_key_not_found: bool = False) -> None:
        self._coverage[query] = ImmutableHistoryObservation(coverage, version_aware,
            delete_marker_observed, latest_key_not_found)

    def prove_coverage(self, query: Any) -> ImmutableHistoryObservation:
        return self._coverage.get(query, ImmutableHistoryObservation(HistoryCoverage.UNAVAILABLE, False))
