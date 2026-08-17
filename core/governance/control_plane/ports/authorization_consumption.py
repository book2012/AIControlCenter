"""Atomic durable SEC-02 governance authorization-consumption boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..domain import (
    AuthorizationState,
    ConsumptionTransactionStatus,
    GovernanceAuthorization,
    GovernanceAuthorizationConsumptionReceipt,
    GovernanceExecutionRequest,
    GovernanceMutationBudget,
    MutationBudgetStatus,
)


def _matching_line_items(
    budget: GovernanceMutationBudget, request: GovernanceExecutionRequest
) -> tuple[object, ...]:
    return tuple(
        item for item in budget.line_items if item.action_type == request.action_type
    )


def _require_exact_type(value: object, expected: type[object], field_name: str) -> None:
    if type(value) is not expected:
        raise ValueError(f"{field_name} must be exactly {expected.__name__}")


def _require_authorization_bindings(
    authorization: GovernanceAuthorization,
    budget: GovernanceMutationBudget,
    request: GovernanceExecutionRequest,
) -> None:
    authorization_request = authorization.request
    authorization_decision = authorization.decision
    authorization_receipt = authorization.receipt
    if request.target != authorization_request.target:
        raise ValueError("execution request target binding does not match")
    if authorization_decision is None or authorization_receipt is None:
        raise ValueError("authorization decision and receipt are required")
    if authorization_receipt.approved_scope != authorization_decision.approved_scope:
        raise ValueError("authorization approved scope binding does not match")
    if not set(authorization_receipt.approved_scope).issubset(
        authorization_request.requested_scope
    ):
        raise ValueError("authorization approved scope exceeds requested scope")
    if request.action_type not in authorization_receipt.approved_scope:
        raise ValueError("execution request action is outside authorization scope")
    if authorization_request.requested_mutation_budget_id != budget.budget_id:
        raise ValueError("authorization request mutation budget binding does not match")
    if authorization_decision.approved_mutation_budget_id != budget.budget_id:
        raise ValueError("authorization decision mutation budget binding does not match")
    if authorization_receipt.mutation_budget_id != budget.budget_id:
        raise ValueError("authorization receipt mutation budget binding does not match")


@dataclass(frozen=True, slots=True)
class AuthorizationConsumptionCommand:
    """Validated facts proposed for one atomic consumption transaction."""

    authorization: GovernanceAuthorization
    mutation_budget: GovernanceMutationBudget
    execution_request: GovernanceExecutionRequest

    def __post_init__(self) -> None:
        _require_exact_type(self.authorization, GovernanceAuthorization, "authorization")
        _require_exact_type(self.mutation_budget, GovernanceMutationBudget, "mutation_budget")
        _require_exact_type(self.execution_request, GovernanceExecutionRequest, "execution_request")

        authorization = self.authorization
        budget = self.mutation_budget
        request = self.execution_request
        if authorization.state is not AuthorizationState.AUTHORIZED:
            raise ValueError("authorization state must be AUTHORIZED")
        if budget.status is not MutationBudgetStatus.AVAILABLE:
            raise ValueError("mutation budget status must be AVAILABLE")
        if budget.authorization_id != authorization.authorization_id:
            raise ValueError("mutation budget authorization binding does not match")
        if request.lifecycle_id != authorization.request.lifecycle_id:
            raise ValueError("execution request lifecycle binding does not match")
        if request.authorization_id != authorization.authorization_id:
            raise ValueError("execution request authorization binding does not match")
        if request.mutation_budget_id != budget.budget_id:
            raise ValueError("execution request mutation budget binding does not match")
        _require_authorization_bindings(authorization, budget, request)

        matches = _matching_line_items(budget, request)
        if len(matches) != 1:
            raise ValueError("action type must match exactly one mutation budget line item")
        matched = matches[0]
        if matched.status is not MutationBudgetStatus.AVAILABLE:
            raise ValueError("matched mutation budget line item must be AVAILABLE")
        if matched.actual_invocation_count != 0:
            raise ValueError("matched mutation budget line item must record zero invocations")


@dataclass(frozen=True, slots=True)
class AuthorizationConsumptionResult:
    """Factual consumption evidence; never authority to invoke an operation."""

    authorization: GovernanceAuthorization
    mutation_budget: GovernanceMutationBudget
    consumption_receipt: GovernanceAuthorizationConsumptionReceipt
    execution_request: GovernanceExecutionRequest

    def __post_init__(self) -> None:
        _require_exact_type(self.authorization, GovernanceAuthorization, "authorization")
        _require_exact_type(self.mutation_budget, GovernanceMutationBudget, "mutation_budget")
        _require_exact_type(
            self.consumption_receipt,
            GovernanceAuthorizationConsumptionReceipt,
            "consumption_receipt",
        )
        _require_exact_type(self.execution_request, GovernanceExecutionRequest, "execution_request")

        authorization = self.authorization
        budget = self.mutation_budget
        receipt = self.consumption_receipt
        request = self.execution_request
        if authorization.state is not AuthorizationState.CONSUMED:
            raise ValueError("authorization state must be CONSUMED")
        if budget.status is not MutationBudgetStatus.CONSUMED:
            raise ValueError("mutation budget status must be exactly CONSUMED")
        if budget.authorization_id != authorization.authorization_id:
            raise ValueError("mutation budget authorization binding does not match")
        if any(item.status is not MutationBudgetStatus.CONSUMED for item in budget.line_items):
            raise ValueError("every mutation budget line item must be CONSUMED")
        if any(item.actual_invocation_count != 0 for item in budget.line_items):
            raise ValueError("every mutation budget line item must record zero invocations")
        if receipt.transaction_status is not ConsumptionTransactionStatus.COMMITTED:
            raise ValueError("consumption receipt transaction must be COMMITTED")
        if receipt.lifecycle_id != authorization.request.lifecycle_id:
            raise ValueError("consumption receipt lifecycle binding does not match")
        if receipt.authorization_id != authorization.authorization_id:
            raise ValueError("consumption receipt authorization binding does not match")
        if receipt.mutation_budget_id != budget.budget_id:
            raise ValueError("consumption receipt mutation budget binding does not match")
        if receipt.execution_request_id != request.execution_request_id:
            raise ValueError("consumption receipt execution request binding does not match")
        if receipt.claim_id != request.claim_id:
            raise ValueError("consumption receipt claim binding does not match")
        if request.lifecycle_id != authorization.request.lifecycle_id:
            raise ValueError("execution request lifecycle binding does not match")
        if request.authorization_id != authorization.authorization_id:
            raise ValueError("execution request authorization binding does not match")
        if request.mutation_budget_id != budget.budget_id:
            raise ValueError("execution request mutation budget binding does not match")
        _require_authorization_bindings(authorization, budget, request)
        if len(_matching_line_items(budget, request)) != 1:
            raise ValueError("action type must match exactly one consumed mutation budget line item")


class AuthorizationConsumptionPort(Protocol):
    """Perform one future atomic durable authorization-consumption transaction.

    A returned result grants no invocation authority. Before invoking a controlled
    execution port, callers must recollect current read-only preconditions and
    receive SEC-02 ALLOW_SINGLE_INVOCATION.
    """

    def consume_once(
        self, command: AuthorizationConsumptionCommand
    ) -> AuthorizationConsumptionResult: ...


__all__ = (
    "AuthorizationConsumptionCommand",
    "AuthorizationConsumptionPort",
    "AuthorizationConsumptionResult",
)
