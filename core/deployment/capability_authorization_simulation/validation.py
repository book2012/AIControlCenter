"""Fail-closed validation for M4-A3 simulation inputs and artifacts."""

from __future__ import annotations

from datetime import datetime, timedelta

from core.deployment.capability_authorization import REQUIRED_RESTRICTIONS
from core.deployment.controlled_activation_architecture import ControlledActivationCapability

from .models import *

MAX_TTL = timedelta(hours=1)
DEPENDENCY = {
    ControlledActivationCapability.ALERT_DISPATCH:
        ControlledActivationCapability.MONITORING_RUNTIME,
    ControlledActivationCapability.EXTERNAL_NOTIFICATION:
        ControlledActivationCapability.ALERT_DISPATCH,
}


def deny(condition: bool, code: str) -> None:
    if condition:
        raise TestOnlyAuthorizationSimulationError(code)


def validate_config(config: TestOnlyAuthorizationSimulationConfig) -> None:
    deny(config.branch != BRANCH, "BRANCH_MISMATCH")
    deny(config.commit != BASELINE_COMMIT, "COMMIT_MISMATCH")
    deny(config.m3_binding != M3_BINDING, "M3_BINDING_INVALID")
    deny(config.m4_a1_binding != M4_A1_BINDING, "M4_A1_BINDING_INVALID")
    deny(config.m4_a2_binding != M4_A2_BINDING, "M4_A2_BINDING_INVALID")
    deny(config.test_only is not True, "TEST_ONLY_MARKER_MISSING")
    deny(config.operationally_valid is not False, "OPERATIONAL_VALIDITY_PROHIBITED")
    deny(config.production_authorized, "PRODUCTION_AUTHORIZATION_PROHIBITED")
    deny(config.ubuntu_participation, "UBUNTU_PARTICIPATION_PROHIBITED")
    deny(config.runtime_activation_allowed, "RUNTIME_ACTIVATION_PROHIBITED")
    deny(config.namespace != TEST_NAMESPACE, "TEST_NAMESPACE_INVALID")
    deny(config.source != TEST_SOURCE, "TEST_SOURCE_INVALID")
    deny(config.maximum_uses != 1, "MAXIMUM_USES_INVALID")
    deny(config.environment_only_authorization, "ENVIRONMENT_AUTHORITY_PROHIBITED")
    deny(config.api_route_authority, "API_AUTHORITY_PROHIBITED")
    deny(config.external_governance_authority.casefold() != "aicontrolcenter",
         "EXTERNAL_GOVERNANCE_AUTHORITY_PROHIBITED")
    deny(config.subprocess_execution, "SUBPROCESS_PROHIBITED")
    deny(config.runtime_command_execution, "RUNTIME_COMMAND_PROHIBITED")
    deny(config.network_access, "NETWORK_ACCESS_PROHIBITED")


def validate_request(request: TestOnlyAuthorizationSimulationRequest, *, now: datetime) -> ControlledActivationCapability:
    deny(not request.simulation_id.startswith("m4-a3-test-simulation-"), "SIMULATION_ID_INVALID")
    deny(request.branch != BRANCH, "BRANCH_MISMATCH")
    deny(request.commit != BASELINE_COMMIT, "COMMIT_MISMATCH")
    if isinstance(request.capability, (tuple, list, set)):
        deny(len(request.capability) != len(set(request.capability)), "DUPLICATE_CAPABILITY")
        raise TestOnlyAuthorizationSimulationError("MULTIPLE_CAPABILITIES_PROHIBITED")
    try:
        capability = ControlledActivationCapability(request.capability)
    except (TypeError, ValueError):
        raise TestOnlyAuthorizationSimulationError("UNKNOWN_CAPABILITY") from None
    deny(not request.independent_approver_identity.strip(), "INDEPENDENT_APPROVER_MISSING")
    deny(request.requester_identity.casefold() == request.independent_approver_identity.casefold(),
         "REQUESTER_APPROVER_COLLISION")
    deny(request.operator_identity.casefold() == request.independent_approver_identity.casefold(),
         "OPERATOR_APPROVER_COLLISION")
    deny(request.operator_identity.casefold() == "root", "ROOT_OPERATOR_PROHIBITED")
    deny(now.tzinfo is None or request.requested_at.tzinfo is None or request.expires_at.tzinfo is None,
         "TIMEZONE_REQUIRED")
    deny(now >= request.expires_at, "APPROVAL_EXPIRED")
    deny(request.expires_at - request.requested_at > MAX_TTL, "TTL_EXCESSIVE")
    deny(set(request.acknowledged_restrictions) != set(REQUIRED_RESTRICTIONS),
         "RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE")
    for value, code in (
        (request.request_digest, "REQUEST_DIGEST_MISSING"),
        (request.approval_digest, "APPROVAL_DIGEST_MISSING"),
        (request.grant_plan_digest, "GRANT_PLAN_DIGEST_MISSING"),
    ):
        deny(not value.startswith("sha256:") or len(value) != 71, code)
    deny(request.monitoring_implies_alert_dispatch, "MONITORING_ESCALATION_PROHIBITED")
    deny(request.alert_dispatch_implies_external_notification, "ALERT_ESCALATION_PROHIBITED")
    dependency = DEPENDENCY.get(capability)
    if dependency:
        deny(request.dependency_authorization_reference != dependency.value,
             "DEPENDENCY_REFERENCE_INVALID")
        digest = request.dependency_authorization_digest or ""
        deny(not digest.startswith("sha256:") or len(digest) != 71,
             "DEPENDENCY_DIGEST_INVALID")
    return capability


