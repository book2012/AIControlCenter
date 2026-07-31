from __future__ import annotations

import ast
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.deployment.capability_authorization import (
    BASELINE_COMMIT,
    BRANCH,
    M3_READINESS,
    M4_A1_DECISION,
    REQUIRED_RESTRICTIONS,
    SCHEMA_VERSION,
    CapabilityAuthorizationApproval,
    CapabilityAuthorizationArchitectureDecision,
    CapabilityAuthorizationDecision,
    CapabilityAuthorizationError,
    CapabilityAuthorizationEvidence,
    CapabilityAuthorizationPlanner,
    CapabilityAuthorizationRequest,
    CapabilityAuthorizationRestriction,
    CapabilityAuthorizationScope,
)
from core.deployment.controlled_activation_architecture import (
    ControlledActivationCapability,
)


ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
REQUESTED = datetime(2026, 7, 31, 12, 0, tzinfo=UTC)
APPROVED = REQUESTED + timedelta(minutes=5)
NOT_BEFORE = REQUESTED + timedelta(minutes=10)
EXPIRES = REQUESTED + timedelta(minutes=50)
NOW = REQUESTED + timedelta(minutes=6)


def evidence(capability: ControlledActivationCapability) -> CapabilityAuthorizationEvidence:
    dependency = {
        ControlledActivationCapability.ALERT_DISPATCH: "MONITORING_RUNTIME",
        ControlledActivationCapability.EXTERNAL_NOTIFICATION: "ALERT_DISPATCH",
    }.get(capability)
    return CapabilityAuthorizationEvidence(
        m3_readiness_binding=M3_READINESS,
        m4_a1_architecture_binding=M4_A1_DECISION,
        rollback_policy="CAPABILITY_SCOPED_ROLLBACK_EVIDENCE_REQUIRED",
        evidence_policy="IMMUTABLE_CANONICAL_EVIDENCE_REQUIRED",
        read_only_health_evidence=(
            ("AUDIT_READ_ONLY_HEALTH", "REPLAY_READ_ONLY_HEALTH")
            if capability is ControlledActivationCapability.MONITORING_RUNTIME
            else ()
        ),
        separately_authorized_capability_reference=dependency,
        separately_authorized_capability_digest=(
            "sha256:" + "a" * 64 if dependency else None
        ),
    )


def request(
    capability: ControlledActivationCapability = ControlledActivationCapability.AUDIT_WRITER,
    **changes: object,
) -> CapabilityAuthorizationRequest:
    value = CapabilityAuthorizationRequest(
        schema_version=SCHEMA_VERSION,
        request_id=f"request-{capability.value.lower()}",
        branch=BRANCH,
        commit=BASELINE_COMMIT,
        capability=capability,
        requester_identity="requester@example.test",
        operator_identity="mac-operator",
        proposed_independent_approver_identity="approver@example.test",
        scope=CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION"),
        requested_at=REQUESTED,
        requested_not_before=NOT_BEFORE,
        requested_expires_at=EXPIRES,
        requested_maximum_uses=1,
        production_authorized=False,
        ubuntu_participation=False,
        evidence=evidence(capability),
        canonical_digest="",
    )
    value = replace(value, **changes)
    return replace(value, canonical_digest=value.computed_digest())


def approval(
    value: CapabilityAuthorizationRequest,
    **changes: object,
) -> CapabilityAuthorizationApproval:
    result = CapabilityAuthorizationApproval(
        schema_version=SCHEMA_VERSION,
        approval_id=f"approval-{value.request_id}",
        request_id=value.request_id,
        request_digest=value.canonical_digest,
        capability=value.capability,
        independent_approver_identity="approver@example.test",
        decision=CapabilityAuthorizationDecision.APPROVED,
        approval_timestamp=APPROVED,
        authorization_not_before=NOT_BEFORE,
        authorization_expires_at=EXPIRES,
        maximum_uses=1,
        production_authorized=False,
        ubuntu_participation=False,
        acknowledged_restrictions=REQUIRED_RESTRICTIONS,
        cryptographic_identity_verified=False,
        canonical_digest="",
    )
    result = replace(result, **changes)
    return replace(result, canonical_digest=result.computed_digest())


