from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.deployment.m2_readiness import M2ReadinessDecision, M2ReadinessGate
from core.deployment.pilot_authorization import (
    PilotAuthorizationError,
    PilotAuthorizationRequest,
    PilotAuthorizationService,
    PilotAuthorizationStatus,
    PilotOperatorApproval,
    PilotRestriction,
    canonical_json,
)
from core.deployment.policy import validate_dependency_boundaries


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/deployment"
ISSUED = "2026-07-29T16:00:00Z"
EXPIRES = "2026-07-29T16:30:00Z"
NOW = "2026-07-29T16:10:00Z"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
COUNTERS = {
    "production_business_writes": 0,
    "persistent_audit_writes": 0,
    "persistent_nonce_writes": 0,
    "real_executor_invocations": 0,
    "sandbox_adapter_invocations": 0,
    "sandbox_artifact_writes": 0,
    "ubuntu_changes": 0,
    "runtime_commands": 0,
    "service_restarts": 0,
    "api_write_routes": 0,
    "pilot_activations": 0,
    "production_activations": 0,
}


def _readiness():
    evidence = json.loads((FIXTURES / "m2-readiness-passing.json").read_text("utf-8"))
    return M2ReadinessGate().evaluate(evidence, evaluated_at="2026-07-29T15:00:00Z")


def _authorization(**changes) -> dict:
    values = {
        "schema_version": "dpl/v1",
        "authorization_id": "exa-" + "1" * 32,
        "request_id": "apr-" + "2" * 32,
        "decision_id": "apd-" + "3" * 32,
        "package_digest": DIGEST_A,
        "plan_digest": DIGEST_B,
        "target_identity": "mac-mini-m4",
        "environment": "staging",
        "action_scope": ["act-" + "4" * 24],
        "requester_identity": "requester-01",
        "approver_identity": "dpl03-approver",
        "nonce": "dpl03-nonce-0001",
        "issued_timestamp": ISSUED,
        "expiry_timestamp": "2026-07-29T17:00:00Z",
        "maximum_uses": 1,
        "execution_authorized": True,
        "production_authorized": False,
        "executor_invoked": False,
        "production_writes": 0,
        "ubuntu_changes": 0,
    }
    values.update(changes)
    return values


def _request(**changes) -> PilotAuthorizationRequest:
    readiness = _readiness()
    values = {
        "execution_authorization_id": "exa-" + "1" * 32,
        "readiness_report_id": readiness.report_id,
        "readiness_report_digest": readiness.report_digest,
        "package_digest": DIGEST_A,
        "plan_digest": DIGEST_B,
        "target_identity": "mac-mini-m4",
        "target_owner": "mac-control-plane",
        "environment": "staging",
        "operation_scope": (
            "VERIFY_SANDBOX_TARGET",
            "PREPARE_SANDBOX",
            "COLLECT_EXECUTION_EVIDENCE",
        ),
        "sandbox_root_identity_digest": DIGEST_C,
        "requester_identity": "requester-01",
        "operator_identity": "operator-01",
        "nonce_reference": "nonce-digest-reference-0001",
        "issued_at": ISSUED,
        "expires_at": EXPIRES,
        "safety_counters": COUNTERS,
    }
    values.update(changes)
    return PilotAuthorizationRequest(**values)


def _approval(**changes) -> PilotOperatorApproval:
    values = {
        "approver_identity": "pilot-approver-01",
        "approver_role": "deployment-approver",
        "operator_identity": "operator-01",
        "approved": True,
        "issued_at": ISSUED,
        "expires_at": EXPIRES,
    }
    values.update(changes)
    return PilotOperatorApproval(**values)


def _decide(**changes):
    values = {
        "request": _request(),
        "approval": _approval(),
        "readiness_report": _readiness(),
        "execution_authorization": _authorization(),
        "evaluated_at": NOW,
    }
    values.update(changes)
    return PilotAuthorizationService().authorize(**values)


