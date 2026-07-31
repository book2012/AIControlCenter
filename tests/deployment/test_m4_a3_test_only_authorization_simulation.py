from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.deployment.capability_authorization import REQUIRED_RESTRICTIONS
from core.deployment.capability_authorization_simulation import *
from core.deployment.controlled_activation_architecture import ControlledActivationCapability

NOW = datetime(2026, 7, 31, 12, 0, tzinfo=timezone.utc)
DIGEST = "sha256:" + "a" * 64


def make_request(capability=ControlledActivationCapability.AUDIT_WRITER, **changes):
    dependency = {
        ControlledActivationCapability.ALERT_DISPATCH:
            ControlledActivationCapability.MONITORING_RUNTIME,
        ControlledActivationCapability.EXTERNAL_NOTIFICATION:
            ControlledActivationCapability.ALERT_DISPATCH,
    }.get(capability)
    request = TestOnlyAuthorizationSimulationRequest(
        simulation_id=f"m4-a3-test-simulation-{str(capability).lower()}",
        scenario_id=f"scenario-{str(capability).lower()}",
        scenario_seed="fixed-seed",
        capability=capability,
        branch=BRANCH,
        commit=BASELINE_COMMIT,
        requester_identity="requester@example.test",
        operator_identity="mac-operator",
        independent_approver_identity="approver@example.test",
        request_digest=DIGEST,
        approval_digest="sha256:" + "b" * 64,
        grant_plan_digest="sha256:" + "c" * 64,
        requested_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(minutes=30),
        acknowledged_restrictions=REQUIRED_RESTRICTIONS,
        dependency_authorization_reference=dependency.value if dependency else None,
        dependency_authorization_digest=DIGEST if dependency else None,
    )
    return replace(request, **changes)


def simulate(request=None, config=None, guard=None):
    return TestOnlyAuthorizationSimulator(
        clock=lambda: NOW, scenario_seed="fixed-seed", replay_guard=guard
    ).simulate(config or TestOnlyAuthorizationSimulationConfig(), request or make_request())


@pytest.mark.parametrize("capability", tuple(ControlledActivationCapability))
def test_each_capability_is_deterministic_and_independent(capability):
    first = simulate(make_request(capability))
    second = simulate(make_request(capability))
    assert first.decision is TestOnlyAuthorizationSimulationDecision.READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION
    assert first.canonical_json() == second.canonical_json()
    assert first.authorization.capability is capability
    assert first.permit.capability is capability
    assert first.claim.capability is capability
    assert first.authorization.authorization_id.startswith("m4-a3-test-authorization-")
    assert first.permit.permit_id.startswith("m4-a3-test-permit-")
    assert first.claim.claim_id.startswith("m4-a3-test-claim-")
    assert json.loads(first.canonical_json()) == first.as_dict()
    assert all(item.canonical_artifact_digest == item.computed_digest()
               for item in first.evidence)


def test_chronological_chain_and_markers():
    result = simulate()
    validate_evidence_chain(result.evidence)
    assert tuple(item.state for item in result.evidence) == tuple(TestOnlyAuthorizationStep)
    assert all(a.timestamp < b.timestamp for a, b in zip(result.evidence, result.evidence[1:]))
    for artifact in (result.authorization, result.permit, result.claim):
        assert artifact.test_only and not artifact.operationally_valid
        assert not artifact.production_authorized and not artifact.ubuntu_participation
        assert not artifact.runtime_activation_allowed
        assert artifact.namespace == TEST_NAMESPACE


def test_one_claim_duplicate_claim_and_permit_reuse_rejected():
    guard = InMemoryTestOnlyReplayGuard()
    first = simulate(guard=guard)
    second = simulate(guard=guard)
    assert first.claim is not None
    assert second.decision is TestOnlyAuthorizationSimulationDecision.BLOCKED
    assert second.errors == ("DUPLICATE_SIMULATED_CLAIM",)
    with pytest.raises(TestOnlyAuthorizationSimulationError, match="SIMULATED_PERMIT_REUSE"):
        guard.reject_reuse(first.permit.permit_id)


@pytest.mark.parametrize(("changes", "code"), (
    ({"capability": "UNKNOWN"}, "UNKNOWN_CAPABILITY"),
    ({"capability": ("AUDIT_WRITER", "REPLAY_WRITER")}, "MULTIPLE_CAPABILITIES_PROHIBITED"),
    ({"capability": ("AUDIT_WRITER", "AUDIT_WRITER")}, "DUPLICATE_CAPABILITY"),
    ({"branch": "main"}, "BRANCH_MISMATCH"),
    ({"commit": "0" * 40}, "COMMIT_MISMATCH"),
    ({"independent_approver_identity": ""}, "INDEPENDENT_APPROVER_MISSING"),
    ({"independent_approver_identity": "requester@example.test"}, "REQUESTER_APPROVER_COLLISION"),
    ({"independent_approver_identity": "mac-operator"}, "OPERATOR_APPROVER_COLLISION"),
    ({"operator_identity": "root"}, "ROOT_OPERATOR_PROHIBITED"),
    ({"expires_at": NOW}, "APPROVAL_EXPIRED"),
    ({"expires_at": NOW + timedelta(hours=2)}, "TTL_EXCESSIVE"),
    ({"acknowledged_restrictions": ()}, "RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE"),
    ({"acknowledged_restrictions": REQUIRED_RESTRICTIONS[:-1]}, "RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE"),
    ({"request_digest": ""}, "REQUEST_DIGEST_MISSING"),
    ({"approval_digest": ""}, "APPROVAL_DIGEST_MISSING"),
    ({"grant_plan_digest": ""}, "GRANT_PLAN_DIGEST_MISSING"),
    ({"monitoring_implies_alert_dispatch": True}, "MONITORING_ESCALATION_PROHIBITED"),
    ({"alert_dispatch_implies_external_notification": True}, "ALERT_ESCALATION_PROHIBITED"),
))
def test_request_negative_scenarios_fail_closed(changes, code):
    result = simulate(make_request(**changes))
    assert result.decision is TestOnlyAuthorizationSimulationDecision.BLOCKED
    assert result.errors == (code,)
    assert result.authorization is result.permit is result.claim is None


