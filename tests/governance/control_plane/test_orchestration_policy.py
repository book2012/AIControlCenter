import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from core.governance.control_plane.application import (
    GovernanceOrchestrationContext,
    OrchestrationDisposition,
    decide_next_disposition,
)
from core.governance.control_plane.domain import (
    AuthorizationDecision,
    AuthorizationState,
    ConsumptionTransactionStatus,
    ExecutionStatus,
    GovernanceAuthorization,
    GovernanceAuthorizationConsumptionReceipt,
    GovernanceAuthorizationDecision,
    GovernanceAuthorizationReceipt,
    GovernanceAuthorizationRequest,
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
    GovernanceIdentity,
    GovernanceMutationBudget,
    GovernancePostconditionReport,
    MutationBudgetLineItem,
    MutationBudgetStatus,
    PostconditionDecision,
    PreconditionComparisonResult,
    PreconditionComparisonStatus,
)

NOW = datetime(2026, 8, 10, tzinfo=timezone.utc)


def authorization(state: AuthorizationState) -> GovernanceAuthorization:
    request = GovernanceAuthorizationRequest(
        "1.0.0", "request-1", "lifecycle-1", GovernanceIdentity("operator-1", "HUMAN"),
        "CONTROLLED_MUTATION", "service-1", "CANDIDATE", "approved change",
        ("SERVICE_RESTART",), "budget-1", NOW,
    )
    decision = GovernanceAuthorizationDecision(
        "1.0.0", "decision-1", "request-1", GovernanceIdentity("approver-1", "HUMAN"),
        AuthorizationDecision.APPROVED, ("EXPLICIT_APPROVAL",), NOW,
        NOW + timedelta(hours=1), ("SERVICE_RESTART",), "budget-1", "snapshot-digest",
    )
    receipt = GovernanceAuthorizationReceipt(
        "1.0.0", "authorization-1", "request-1", "decision-1", "lifecycle-1",
        state, ("SERVICE_RESTART",), "budget-1", "snapshot-digest", NOW,
        NOW + timedelta(hours=1),
    )
    return GovernanceAuthorization(request, state, "authorization-1", decision, receipt)


def comparison(status: PreconditionComparisonStatus = PreconditionComparisonStatus.MATCH) -> PreconditionComparisonResult:
    return PreconditionComparisonResult(
        status, "snapshot-expected", "snapshot-current", (),
        "snapshot-digest", "snapshot-digest" if status is PreconditionComparisonStatus.MATCH else "drift",
    )


def budget(state: MutationBudgetStatus) -> GovernanceMutationBudget:
    return GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", 1, status=state),), state,
    )


def execution_request() -> GovernanceExecutionRequest:
    return GovernanceExecutionRequest(
        "1.0.0", "execution-1", "lifecycle-1", "authorization-1", "claim-1",
        "budget-1", "SERVICE_RESTART", "service-1", "plan-digest", NOW,
    )


def consumption() -> GovernanceAuthorizationConsumptionReceipt:
    return GovernanceAuthorizationConsumptionReceipt(
        "1.0.0", "claim-1", "lifecycle-1", "authorization-1", "budget-1",
        "execution-1", NOW, ConsumptionTransactionStatus.COMMITTED,
    )


def execution(status: ExecutionStatus = ExecutionStatus.COMPLETED) -> GovernanceExecutionReceipt:
    return GovernanceExecutionReceipt(
        "1.0.0", "receipt-1", "lifecycle-1", "execution-1", "authorization-1",
        "claim-1", "budget-1", "SERVICE_RESTART", status, 1,
        1 if status is ExecutionStatus.COMPLETED else 0,
        1 if status is ExecutionStatus.UNCERTAIN else 0,
        NOW, NOW, "result-digest", ("FACT_RECORDED",),
    )


def postcondition(decision: PostconditionDecision) -> GovernancePostconditionReport:
    return GovernancePostconditionReport(
        "1.0.0", "report-1", "lifecycle-1", "receipt-1", "validator-1",
        decision, ("VALIDATION_COMPLETE",), "expected", "observed", "report-digest", NOW,
    )


def consumed_context(**changes: object) -> GovernanceOrchestrationContext:
    values = dict(
        authorization=authorization(AuthorizationState.CONSUMED),
        precondition_comparison=comparison(), mutation_budget=budget(MutationBudgetStatus.CONSUMED),
        consumption_receipt=consumption(), execution_request=execution_request(),
    )
    values.update(changes)
    return GovernanceOrchestrationContext(**values)  # type: ignore[arg-type]


def test_authorized_match_available_allows_consumption_without_consuming() -> None:
    authority = authorization(AuthorizationState.AUTHORIZED)
    mutation_budget = budget(MutationBudgetStatus.AVAILABLE)
    before = (authority.to_dict(), mutation_budget.to_dict())
    decision = decide_next_disposition(
        GovernanceOrchestrationContext(authority, comparison(), mutation_budget, execution_request=execution_request())
    )
    assert decision.disposition is OrchestrationDisposition.ALLOW_AUTHORIZATION_CONSUMPTION
    assert (authority.to_dict(), mutation_budget.to_dict()) == before
    assert authority.state is AuthorizationState.AUTHORIZED


def test_consumed_receipt_match_budget_request_allows_exactly_one_boundary() -> None:
    context = consumed_context()
    before = (context.authorization.to_dict(), context.mutation_budget.to_dict(), context.execution_request.to_dict())
    decision = decide_next_disposition(context)
    assert decision.disposition is OrchestrationDisposition.ALLOW_SINGLE_INVOCATION
    assert context.execution_receipt is None
    assert (context.authorization.to_dict(), context.mutation_budget.to_dict(), context.execution_request.to_dict()) == before


def test_completed_requires_postcondition_validation() -> None:
    decision = decide_next_disposition(consumed_context(execution_receipt=execution()))
    assert decision.disposition is OrchestrationDisposition.REQUIRE_POSTCONDITION_VALIDATION


def test_completed_pass_allows_closeout_only() -> None:
    decision = decide_next_disposition(consumed_context(
        execution_receipt=execution(), postcondition_report=postcondition(PostconditionDecision.PASS),
    ))
    assert decision.disposition is OrchestrationDisposition.ALLOW_CLOSEOUT


def test_decision_projection_is_repeatedly_deterministic_json_safe_and_immutable() -> None:
    decision = decide_next_disposition(consumed_context())
    first = decision.to_dict()
    assert decision.to_dict() == first
    assert json.loads(json.dumps(first)) == first
    with pytest.raises(FrozenInstanceError):
        decision.manual_action_required = True  # type: ignore[misc]
