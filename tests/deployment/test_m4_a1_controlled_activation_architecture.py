from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from core.deployment.controlled_activation_architecture import (
    BASELINE_COMMIT,
    BRANCH,
    M3_READINESS,
    CANONICAL_CAPABILITY_ORDER,
    CAPABILITY_REGISTRY,
    ControlledActivationArchitectureConfig,
    ControlledActivationArchitectureDecision,
    ControlledActivationArchitectureError,
    ControlledActivationArchitectureValidationService,
    ControlledActivationCapability,
    ControlledActivationPlanRequest,
    ControlledActivationPlanner,
    ControlledActivationState,
    ControlledActivationStateMachine,
    ControlledActivationTransition,
)


ROOT = Path(__file__).resolve().parents[2]


def request(*capabilities: ControlledActivationCapability | str):
    return ControlledActivationPlanRequest(
        branch=BRANCH,
        commit=BASELINE_COMMIT,
        requested_capabilities=capabilities,
        requester_identity="requester@example.test",
        operator_identity="mac-operator@example.test",
        proposed_independent_approver_identity="approver@example.test",
        scope="CONTROLLED_NON_PRODUCTION",
        m3_readiness_binding=M3_READINESS,
    )


def transition(
    from_state: ControlledActivationState,
    to_state: ControlledActivationState,
    **changes: object,
) -> ControlledActivationTransition:
    values = {
        "capability": ControlledActivationCapability.AUDIT_WRITER,
        "from_state": from_state,
        "to_state": to_state,
        "branch": BRANCH,
        "commit": BASELINE_COMMIT,
        "evidence_artifacts": ("immutable-evidence.json",),
    }
    values.update(changes)
    return ControlledActivationTransition(**values)


def assert_code(code: str, callable_: object) -> None:
    with pytest.raises(ControlledActivationArchitectureError) as error:
        callable_()
    assert error.value.code == code


def test_complete_registry_defaults_and_eligibility():
    assert tuple(item.identifier for item in CAPABILITY_REGISTRY) == tuple(
        ControlledActivationCapability
    )
    assert all(item.default_state is ControlledActivationState.INACTIVE for item in CAPABILITY_REGISTRY)
    assert all(item.default_authorized is False for item in CAPABILITY_REGISTRY)
    assert all(item.production_eligible is False for item in CAPABILITY_REGISTRY)
    assert all(item.ubuntu_eligible is False for item in CAPABILITY_REGISTRY)


@pytest.mark.parametrize(
    "capability",
    (
        ControlledActivationCapability.AUDIT_WRITER,
        ControlledActivationCapability.REPLAY_WRITER,
        ControlledActivationCapability.MONITORING_RUNTIME,
    ),
)
def test_valid_single_capability_architecture_plans(capability):
    plan = ControlledActivationPlanner().plan(request(capability))
    assert plan.capability_order == (capability,)
    assert plan.steps[0].capability is capability
    assert plan.activation_authorizations_created == 0
    assert plan.operational_permits_issued == 0
    assert plan.live_claims_created == 0
    assert plan.runtime_side_effects == 0


def test_deterministic_canonical_order_plan_and_digest():
    requested = (
        ControlledActivationCapability.EXTERNAL_NOTIFICATION,
        ControlledActivationCapability.AUDIT_WRITER,
        ControlledActivationCapability.ALERT_DISPATCH,
    )
    first = ControlledActivationPlanner().plan(request(*requested))
    second = ControlledActivationPlanner().plan(request(*reversed(requested)))
    assert first.capability_order == tuple(
        item for item in CANONICAL_CAPABILITY_ORDER if item in requested
    )
    assert first.steps == second.steps
    assert first.plan_digest == second.plan_digest
    assert first.canonical_json() == second.canonical_json()


def test_multiple_capabilities_remain_independent_without_escalation():
    plan = ControlledActivationPlanner().plan(
        request(
            ControlledActivationCapability.MONITORING_RUNTIME,
            ControlledActivationCapability.ALERT_DISPATCH,
        )
    )
    monitoring, dispatch = plan.steps
    assert monitoring.required_authorization_contracts != dispatch.required_authorization_contracts
    assert monitoring.permit_boundary != dispatch.permit_boundary
    assert monitoring.claim_boundary != dispatch.claim_boundary
    assert monitoring.dependencies == ()
    assert dispatch.dependencies == (ControlledActivationCapability.MONITORING_RUNTIME,)
    assert ControlledActivationCapability.EXTERNAL_NOTIFICATION not in plan.capability_order


