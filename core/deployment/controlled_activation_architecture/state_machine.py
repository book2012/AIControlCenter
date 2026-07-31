"""Deterministic per-capability controlled activation state machine."""

from __future__ import annotations

from .models import (
    BASELINE_COMMIT,
    BRANCH,
    ControlledActivationArchitectureError,
    ControlledActivationState,
    ControlledActivationTransition,
    ControlledActivationValidationResult,
)


_NEXT = {
    ControlledActivationState.INACTIVE: ControlledActivationState.REQUESTED,
    ControlledActivationState.REQUESTED: ControlledActivationState.INDEPENDENTLY_APPROVED,
    ControlledActivationState.INDEPENDENTLY_APPROVED: ControlledActivationState.AUTHORIZED,
    ControlledActivationState.AUTHORIZED: ControlledActivationState.PERMITTED,
    ControlledActivationState.PERMITTED: ControlledActivationState.CLAIMED,
    ControlledActivationState.CLAIMED: ControlledActivationState.CONTROLLED_ACTIVE,
    ControlledActivationState.CONTROLLED_ACTIVE: ControlledActivationState.VALIDATED,
    ControlledActivationState.VALIDATED: ControlledActivationState.DEACTIVATED,
}
FAILURE_STATES = {
    ControlledActivationState.BLOCKED,
    ControlledActivationState.FAILED_CLOSED,
}


class ControlledActivationStateMachine:
    def validate(
        self, transition: ControlledActivationTransition
    ) -> ControlledActivationValidationResult:
        if not transition.branch or transition.branch != BRANCH:
            raise ControlledActivationArchitectureError("BRANCH_MISMATCH")
        if not transition.commit or transition.commit != BASELINE_COMMIT:
            raise ControlledActivationArchitectureError("COMMIT_MISMATCH")
        if transition.production_transition:
            raise ControlledActivationArchitectureError("PRODUCTION_TRANSITION_PROHIBITED")
        if transition.ubuntu_delegation:
            raise ControlledActivationArchitectureError("UBUNTU_DELEGATION_PROHIBITED")
        if transition.environment_only:
            raise ControlledActivationArchitectureError("ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED")
        if not transition.evidence_artifacts:
            raise ControlledActivationArchitectureError("EVIDENCE_REQUIREMENT_MISSING")
        expected = _NEXT.get(transition.from_state)
        if transition.to_state not in FAILURE_STATES and transition.to_state != expected:
            raise ControlledActivationArchitectureError("SKIPPED_OR_BACKWARD_TRANSITION")
        if transition.to_state is ControlledActivationState.INDEPENDENTLY_APPROVED:
            _require(transition.independent_approval_present, "INDEPENDENT_APPROVAL_MISSING")
        if transition.to_state is ControlledActivationState.AUTHORIZED:
            _require(transition.authorization_valid, "AUTHORIZATION_INVALID")
            _require(not transition.authorization_expired, "AUTHORIZATION_EXPIRED")
        if transition.to_state is ControlledActivationState.PERMITTED:
            _require(transition.single_use_permit_present, "PERMIT_MISSING")
            _require(not transition.permit_reusable, "REUSABLE_PERMIT_PROHIBITED")
        if transition.to_state is ControlledActivationState.CLAIMED:
            _require(transition.atomic_claim_count == 1, "EXACTLY_ONE_ATOMIC_CLAIM_REQUIRED")
        if transition.to_state is ControlledActivationState.CONTROLLED_ACTIVE:
            _require(transition.single_use_permit_present, "PERMIT_MISSING")
            _require(not transition.permit_reusable, "REUSABLE_PERMIT_PROHIBITED")
            _require(transition.atomic_claim_count == 1, "ACTIVATION_BEFORE_PERMIT_CLAIM")
        if transition.to_state is ControlledActivationState.DEACTIVATED:
            _require(transition.rollback_evidence_present, "ROLLBACK_EVIDENCE_MISSING")
        return ControlledActivationValidationResult(
            valid=True,
            capability=transition.capability,
            from_state=transition.from_state,
            to_state=transition.to_state,
            evidence_artifacts=transition.evidence_artifacts,
            decision="TRANSITION_VALIDATED_ARCHITECTURE_ONLY",
        )


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ControlledActivationArchitectureError(code)
