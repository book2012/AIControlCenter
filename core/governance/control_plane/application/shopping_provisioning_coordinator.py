"""Govern Shopping provisioning through existing SEC-02 boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json

from core.secrets.provisioning import ProvisioningPlan, Readiness

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


SHOPPING_SECRET_PROVISIONING = "SHOPPING_SECRET_PROVISIONING"
SOPS_INSTALL_ENSURE = "SHOPPING_SECRET_TOOL:SOPS_INSTALL_ENSURE"
AGE_INSTALL_ENSURE = "SHOPPING_SECRET_TOOL:AGE_INSTALL_ENSURE"
CONTROL_PLANE_IDENTITY_CREATE = "SHOPPING_SECRET_IDENTITY:CONTROL_PLANE_CREATE"
CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE = (
    "SHOPPING_SECRET_RECIPIENT:CONTROL_PLANE_REGISTER_VALIDATE"
)
OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE = (
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_REGISTER_VALIDATE"
)
OFFLINE_RECOVERY_RECIPIENT_INTAKE = (
    "SHOPPING_SECRET_RECIPIENT:OFFLINE_RECOVERY_INTAKE"
)
PROVISIONING_ACTIONS = (
    SOPS_INSTALL_ENSURE,
    AGE_INSTALL_ENSURE,
    CONTROL_PLANE_IDENTITY_CREATE,
    CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE,
    OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE,
    OFFLINE_RECOVERY_RECIPIENT_INTAKE,
)


class CoordinatorDisposition(StrEnum):
    CLOSEOUT = "CLOSEOUT"
    STOP = "STOP"


@dataclass(frozen=True, slots=True)
class ShoppingProvisioningLifecycle:
    """Already explicit human-authorized facts; constructing this grants nothing."""

    authorization: GovernanceAuthorization
    mutation_budget: GovernanceMutationBudget
    execution_request: GovernanceExecutionRequest
    expected_preconditions: GovernancePreconditionSnapshot


@dataclass(frozen=True, slots=True)
class ShoppingProvisioningResult:
    """Value-free closeout facts with no authorization or execution capability."""

    disposition: CoordinatorDisposition
    readiness: Readiness
    action: str
    reason_codes: tuple[str, ...]
    authorization_consumed: bool = False
    invocation_count: int = 0
    execution_status: ExecutionStatus | None = None
    postcondition_decision: PostconditionDecision | None = None
    retry_prohibited: bool = True
    rollback_prohibited: bool = True
    compensation_prohibited: bool = True
    secret_values_read: bool = False

    def __post_init__(self) -> None:
        if self.retry_prohibited is not True or self.rollback_prohibited is not True:
            raise ValueError("retry and rollback must be prohibited")
        if self.compensation_prohibited is not True:
            raise ValueError("compensation must be prohibited")
        if self.secret_values_read is not False:
            raise ValueError("secret values must not be read")
        if self.invocation_count not in (0, 1):
            raise ValueError("invocation count must be zero or one")

    def to_dict(self) -> dict[str, object]:
        return {
            "disposition": self.disposition.value,
            "readiness": self.readiness.value,
            "action": self.action,
            "reason_codes": list(self.reason_codes),
            "authorization_consumed": self.authorization_consumed,
            "invocation_count": self.invocation_count,
            "execution_status": self.execution_status.value if self.execution_status else None,
            "postcondition_decision": (
                self.postcondition_decision.value if self.postcondition_decision else None
            ),
            "retry_prohibited": self.retry_prohibited,
            "rollback_prohibited": self.rollback_prohibited,
            "compensation_prohibited": self.compensation_prohibited,
            "secret_values_read": self.secret_values_read,
        }


def provisioning_plan_digest(plan: ProvisioningPlan) -> str:
    """Bind the execution request to the exact value-free planner output."""
    if not isinstance(plan, ProvisioningPlan):
        raise TypeError("plan must be ProvisioningPlan")
    payload = json.dumps(
        plan.to_dict(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class ShoppingProvisioningGovernanceCoordinator:
    def __init__(
        self,
        *,
        authorization_consumption: AuthorizationConsumptionPort,
        precondition_observation: PreconditionObservationPort,
        postcondition_validation: PostconditionValidationPort,
        sops_install: ControlledExecutionPort,
        age_install: ControlledExecutionPort,
        control_plane_identity_create: ControlledExecutionPort,
        control_plane_recipient_register_validate: ControlledExecutionPort,
        offline_recovery_recipient_intake: ControlledExecutionPort,
        offline_recovery_recipient_register_validate: ControlledExecutionPort,
    ) -> None:
        self._authorization_consumption = authorization_consumption
        self._precondition_observation = precondition_observation
        self._postcondition_validation = postcondition_validation
        self._execution_ports = {
            SOPS_INSTALL_ENSURE: sops_install,
            AGE_INSTALL_ENSURE: age_install,
            CONTROL_PLANE_IDENTITY_CREATE: control_plane_identity_create,
            CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE: (
                control_plane_recipient_register_validate
            ),
            OFFLINE_RECOVERY_RECIPIENT_INTAKE: offline_recovery_recipient_intake,
            OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE: (
                offline_recovery_recipient_register_validate
            ),
        }

    def coordinate(
        self,
        plan: ProvisioningPlan,
        lifecycle: ShoppingProvisioningLifecycle | None = None,
    ) -> ShoppingProvisioningResult:
        if not isinstance(plan, ProvisioningPlan):
            raise TypeError("plan must be ProvisioningPlan")
        if plan.current_readiness is Readiness.READY:
            return self._result(plan, CoordinatorDisposition.CLOSEOUT, "PLAN_ALREADY_READY")
        if plan.current_readiness in (Readiness.BLOCKED, Readiness.MALFORMED):
            return self._result(
                plan, CoordinatorDisposition.STOP, f"PLAN_{plan.current_readiness.value}"
            )
        if lifecycle is None or not isinstance(lifecycle, ShoppingProvisioningLifecycle):
            return self._result(plan, CoordinatorDisposition.STOP, "AUTHORIZATION_PATH_INVALID")
        if plan.action not in self._execution_ports:
            return self._result(plan, CoordinatorDisposition.STOP, "ACTION_NOT_SUPPORTED")

        request = lifecycle.execution_request
        authorization = lifecycle.authorization
        budget = lifecycle.mutation_budget
        if (
            request.action_type != plan.action
            or request.target != SHOPPING_SECRET_PROVISIONING
            or request.plan_digest != provisioning_plan_digest(plan)
        ):
            return self._result(plan, CoordinatorDisposition.STOP, "PLAN_BINDING_MISMATCH")

        try:
            observed = self._precondition_observation.observe_preconditions(
                authorization.request
            )
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
            return self._result(plan, CoordinatorDisposition.STOP, "PRECONSUMPTION_GATE_FAILED")
        if (
            consumption_decision.disposition
            is not OrchestrationDisposition.ALLOW_AUTHORIZATION_CONSUMPTION
        ):
            return self._result(
                plan, CoordinatorDisposition.STOP, *consumption_decision.reason_codes
            )

        try:
            consumed = self._authorization_consumption.consume_once(
                AuthorizationConsumptionCommand(authorization, budget, request)
            )
        except Exception:
            return self._result(plan, CoordinatorDisposition.STOP, "CONSUMPTION_FAILED")

        # Consumption evidence is not invocation authority. Re-observe and ask SEC-02.
        try:
            if consumed.execution_request != request:
                return self._result(
                    plan, CoordinatorDisposition.STOP, "CONSUMED_REQUEST_BINDING_MISMATCH",
                    consumed=True,
                )
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
            return self._result(
                plan, CoordinatorDisposition.STOP, "POSTCONSUMPTION_GATE_FAILED",
                consumed=True,
            )
        if (
            invocation_decision.disposition
            is not OrchestrationDisposition.ALLOW_SINGLE_INVOCATION
        ):
            return self._result(
                plan, CoordinatorDisposition.STOP, *invocation_decision.reason_codes,
                consumed=True,
            )

        try:
            execution = self._execution_ports[plan.action].invoke_once(request)
        except Exception:
            return self._result(
                plan, CoordinatorDisposition.STOP, "EXECUTION_UNCERTAIN",
                consumed=True, invoked=1, status=ExecutionStatus.UNCERTAIN,
            )

        if execution.status is ExecutionStatus.FAILED:
            return self._result(
                plan, CoordinatorDisposition.STOP, "EXECUTION_FAILED",
                consumed=True, invoked=1, status=execution.status,
            )
        if execution.status is ExecutionStatus.UNCERTAIN:
            return self._result(
                plan, CoordinatorDisposition.STOP, "EXECUTION_UNCERTAIN",
                consumed=True, invoked=1, status=execution.status,
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
        if (
            completed_decision.disposition
            is not OrchestrationDisposition.REQUIRE_POSTCONDITION_VALIDATION
        ):
            return self._result(
                plan, CoordinatorDisposition.STOP, *completed_decision.reason_codes,
                consumed=True, invoked=1, status=execution.status,
            )
        try:
            postcondition = self._postcondition_validation.validate_postconditions(execution)
            closeout_decision = decide_next_disposition(
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
            return self._result(
                plan, CoordinatorDisposition.STOP, "POSTCONDITION_VALIDATION_FAILED",
                consumed=True, invoked=1, status=execution.status,
            )
        disposition = (
            CoordinatorDisposition.CLOSEOUT
            if closeout_decision.disposition is OrchestrationDisposition.ALLOW_CLOSEOUT
            else CoordinatorDisposition.STOP
        )
        return self._result(
            plan, disposition, *closeout_decision.reason_codes,
            consumed=True, invoked=1, status=execution.status,
            postcondition=postcondition.decision,
        )

    @staticmethod
    def _result(
        plan: ProvisioningPlan,
        disposition: CoordinatorDisposition,
        *reason_codes: str,
        consumed: bool = False,
        invoked: int = 0,
        status: ExecutionStatus | None = None,
        postcondition: PostconditionDecision | None = None,
    ) -> ShoppingProvisioningResult:
        return ShoppingProvisioningResult(
            disposition=disposition,
            readiness=plan.current_readiness,
            action=plan.action,
            reason_codes=tuple(reason_codes),
            authorization_consumed=consumed,
            invocation_count=invoked,
            execution_status=status,
            postcondition_decision=postcondition,
        )


__all__ = (
    "AGE_INSTALL_ENSURE",
    "CONTROL_PLANE_IDENTITY_CREATE",
    "CONTROL_PLANE_RECIPIENT_REGISTER_VALIDATE",
    "CoordinatorDisposition",
    "OFFLINE_RECOVERY_RECIPIENT_REGISTER_VALIDATE",
    "OFFLINE_RECOVERY_RECIPIENT_INTAKE",
    "PROVISIONING_ACTIONS",
    "SHOPPING_SECRET_PROVISIONING",
    "SOPS_INSTALL_ENSURE",
    "ShoppingProvisioningGovernanceCoordinator",
    "ShoppingProvisioningLifecycle",
    "ShoppingProvisioningResult",
    "provisioning_plan_digest",
)
