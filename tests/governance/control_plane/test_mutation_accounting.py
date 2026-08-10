from core.governance.control_plane.domain import (
    GovernanceMutationBudget,
    MutationBudgetLineItem,
    MutationBudgetStatus,
    MutationInvocationOutcome,
    account_mutation_invocation,
    consume_mutation_budget,
)


def budget(allowed: int = 3) -> GovernanceMutationBudget:
    return GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (MutationBudgetLineItem("SERVICE_RESTART", allowed),),
    )


def test_consumption_is_distinct_from_invocation() -> None:
    original = budget()
    consumed = consume_mutation_budget(original)
    assert original.status is MutationBudgetStatus.AVAILABLE
    assert consumed.status is MutationBudgetStatus.CONSUMED
    assert consumed.line_items[0].actual_invocation_count == 0
    assert consumed.remaining_count == 3


def test_completed_accounting() -> None:
    result = account_mutation_invocation(
        consume_mutation_budget(budget()), "SERVICE_RESTART",
        MutationInvocationOutcome.COMPLETED,
    )
    assert result.line_items[0].actual_invocation_count == 1
    assert result.line_items[0].completed_count == 1
    assert result.line_items[0].uncertain_count == 0


def test_confirmed_zero_effect_still_accounts_invocation() -> None:
    result = account_mutation_invocation(
        consume_mutation_budget(budget()), "SERVICE_RESTART",
        MutationInvocationOutcome.CONFIRMED_ZERO_EFFECT,
    )
    assert result.line_items[0].actual_invocation_count == 1
    assert result.line_items[0].completed_count == 0
    assert result.line_items[0].uncertain_count == 0


def test_uncertain_accounting() -> None:
    result = account_mutation_invocation(
        consume_mutation_budget(budget()), "SERVICE_RESTART",
        MutationInvocationOutcome.UNCERTAIN,
    )
    assert result.line_items[0].actual_invocation_count == 1
    assert result.line_items[0].completed_count == 0
    assert result.line_items[0].uncertain_count == 1


def test_exact_total_boundary_exhausts_budget() -> None:
    result = account_mutation_invocation(
        consume_mutation_budget(budget(1)), "SERVICE_RESTART",
        MutationInvocationOutcome.CONFIRMED_ZERO_EFFECT,
    )
    assert result.status is MutationBudgetStatus.EXHAUSTED
    assert result.line_items[0].status is MutationBudgetStatus.EXHAUSTED
    assert result.remaining_count == 0


def test_composite_accounting_isolated_and_inputs_unchanged() -> None:
    original = GovernanceMutationBudget(
        "1.0.0", "budget-1", "authorization-1",
        (
            MutationBudgetLineItem("SERVICE_RESTART", 1),
            MutationBudgetLineItem("RUNTIME_ACTIVATE", 1),
        ),
    )
    consumed = consume_mutation_budget(original)
    result = account_mutation_invocation(
        consumed, "SERVICE_RESTART", MutationInvocationOutcome.COMPLETED,
    )
    by_action = {item.action_type: item for item in result.line_items}
    assert by_action["SERVICE_RESTART"].actual_invocation_count == 1
    assert by_action["RUNTIME_ACTIVATE"].actual_invocation_count == 0
    assert result.status is MutationBudgetStatus.CONSUMED
    assert original.status is MutationBudgetStatus.AVAILABLE
    assert consumed.line_items[1].actual_invocation_count == 0


def test_remaining_count_is_not_retry_authority() -> None:
    result = account_mutation_invocation(
        consume_mutation_budget(budget()), "SERVICE_RESTART",
        MutationInvocationOutcome.UNCERTAIN,
    )
    assert result.remaining_count == 2
    assert not hasattr(result, "retry_allowed")
    assert not hasattr(result, "retry")
