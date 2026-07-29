from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.deployment.executor_contracts import create_executor_result
from core.deployment.m2_readiness import M2ReadinessDecision, M2ReadinessGate
from core.deployment.pilot_activation import (
    InMemoryPilotPermitUseRegistry, PilotActivationError,
    PilotActivationRequest, PilotActivationService, PilotActivationStatus,
    canonical_json,
)
from core.deployment.pilot_authorization import (
    PilotAuthorizationRequest, PilotAuthorizationService, PilotOperatorApproval,
)
from core.deployment.policy import validate_dependency_boundaries
from core.deployment.sandbox_adapter import MacSandboxAdapter

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/deployment"
STAMP = "2026-07-29T16:10:00Z"
ISSUED = "2026-07-29T16:00:00Z"
EXPIRES = "2026-07-29T16:30:00Z"
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64
OPS = ("COLLECT_EXECUTION_EVIDENCE", "PREPARE_SANDBOX", "VERIFY_SANDBOX_TARGET")
ORDERED = ("VERIFY_SANDBOX_TARGET", "PREPARE_SANDBOX", "COLLECT_EXECUTION_EVIDENCE")
ZERO = {
    "production_business_writes": 0, "persistent_audit_writes": 0,
    "persistent_nonce_writes": 0, "ubuntu_changes": 0, "runtime_commands": 0,
    "service_restarts": 0, "api_write_routes": 0, "production_activations": 0,
}


def readiness():
    evidence = json.loads((FIXTURES / "m2-readiness-passing.json").read_text())
    return M2ReadinessGate().evaluate(evidence, evaluated_at="2026-07-29T15:00:00Z")


def authorization(**changes):
    value = {
        "schema_version": "dpl/v1", "authorization_id": "exa-" + "1" * 32,
        "request_id": "apr-" + "2" * 32, "decision_id": "apd-" + "3" * 32,
        "package_digest": DIGEST_A, "plan_digest": DIGEST_B,
        "target_identity": "mac-mini-m4", "environment": "staging",
        "action_scope": ["act-" + "4" * 24], "requester_identity": "requester-01",
        "approver_identity": "dpl03-approver", "nonce": "dpl03-nonce-0001",
        "issued_timestamp": ISSUED, "expiry_timestamp": "2026-07-29T17:00:00Z",
        "maximum_uses": 1, "execution_authorized": True,
        "production_authorized": False, "executor_invoked": False,
        "production_writes": 0, "ubuntu_changes": 0,
    }
    value.update(changes)
    return value


def permit():
    ready = readiness()
    request = PilotAuthorizationRequest(
        execution_authorization_id="exa-" + "1" * 32,
        readiness_report_id=ready.report_id, readiness_report_digest=ready.report_digest,
        package_digest=DIGEST_A, plan_digest=DIGEST_B,
        target_identity="mac-mini-m4", target_owner="mac-control-plane",
        environment="staging", operation_scope=OPS,
        sandbox_root_identity_digest=DIGEST_C, requester_identity="requester-01",
        operator_identity="operator-01", nonce_reference="safe-reference",
        issued_at=ISSUED, expires_at=EXPIRES, safety_counters=ZERO,
    )
    approval = PilotOperatorApproval(
        approver_identity="pilot-approver-01", approver_role="deployment-approver",
        operator_identity="operator-01", approved=True, issued_at=ISSUED, expires_at=EXPIRES,
    )
    decision = PilotAuthorizationService().authorize(
        request=request, approval=approval, readiness_report=ready,
        execution_authorization=authorization(), evaluated_at=STAMP,
    )
    assert decision.permit is not None
    return decision.permit


def activation_request(**changes):
    value = permit()
    fields = {
        "permit": value, "permit_id": value.permit_id, "permit_digest": value.permit_digest,
        "execution_authorization_id": value.execution_authorization_id,
        "readiness_report_id": value.readiness_report_id,
        "readiness_report_digest": value.readiness_report_digest,
        "package_digest": value.package_digest, "plan_digest": value.plan_digest,
        "target_identity": value.target_identity, "target_owner": value.target_owner,
        "environment": value.environment, "operation_scope": OPS,
        "sandbox_root_identity_digest": value.sandbox_root_identity_digest,
        "requester_identity": value.requester_identity,
        "operator_identity": value.operator_identity,
        "approver_identity": value.approver_identity,
        "activation_id": "m2a-" + "5" * 32, "activation_timestamp": STAMP,
        "safety_counters": ZERO,
    }
    fields.update(changes)
    return PilotActivationRequest(**fields)


