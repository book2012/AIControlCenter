"""Validation-only intake for one exact WU09 Production image preload."""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import AuthorizationState, MutationBudgetStatus
from ..trust.intake import intake_trusted_authorization
from ..trust.models import TrustedAuthorizationFacts
from .wu09_image_preload_coordinator import (
    WU09_PRELOAD_ACTION_TYPE,
    WU09_PRELOAD_TARGET,
    wu09_preload_plan_digest,
)


WU09_PRELOAD_PURPOSE = WU09_PRELOAD_ACTION_TYPE
WU09_PRODUCTION_ENVIRONMENT = "PRODUCTION"


class WU09AuthorizationIntakeError(ValueError):
    """The trusted artifact is not the exact bounded WU09 preload authority."""


@dataclass(frozen=True, slots=True)
class WU09TrustedProductionAuthorization:
    """Validated immutable facts only; this grants no invocation authority."""

    facts: TrustedAuthorizationFacts
    purpose: str = WU09_PRELOAD_PURPOSE
    action_type: str = WU09_PRELOAD_ACTION_TYPE
    target: str = WU09_PRELOAD_TARGET
    environment: str = WU09_PRODUCTION_ENVIRONMENT
    allowed_invocation_count: int = 1
    execution_authorized: bool = False
    retry_authorized: bool = False
    rollback_authorized: bool = False
    ubuntu_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.facts, TrustedAuthorizationFacts):
            raise TypeError("facts must be TrustedAuthorizationFacts")
        if (
            self.purpose != WU09_PRELOAD_PURPOSE
            or self.action_type != WU09_PRELOAD_ACTION_TYPE
            or self.target != WU09_PRELOAD_TARGET
            or self.environment != WU09_PRODUCTION_ENVIRONMENT
            or self.allowed_invocation_count != 1
        ):
            raise ValueError("WU09 intake constants are immutable")
        if any(
            (
                self.execution_authorized,
                self.retry_authorized,
                self.rollback_authorized,
                self.ubuntu_authorized,
            )
        ):
            raise ValueError("validation-only intake cannot grant authority")


def intake_wu09_trusted_production_authorization(
    raw_envelope: bytes,
) -> WU09TrustedProductionAuthorization:
    """Verify and freeze exact WU09 facts without consuming or invoking."""

    return _validate_wu09_facts(intake_trusted_authorization(raw_envelope))


def _validate_wu09_facts(
    facts: TrustedAuthorizationFacts,
) -> WU09TrustedProductionAuthorization:
    if not isinstance(facts, TrustedAuthorizationFacts):
        raise WU09AuthorizationIntakeError("trusted authorization facts are required")

    authorization = facts.authorization
    request = authorization.request
    receipt = authorization.receipt
    budget = facts.mutation_budget
    execution = facts.execution_request
    line_items = budget.line_items

    if request.operation_type != WU09_PRELOAD_PURPOSE:
        raise WU09AuthorizationIntakeError("wrong WU09 authorization purpose")
    if request.environment != WU09_PRODUCTION_ENVIRONMENT:
        raise WU09AuthorizationIntakeError("wrong WU09 authorization environment")
    if request.target != WU09_PRELOAD_TARGET:
        raise WU09AuthorizationIntakeError("wrong WU09 authorization target")
    if request.requested_scope != (WU09_PRELOAD_ACTION_TYPE,):
        raise WU09AuthorizationIntakeError("WU09 requested scope is not exact")
    if (
        authorization.state is not AuthorizationState.AUTHORIZED
        or receipt is None
        or receipt.approved_scope != (WU09_PRELOAD_ACTION_TYPE,)
    ):
        raise WU09AuthorizationIntakeError("WU09 approved authority is not exact and fresh")
    if (
        budget.status is not MutationBudgetStatus.AVAILABLE
        or len(line_items) != 1
        or line_items[0].action_type != WU09_PRELOAD_ACTION_TYPE
        or line_items[0].allowed_count != 1
        or line_items[0].actual_invocation_count != 0
        or line_items[0].remaining_count != 1
    ):
        raise WU09AuthorizationIntakeError("WU09 mutation budget is not pristine and bounded")
    if (
        execution.action_type != WU09_PRELOAD_ACTION_TYPE
        or execution.target != WU09_PRELOAD_TARGET
        or execution.plan_digest != wu09_preload_plan_digest()
    ):
        raise WU09AuthorizationIntakeError("WU09 execution intent binding is not exact")
    if (
        request.requester.identity_type != "HUMAN"
        or authorization.decision is None
        or authorization.decision.approver.identity_type != "HUMAN"
        or facts.expected_operator.identity_type != "MAC_LOCAL_OPERATOR_V1"
    ):
        raise WU09AuthorizationIntakeError("WU09 human/Mac authority roles are not exact")

    return WU09TrustedProductionAuthorization(facts=facts)


__all__ = (
    "WU09AuthorizationIntakeError",
    "WU09TrustedProductionAuthorization",
    "WU09_PRELOAD_PURPOSE",
    "WU09_PRODUCTION_ENVIRONMENT",
    "intake_wu09_trusted_production_authorization",
)
