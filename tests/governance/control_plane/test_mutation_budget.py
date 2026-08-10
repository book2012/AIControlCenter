import json
from dataclasses import FrozenInstanceError

import pytest

from core.governance.control_plane.domain import (
    DuplicateMutationActionType,
    GovernanceMutationBudget,
    InvalidMutationBudgetModel,
    InvalidMutationCountInvariant,
    MutationBudgetLineItem,
    MutationBudgetStatus,
)


def budget(*items: MutationBudgetLineItem) -> GovernanceMutationBudget:
    return GovernanceMutationBudget("1.0.0", "budget-1", "authorization-1", items)


def test_budget_and_line_items_are_immutable_and_initially_available() -> None:
    value = budget(MutationBudgetLineItem("SERVICE_RESTART", 1))
    assert value.status is MutationBudgetStatus.AVAILABLE
    assert value.line_items[0].status is MutationBudgetStatus.AVAILABLE
    with pytest.raises(FrozenInstanceError):
        value.status = MutationBudgetStatus.CONSUMED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        value.line_items[0].allowed_count = 2  # type: ignore[misc]


@pytest.mark.parametrize("action_type", ["", "MUTATE", "WRITE", "service restart"])
def test_action_type_must_be_an_explicit_stable_capability(action_type: str) -> None:
    with pytest.raises(InvalidMutationBudgetModel) as captured:
        MutationBudgetLineItem(action_type, 1)
    assert "MutationBudgetLineItem(" not in str(captured.value)


def test_duplicate_action_types_fail_closed() -> None:
    with pytest.raises(DuplicateMutationActionType):
        budget(
            MutationBudgetLineItem("SERVICE_RESTART", 1),
            MutationBudgetLineItem("SERVICE_RESTART", 2),
        )


@pytest.mark.parametrize("count", [0, -1, True, 1.5])
def test_allowed_count_must_be_a_positive_integer(count: object) -> None:
    with pytest.raises(InvalidMutationCountInvariant):
        MutationBudgetLineItem("SERVICE_RESTART", count)  # type: ignore[arg-type]


def test_order_projection_and_remaining_count_are_deterministic() -> None:
    value = budget(
        MutationBudgetLineItem("RUNTIME_ACTIVATE", 2),
        MutationBudgetLineItem("SERVICE_RESTART", 1),
    )
    assert [item.action_type for item in value.line_items] == [
        "RUNTIME_ACTIVATE", "SERVICE_RESTART"
    ]
    assert value.remaining_count == 3
    first = value.to_dict()
    assert first == value.to_dict()
    assert json.loads(json.dumps(first)) == first
    assert [item["action_type"] for item in first["line_items"]] == [
        "RUNTIME_ACTIVATE", "SERVICE_RESTART"
    ]


def test_multiple_line_items_have_independent_counts() -> None:
    value = budget(
        MutationBudgetLineItem("SERVICE_RESTART", 1),
        MutationBudgetLineItem("RUNTIME_ACTIVATE", 2),
    )
    assert value.line_items[0].remaining_count == 2
    assert value.line_items[1].remaining_count == 1