class FakeExecutor:
    def __init__(self, capability, fail_at=None, mutate=None):
        self.cap = capability
        self.fail_at = fail_at
        self.mutate = mutate
        self.calls = []

    def execute(self, request, *, result_timestamp):
        operation = request["operation_scope"][0]
        self.calls.append(operation)
        status = "DENIED" if operation == self.fail_at else "ALLOWED"
        result = create_executor_result(
            request=request, capability=self.cap, status=status,
            reason_codes=("TEST_FAILURE",) if status == "DENIED" else (),
            result_timestamp=result_timestamp,
        )
        if self.mutate:
            result = dict(result)
            self.mutate(result)
        return result


def adapter_and_service(tmp_path):
    adapter = MacSandboxAdapter(
        sandbox_root=tmp_path, authorization=authorization(), environment="staging",
        capability_timestamp=STAMP, repository_root=ROOT,
    )
    registry = InMemoryPilotPermitUseRegistry()
    return adapter, registry, PilotActivationService(
        executor=adapter, capability=adapter.capability(), registry=registry
    )


def fake_service(fail_at=None, mutate=None, registry=None):
    adapter = MacSandboxAdapter(
        sandbox_root=None, authorization=authorization(), environment="staging",
        capability_timestamp=STAMP, repository_root=ROOT,
    )
    fake = FakeExecutor(adapter.capability(), fail_at, mutate)
    registry = registry or InMemoryPilotPermitUseRegistry()
    return fake, registry, PilotActivationService(
        executor=fake, capability=adapter.capability(), registry=registry
    )


def test_exactly_one_successful_controlled_pytest_activation(tmp_path):
    adapter, registry, service = adapter_and_service(tmp_path)
    request = activation_request()
    first = service.activate(
        request=request, readiness_report=readiness(),
        execution_authorization=authorization(),
    )
    assert first.status is PilotActivationStatus.ACTIVATED
    assert registry.is_consumed(request.permit_id)
    assert [step.operation for step in first.receipt.evidence.ordered_steps] == list(ORDERED)
    assert first.receipt.permit_consumed is True
    assert first.receipt.controlled_test_sandbox is True
    assert first.receipt.production_authorized is False
    assert first.receipt.production_writes == first.receipt.repository_runtime_writes == 0
    assert first.receipt.ubuntu_changes == first.receipt.network_accesses == 0
    assert first.receipt.runtime_commands == first.receipt.service_restarts == 0
    assert first.receipt.evidence.evidence_digests == tuple(sorted(first.receipt.evidence.evidence_digests))
    receipt_semantic = first.receipt.to_dict()
    receipt_digest = receipt_semantic.pop("receipt_digest")
    assert receipt_digest == "sha256:" + hashlib.sha256(
        canonical_json(receipt_semantic).encode()
    ).hexdigest()
    assert (tmp_path / "artifacts").is_dir()
    assert not any(path.is_file() for path in ROOT.glob("**/manifest.json"))
    replay = service.activate(
        request=request, readiness_report=readiness(),
        execution_authorization=authorization(),
    )
    assert replay.status is PilotActivationStatus.REPLAYED


def test_immutable_canonical_and_stable_identity_contracts():
    request = activation_request()
    with pytest.raises(FrozenInstanceError):
        request.environment = "test"
    with pytest.raises(TypeError):
        request.safety_counters["runtime_commands"] = 1
    assert request.activation_id == activation_request().activation_id
    assert canonical_json(request) == canonical_json(activation_request())


@pytest.mark.parametrize("operation", ORDERED)
def test_each_adapter_failure_stops_and_consumes(operation):
    fake, registry, service = fake_service(fail_at=operation)
    request = activation_request()
    decision = service.activate(
        request=request, readiness_report=readiness(), execution_authorization=authorization()
    )
    assert decision.status is PilotActivationStatus.FAILED
    assert fake.calls[-1] == operation
    assert len(fake.calls) == ORDERED.index(operation) + 1
    assert registry.is_consumed(request.permit_id)
    replay = service.activate(
        request=request, readiness_report=readiness(), execution_authorization=authorization()
    )
    assert replay.status is PilotActivationStatus.REPLAYED


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda value: value.pop("result_digest"), "MALFORMED_ADAPTER_RESULT"),
        (lambda value: value.update(request_id="exr-" + "0" * 32), "ADAPTER_RESULT_BINDING_MISMATCH"),
        (lambda value: value.update(network_accesses=1), "NONZERO_ADAPTER_SAFETY_COUNTER"),
    ],
)
def test_malformed_binding_and_safety_result_fail_closed(mutate, reason):
    fake, registry, service = fake_service(mutate=mutate)
    request = activation_request()
    decision = service.activate(
        request=request, readiness_report=readiness(), execution_authorization=authorization()
    )
    assert decision.status is PilotActivationStatus.FAILED
    assert reason in decision.reason_codes
    assert registry.is_consumed(request.permit_id)
    assert len(fake.calls) == 1


