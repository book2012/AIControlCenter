"""Pure immutable SEC-02 mutation-budget and invocation accounting."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
import re
from typing import Any

from .failures import (
    DuplicateMutationActionType,
    InvalidMutationBudgetModel,
    InvalidMutationCountInvariant,
    InvalidMutationInvocationOutcome,
    InvocationBeforeAuthorizationConsumption,
    MutationBudgetExhausted,
    MutationBudgetViolated,
    MutationInvocationCountExceeded,
    RepeatedAuthorizationConsumption,
    UnknownMutationActionType,
)


class MutationBudgetStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    CONSUMED = "CONSUMED"
    EXHAUSTED = "EXHAUSTED"
    VIOLATED = "VIOLATED"


class MutationInvocationOutcome(StrEnum):
    COMPLETED = "COMPLETED"
    CONFIRMED_ZERO_EFFECT = "CONFIRMED_ZERO_EFFECT"
    UNCERTAIN = "UNCERTAIN"


_ACTION_TYPE = re.compile(r"^[A-Z][A-Z0-9]*(?:[_:.][A-Z0-9]+)+$")
_REASON_CODE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
_GENERIC_ACTION_TYPES = frozenset({"ACTION", "EXECUTE", "MUTATE", "WRITE"})


def _require_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidMutationBudgetModel(f"{field_name} must not be empty")
    if value != value.strip():
        raise InvalidMutationBudgetModel(f"{field_name} must be canonical text")
    return value


def _require_count(value: int, field_name: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidMutationCountInvariant(f"{field_name} must be an integer")
    if value < 0 or (positive and value == 0):
        qualifier = "greater than zero" if positive else "non-negative"
        raise InvalidMutationCountInvariant(f"{field_name} must be {qualifier}")
    return value


def _require_action_type(value: str) -> str:
    _require_text(value, "action_type")
    if value in _GENERIC_ACTION_TYPES or _ACTION_TYPE.fullmatch(value) is None:
        raise InvalidMutationBudgetModel("action_type must be an explicit stable capability identifier")
    return value


def _require_reason_code(value: str) -> str:
    _require_text(value, "reason_code")
    if _REASON_CODE.fullmatch(value) is None:
        raise InvalidMutationBudgetModel("reason_code must be a stable code")
    return value


@dataclass(frozen=True, slots=True)
class MutationBudgetLineItem:
    action_type: str
    allowed_count: int
    actual_invocation_count: int = 0
    completed_count: int = 0
    uncertain_count: int = 0
    status: MutationBudgetStatus = MutationBudgetStatus.AVAILABLE

    def __post_init__(self) -> None:
        _require_action_type(self.action_type)
        _require_count(self.allowed_count, "allowed_count", positive=True)
        _require_count(self.actual_invocation_count, "actual_invocation_count")
        _require_count(self.completed_count, "completed_count")
        _require_count(self.uncertain_count, "uncertain_count")
        if not isinstance(self.status, MutationBudgetStatus):
            raise InvalidMutationBudgetModel("line item status must be MutationBudgetStatus")
        if self.actual_invocation_count > self.allowed_count and self.status is not MutationBudgetStatus.VIOLATED:
            raise InvalidMutationCountInvariant("actual_invocation_count exceeds allowed_count")
        if self.completed_count > self.actual_invocation_count:
            raise InvalidMutationCountInvariant("completed_count exceeds actual_invocation_count")
        if self.uncertain_count > self.actual_invocation_count:
            raise InvalidMutationCountInvariant("uncertain_count exceeds actual_invocation_count")
        if self.completed_count + self.uncertain_count > self.actual_invocation_count:
            raise InvalidMutationCountInvariant("completed_count plus uncertain_count exceeds actual_invocation_count")
        if self.status is MutationBudgetStatus.AVAILABLE and self.actual_invocation_count != 0:
            raise InvalidMutationCountInvariant("available line item cannot contain invocations")
        if self.status is MutationBudgetStatus.EXHAUSTED and self.actual_invocation_count != self.allowed_count:
            raise InvalidMutationCountInvariant("exhausted line item must be at its allowed boundary")
        if self.status is MutationBudgetStatus.CONSUMED and self.actual_invocation_count >= self.allowed_count:
            raise InvalidMutationCountInvariant("consumed line item must have remaining count")

    @property
    def remaining_count(self) -> int:
        """Return accounting remainder only; this is never retry authority."""
        return max(0, self.allowed_count - self.actual_invocation_count)

    def to_dict(self) -> dict[str, str | int]:
        return {
            "action_type": self.action_type,
            "allowed_count": self.allowed_count,
            "actual_invocation_count": self.actual_invocation_count,
            "completed_count": self.completed_count,
            "uncertain_count": self.uncertain_count,
            "remaining_count": self.remaining_count,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class GovernanceMutationBudget:
    schema_version: str
    budget_id: str
    authorization_id: str
    line_items: tuple[MutationBudgetLineItem, ...]
    status: MutationBudgetStatus = MutationBudgetStatus.AVAILABLE
    violation_reason_code: str | None = None

    def __post_init__(self) -> None:
        for name in ("schema_version", "budget_id", "authorization_id"):
            _require_text(getattr(self, name), name)
        if not isinstance(self.line_items, tuple) or not self.line_items:
            raise InvalidMutationBudgetModel("line_items must be a non-empty tuple")
        if any(not isinstance(item, MutationBudgetLineItem) for item in self.line_items):
            raise InvalidMutationBudgetModel("line_items must contain MutationBudgetLineItem values")
        action_types = tuple(item.action_type for item in self.line_items)
        if len(set(action_types)) != len(action_types):
            raise DuplicateMutationActionType("line_items contain a duplicate action_type")
        object.__setattr__(self, "line_items", tuple(sorted(self.line_items, key=lambda item: item.action_type)))
        if not isinstance(self.status, MutationBudgetStatus):
            raise InvalidMutationBudgetModel("budget status must be MutationBudgetStatus")
        if self.status is MutationBudgetStatus.VIOLATED:
            _require_reason_code(self.violation_reason_code)
            if any(item.status is not MutationBudgetStatus.VIOLATED for item in self.line_items):
                raise InvalidMutationBudgetModel("violated budget requires violated line items")
        elif self.violation_reason_code is not None:
            raise InvalidMutationBudgetModel("usable budget cannot contain a violation reason")
        elif any(item.status is MutationBudgetStatus.VIOLATED for item in self.line_items):
            raise InvalidMutationBudgetModel("violated line item requires violated budget")
        elif self.status is MutationBudgetStatus.AVAILABLE:
            if any(item.status is not MutationBudgetStatus.AVAILABLE for item in self.line_items):
                raise InvalidMutationBudgetModel("available budget requires available line items")
        elif self.status is MutationBudgetStatus.CONSUMED:
            if any(item.status not in {MutationBudgetStatus.CONSUMED, MutationBudgetStatus.EXHAUSTED} for item in self.line_items):
                raise InvalidMutationBudgetModel("consumed budget has inconsistent line item status")
            if all(item.status is MutationBudgetStatus.EXHAUSTED for item in self.line_items):
                raise InvalidMutationBudgetModel("fully used budget must be exhausted")
        elif self.status is MutationBudgetStatus.EXHAUSTED:
            if any(item.status is not MutationBudgetStatus.EXHAUSTED for item in self.line_items):
                raise InvalidMutationBudgetModel("exhausted budget requires exhausted line items")

    @property
    def remaining_count(self) -> int:
        """Return total accounting remainder only; this is never retry authority."""
        return sum(item.remaining_count for item in self.line_items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "budget_id": self.budget_id,
            "authorization_id": self.authorization_id,
            "status": self.status.value,
            "line_items": [item.to_dict() for item in self.line_items],
            "remaining_count": self.remaining_count,
            "violation_reason_code": self.violation_reason_code,
        }


def consume_mutation_budget(budget: GovernanceMutationBudget) -> GovernanceMutationBudget:
    """Irreversibly mark authorization consumed without recording an invocation."""
    if not isinstance(budget, GovernanceMutationBudget):
        raise InvalidMutationBudgetModel("budget must be GovernanceMutationBudget")
    if budget.status is MutationBudgetStatus.VIOLATED:
        raise MutationBudgetViolated("violated budget cannot be consumed")
    if budget.status is MutationBudgetStatus.EXHAUSTED:
        raise MutationBudgetExhausted("exhausted budget cannot be consumed")
    if budget.status is MutationBudgetStatus.CONSUMED:
        raise RepeatedAuthorizationConsumption("authorization consumption is irreversible")
    return replace(
        budget,
        status=MutationBudgetStatus.CONSUMED,
        line_items=tuple(replace(item, status=MutationBudgetStatus.CONSUMED) for item in budget.line_items),
    )


def account_mutation_invocation(
    budget: GovernanceMutationBudget,
    action_type: str,
    outcome: MutationInvocationOutcome,
) -> GovernanceMutationBudget:
    """Account for exactly one already-crossed typed adapter invocation boundary."""
    if not isinstance(budget, GovernanceMutationBudget):
        raise InvalidMutationBudgetModel("budget must be GovernanceMutationBudget")
    if budget.status is MutationBudgetStatus.VIOLATED:
        raise MutationBudgetViolated("violated budget cannot account an invocation")
    if budget.status is MutationBudgetStatus.EXHAUSTED:
        raise MutationBudgetExhausted("exhausted budget cannot account an invocation")
    if budget.status is MutationBudgetStatus.AVAILABLE:
        raise InvocationBeforeAuthorizationConsumption("authorization must be consumed before invocation")
    if not isinstance(outcome, MutationInvocationOutcome):
        raise InvalidMutationInvocationOutcome("outcome must be MutationInvocationOutcome")
    if not isinstance(action_type, str):
        raise UnknownMutationActionType("action_type does not match an authorized line item")
    target = next((item for item in budget.line_items if item.action_type == action_type), None)
    if target is None:
        raise UnknownMutationActionType("action_type does not match an authorized line item")
    if target.actual_invocation_count >= target.allowed_count:
        raise MutationInvocationCountExceeded("authorized invocation count would be exceeded")

    actual = target.actual_invocation_count + 1
    completed = target.completed_count + (outcome is MutationInvocationOutcome.COMPLETED)
    uncertain = target.uncertain_count + (outcome is MutationInvocationOutcome.UNCERTAIN)
    target_status = (
        MutationBudgetStatus.EXHAUSTED
        if actual == target.allowed_count
        else MutationBudgetStatus.CONSUMED
    )
    updated_target = replace(
        target,
        actual_invocation_count=actual,
        completed_count=completed,
        uncertain_count=uncertain,
        status=target_status,
    )
    line_items = tuple(updated_target if item.action_type == action_type else item for item in budget.line_items)
    budget_status = (
        MutationBudgetStatus.EXHAUSTED
        if all(item.status is MutationBudgetStatus.EXHAUSTED for item in line_items)
        else MutationBudgetStatus.CONSUMED
    )
    return replace(budget, line_items=line_items, status=budget_status)


def mark_mutation_budget_violated(
    budget: GovernanceMutationBudget,
    reason_code: str,
) -> GovernanceMutationBudget:
    """Record an explicit terminal safety incident without compensation."""
    if not isinstance(budget, GovernanceMutationBudget):
        raise InvalidMutationBudgetModel("budget must be GovernanceMutationBudget")
    if budget.status is MutationBudgetStatus.VIOLATED:
        raise MutationBudgetViolated("violated budget is terminal")
    _require_reason_code(reason_code)
    return replace(
        budget,
        status=MutationBudgetStatus.VIOLATED,
        violation_reason_code=reason_code,
        line_items=tuple(replace(item, status=MutationBudgetStatus.VIOLATED) for item in budget.line_items),
    )
