"""Deterministic delivery lifecycle validation."""

from __future__ import annotations

from .models import DeliveryDecision, DeliveryRunState, DeliveryTransition

_SUCCESSORS = {
    DeliveryRunState.PLANNED: DeliveryRunState.PREFLIGHT,
    DeliveryRunState.PREFLIGHT: DeliveryRunState.RUNNING,
    DeliveryRunState.RUNNING: DeliveryRunState.VALIDATING,
    DeliveryRunState.VALIDATING: DeliveryRunState.DOCUMENTING,
    DeliveryRunState.DOCUMENTING: DeliveryRunState.COMMITTING,
    DeliveryRunState.COMMITTING: DeliveryRunState.PUSHING,
    DeliveryRunState.PUSHING: DeliveryRunState.CLOSED,
}
_FAILURE = {
    DeliveryRunState.BLOCKED,
    DeliveryRunState.FAILED_CLOSED,
    DeliveryRunState.AWAITING_APPROVAL,
    DeliveryRunState.RECOVERY_REQUIRED,
    DeliveryRunState.CANCELLED,
}


def validate_transition(value: DeliveryTransition) -> DeliveryDecision:
    if not value.evidence:
        return DeliveryDecision(False, "IMMUTABLE_EVIDENCE_REQUIRED", value.from_state)
    if value.to_state is DeliveryRunState.AWAITING_APPROVAL and value.automatic:
        return DeliveryDecision(False, "AUTOMATIC_APPROVAL_TRANSITION_PROHIBITED", value.from_state)
    if value.to_state not in _FAILURE and _SUCCESSORS.get(value.from_state) is not value.to_state:
        return DeliveryDecision(False, "SKIPPED_LIFECYCLE_STATE", value.from_state)
    if value.to_state is DeliveryRunState.RUNNING and not value.exact_baseline_verified:
        return DeliveryDecision(False, "EXACT_BASELINE_REQUIRED", value.from_state)
    if value.to_state is DeliveryRunState.COMMITTING and not (
        value.tests_passed and value.documentation_passed
    ):
        return DeliveryDecision(False, "TESTS_AND_DOCUMENTATION_REQUIRED", value.from_state)
    if value.to_state is DeliveryRunState.PUSHING and not value.commit_evidence_present:
        return DeliveryDecision(False, "COMMIT_EVIDENCE_REQUIRED", value.from_state)
    if value.to_state is DeliveryRunState.CLOSED and not value.remote_commit_verified:
        return DeliveryDecision(False, "REMOTE_VERIFICATION_REQUIRED", value.from_state)
    return DeliveryDecision(True, "TRANSITION_ALLOWED", value.to_state)