@pytest.mark.parametrize(
    ("changes", "ready_change", "auth_change", "reason"),
    [
        ({"activation_timestamp": EXPIRES}, None, {}, "PERMIT_EXPIRED"),
        ({"environment": "production"}, None, {"environment": "production"}, "ENVIRONMENT_DENIED"),
        ({"target_owner": "ubuntu-worker"}, None, {}, "TARGET_DENIED"),
        ({"sandbox_root_identity_digest": DIGEST_A}, None, {}, "SANDBOX_ROOT_IDENTITY_MISMATCH"),
        ({"permit_digest": DIGEST_A}, None, {}, "PERMIT_DIGEST_MISMATCH"),
        ({"operation_scope": ("VERIFY_SANDBOX_TARGET",)}, None, {}, "OPERATION_SCOPE_MISMATCH"),
        ({}, M2ReadinessDecision.NOT_READY, {}, "READINESS_EVIDENCE_CHANGED"),
        ({"package_digest": DIGEST_C}, None, {}, "PACKAGE_DIGEST_MISMATCH"),
        ({"plan_digest": DIGEST_C}, None, {}, "PLAN_DIGEST_MISMATCH"),
    ],
)
def test_pre_invocation_default_denials(changes, ready_change, auth_change, reason):
    fake, registry, service = fake_service()
    report = readiness()
    if ready_change:
        report = replace(report, decision=ready_change)
    decision = service.activate(
        request=activation_request(**changes), readiness_report=report,
        execution_authorization=authorization(**auth_change),
    )
    assert decision.status is PilotActivationStatus.DENIED
    assert reason in decision.reason_codes
    assert fake.calls == []
    assert not registry.is_consumed(activation_request().permit_id)


def test_missing_adapter_and_registry_default_deny():
    request = activation_request()
    adapter = MacSandboxAdapter(
        sandbox_root=None, authorization=authorization(), environment="staging",
        capability_timestamp=STAMP,
    )
    assert PilotActivationService(
        executor=None, capability=None, registry=InMemoryPilotPermitUseRegistry()
    ).activate(
        request=request, readiness_report=readiness(), execution_authorization=authorization()
    ).status is PilotActivationStatus.BLOCKED
    assert PilotActivationService(
        executor=adapter, capability=adapter.capability(), registry=None
    ).activate(
        request=request, readiness_report=readiness(), execution_authorization=authorization()
    ).status is PilotActivationStatus.BLOCKED


@pytest.mark.parametrize(
    "field",
    ["password", "api_key", "token", "private_key", "cookies",
     "authorization_header", "raw_environment", "shell", "command", "argv", "script"],
)
def test_schema_security_fields_rejected(field):
    counters = dict(ZERO)
    counters[field] = 0
    with pytest.raises(PilotActivationError):
        activation_request(safety_counters=counters)


def test_fixtures_are_safe_and_complete():
    expected = {
        "m2-p2-controlled-success.json": "controlled_success",
        "m2-p2-replay.json": "replay", "m2-p2-expired-permit.json": "expired_permit",
        "m2-p2-root-digest-mismatch.json": "root_digest_mismatch",
        "m2-p2-operation-mismatch.json": "operation_mismatch",
        "m2-p2-adapter-failure.json": "adapter_failure",
    }
    for name, scenario in expected.items():
        value = json.loads((FIXTURES / name).read_text())
        assert value == {"schema_version": "dpl/m2-p2-fixture/v1", "scenario": scenario}
        assert not any(marker in canonical_json(value) for marker in ("password", "token", "secret"))


def test_dependencies_and_compatibility_are_safe():
    forbidden = {
        "subprocess", "socket", "requests", "paramiko", "sqlite3",
        "core.api", "core.worker", "core.deployment.sandbox_adapter",
    }
    text = ""
    for source in (ROOT / "core/deployment/pilot_activation").glob("*.py"):
        content = source.read_text()
        text += content
        tree = ast.parse(content)
        imports = {
            node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        }
        assert not any(item == prefix or item.startswith(prefix + ".") for item in imports for prefix in forbidden)
    assert "MacSandboxAdapter" not in text
    assert not list((ROOT / "core/deployment/pilot_activation").glob("*.db"))
    assert not list((ROOT / "core/deployment/pilot_activation").glob("*.sqlite*"))
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    assert report["production_authorized"] is False
