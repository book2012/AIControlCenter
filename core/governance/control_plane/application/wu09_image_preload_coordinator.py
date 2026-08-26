"""Govern the single, separately-authorized Macro-WU09 image preload."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json

from ..domain import (
    ExecutionStatus,
    GovernanceAuthorization,
    GovernanceExecutionRequest,
    GovernanceMutationBudget,
    GovernancePreconditionSnapshot,
    PostconditionDecision,
    compare_precondition_snapshots,
)
from ..ports.authorization_consumption import (
    AuthorizationConsumptionCommand,
    AuthorizationConsumptionPort,
)
from ..ports.execution import ControlledExecutionPort, PostconditionValidationPort
from ..ports.preconditions import PreconditionObservationPort
from .orchestration_policy import (
    GovernanceOrchestrationContext,
    OrchestrationDisposition,
    decide_next_disposition,
)


WU09_PRELOAD_ACTION_TYPE = "SHOPPING_MARIADB_LOOPBACK_IMAGE:PRELOAD_EXACT"
WU09_PRELOAD_TARGET = "SHOPPING_MARIADB_LOOPBACK_IMAGE"

_PRELOAD_PLAN = {
    "action_type": WU09_PRELOAD_ACTION_TYPE,
    "docker_context": "colima-aicontrolcenter-commerce",
    "image": "alpine/socat@sha256:cc2ab2488d6b39cbac670d18fdca5f87ea44fe630697a09d8558afb17f3269a1",
    "target": WU09_PRELOAD_TARGET,
}


def wu09_preload_plan_digest() -> str:
    payload = json.dumps(_PRELOAD_PLAN, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class WU09PreloadDisposition(StrEnum):
    CLOSEOUT = "CLOSEOUT"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class WU09PreloadLifecycle:
    """Pre-existing authority and expected facts; this grants no authority."""

    authorization: GovernanceAuthorization
    mutation_budget: GovernanceMutationBudget
    execution_request: GovernanceExecutionRequest
    expected_preconditions: GovernancePreconditionSnapshot


@dataclass(frozen=True, slots=True)
class WU09PreloadResult:
    disposition: WU09PreloadDisposition
    reason_codes: tuple[str, ...]
    authorization_consumed: bool = False
    invocation_count: int = 0
    execution_status: ExecutionStatus | None = None
    postcondition_decision: PostconditionDecision | None = None
    wu09_deployment_authorized: bool = False
    wu10_authorized: bool = False
    wu11_authorized: bool = False
    retry_prohibited: bool = True
    rollback_prohibited: bool = True
    compensation_prohibited: bool = True

    def __post_init__(self) -> None:
        if self.invocation_count not in (0, 1):
            raise ValueError("invocation count must be zero or one")
        if not (self.retry_prohibited and self.rollback_prohibited and self.compensation_prohibited):
            raise ValueError("retry, rollback, and compensation must be prohibited")
        if self.wu09_deployment_authorized or self.wu10_authorized or self.wu11_authorized:
            raise ValueError("preload result cannot grant deployment or later-work-unit authority")


class WU09ImagePreloadCoordinator:
    """Cross at most one exact preload boundary after all SEC-02 gates."""

    def __init__(
        self,
        *,
        authorization_consumption: AuthorizationConsumptionPort,
        precondition_observation: PreconditionObservationPort,
        controlled_execution: ControlledExecutionPort,
        postcondition_validation: PostconditionValidationPort,
    ) -> None:
        self._authorization_consumption = authorization_consumption
        self._precondition_observation = precondition_observation
        self._controlled_execution = controlled_execution
        self._postcondition_validation = postcondition_validation

    def coordinate(self, lifecycle: WU09PreloadLifecycle) -> WU09PreloadResult:
        if not isinstance(lifecycle, WU09PreloadLifecycle):
            raise TypeError("lifecycle must be WU09PreloadLifecycle")
        authorization = lifecycle.authorization
        budget = lifecycle.mutation_budget
        request = lifecycle.execution_request
        if (
            request.action_type != WU09_PRELOAD_ACTION_TYPE
            or request.target != WU09_PRELOAD_TARGET
            or request.plan_digest != wu09_preload_plan_digest()
        ):
            return self._stop("PRELOAD_REQUEST_BINDING_MISMATCH")

        try:
            observed = self._precondition_observation.observe_preconditions(authorization.request)
            comparison = compare_precondition_snapshots(
                lifecycle.expected_preconditions, observed
            )
            consumption_decision = decide_next_disposition(
                GovernanceOrchestrationContext(
                    authorization=authorization,
                    precondition_comparison=comparison,
                    mutation_budget=budget,
                    execution_request=request,
                )
            )
        except Exception:
            return self._stop("PRECONSUMPTION_GATE_FAILED")
        if consumption_decision.disposition is not OrchestrationDisposition.ALLOW_AUTHORIZATION_CONSUMPTION:
            return self._stop(*consumption_decision.reason_codes)

        try:
            consumed = self._authorization_consumption.consume_once(
                AuthorizationConsumptionCommand(authorization, budget, request)
            )
        except Exception:
            return self._stop("CONSUMPTION_FAILED")

        try:
            if consumed.execution_request != request:
                return self._stop("CONSUMED_REQUEST_BINDING_MISMATCH", consumed=True)
            observed_after = self._precondition_observation.observe_preconditions(
                consumed.authorization.request
            )
            comparison_after = compare_precondition_snapshots(
                lifecycle.expected_preconditions, observed_after
            )
            invocation_decision = decide_next_disposition(
                GovernanceOrchestrationContext(
                    authorization=consumed.authorization,
                    precondition_comparison=comparison_after,
                    mutation_budget=consumed.mutation_budget,
                    consumption_receipt=consumed.consumption_receipt,
                    execution_request=consumed.execution_request,
                )
            )
        except Exception:
            return self._stop("POSTCONSUMPTION_GATE_FAILED", consumed=True)
        if invocation_decision.disposition is not OrchestrationDisposition.ALLOW_SINGLE_INVOCATION:
            return self._stop(*invocation_decision.reason_codes, consumed=True)

        try:
            execution = self._controlled_execution.invoke_once(request)
        except Exception:
            return self._stop(
                "EXECUTION_UNCERTAIN", consumed=True, invoked=1,
                status=ExecutionStatus.UNCERTAIN,
            )
        if execution.status is not ExecutionStatus.COMPLETED:
            return self._stop(
                f"EXECUTION_{execution.status.value}", consumed=True, invoked=1,
                status=execution.status,
            )

        completed_decision = decide_next_disposition(
            GovernanceOrchestrationContext(
                authorization=consumed.authorization,
                precondition_comparison=comparison_after,
                mutation_budget=consumed.mutation_budget,
                consumption_receipt=consumed.consumption_receipt,
                execution_request=request,
                execution_receipt=execution,
                invocation_already_attempted=True,
            )
        )
        if completed_decision.disposition is not OrchestrationDisposition.REQUIRE_POSTCONDITION_VALIDATION:
            return self._stop(
                *completed_decision.reason_codes, consumed=True, invoked=1,
                status=execution.status,
            )
        try:
            postcondition = self._postcondition_validation.validate_postconditions(execution)
            closeout = decide_next_disposition(
                GovernanceOrchestrationContext(
                    authorization=consumed.authorization,
                    precondition_comparison=comparison_after,
                    mutation_budget=consumed.mutation_budget,
                    consumption_receipt=consumed.consumption_receipt,
                    execution_request=request,
                    execution_receipt=execution,
                    postcondition_report=postcondition,
                    invocation_already_attempted=True,
                )
            )
        except Exception:
            return self._stop(
                "POSTCONDITION_VALIDATION_FAILED", consumed=True, invoked=1,
                status=execution.status,
            )
        disposition = (
            WU09PreloadDisposition.CLOSEOUT
            if closeout.disposition is OrchestrationDisposition.ALLOW_CLOSEOUT
            else WU09PreloadDisposition.STOP
        )
        return WU09PreloadResult(
            disposition, closeout.reason_codes, True, 1, execution.status,
            postcondition.decision,
        )

    @staticmethod
    def _stop(
        *reasons: str,
        consumed: bool = False,
        invoked: int = 0,
        status: ExecutionStatus | None = None,
    ) -> WU09PreloadResult:
        return WU09PreloadResult(
            WU09PreloadDisposition.STOP, tuple(reasons), consumed, invoked, status
        )


__all__ = (
    "WU09ImagePreloadCoordinator", "WU09PreloadDisposition", "WU09PreloadLifecycle",
    "WU09PreloadResult", "WU09_PRELOAD_ACTION_TYPE", "WU09_PRELOAD_TARGET",
    "wu09_preload_plan_digest",
)