def plan(value: CapabilityAuthorizationRequest | None = None):
    req = value or request()
    return CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req))


def assert_denied(code: str, callable_: object) -> None:
    with pytest.raises(CapabilityAuthorizationError) as error:
        callable_()
    assert error.value.code == code


@pytest.mark.parametrize("capability", tuple(ControlledActivationCapability))
def test_valid_independent_request_approval_and_test_only_grant_plan(capability):
    req = request(capability)
    result = CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req))
    assert result.validation.valid is True
    assert result.grant.capability is capability
    assert result.grant.maximum_uses == 1
    assert result.grant.production_authorized is False
    assert result.grant.ubuntu_participation is False
    assert result.grant.cryptographic_identity_verified is False
    assert result.decision is (
        CapabilityAuthorizationArchitectureDecision
        .READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION
    )


def test_capabilities_are_never_bundled_or_implied():
    monitoring = plan(request(ControlledActivationCapability.MONITORING_RUNTIME))
    dispatch = plan(request(ControlledActivationCapability.ALERT_DISPATCH))
    external = plan(request(ControlledActivationCapability.EXTERNAL_NOTIFICATION))
    assert {item.grant.capability for item in (monitoring, dispatch, external)} == {
        ControlledActivationCapability.MONITORING_RUNTIME,
        ControlledActivationCapability.ALERT_DISPATCH,
        ControlledActivationCapability.EXTERNAL_NOTIFICATION,
    }
    assert all(item.grant.request_id != monitoring.grant.request_id for item in (dispatch, external))


def test_canonical_json_and_all_digests_are_deterministic():
    req = request()
    app = approval(req)
    first = CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, app)
    second = CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, app)
    assert json.loads(req.canonical_json()) == req.as_dict()
    assert json.loads(app.canonical_json()) == app.as_dict()
    assert first.canonical_json() == second.canonical_json()
    assert req.computed_digest() == req.canonical_digest
    assert app.computed_digest() == app.canonical_digest
    assert first.computed_digest() == first.plan_digest


def test_timezone_normalization_and_injected_clock_are_deterministic():
    offset = timezone(timedelta(hours=9))
    req = request(
        requested_at=REQUESTED.astimezone(offset),
        requested_not_before=NOT_BEFORE.astimezone(offset),
        requested_expires_at=EXPIRES.astimezone(offset),
    )
    assert req.as_dict()["requested_at"] == "2026-07-31T12:00:00Z"
    first = CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req))
    second = CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req))
    assert first.validation.checked_at == second.validation.checked_at == NOW