@pytest.mark.parametrize(("changes", "code"), (
    ({"m3_binding": "bad"}, "M3_BINDING_INVALID"),
    ({"m4_a1_binding": "bad"}, "M4_A1_BINDING_INVALID"),
    ({"m4_a2_binding": "bad"}, "M4_A2_BINDING_INVALID"),
    ({"test_only": False}, "TEST_ONLY_MARKER_MISSING"),
    ({"operationally_valid": True}, "OPERATIONAL_VALIDITY_PROHIBITED"),
    ({"production_authorized": True}, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
    ({"ubuntu_participation": True}, "UBUNTU_PARTICIPATION_PROHIBITED"),
    ({"runtime_activation_allowed": True}, "RUNTIME_ACTIVATION_PROHIBITED"),
    ({"namespace": "operational"}, "TEST_NAMESPACE_INVALID"),
    ({"maximum_uses": 2}, "MAXIMUM_USES_INVALID"),
    ({"environment_only_authorization": True}, "ENVIRONMENT_AUTHORITY_PROHIBITED"),
    ({"api_route_authority": True}, "API_AUTHORITY_PROHIBITED"),
    ({"external_governance_authority": "n8n"}, "EXTERNAL_GOVERNANCE_AUTHORITY_PROHIBITED"),
    ({"external_governance_authority": "WordPress"}, "EXTERNAL_GOVERNANCE_AUTHORITY_PROHIBITED"),
    ({"external_governance_authority": "WooCommerce"}, "EXTERNAL_GOVERNANCE_AUTHORITY_PROHIBITED"),
    ({"external_governance_authority": "Ubuntu"}, "EXTERNAL_GOVERNANCE_AUTHORITY_PROHIBITED"),
    ({"subprocess_execution": True}, "SUBPROCESS_PROHIBITED"),
    ({"runtime_command_execution": True}, "RUNTIME_COMMAND_PROHIBITED"),
    ({"network_access": True}, "NETWORK_ACCESS_PROHIBITED"),
))
def test_configuration_negative_scenarios_fail_closed(changes, code):
    result = simulate(config=replace(TestOnlyAuthorizationSimulationConfig(), **changes))
    assert result.decision is TestOnlyAuthorizationSimulationDecision.BLOCKED
    assert result.errors == (code,)


def test_dependency_reference_is_not_cross_authorization():
    monitoring = simulate(make_request(ControlledActivationCapability.MONITORING_RUNTIME))
    dispatch = simulate(make_request(ControlledActivationCapability.ALERT_DISPATCH))
    external = simulate(make_request(ControlledActivationCapability.EXTERNAL_NOTIFICATION))
    assert dispatch.scenario.dependency_authorization_reference == "MONITORING_RUNTIME"
    assert external.scenario.dependency_authorization_reference == "ALERT_DISPATCH"
    assert len({x.authorization.capability for x in (monitoring, dispatch, external)}) == 3


def test_binding_and_evidence_tampering_fail_closed():
    result = simulate()
    with pytest.raises(TestOnlyAuthorizationSimulationError, match="CAPABILITY_MISMATCH"):
        validate_bindings(result.authorization,
                          replace(result.permit, capability=ControlledActivationCapability.REPLAY_WRITER),
                          result.claim)
    with pytest.raises(TestOnlyAuthorizationSimulationError, match="PRIOR_STEP_DIGEST_TAMPERED"):
        validate_evidence_chain((result.evidence[0],
            replace(result.evidence[1], prior_step_digest=DIGEST), *result.evidence[2:]))
    with pytest.raises(TestOnlyAuthorizationSimulationError, match="SKIPPED_SIMULATION_STATE"):
        validate_evidence_chain(result.evidence[:-1])
    with pytest.raises(TestOnlyAuthorizationSimulationError, match="NON_MONOTONIC_TIMESTAMP"):
        validate_evidence_chain((result.evidence[0],
            replace(result.evidence[1], timestamp=result.evidence[0].timestamp,
                    prior_step_digest=result.evidence[0].canonical_artifact_digest,
                    canonical_artifact_digest=""), *result.evidence[2:]))


def test_live_boundaries_reject_artifacts_and_field_renaming_cannot_convert():
    result = simulate()
    for artifact in (result.authorization, result.permit, result.claim):
        with pytest.raises(TestOnlyAuthorizationSimulationError, match="OPERATIONALLY_INVALID"):
            reject_at_operational_boundary(artifact)
        renamed = artifact.as_dict()
        renamed.pop("test_only")
        renamed["id"] = renamed.pop(next(k for k in tuple(renamed) if k.endswith("_id")))
        with pytest.raises(TestOnlyAuthorizationSimulationError, match="OPERATIONALLY_INVALID"):
            reject_at_operational_boundary(type("Renamed", (), renamed)())


def test_optional_report_is_confined_to_injected_test_root(tmp_path):
    result = simulate()
    path = emit_json_report(result, root=tmp_path, relative_name="m4-a3/report.json")
    assert path.read_text() == result.canonical_json()
    with pytest.raises(TestOnlyAuthorizationSimulationError, match="REPORT_PATH_PROHIBITED"):
        emit_json_report(result, root=tmp_path, relative_name="../escape.json")