def test_dependency_satisfaction_never_adds_or_authorizes_capability():
    plan = ControlledActivationPlanner().plan(
        request(ControlledActivationCapability.EXTERNAL_NOTIFICATION)
    )
    assert plan.capability_order == (ControlledActivationCapability.EXTERNAL_NOTIFICATION,)
    assert plan.steps[0].dependencies == (ControlledActivationCapability.ALERT_DISPATCH,)
    assert plan.activation_authorizations_created == 0


def test_exact_state_machine_transitions_and_immutable_records():
    states = (
        ControlledActivationState.INACTIVE,
        ControlledActivationState.REQUESTED,
        ControlledActivationState.INDEPENDENTLY_APPROVED,
        ControlledActivationState.AUTHORIZED,
        ControlledActivationState.PERMITTED,
        ControlledActivationState.CLAIMED,
        ControlledActivationState.CONTROLLED_ACTIVE,
        ControlledActivationState.VALIDATED,
        ControlledActivationState.DEACTIVATED,
    )
    flags = (
        {},
        {"independent_approval_present": True},
        {"authorization_valid": True},
        {"single_use_permit_present": True},
        {"atomic_claim_count": 1},
        {"single_use_permit_present": True, "atomic_claim_count": 1},
        {},
        {"rollback_evidence_present": True},
    )
    machine = ControlledActivationStateMachine()
    for before, after, values in zip(states[:-1], states[1:], flags, strict=True):
        assert machine.validate(transition(before, after, **values)).valid is True
    with pytest.raises((AttributeError, TypeError)):
        transition(states[0], states[1]).to_state = states[2]


@pytest.mark.parametrize(
    ("record", "code"),
    (
        (
            transition(ControlledActivationState.INACTIVE, ControlledActivationState.AUTHORIZED),
            "SKIPPED_OR_BACKWARD_TRANSITION",
        ),
        (
            transition(
                ControlledActivationState.PERMITTED,
                ControlledActivationState.CLAIMED,
                atomic_claim_count=2,
            ),
            "EXACTLY_ONE_ATOMIC_CLAIM_REQUIRED",
        ),
        (
            transition(
                ControlledActivationState.AUTHORIZED,
                ControlledActivationState.PERMITTED,
                single_use_permit_present=True,
                permit_reusable=True,
            ),
            "REUSABLE_PERMIT_PROHIBITED",
        ),
        (
            transition(
                ControlledActivationState.CLAIMED,
                ControlledActivationState.CONTROLLED_ACTIVE,
                single_use_permit_present=True,
                atomic_claim_count=0,
            ),
            "ACTIVATION_BEFORE_PERMIT_CLAIM",
        ),
        (
            transition(
                ControlledActivationState.CLAIMED,
                ControlledActivationState.CONTROLLED_ACTIVE,
                single_use_permit_present=True,
                atomic_claim_count=1,
                production_transition=True,
            ),
            "PRODUCTION_TRANSITION_PROHIBITED",
        ),
        (
            transition(
                ControlledActivationState.INACTIVE,
                ControlledActivationState.REQUESTED,
                ubuntu_delegation=True,
            ),
            "UBUNTU_DELEGATION_PROHIBITED",
        ),
        (
            transition(
                ControlledActivationState.INACTIVE,
                ControlledActivationState.REQUESTED,
                environment_only=True,
            ),
            "ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED",
        ),
    ),
)
def test_invalid_transitions_are_default_denied(record, code):
    assert_code(code, lambda: ControlledActivationStateMachine().validate(record))