@pytest.mark.parametrize(
    ("changes", "code"),
    (
        ({"capability": "UNKNOWN"}, "UNKNOWN_CAPABILITY"),
        ({"capability": ("AUDIT_WRITER", "REPLAY_WRITER")}, "MULTIPLE_CAPABILITIES_PROHIBITED"),
        ({"capability": ("AUDIT_WRITER", "AUDIT_WRITER")}, "DUPLICATE_CAPABILITY"),
        ({"branch": "main"}, "BRANCH_MISMATCH"),
        ({"commit": "0" * 40}, "COMMIT_MISMATCH"),
        ({"requester_identity": " "}, "REQUESTER_IDENTITY_MISSING"),
        ({"operator_identity": ""}, "OPERATOR_IDENTITY_MISSING"),
        ({"proposed_independent_approver_identity": ""}, "APPROVER_IDENTITY_MISSING"),
        ({"proposed_independent_approver_identity": "requester@example.test"}, "REQUESTER_APPROVER_COLLISION"),
        ({"proposed_independent_approver_identity": "mac-operator"}, "OPERATOR_APPROVER_COLLISION"),
        ({"operator_identity": "root"}, "ROOT_OPERATOR_PROHIBITED"),
        ({"production_authorized": True}, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
        ({"ubuntu_participation": True}, "UBUNTU_PARTICIPATION_PROHIBITED"),
        ({"requested_maximum_uses": 2}, "MAXIMUM_USES_INVALID"),
        ({"requested_not_before": REQUESTED.replace(tzinfo=None)}, "NAIVE_DATETIME"),
        ({"requested_expires_at": NOT_BEFORE}, "AUTHORIZATION_WINDOW_INVALID"),
        ({"requested_expires_at": NOT_BEFORE + timedelta(hours=2)}, "TTL_EXCESSIVE"),
        ({"bundled_capability_escalation": True}, "BUNDLED_CAPABILITY_ESCALATION_PROHIBITED"),
        ({"monitoring_implies_alert_dispatch": True}, "MONITORING_ESCALATION_PROHIBITED"),
        ({"alert_dispatch_implies_external_notification": True}, "ALERT_ESCALATION_PROHIBITED"),
    ),
)
def test_request_default_deny(changes, code):
    req = request()
    req = replace(req, **changes, canonical_digest="")
    req = replace(req, canonical_digest=req.computed_digest())
    assert_denied(code, lambda: CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req)))


@pytest.mark.parametrize(
    ("scope", "code"),
    (
        (CapabilityAuthorizationScope("PRODUCTION"), "SCOPE_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", authorization_from_environment=True), "ENVIRONMENT_AUTHORITY_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", api_route_authority=True), "API_AUTHORITY_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", runtime_command_execution=True), "RUNTIME_COMMAND_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", governance_authority="n8n"), "EXTERNAL_GOVERNANCE_OWNER_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", governance_authority="WordPress"), "EXTERNAL_GOVERNANCE_OWNER_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", governance_authority="WooCommerce"), "EXTERNAL_GOVERNANCE_OWNER_PROHIBITED"),
        (CapabilityAuthorizationScope("CONTROLLED_NON_PRODUCTION", state_owner="UbuntuWorker"), "EXTERNAL_GOVERNANCE_OWNER_PROHIBITED"),
    ),
)
def test_authority_and_operational_boundaries_default_deny(scope, code):
    req = request(scope=scope)
    assert_denied(code, lambda: CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req)))


@pytest.mark.parametrize(
    ("evidence_change", "code"),
    (
        ({"m3_readiness_binding": ""}, "M3_READINESS_INVALID"),
        ({"m3_readiness_binding": "INVALID"}, "M3_READINESS_INVALID"),
        ({"m4_a1_architecture_binding": ""}, "M4_A1_BINDING_INVALID"),
        ({"m4_a1_architecture_binding": "INVALID"}, "M4_A1_BINDING_INVALID"),
        ({"rollback_policy": ""}, "ROLLBACK_REQUIREMENT_MISSING"),
        ({"evidence_policy": ""}, "EVIDENCE_REQUIREMENT_MISSING"),
    ),
)
def test_readiness_rollback_and_evidence_default_deny(evidence_change, code):
    invalid_evidence = replace(evidence(ControlledActivationCapability.AUDIT_WRITER), **evidence_change)
    req = request(evidence=invalid_evidence)
    assert_denied(code, lambda: CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, approval(req)))


def test_capability_specific_evidence_default_deny():
    monitoring = request(
        ControlledActivationCapability.MONITORING_RUNTIME,
        evidence=replace(evidence(ControlledActivationCapability.MONITORING_RUNTIME), read_only_health_evidence=()),
    )
    assert_denied("READ_ONLY_HEALTH_EVIDENCE_INVALID", lambda: plan(monitoring))
    dispatch = request(
        ControlledActivationCapability.ALERT_DISPATCH,
        evidence=replace(evidence(ControlledActivationCapability.ALERT_DISPATCH), separately_authorized_capability_reference=None),
    )
    assert_denied("SEPARATE_CAPABILITY_REFERENCE_MISSING", lambda: plan(dispatch))