def validate_test_artifact(artifact: object, prefix: str) -> None:
    for name, expected in (
        ("test_only", True), ("operationally_valid", False),
        ("production_authorized", False), ("ubuntu_participation", False),
        ("runtime_activation_allowed", False), ("namespace", TEST_NAMESPACE),
        ("source", TEST_SOURCE),
    ):
        deny(getattr(artifact, name, None) is not expected if isinstance(expected, bool)
             else getattr(artifact, name, None) != expected, f"ARTIFACT_{name.upper()}_INVALID")
    field = {
        "m4-a3-test-authorization-": "authorization_id",
        "m4-a3-test-permit-": "permit_id",
        "m4-a3-test-claim-": "claim_id",
    }[prefix]
    identity = getattr(artifact, field, "")
    deny(not identity.startswith(prefix), "TEST_ARTIFACT_ID_INVALID")


def reject_at_operational_boundary(artifact: object) -> None:
    """Every M4-A3 shape is unconditionally invalid at a live boundary."""
    markers = (
        getattr(artifact, "test_only", None) is True,
        getattr(artifact, "operationally_valid", None) is False,
        getattr(artifact, "namespace", None) == TEST_NAMESPACE,
        getattr(artifact, "source", None) == TEST_SOURCE,
        any(str(getattr(artifact, name, "")).startswith("m4-a3-test-")
            for name in ("authorization_id", "permit_id", "claim_id", "simulation_id")),
    )
    if any(markers):
        raise TestOnlyAuthorizationSimulationError("SIMULATION_ARTIFACT_OPERATIONALLY_INVALID")
    raise TestOnlyAuthorizationSimulationError("UNKNOWN_ARTIFACT_OPERATIONALLY_INVALID")


def validate_evidence_chain(evidence) -> None:
    deny(len(evidence) != len(TestOnlyAuthorizationStep), "SKIPPED_SIMULATION_STATE")
    prior = "sha256:" + "0" * 64
    timestamp = None
    for sequence, (item, state) in enumerate(zip(evidence, TestOnlyAuthorizationStep), 1):
        deny(item.sequence != sequence or item.state is not state, "SKIPPED_SIMULATION_STATE")
        deny(item.test_only is not True, "TEST_ONLY_MARKER_MISSING")
        deny(item.prior_step_digest != prior, "PRIOR_STEP_DIGEST_TAMPERED")
        deny(timestamp is not None and item.timestamp <= timestamp,
             "NON_MONOTONIC_TIMESTAMP")
        deny(item.canonical_artifact_digest != item.computed_digest(),
             "EVIDENCE_DIGEST_MISMATCH")
        timestamp = item.timestamp
        prior = item.canonical_artifact_digest


def validate_bindings(authorization, permit, claim) -> None:
    deny(not (authorization.capability is permit.capability is claim.capability),
         "CAPABILITY_MISMATCH")
    deny(permit.authorization_id != authorization.authorization_id
         or permit.authorization_digest != authorization.digest(),
         "PERMIT_AUTHORIZATION_BINDING_MISMATCH")
    deny(claim.permit_id != permit.permit_id or claim.permit_digest != permit.digest(),
         "CLAIM_PERMIT_BINDING_MISMATCH")
    deny(claim.authorization_id != authorization.authorization_id
         or claim.authorization_digest != authorization.digest(),
         "CLAIM_AUTHORIZATION_BINDING_MISMATCH")
    deny(len({authorization.request_digest, permit.request_digest, claim.request_digest}) != 1,
         "REQUEST_DIGEST_MISMATCH")
    deny(len({authorization.approval_digest, permit.approval_digest, claim.approval_digest}) != 1,
         "APPROVAL_DIGEST_MISMATCH")
    deny(len({authorization.grant_plan_digest, permit.grant_plan_digest,
              claim.grant_plan_digest}) != 1, "GRANT_PLAN_MISMATCH")
