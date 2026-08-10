from dataclasses import replace

import pytest

from core.governance.control_plane.application import OrchestrationDisposition, decide_next_disposition
from core.governance.control_plane.domain import (
    AuthorizationDecision, AuthorizationState, ExecutionStatus, FailureClass, FailurePhase,
    GovernanceAuthorization, GovernanceAuthorizationDecision, GovernanceFailureEvidence,
    GovernanceMutationBudget, MutationBudgetLineItem, MutationBudgetStatus,
    PostconditionDecision, PreconditionComparisonStatus,
)
from tests.governance.control_plane.test_orchestration_policy import (
    NOW, authorization, budget, comparison, consumed_context, consumption,
    execution, execution_request, postcondition,
)


def stopped(context) -> object:
    return decide_next_disposition(context)


@pytest.mark.parametrize("state", [
    AuthorizationState.REQUESTED, AuthorizationState.STALE, AuthorizationState.REJECTED,
])
def test_non_authoritative_states_stop(state: AuthorizationState) -> None:
    if state is AuthorizationState.REQUESTED:
        authority = GovernanceAuthorization(authorization(AuthorizationState.AUTHORIZED).request)
    elif state is AuthorizationState.REJECTED:
        base = authorization(AuthorizationState.AUTHORIZED)
        rejected = replace(base.decision, decision=AuthorizationDecision.REJECTED, expiry=None,
                           approved_scope=None, approved_mutation_budget_id=None,
                           precondition_snapshot_digest=None)
        authority = GovernanceAuthorization(base.request, state, "authorization-1", rejected, None)
    else:
        authority = authorization(state)
    context = consumed_context(authorization=authority)
    assert stopped(context).disposition is OrchestrationDisposition.STOP


def test_drift_before_and_after_consumption_stops() -> None:
    before = consumed_context(
        authorization=authorization(AuthorizationState.AUTHORIZED),
        mutation_budget=budget(MutationBudgetStatus.AVAILABLE),
        consumption_receipt=None, precondition_comparison=comparison(PreconditionComparisonStatus.DRIFT),
    )
    after = consumed_context(precondition_comparison=comparison(PreconditionComparisonStatus.DRIFT))
    assert stopped(before).disposition is OrchestrationDisposition.STOP
    after_decision = stopped(after)
    assert after_decision.disposition is OrchestrationDisposition.STOP
    assert after_decision.manual_action_required is True


def test_missing_consumption_receipt_stops() -> None:
    assert stopped(consumed_context(consumption_receipt=None)).disposition is OrchestrationDisposition.STOP


@pytest.mark.parametrize("field,value", [
    ("lifecycle_id", "other-lifecycle"), ("mutation_budget_id", "other-budget"),
])
def test_consumption_binding_mismatch_stops(field: str, value: str) -> None:
    assert stopped(consumed_context(consumption_receipt=replace(consumption(), **{field: value}))).disposition is OrchestrationDisposition.STOP


def test_action_mismatch_stops() -> None:
    request = replace(execution_request(), action_type="RUNTIME_ACTIVATE")
    assert stopped(consumed_context(execution_request=request)).disposition is OrchestrationDisposition.STOP


def test_violated_and_exhausted_budget_stop() -> None:
    violated = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", 1, status=MutationBudgetStatus.VIOLATED),),
        MutationBudgetStatus.VIOLATED, "SAFETY_VIOLATION",
    )
    exhausted = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", 1, 1, status=MutationBudgetStatus.EXHAUSTED),),
        MutationBudgetStatus.EXHAUSTED,
    )
    assert stopped(consumed_context(mutation_budget=violated)).disposition is OrchestrationDisposition.STOP
    assert stopped(consumed_context(mutation_budget=exhausted)).disposition is OrchestrationDisposition.STOP


def test_failure_evidence_has_highest_priority_and_requires_manual_action() -> None:
    evidence = GovernanceFailureEvidence(
        "1.0.0", "failure-1", "lifecycle-1", FailurePhase.EXECUTION,
        FailureClass.EXECUTION_FAILED, ("EXECUTION_STOPPED",), AuthorizationState.CONSUMED,
        True, 1, 0, 0, True, True, True, NOW,
    )
    decision = stopped(consumed_context(failure_evidence=evidence, execution_receipt=execution()))
    assert decision.reason_codes == ("FAILURE_EVIDENCE_PRESENT",)
    assert decision.manual_action_required is True


@pytest.mark.parametrize("status", [ExecutionStatus.FAILED, ExecutionStatus.UNCERTAIN])
def test_failed_or_uncertain_execution_stops_for_manual_action(status: ExecutionStatus) -> None:
    decision = stopped(consumed_context(execution_receipt=execution(status)))
    assert decision.disposition is OrchestrationDisposition.STOP
    assert decision.manual_action_required is True


def test_postcondition_fail_stops_for_manual_action() -> None:
    decision = stopped(consumed_context(
        execution_receipt=execution(), postcondition_report=postcondition(PostconditionDecision.FAIL),
    ))
    assert decision.disposition is OrchestrationDisposition.STOP
    assert decision.manual_action_required is True
