"""Pure deterministic M4-A1 architecture planner."""

from __future__ import annotations

from dataclasses import replace

from core.deployment.contracts import sha256_digest

from .models import (
    TASK,
    ControlledActivationArchitectureDecision,
    ControlledActivationPlan,
    ControlledActivationPlanRequest,
    ControlledActivationPlanStep,
)
from .architecture_policy import validate_plan_request
from .registry import CANONICAL_CAPABILITY_ORDER, CAPABILITY_BY_ID


class ControlledActivationPlanner:
    """Builds requirements only and cannot authorize, permit, claim, or activate."""

    def plan(self, request: ControlledActivationPlanRequest) -> ControlledActivationPlan:
        requested = set(validate_plan_request(request))
        ordered = tuple(item for item in CANONICAL_CAPABILITY_ORDER if item in requested)
        steps = tuple(
            ControlledActivationPlanStep(
                sequence=index,
                capability=capability,
                required_gates=(
                    "EXACT_GIT_BINDING",
                    "M3_READINESS_BINDING",
                    "INDEPENDENT_APPROVAL",
                    "BOUNDED_AUTHORIZATION",
                    "SINGLE_USE_PERMIT",
                    "ATOMIC_CLAIM",
                    "ROLLBACK_EVIDENCE",
                    "FAIL_CLOSED_VALIDATION",
                ),
                required_authorization_contracts=(
                    f"{capability.value}_REQUEST",
                    f"{capability.value}_INDEPENDENT_APPROVAL",
                    f"{capability.value}_AUTHORIZATION",
                ),
                permit_boundary=f"{capability.value}_SINGLE_USE_PERMIT",
                claim_boundary=f"{capability.value}_ATOMIC_CLAIM",
                required_evidence_artifacts=(
                    f"{capability.value}_REQUEST_EVIDENCE",
                    f"{capability.value}_AUTHORIZATION_EVIDENCE",
                    f"{capability.value}_ROLLBACK_EVIDENCE",
                    f"{capability.value}_VALIDATION_EVIDENCE",
                ),
                rollback_requirement="CAPABILITY_SCOPED_ROLLBACK_REQUIRED",
                fail_closed_requirement="FAIL_CLOSED_ON_ANY_MISSING_OR_INVALID_EVIDENCE",
                dependencies=CAPABILITY_BY_ID[capability].dependency_requirements,
                prohibited_transitions=(
                    "SKIPPED_TRANSITION",
                    "IMPLICIT_CAPABILITY_ESCALATION",
                    "PRODUCTION_TRANSITION",
                    "UBUNTU_DELEGATION",
                    "ENVIRONMENT_ONLY_ACTIVATION",
                ),
            )
            for index, capability in enumerate(ordered, start=1)
        )
        plan = ControlledActivationPlan(
            task=TASK,
            branch=request.branch,
            commit=request.commit,
            scope=request.scope,
            requester_identity=request.requester_identity,
            operator_identity=request.operator_identity,
            proposed_independent_approver_identity=(
                request.proposed_independent_approver_identity
            ),
            capability_order=ordered,
            steps=steps,
            production_authorized=False,
            ubuntu_participation=False,
            activation_authorizations_created=0,
            operational_permits_issued=0,
            live_claims_created=0,
            runtime_side_effects=0,
            decision=(
                ControlledActivationArchitectureDecision
                .READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS
            ),
            plan_digest="",
        )
        digest_payload = plan.as_dict()
        digest_payload["plan_digest"] = ""
        return replace(plan, plan_digest=sha256_digest(digest_payload))