@pytest.mark.parametrize(
    ("changes", "code"),
    (
        ({"request_id": "other"}, "REQUEST_ID_MISMATCH"),
        ({"request_digest": "sha256:" + "0" * 64}, "REQUEST_DIGEST_MISMATCH"),
        ({"capability": "REPLAY_WRITER"}, "CAPABILITY_MISMATCH"),
        ({"independent_approver_identity": "other@example.test"}, "APPROVER_IDENTITY_MISMATCH"),
        ({"decision": CapabilityAuthorizationDecision.DENIED}, "APPROVAL_DECISION_DENIED"),
        ({"approval_timestamp": REQUESTED - timedelta(seconds=1)}, "APPROVAL_BEFORE_REQUEST"),
        ({"authorization_not_before": APPROVED - timedelta(seconds=1)}, "APPROVAL_WINDOW_INVALID"),
        ({"authorization_expires_at": EXPIRES + timedelta(seconds=1)}, "APPROVAL_WINDOW_INVALID"),
        ({"maximum_uses": 0}, "MAXIMUM_USES_INVALID"),
        ({"production_authorized": True}, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
        ({"ubuntu_participation": True}, "UBUNTU_PARTICIPATION_PROHIBITED"),
        ({"cryptographic_identity_verified": True}, "CRYPTOGRAPHIC_IDENTITY_UNSUPPORTED"),
        ({"acknowledged_restrictions": REQUIRED_RESTRICTIONS[:-1]}, "RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE"),
    ),
)
def test_approval_default_deny(changes, code):
    req = request()
    app = approval(req, **changes)
    assert_denied(code, lambda: CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, app))


def test_digest_tampering_and_expiry_default_deny():
    req = request()
    tampered = replace(req, requester_identity="tampered@example.test")
    assert_denied("REQUEST_DIGEST_MISMATCH", lambda: plan(tampered))
    app = approval(req)
    tampered_approval = replace(app, approval_id="tampered")
    assert_denied(
        "APPROVAL_DIGEST_MISMATCH",
        lambda: CapabilityAuthorizationPlanner(clock=lambda: NOW).plan(req, tampered_approval),
    )
    assert_denied(
        "REQUEST_EXPIRED",
        lambda: CapabilityAuthorizationPlanner(clock=lambda: EXPIRES).plan(req, app),
    )
    assert_denied(
        "GRANT_PLANNING_BEFORE_APPROVAL",
        lambda: CapabilityAuthorizationPlanner(clock=lambda: REQUESTED).plan(req, app),
    )


def test_all_public_contracts_are_immutable_and_canonical():
    req = request()
    app = approval(req)
    result = plan(req)
    restriction = CapabilityAuthorizationRestriction()
    for contract in (
        req.scope, req.evidence, req, app, restriction, result.validation,
        result.grant, result,
    ):
        assert json.loads(contract.canonical_json()) == contract.as_dict()
        assert contract.digest().startswith("sha256:")
        with pytest.raises((AttributeError, TypeError)):
            contract.invalid = True


def test_no_authorization_permit_claim_activation_or_operational_side_effect(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: calls.append("subprocess"))
    result = plan()
    assert calls == []
    assert (
        result.activation_authorizations_created,
        result.operational_permits_issued,
        result.live_claims_created,
        result.runtime_activations,
    ) == (0, 0, 0, 0)
    assert result.grant.authorization_created is False
    assert result.grant.permit_issued is False
    assert result.grant.claim_created is False
    assert result.grant.runtime_activation_authorized is False
    package = ROOT / "core/deployment/capability_authorization"
    forbidden = {
        "subprocess", "requests", "httpx", "ssh", "docker", "n8n",
        "wordpress", "woocommerce", "core.api", "core.worker",
    }
    for path in package.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        assert not any(
            imported == item or imported.startswith(item + ".")
            for imported in imports
            for item in forbidden
        )