def test_immutable_contracts_schema_and_deterministic_permit() -> None:
    request = _request(operation_scope=tuple(reversed(_request().operation_scope)))
    with pytest.raises(FrozenInstanceError):
        request.environment = "test"
    with pytest.raises(TypeError):
        request.safety_counters["runtime_commands"] = 1
    first = _decide(request=request)
    second = _decide(request=_request())
    assert first.status is PilotAuthorizationStatus.AUTHORIZED
    assert first == second
    assert first.permit is not None
    assert first.permit.max_uses == 1
    assert first.permit.production_authorized is False
    assert first.permit.pilot_activation_started is False
    assert first.permit.permit_id == second.permit.permit_id
    assert first.permit.permit_digest == second.permit.permit_digest
    assert canonical_json(first) == canonical_json(second)
    assert first.restrictions == tuple(sorted(PilotRestriction, key=lambda item: item.value))


@pytest.mark.parametrize(
    ("request_change", "auth_change", "reason"),
    [
        ({"execution_authorization_id": "exa-" + "9" * 32}, {}, "EXECUTION_AUTHORIZATION_MISMATCH"),
        ({"package_digest": DIGEST_C}, {}, "PACKAGE_DIGEST_MISMATCH"),
        ({"plan_digest": DIGEST_C}, {}, "PLAN_DIGEST_MISMATCH"),
        ({"target_identity": "other-mac"}, {}, "TARGET_IDENTITY_MISMATCH"),
        ({"environment": "test"}, {}, "ENVIRONMENT_MISMATCH"),
    ],
)
def test_execution_authorization_exact_bindings(request_change, auth_change, reason) -> None:
    decision = _decide(
        request=_request(**request_change), execution_authorization=_authorization(**auth_change)
    )
    assert decision.status is PilotAuthorizationStatus.DENIED
    assert reason in decision.reason_codes


def test_readiness_acceptance_digest_and_integrity_required() -> None:
    report = _readiness()
    assert "READINESS_REPORT_DIGEST_MISMATCH" in _decide(
        request=_request(readiness_report_digest=DIGEST_C)
    ).reason_codes
    assert "READINESS_NOT_ACCEPTED" in _decide(
        readiness_report=replace(report, decision=M2ReadinessDecision.NOT_READY)
    ).reason_codes
    assert "READINESS_REPORT_INTEGRITY_INVALID" in _decide(
        readiness_report=replace(report, report_digest=DIGEST_C)
    ).reason_codes


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"target_owner": "ubuntu-worker"}, "TARGET_OWNER_DENIED"),
        ({"target_owner": "external"}, "TARGET_OWNER_DENIED"),
        ({"environment": "production"}, "ENVIRONMENT_DENIED"),
        ({"environment": "prod"}, "ENVIRONMENT_DENIED"),
        ({"environment": "live"}, "ENVIRONMENT_DENIED"),
        ({"environment": "customer-production"}, "ENVIRONMENT_DENIED"),
        ({"environment": "privileged-unknown"}, "ENVIRONMENT_DENIED"),
        ({"operation_scope": ("SIMULATE_EXECUTION",)}, "OPERATION_SCOPE_DENIED"),
        ({"operation_scope": ("RUN_COMMAND",)}, "OPERATION_SCOPE_DENIED"),
        ({"sandbox_root_identity_digest": ""}, "IDENTITY_OR_BINDING_EVIDENCE_MISSING"),
        ({"max_uses": 2}, "MAX_USES_INVALID"),
        ({"production_authorized": True}, "PRODUCTION_AUTHORIZATION_DENIED"),
        ({"pilot_activation_requested": True}, "PILOT_ACTIVATION_DENIED"),
        ({"persistent_sqlite_audit_operational": True}, "PERSISTENT_SQLITE_AUDIT_CLAIM_DENIED"),
        ({"expires_at": ISSUED}, "INVALID_EXPIRATION"),
        ({"expires_at": "2026-07-29T17:01:00Z"}, "MAXIMUM_LIFETIME_EXCEEDED"),
    ],
)
def test_default_denials(changes, reason) -> None:
    decision = _decide(request=_request(**changes))
    assert decision.status is PilotAuthorizationStatus.DENIED
    assert reason in decision.reason_codes
    assert decision.permit is None


