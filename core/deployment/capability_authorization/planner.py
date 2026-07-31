"""Deterministic M4-A2 test-only grant planner."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from .models import (
    TASK,
    CapabilityAuthorizationApproval,
    CapabilityAuthorizationArchitectureDecision,
    CapabilityAuthorizationGrant,
    CapabilityAuthorizationPlan,
    CapabilityAuthorizationRequest,
    CapabilityAuthorizationValidationResult,
)
from .capability_policy import REQUIRED_RESTRICTIONS
from .validation import validate_approval


class CapabilityAuthorizationPlanner:
    """Plans a grant contract; it cannot authorize, issue, claim, or activate."""

    def __init__(self, *, clock: Callable[[], datetime]) -> None:
        self._clock = clock

    def plan(
        self,
        request: CapabilityAuthorizationRequest,
        approval: CapabilityAuthorizationApproval,
    ) -> CapabilityAuthorizationPlan:
        capability = validate_approval(request, approval, clock=self._clock)
        checked_at = self._clock()
        validation = CapabilityAuthorizationValidationResult(
            valid=True,
            request_id=request.request_id,
            capability=capability,
            errors=(),
            checked_at=checked_at,
        )
        grant = CapabilityAuthorizationGrant(
            grant_plan_id=f"test-plan:{request.request_id}:{capability.value}",
            request_id=request.request_id,
            request_digest=request.canonical_digest,
            approval_id=approval.approval_id,
            approval_digest=approval.canonical_digest,
            capability=capability,
            branch=request.branch,
            commit=request.commit,
            not_before=approval.authorization_not_before,
            expires_at=approval.authorization_expires_at,
            maximum_uses=1,
            production_authorized=False,
            ubuntu_participation=False,
            cryptographic_identity_verified=False,
            authorization_created=False,
            permit_issued=False,
            claim_created=False,
            runtime_activation_authorized=False,
        )
        plan = CapabilityAuthorizationPlan(
            task=TASK,
            validation=validation,
            grant=grant,
            required_restrictions=REQUIRED_RESTRICTIONS,
            activation_authorizations_created=0,
            operational_permits_issued=0,
            live_claims_created=0,
            runtime_activations=0,
            decision=(
                CapabilityAuthorizationArchitectureDecision
                .READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION
            ),
            plan_digest="",
        )
        return replace(plan, plan_digest=plan.computed_digest())
