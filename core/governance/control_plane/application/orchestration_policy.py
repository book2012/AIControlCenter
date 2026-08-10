"""Deterministic, side-effect-free SEC-02A8 orchestration policy.

This module only inspects immutable Governance domain facts.  A progress
disposition permits an external coordinator to cross one later governance
boundary; it performs no consumption, invocation, validation, or closeout.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ..domain import (
    AuthorizationState,
    ExecutionStatus,
    GovernanceAuthorization,
    GovernanceAuthorizationConsumptionReceipt,
    GovernanceExecutionReceipt,
    GovernanceExecutionRequest,
    GovernanceFailureEvidence,
    GovernanceMutationBudget,
    GovernancePostconditionReport,
    MutationBudgetLineItem,
    MutationBudgetStatus,
    PostconditionDecision,
    PreconditionComparisonResult,
    PreconditionComparisonStatus,
)


class OrchestrationDisposition(StrEnum):
    ALLOW_AUTHORIZATION_CONSUMPTION = "ALLOW_AUTHORIZATION_CONSUMPTION"
    ALLOW_SINGLE_INVOCATION = "ALLOW_SINGLE_INVOCATION"
    REQUIRE_POSTCONDITION_VALIDATION = "REQUIRE_POSTCONDITION_VALIDATION"
    ALLOW_CLOSEOUT = "ALLOW_CLOSEOUT"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class GovernanceOrchestrationContext:
    """Immutable facts supplied by an external governance coordinator."""

    authorization: GovernanceAuthorization
    precondition_comparison: PreconditionComparisonResult | None
    mutation_budget: GovernanceMutationBudget
    consumption_receipt: GovernanceAuthorizationConsumptionReceipt | None = None
    execution_request: GovernanceExecutionRequest | None = None
    execution_receipt: GovernanceExecutionReceipt | None = None
    postcondition_report: GovernancePostconditionReport | None = None
    failure_evidence: GovernanceFailureEvidence | None = None
    invocation_already_attempted: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.authorization, GovernanceAuthorization):
            raise TypeError("authorization must be GovernanceAuthorization")
        if self.precondition_comparison is not None and not isinstance(
            self.precondition_comparison, PreconditionComparisonResult
        ):
            raise TypeError("precondition_comparison must be typed")
        if not isinstance(self.mutation_budget, GovernanceMutationBudget):
            raise TypeError("mutation_budget must be GovernanceMutationBudget")
        if self.consumption_receipt is not None and not isinstance(
            self.consumption_receipt, GovernanceAuthorizationConsumptionReceipt
        ):
            raise TypeError("consumption_receipt must be typed")
        if self.execution_request is not None and not isinstance(
            self.execution_request, GovernanceExecutionRequest
        ):
            raise TypeError("execution_request must be typed")
        if self.execution_receipt is not None and not isinstance(
            self.execution_receipt, GovernanceExecutionReceipt
        ):
            raise TypeError("execution_receipt must be typed")
        if self.postcondition_report is not None and not isinstance(
            self.postcondition_report, GovernancePostconditionReport
        ):
            raise TypeError("postcondition_report must be typed")
        if self.failure_evidence is not None and not isinstance(
            self.failure_evidence, GovernanceFailureEvidence
        ):
            raise TypeError("failure_evidence must be typed")
        if not isinstance(self.invocation_already_attempted, bool):
            raise TypeError("invocation_already_attempted must be boolean")


@dataclass(frozen=True, slots=True)
class GovernanceOrchestrationDecision:
    disposition: OrchestrationDisposition
    reason_codes: tuple[str, ...]
    retry_prohibited: bool = True
    rollback_prohibited: bool = True
    manual_action_required: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.disposition, OrchestrationDisposition):
            raise TypeError("disposition must be OrchestrationDisposition")
        if not isinstance(self.reason_codes, tuple) or not self.reason_codes:
            raise TypeError("reason_codes must be a non-empty tuple")
        if self.retry_prohibited is not True:
            raise ValueError("retry_prohibited must be true")
        if self.rollback_prohibited is not True:
            raise ValueError("rollback_prohibited must be true")
        if not isinstance(self.manual_action_required, bool):
            raise TypeError("manual_action_required must be boolean")

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition.value,
            "reason_codes": list(self.reason_codes),
            "retry_prohibited": self.retry_prohibited,
            "rollback_prohibited": self.rollback_prohibited,
            "manual_action_required": self.manual_action_required,
        }


def _decision(
    disposition: OrchestrationDisposition,
    reason_code: str,
    *,
    manual: bool = False,
) -> GovernanceOrchestrationDecision:
    return GovernanceOrchestrationDecision(
        disposition=disposition,
        reason_codes=(reason_code,),
        manual_action_required=manual,
    )


def _stop(reason_code: str, *, manual: bool = False) -> GovernanceOrchestrationDecision:
    return _decision(OrchestrationDisposition.STOP, reason_code, manual=manual)


def _line_item(
    budget: GovernanceMutationBudget, action_type: str
) -> MutationBudgetLineItem | None:
    return next(filter(lambda item: item.action_type == action_type, budget.line_items), None)


def decide_next_disposition(
    context: GovernanceOrchestrationContext,
) -> GovernanceOrchestrationDecision:
    """Return the next permitted disposition without performing any action."""
    if not isinstance(context, GovernanceOrchestrationContext):
        raise TypeError("context must be GovernanceOrchestrationContext")

    authorization = context.authorization
    authorization_receipt = authorization.receipt
    request = authorization.request
    budget = context.mutation_budget
    consumption = context.consumption_receipt
    execution_request = context.execution_request
    execution = context.execution_receipt
    postcondition = context.postcondition_report

    # Safety blockers are intentionally evaluated before every progress gate.
    if context.failure_evidence is not None:
        return _stop("FAILURE_EVIDENCE_PRESENT", manual=True)

    if authorization_receipt is not None and (
        authorization_receipt.lifecycle_id != request.lifecycle_id
        or authorization_receipt.request_id != request.request_id
        or authorization_receipt.authorization_id != authorization.authorization_id
        or authorization_receipt.mutation_budget_id != budget.budget_id
    ):
        return _stop("AUTHORIZATION_LIFECYCLE_BINDING_MISMATCH", manual=True)
    if budget.authorization_id != authorization.authorization_id:
        return _stop("MUTATION_BUDGET_BINDING_MISMATCH", manual=True)
    if consumption is not None and (
        consumption.lifecycle_id != request.lifecycle_id
        or consumption.authorization_id != authorization.authorization_id
        or consumption.mutation_budget_id != budget.budget_id
    ):
        return _stop("CONSUMPTION_RECEIPT_BINDING_MISMATCH", manual=True)
    if execution_request is not None and (
        execution_request.lifecycle_id != request.lifecycle_id
        or execution_request.authorization_id != authorization.authorization_id
        or execution_request.mutation_budget_id != budget.budget_id
        or (consumption is not None and execution_request.claim_id != consumption.claim_id)
        or (
            consumption is not None
            and execution_request.execution_request_id != consumption.execution_request_id
        )
    ):
        return _stop("EXECUTION_REQUEST_BINDING_MISMATCH", manual=True)
    if execution is not None and (
        execution.lifecycle_id != request.lifecycle_id
        or execution.authorization_id != authorization.authorization_id
        or execution.mutation_budget_id != budget.budget_id
        or execution_request is None
        or execution.execution_request_id != execution_request.execution_request_id
        or execution.claim_id != execution_request.claim_id
        or execution.action_type != execution_request.action_type
    ):
        return _stop("EXECUTION_RECEIPT_BINDING_MISMATCH", manual=True)
    if postcondition is not None and (
        execution is None
        or postcondition.lifecycle_id != request.lifecycle_id
        or postcondition.execution_receipt_id != execution.receipt_id
    ):
        return _stop("POSTCONDITION_BINDING_MISMATCH", manual=True)

    if authorization.state is AuthorizationState.REQUESTED:
        return _stop("AUTHORIZATION_REQUESTED")
    if authorization.state is AuthorizationState.STALE:
        return _stop("AUTHORIZATION_STALE")
    if authorization.state is AuthorizationState.REJECTED:
        return _stop("AUTHORIZATION_REJECTED")

    comparison = context.precondition_comparison
    if comparison is None:
        return _stop("CURRENT_PRECONDITION_COMPARISON_ABSENT", manual=True)
    if comparison.status is PreconditionComparisonStatus.DRIFT:
        return _stop(
            "CURRENT_PRECONDITION_DRIFT",
            manual=authorization.state is AuthorizationState.CONSUMED,
        )
    if authorization_receipt is not None and (
        comparison.expected_snapshot_digest
        != authorization_receipt.precondition_snapshot_digest
    ):
        return _stop("PRECONDITION_SNAPSHOT_BINDING_MISMATCH", manual=True)

    if authorization.state is AuthorizationState.AUTHORIZED:
        if consumption is not None:
            return _stop("AUTHORIZATION_CONSUMPTION_ALREADY_RECORDED", manual=True)
        if execution is not None:
            return _stop("EXECUTION_EXISTS_BEFORE_CONSUMPTION", manual=True)
        if context.invocation_already_attempted:
            return _stop("PRIOR_INVOCATION_AMBIGUITY", manual=True)
        if budget.status is MutationBudgetStatus.VIOLATED:
            return _stop("MUTATION_BUDGET_VIOLATED", manual=True)
        if budget.status is not MutationBudgetStatus.AVAILABLE:
            return _stop("MUTATION_BUDGET_NOT_AVAILABLE")
        return _decision(
            OrchestrationDisposition.ALLOW_AUTHORIZATION_CONSUMPTION,
            "AUTHORIZATION_CONSUMPTION_GATE_SATISFIED",
        )

    # The only remaining valid lifecycle is CONSUMED. Missing or ambiguous
    # claim evidence cannot be repaired or inferred by this policy.
    if consumption is None:
        return _stop("CONSUMPTION_RECEIPT_MISSING", manual=True)
    if budget.status is MutationBudgetStatus.VIOLATED:
        return _stop("MUTATION_BUDGET_VIOLATED", manual=True)

    if execution is not None:
        if execution.status is ExecutionStatus.FAILED:
            return _stop("EXECUTION_FAILED", manual=True)
        if execution.status is ExecutionStatus.UNCERTAIN:
            return _stop("EXECUTION_UNCERTAIN", manual=True)
        if postcondition is None:
            return _decision(
                OrchestrationDisposition.REQUIRE_POSTCONDITION_VALIDATION,
                "COMPLETED_EXECUTION_REQUIRES_POSTCONDITION",
            )
        if postcondition.decision is PostconditionDecision.FAIL:
            return _stop("POSTCONDITION_FAILED", manual=True)
        return _decision(
            OrchestrationDisposition.ALLOW_CLOSEOUT,
            "POSTCONDITION_PASSED",
        )

    if postcondition is not None:
        return _stop("POSTCONDITION_WITHOUT_EXECUTION", manual=True)
    if execution_request is None:
        return _stop("EXECUTION_REQUEST_MISSING")
    action = _line_item(budget, execution_request.action_type)
    if action is None:
        return _stop("ACTION_NOT_IN_MUTATION_BUDGET")
    if budget.status is MutationBudgetStatus.EXHAUSTED:
        return _stop("MUTATION_BUDGET_EXHAUSTED")
    if budget.status is not MutationBudgetStatus.CONSUMED:
        return _stop("MUTATION_BUDGET_NOT_CONSUMED")
    if action.status is MutationBudgetStatus.VIOLATED:
        return _stop("MUTATION_ACTION_VIOLATED", manual=True)
    if action.status is MutationBudgetStatus.EXHAUSTED or action.remaining_count == 0:
        return _stop("MUTATION_ACTION_EXHAUSTED")
    if action.actual_invocation_count > 0 or context.invocation_already_attempted:
        return _stop("ACTION_ALREADY_ATTEMPTED", manual=True)
    return _decision(
        OrchestrationDisposition.ALLOW_SINGLE_INVOCATION,
        "SINGLE_INVOCATION_GATE_SATISFIED",
    )


__all__ = (
    "GovernanceOrchestrationContext",
    "GovernanceOrchestrationDecision",
    "OrchestrationDisposition",
    "decide_next_disposition",
)