def test_expired_nonzero_safety_and_separation_of_duties_denied() -> None:
    assert "REQUEST_EXPIRED" in _decide(evaluated_at=EXPIRES).reason_codes
    counters = dict(COUNTERS)
    counters["persistent_audit_writes"] = 1
    assert "NONZERO_SAFETY_COUNTER" in _decide(
        request=_request(safety_counters=counters)
    ).reason_codes
    assert "REQUESTER_APPROVER_SEPARATION_FAILED" in _decide(
        approval=_approval(approver_identity="requester-01")
    ).reason_codes
    assert "OPERATOR_APPROVER_SEPARATION_FAILED" in _decide(
        approval=_approval(approver_identity="operator-01")
    ).reason_codes
    assert "APPROVER_ROLE_DENIED" in _decide(
        approval=_approval(approver_role="unknown-role")
    ).reason_codes
    assert "OPERATOR_IDENTITY_MISMATCH" in _decide(
        approval=_approval(operator_identity="other-operator")
    ).reason_codes


@pytest.mark.parametrize(
    "missing",
    ["request", "approval", "readiness_report", "execution_authorization"],
)
def test_missing_evidence_is_blocked(missing: str) -> None:
    decision = _decide(**{missing: None})
    assert decision.status is PilotAuthorizationStatus.BLOCKED


def test_malformed_evidence_is_blocked() -> None:
    authorization = _authorization()
    authorization["maximum_uses"] = "one"
    assert _decide(execution_authorization=authorization).status is PilotAuthorizationStatus.BLOCKED


@pytest.mark.parametrize(
    "field",
    [
        "password", "api_key", "access_token", "private_key", "cookie",
        "authorization_header", "raw_environment", "shell", "command", "argv", "script",
    ],
)
def test_secret_and_executable_fields_rejected(field: str) -> None:
    values = dict(COUNTERS)
    values[field] = 0
    with pytest.raises(PilotAuthorizationError):
        _request(safety_counters=values)


def test_safe_fixtures_are_immutable_policy_inputs() -> None:
    expected = {
        "m2-p1-pilot-accepted.json": "accepted",
        "m2-p1-readiness-digest-mismatch.json": "readiness_digest_mismatch",
        "m2-p1-separation-of-duty-failure.json": "separation_of_duty_failure",
        "m2-p1-expired-request.json": "expired",
        "m2-p1-production-request.json": "production",
        "m2-p1-ubuntu-target-request.json": "ubuntu_target",
    }
    for name, scenario in expected.items():
        value = json.loads((FIXTURES / name).read_text("utf-8"))
        assert value == {"schema_version": "dpl/m2-p1-fixture/v1", "scenario": scenario}
        assert "credential" not in canonical_json(value)
        assert "production_authorized" not in value


def test_dependency_boundary_and_no_runtime_or_persistent_implementation() -> None:
    forbidden = {
        "core.api", "core.worker", "core.deployment.sandbox_adapter",
        "subprocess", "socket", "requests", "paramiko", "sqlite3",
    }
    text = ""
    for source in (ROOT / "core/deployment/pilot_authorization").glob("*.py"):
        source_text = source.read_text("utf-8")
        text += source_text
        tree = ast.parse(source_text)
        imports = {
            node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        }
        assert not any(
            item == prefix or item.startswith(prefix + ".")
            for item in imports for prefix in forbidden
        )
    for marker in (
        "MacSandboxAdapter", ".consume(", ".db", ".sqlite", "connect(",
        "UbuntuWorkerClient", "CommandRunner",
    ):
        assert marker not in text
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    assert report["production_authorized"] is False
