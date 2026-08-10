from dataclasses import replace

import pytest

from core.governance.control_plane.domain import (
    GovernanceMutationBudget,
    InvalidMutationCountInvariant,
    InvalidMutationInvocationOutcome,
    InvocationBeforeAuthorizationConsumption,
    MutationBudgetExhausted,
    MutationBudgetLineItem,
    MutationBudgetViolated,
    MutationInvocationCountExceeded,
    MutationInvocationOutcome,
    RepeatedAuthorizationConsumption,
    UnknownMutationActionType,
    account_mutation_invocation,
    consume_mutation_budget,
    mark_mutation_budget_violated,
)


def budget(allowed: int = 1) -> GovernanceMutationBudget:
    return GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", allowed),),
    )


def test_invocation_before_consumption_fails() -> None:
    with pytest.raises(InvocationBeforeAuthorizationConsumption):
        account_mutation_invocation(
            budget(), "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED,
        )


def test_repeated_consumption_fails() -> None:
    with pytest.raises(RepeatedAuthorizationConsumption):
        consume_mutation_budget(consume_mutation_budget(budget()))


def test_unknown_action_fails_without_payload_dump() -> None:
    value = consume_mutation_budget(budget())
    with pytest.raises(UnknownMutationActionType) as captured:
        account_mutation_invocation(
            value, "SECRET_LIKE_UNKNOWN", MutationInvocationOutcome.COMPLETED,
        )
    message = str(captured.value)
    assert "SECRET_LIKE_UNKNOWN" not in message
    assert "GovernanceMutationBudget(" not in message


def test_over_budget_line_item_fails_even_when_composite_budget_remains() -> None:
    value = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (
            MutationBudgetLineItem("SERVICE_RESTART", 1),
            MutationBudgetLineItem("RUNTIME_ACTIVATE", 1),
        ),
    )
    value = account_mutation_invocation(
        consume_mutation_budget(value), "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED,
    )
    with pytest.raises(MutationInvocationCountExceeded):
        account_mutation_invocation(
            value, "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED,
        )


def test_exhausted_budget_cannot_be_reused() -> None:
    value = account_mutation_invocation(
        consume_mutation_budget(budget()), "SERVICE_RESTART",
        MutationInvocationOutcome.CONFIRMED_ZERO_EFFECT,
    )
    with pytest.raises(MutationBudgetExhausted):
        account_mutation_invocation(
            value, "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED,
        )


def test_violated_budget_is_terminal_and_preserves_counts() -> None:
    consumed = consume_mutation_budget(budget(2))
    accounted = account_mutation_invocation(
        consumed, "SERVICE_RESTART", MutationInvocationOutcome.UNCERTAIN,
    )
    violated = mark_mutation_budget_violated(accounted, "ACCOUNTING_UNPROVABLE")
    assert violated.line_items[0].actual_invocation_count == 1
    assert violated.line_items[0].uncertain_count == 1
    with pytest.raises(MutationBudgetViolated):
        account_mutation_invocation(
            violated, "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED,
        )
    with pytest.raises(MutationBudgetViolated):
        mark_mutation_budget_violated(violated, "SECOND_REASON")


@pytest.mark.parametrize(
    "changes",
    [
        {"actual_invocation_count": -1},
        {"completed_count": 2, "actual_invocation_count": 1},
        {"uncertain_count": 2, "actual_invocation_count": 1},
        {"completed_count": 1, "uncertain_count": 1, "actual_invocation_count": 1},
    ],
)
def test_invalid_counts_fail_closed(changes: dict[str, int]) -> None:
    with pytest.raises(InvalidMutationCountInvariant):
        replace(MutationBudgetLineItem("SERVICE_RESTART", 3), **changes)


def test_invalid_outcome_fails_closed() -> None:
    with pytest.raises(InvalidMutationInvocationOutcome):
        account_mutation_invocation(
            consume_mutation_budget(budget()), "SERVICE_RESTART", "COMPLETED",  # type: ignore[arg-type]
        )


def test_no_automatic_retry_or_rollback_api() -> None:
    value = consume_mutation_budget(budget())
    for forbidden in ("retry", "retry_allowed", "rollback", "compensate"):
        assert not hasattr(value, forbidden)