@pytest.mark.parametrize(
    ("changes", "code"),
    (
        ({"requested_capabilities": ("UNKNOWN",)}, "UNKNOWN_CAPABILITY"),
        (
            {
                "requested_capabilities": (
                    ControlledActivationCapability.AUDIT_WRITER,
                    ControlledActivationCapability.AUDIT_WRITER,
                )
            },
            "DUPLICATE_CAPABILITY",
        ),
        ({"branch": "main"}, "BRANCH_MISMATCH"),
        ({"commit": "0" * 40}, "COMMIT_MISMATCH"),
        ({"m3_readiness_binding": "INVALID"}, "M3_READINESS_INVALID"),
        ({"proposed_independent_approver_identity": "requester@example.test"}, "REQUESTER_APPROVER_COLLISION"),
        ({"operator_identity": "root"}, "ROOT_OPERATOR_PROHIBITED"),
        ({"scope": "LINUX_LIVE_CONTROL"}, "SCOPE_PROHIBITED"),
        ({"production_authorized": True}, "PRODUCTION_AUTHORIZATION_PROHIBITED"),
        ({"ubuntu_participation": True}, "UBUNTU_DELEGATION_PROHIBITED"),
        ({"environment_only_activation": True}, "ENVIRONMENT_ONLY_ACTIVATION_PROHIBITED"),
        ({"governance_authority": "n8n"}, "N8N_GOVERNANCE_PROHIBITED"),
        ({"business_logic_authority": "WordPress"}, "WORDPRESS_GOVERNANCE_PROHIBITED"),
        ({"business_logic_authority": "WooCommerce"}, "WOOCOMMERCE_GOVERNANCE_PROHIBITED"),
        ({"activation_authority": "API_WRITE_ROUTE"}, "API_ACTIVATION_AUTHORITY_PROHIBITED"),
        ({"state_owner": "UbuntuWorker"}, "UBUNTU_STATE_OWNER_PROHIBITED"),
        ({"caller_supplied_capability_order": ("AUDIT_WRITER",)}, "CALLER_ORDER_PROHIBITED"),
        ({"authorization_expired": True}, "AUTHORIZATION_EXPIRED"),
        ({"permit_single_use": False}, "REUSABLE_PERMIT_PROHIBITED"),
        ({"duplicate_claim_representation": True}, "DUPLICATE_CLAIM_PROHIBITED"),
        ({"rollback_required": False}, "ROLLBACK_REQUIREMENT_MISSING"),
        ({"evidence_required": False}, "EVIDENCE_REQUIREMENT_MISSING"),
        ({"bundled_implicit_escalation": True}, "IMPLICIT_CAPABILITY_ESCALATION"),
        ({"monitoring_implies_alert_dispatch": True}, "MONITORING_ESCALATION_PROHIBITED"),
        ({"alert_dispatch_implies_external_notification": True}, "ALERT_ESCALATION_PROHIBITED"),
        ({"arbitrary_command_execution": True}, "ARBITRARY_COMMAND_EXECUTION_PROHIBITED"),
        ({"runtime_subprocess_execution": True}, "RUNTIME_SUBPROCESS_PROHIBITED"),
    ),
)
def test_plan_request_default_deny(changes, code):
    invalid = replace(request(ControlledActivationCapability.AUDIT_WRITER), **changes)
    assert_code(code, lambda: ControlledActivationPlanner().plan(invalid))


def test_architecture_validation_facade_and_decision():
    plan = ControlledActivationArchitectureValidationService().validate_and_plan(
        ControlledActivationArchitectureConfig(),
        request(ControlledActivationCapability.AUDIT_WRITER),
    )
    assert plan.decision is (
        ControlledActivationArchitectureDecision
        .READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS
    )


def test_public_results_canonical_json_round_trip():
    plan = ControlledActivationPlanner().plan(
        request(ControlledActivationCapability.REPLAY_WRITER)
    )
    assert json.loads(plan.canonical_json()) == plan.as_dict()
    record = transition(
        ControlledActivationState.PERMITTED,
        ControlledActivationState.CLAIMED,
        atomic_claim_count=1,
    )
    result = ControlledActivationStateMachine().validate(record)
    assert json.loads(record.canonical_json()) == record.as_dict()
    assert json.loads(result.canonical_json()) == result.as_dict()


def test_no_runtime_boundary_or_actual_side_effects(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: calls.append("subprocess"))
    plan = ControlledActivationPlanner().plan(
        request(ControlledActivationCapability.AUDIT_WRITER)
    )
    assert calls == []
    assert (
        plan.activation_authorizations_created,
        plan.operational_permits_issued,
        plan.live_claims_created,
        plan.runtime_side_effects,
    ) == (0, 0, 0, 0)

    package = ROOT / "core/deployment/controlled_activation_architecture"
    forbidden_imports = {
        "subprocess", "core.worker", "core.api", "ssh", "docker", "n8n",
        "wordpress", "woocommerce", "requests", "httpx",
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
            imported == denied or imported.startswith(denied + ".")
            for imported in imports
            for denied in forbidden_imports
        )
