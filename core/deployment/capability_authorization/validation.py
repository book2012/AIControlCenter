"""Pure, injected-clock M4-A2 canonical validation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from core.deployment.controlled_activation_architecture import (
    CAPABILITY_BY_ID,
    ControlledActivationCapability,
)

from .models import (
    BASELINE_COMMIT,
    BRANCH,
    M3_READINESS,
    M4_A1_DECISION,
    SCHEMA_VERSION,
    CapabilityAuthorizationApproval,
    CapabilityAuthorizationError,
    CapabilityAuthorizationRequest,
)
from .capability_policy import (
    DEPENDENCY_CAPABILITY,
    MAXIMUM_AUTHORIZATION_TTL,
    REQUIRED_RESTRICTIONS,
)


Clock = Callable[[], datetime]
EXTERNAL_AUTHORITIES = {
    "n8n", "wordpress", "woocommerce", "ubuntu", "ubuntuworker",
    "external_component", "api", "api_write_route",
}


def _deny(condition: bool, code: str) -> None:
    if condition:
        raise CapabilityAuthorizationError(code)


def _identity(value: str, code: str) -> str:
    _deny(not isinstance(value, str) or not value.strip(), code)
    return value.strip()


def _aware(value: datetime, code: str) -> None:
    _deny(
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None,
        code,
    )


def _capability(value: object) -> ControlledActivationCapability:
    if isinstance(value, (tuple, list, set)):
        _deny(len(value) != len(set(value)), "DUPLICATE_CAPABILITY")
        raise CapabilityAuthorizationError("MULTIPLE_CAPABILITIES_PROHIBITED")
    try:
        capability = ControlledActivationCapability(value)
    except (TypeError, ValueError):
        raise CapabilityAuthorizationError("UNKNOWN_CAPABILITY") from None
    _deny(capability not in CAPABILITY_BY_ID, "UNKNOWN_CAPABILITY")
    return capability


def validate_request(
    request: CapabilityAuthorizationRequest,
    *,
    clock: Clock,
) -> ControlledActivationCapability:
    now = clock()
    _aware(now, "NAIVE_CLOCK")
    _deny(request.schema_version != SCHEMA_VERSION, "SCHEMA_VERSION_INVALID")
    _deny(not request.request_id.strip(), "REQUEST_ID_MISSING")
    _deny(request.branch != BRANCH, "BRANCH_MISMATCH")
    _deny(request.commit != BASELINE_COMMIT, "COMMIT_MISMATCH")
    capability = _capability(request.capability)
    requester = _identity(request.requester_identity, "REQUESTER_IDENTITY_MISSING")
    operator = _identity(request.operator_identity, "OPERATOR_IDENTITY_MISSING")
    approver = _identity(
        request.proposed_independent_approver_identity,
        "APPROVER_IDENTITY_MISSING",
    )
    _deny(approver.casefold() == requester.casefold(), "REQUESTER_APPROVER_COLLISION")
    _deny(approver.casefold() == operator.casefold(), "OPERATOR_APPROVER_COLLISION")
    _deny(operator.casefold() == "root", "ROOT_OPERATOR_PROHIBITED")
    owners = (
        request.scope.control_plane_owner,
        request.scope.governance_authority,
        request.scope.state_owner,
    )
    _deny(
        any(
            not isinstance(owner, str)
            or owner.strip() != "AIControlCenter"
            or owner.strip().casefold() in EXTERNAL_AUTHORITIES
            for owner in owners
        ),
        "EXTERNAL_GOVERNANCE_OWNER_PROHIBITED",
    )
    _deny(
        any(
            identity.casefold().startswith(("ubuntu", "n8n", "wordpress", "woocommerce", "api:"))
            for identity in (requester, operator, approver)
        ),
        "AUTHORIZATION_OWNER_PROHIBITED",
    )
    _deny(
        request.scope.environment != "CONTROLLED_NON_PRODUCTION",
        "SCOPE_PROHIBITED",
    )
    _deny(
        request.production_authorized or request.scope.production_authorized,
        "PRODUCTION_AUTHORIZATION_PROHIBITED",
    )
    _deny(
        request.ubuntu_participation or request.scope.ubuntu_participation,
        "UBUNTU_PARTICIPATION_PROHIBITED",
    )
    _deny(
        request.scope.authorization_from_environment,
        "ENVIRONMENT_AUTHORITY_PROHIBITED",
    )
    _deny(request.scope.api_route_authority, "API_AUTHORITY_PROHIBITED")
    _deny(request.scope.runtime_command_execution, "RUNTIME_COMMAND_PROHIBITED")
    _deny(
        request.evidence.m3_readiness_binding != M3_READINESS,
        "M3_READINESS_INVALID",
    )
    _deny(
        request.evidence.m4_a1_architecture_binding != M4_A1_DECISION,
        "M4_A1_BINDING_INVALID",
    )
    _deny(not request.evidence.rollback_policy.strip(), "ROLLBACK_REQUIREMENT_MISSING")
    _deny(not request.evidence.evidence_policy.strip(), "EVIDENCE_REQUIREMENT_MISSING")
    _deny(request.requested_maximum_uses != 1, "MAXIMUM_USES_INVALID")
    for value in (
        request.requested_at,
        request.requested_not_before,
        request.requested_expires_at,
    ):
        _aware(value, "NAIVE_DATETIME")
    _deny(
        request.requested_not_before >= request.requested_expires_at,
        "AUTHORIZATION_WINDOW_INVALID",
    )
    _deny(
        request.requested_expires_at - request.requested_not_before
        > MAXIMUM_AUTHORIZATION_TTL,
        "TTL_EXCESSIVE",
    )
    _deny(now >= request.requested_expires_at, "REQUEST_EXPIRED")
    _deny(
        request.bundled_capability_escalation,
        "BUNDLED_CAPABILITY_ESCALATION_PROHIBITED",
    )
    _deny(
        request.monitoring_implies_alert_dispatch,
        "MONITORING_ESCALATION_PROHIBITED",
    )
    _deny(
        request.alert_dispatch_implies_external_notification,
        "ALERT_ESCALATION_PROHIBITED",
    )
    if capability is ControlledActivationCapability.MONITORING_RUNTIME:
        _deny(
            request.evidence.read_only_health_evidence
            != CAPABILITY_BY_ID[capability].read_only_health_dependencies,
            "READ_ONLY_HEALTH_EVIDENCE_INVALID",
        )
    dependency = DEPENDENCY_CAPABILITY.get(capability)
    if dependency is not None:
        _deny(
            request.evidence.separately_authorized_capability_reference
            != dependency.value,
            "SEPARATE_CAPABILITY_REFERENCE_MISSING",
        )
        digest = request.evidence.separately_authorized_capability_digest
        _deny(
            not isinstance(digest, str)
            or len(digest) != 71
            or not digest.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in digest[7:]),
            "SEPARATE_CAPABILITY_DIGEST_MISSING",
        )
    _deny(
        request.canonical_digest != request.computed_digest(),
        "REQUEST_DIGEST_MISMATCH",
    )
    return capability


def validate_approval(
    request: CapabilityAuthorizationRequest,
    approval: CapabilityAuthorizationApproval,
    *,
    clock: Clock,
) -> ControlledActivationCapability:
    capability = validate_request(request, clock=clock)
    now = clock()
    _aware(now, "NAIVE_CLOCK")
    _deny(approval.schema_version != SCHEMA_VERSION, "SCHEMA_VERSION_INVALID")
    _deny(approval.request_id != request.request_id, "REQUEST_ID_MISMATCH")
    _deny(approval.request_digest != request.canonical_digest, "REQUEST_DIGEST_MISMATCH")
    _deny(_capability(approval.capability) is not capability, "CAPABILITY_MISMATCH")
    approver = _identity(
        approval.independent_approver_identity, "APPROVER_IDENTITY_MISSING"
    )
    _deny(
        approver.casefold() != request.proposed_independent_approver_identity.strip().casefold(),
        "APPROVER_IDENTITY_MISMATCH",
    )
    _deny(
        approver.casefold() == request.requester_identity.strip().casefold(),
        "REQUESTER_APPROVER_COLLISION",
    )
    _deny(
        approver.casefold() == request.operator_identity.strip().casefold(),
        "OPERATOR_APPROVER_COLLISION",
    )
    _deny(approval.decision != "APPROVED", "APPROVAL_DECISION_DENIED")
    for value in (
        approval.approval_timestamp,
        approval.authorization_not_before,
        approval.authorization_expires_at,
    ):
        _aware(value, "NAIVE_DATETIME")
    _deny(
        approval.approval_timestamp < request.requested_at,
        "APPROVAL_BEFORE_REQUEST",
    )
    _deny(now < approval.approval_timestamp, "GRANT_PLANNING_BEFORE_APPROVAL")
    _deny(
        approval.authorization_not_before < approval.approval_timestamp
        or approval.authorization_not_before < request.requested_not_before,
        "APPROVAL_WINDOW_INVALID",
    )
    _deny(
        approval.authorization_not_before >= approval.authorization_expires_at
        or approval.authorization_expires_at > request.requested_expires_at,
        "APPROVAL_WINDOW_INVALID",
    )
    _deny(
        approval.authorization_expires_at - approval.authorization_not_before
        > MAXIMUM_AUTHORIZATION_TTL,
        "TTL_EXCESSIVE",
    )
    _deny(now >= approval.authorization_expires_at, "APPROVAL_EXPIRED")
    _deny(approval.maximum_uses != 1, "MAXIMUM_USES_INVALID")
    _deny(approval.production_authorized, "PRODUCTION_AUTHORIZATION_PROHIBITED")
    _deny(approval.ubuntu_participation, "UBUNTU_PARTICIPATION_PROHIBITED")
    _deny(approval.cryptographic_identity_verified, "CRYPTOGRAPHIC_IDENTITY_UNSUPPORTED")
    acknowledged = approval.acknowledged_restrictions
    _deny(len(acknowledged) != len(set(acknowledged)), "DUPLICATE_RESTRICTION")
    _deny(
        set(acknowledged) != set(REQUIRED_RESTRICTIONS),
        "RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE",
    )
    _deny(
        approval.canonical_digest != approval.computed_digest(),
        "APPROVAL_DIGEST_MISMATCH",
    )
    return capability
