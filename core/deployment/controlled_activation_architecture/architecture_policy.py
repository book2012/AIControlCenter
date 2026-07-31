"""Default-deny architecture and request policy."""

from __future__ import annotations

from .models import (
    BASELINE_COMMIT,
    BRANCH,
    M3_READINESS,
    ControlledActivationArchitectureConfig,
    ControlledActivationArchitectureError,
    ControlledActivationCapability,
    ControlledActivationPlanRequest,
)


def validate_architecture_config(config: ControlledActivationArchitectureConfig) -> None:
    checks = (
        (bool(config.branch), "BRANCH_EMPTY"),
        (bool(config.commit), "COMMIT_EMPTY"),
        (config.branch == BRANCH, "BRANCH_MISMATCH"),
        (config.commit == BASELINE_COMMIT, "COMMIT_MISMATCH"),
        (bool(config.m3_readiness_binding), "M3_READINESS_BINDING_MISSING"),
        (config.m3_readiness_binding == M3_READINESS, "M3_READINESS_INVALID"),
        (not config.production_authorized, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
        (not config.ubuntu_participation, "UBUNTU_DELEGATION_PROHIBITED"),
        (config.live_control_scope != "LINUX_LIVE_CONTROL", "LINUX_LIVE_CONTROL_PROHIBITED"),
        (config.control_plane_owner == "AIControlCenter", "CONTROL_PLANE_OWNER_INVALID"),
        (config.authorization_owner == "AIControlCenter", "AUTHORIZATION_OWNER_INVALID"),
        (config.state_owner == "AIControlCenter", "STATE_OWNER_INVALID"),
        (config.activation_authority != "API_WRITE_ROUTE", "API_ACTIVATION_AUTHORITY_PROHIBITED"),
        (config.governance_authority != "n8n", "N8N_GOVERNANCE_PROHIBITED"),
        (config.business_logic_authority != "WordPress", "WORDPRESS_GOVERNANCE_PROHIBITED"),
        (config.business_logic_authority != "WooCommerce", "WOOCOMMERCE_GOVERNANCE_PROHIBITED"),
        (not config.environment_only_activation, "ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED"),
        (not config.arbitrary_command_execution, "ARBITRARY_COMMAND_EXECUTION_PROHIBITED"),
        (not config.runtime_subprocess_execution, "RUNTIME_SUBPROCESS_PROHIBITED"),
    )
    _require(checks)


def validate_plan_request(
    request: ControlledActivationPlanRequest,
) -> tuple[ControlledActivationCapability, ...]:
    _require((
        (bool(request.branch), "BRANCH_EMPTY"),
        (bool(request.commit), "COMMIT_EMPTY"),
        (request.branch == BRANCH, "BRANCH_MISMATCH"),
        (request.commit == BASELINE_COMMIT, "COMMIT_MISMATCH"),
        (bool(request.m3_readiness_binding), "M3_READINESS_BINDING_MISSING"),
        (request.m3_readiness_binding == M3_READINESS, "M3_READINESS_INVALID"),
        (request.scope == "CONTROLLED_NON_PRODUCTION", "SCOPE_PROHIBITED"),
        (not request.production_authorized, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
        (not request.ubuntu_participation, "UBUNTU_DELEGATION_PROHIBITED"),
        (request.operator_identity.strip().lower() != "root", "ROOT_OPERATOR_PROHIBITED"),
        (
            request.requester_identity != request.proposed_independent_approver_identity,
            "REQUESTER_APPROVER_COLLISION",
        ),
        (not request.caller_supplied_capability_order, "CALLER_ORDER_PROHIBITED"),
        (not request.authorization_expired, "AUTHORIZATION_EXPIRED"),
        (request.permit_single_use, "REUSABLE_PERMIT_PROHIBITED"),
        (not request.duplicate_claim_representation, "DUPLICATE_CLAIM_PROHIBITED"),
        (request.rollback_required, "ROLLBACK_REQUIREMENT_MISSING"),
        (request.evidence_required, "EVIDENCE_REQUIREMENT_MISSING"),
        (not request.bundled_implicit_escalation, "IMPLICIT_CAPABILITY_ESCALATION"),
        (not request.monitoring_implies_alert_dispatch, "MONITORING_ESCALATION_PROHIBITED"),
        (not request.alert_dispatch_implies_external_notification, "ALERT_ESCALATION_PROHIBITED"),
        (not request.environment_only_activation, "ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED"),
        (request.activation_authority != "API_WRITE_ROUTE", "API_ACTIVATION_AUTHORITY_PROHIBITED"),
        (request.governance_authority != "n8n", "N8N_GOVERNANCE_PROHIBITED"),
        (request.business_logic_authority != "WordPress", "WORDPRESS_GOVERNANCE_PROHIBITED"),
        (request.business_logic_authority != "WooCommerce", "WOOCOMMERCE_GOVERNANCE_PROHIBITED"),
        (request.state_owner != "UbuntuWorker", "UBUNTU_STATE_OWNER_PROHIBITED"),
        (not request.arbitrary_command_execution, "ARBITRARY_COMMAND_EXECUTION_PROHIBITED"),
        (not request.runtime_subprocess_execution, "RUNTIME_SUBPROCESS_PROHIBITED"),
    ))
    capabilities: list[ControlledActivationCapability] = []
    for item in request.requested_capabilities:
        try:
            capability = ControlledActivationCapability(item)
        except (TypeError, ValueError) as error:
            raise ControlledActivationArchitectureError("UNKNOWN_CAPABILITY") from error
        if capability in capabilities:
            raise ControlledActivationArchitectureError("DUPLICATE_CAPABILITY")
        capabilities.append(capability)
    if not capabilities:
        raise ControlledActivationArchitectureError("CAPABILITY_SET_EMPTY")
    return tuple(capabilities)


def _require(checks: tuple[tuple[bool, str], ...]) -> None:
    for passed, code in checks:
        if not passed:
            raise ControlledActivationArchitectureError(code)
