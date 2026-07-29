from __future__ import annotations

import ast
import copy
import importlib
import json
from pathlib import Path

import pytest

from core.deployment.authorization import (
    AuthorizationInputError,
    create_approval_decision,
    create_approval_request,
    materialize_execution_authorization,
)
from core.deployment.contracts import (
    DeploymentContractValidationError,
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.planning import DeploymentPlanBuilder
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/deployment"
ISSUED = "2026-07-29T01:00:00Z"
EXPIRES = "2026-07-29T02:00:00Z"
NOW = "2026-07-29T01:30:00Z"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def _plan() -> dict:
    package = _load("immutable-deployment-package.json")
    inventory = _load("inventory-result.json")
    template = inventory["items"][0]
    inventory["items"] = [
        {
            **copy.deepcopy(template),
            "component_id": component,
            "component_type": "policy" if "policy" in component else "observation",
        }
        for component in (
            "git-repository", "runtime-metadata", "mac-production-profile",
            "launchd-services", "host-caddy", "public-edge-policy",
        )
    ]
    policy = {
        "schema_version": "dpl/v1",
        "policy_digest": "sha256:" + "1" * 64,
        "repository_root_identity": "AIControlCenter",
        "analyzed_files": [],
        "classified_modules": [],
        "allowed_imports": [],
        "violations": [],
        "quarantine_findings": [],
        "warnings": [],
        "overall_result": "PASS",
        "production_authorized": False,
        "production_writes": 0,
        "ubuntu_changes": 0,
    }
    return DeploymentPlanBuilder().build(
        package=package,
        package_digest=sha256_digest(package),
        mac_inventory=inventory,
        ingress_readiness=_load("ingress-readiness-report.json"),
        dependency_policy=policy,
        target_profile={
            "target_id": "mac-mini-m4",
            "platform": "macos",
            "role": "control-plane",
            "profile": "mac-standalone-production",
            "control_plane_owner": "aicontrolcenter",
            "public_edge_owner": "host-caddy",
            "cms_owner": "wordpress",
            "commerce_owner": "woocommerce",
        },
        actor_identity="test-actor",
        context_identity="dpl-03c-test",
    )["plan"]


def _request(plan: dict | None = None, **overrides) -> dict:
    plan = plan or _plan()
    values = {
        "plan": plan,
        "environment": "staging",
        "requested_action_scope": [plan["actions"][-1]["action_id"]],
        "requester_identity": "requester-a",
        "approver_identity": "approver-b",
        "context_identity": "dpl-03c-test",
        "reason": "Authorize the exact reviewed staging action.",
        "requested_timestamp": ISSUED,
        "issued_timestamp": ISSUED,
        "expiry_timestamp": EXPIRES,
        "nonce": "request-nonce-0001",
    }
    values.update(overrides)
    return create_approval_request(**values)


def _decision(request: dict | None = None, **overrides) -> dict:
    request = request or _request()
    values = {
        "request": request,
        "decision": "APPROVED",
        "decision_reason": "Reviewed deterministic evidence.",
        "issued_timestamp": ISSUED,
        "expiry_timestamp": EXPIRES,
        "nonce": "decision-nonce-001",
        "approver_identity": "approver-b",
    }
    values.update(overrides)
    return create_approval_decision(**values)


class FakeVerifier:
    def __init__(self, valid: bool = True):
        self.valid = valid
        self.calls = 0

    def verify(self, decision) -> bool:
        self.calls += 1
        return self.valid


class FakeReplayGuard:
    def __init__(self, consumed: bool = False):
        self.consumed = consumed
        self.calls = 0

    def was_consumed(self, nonce: str) -> bool:
        self.calls += 1
        return self.consumed


def _authorize(
    plan: dict | None = None, request: dict | None = None,
    decision: dict | None = None, **overrides,
):
    plan = plan or _plan()
    request = request or _request(plan)
    decision = decision or _decision(request)
    values = {
        "request": request, "decision": decision, "plan": plan, "now": NOW,
        "verifier": FakeVerifier(), "replay_guard": FakeReplayGuard(),
    }
    values.update(overrides)
    return materialize_execution_authorization(**values)


def test_all_four_schemas_and_authorized_result() -> None:
    plan = _plan()
    request = _request(plan)
    decision = _decision(request)
    authorization, report = _authorize(plan, request, decision)
    registry = load_schema_registry()
    for name, payload in (
        ("ApprovalRequest", request),
        ("ApprovalDecision", decision),
        ("ExecutionAuthorization", authorization),
        ("AuthorizationValidationReport", report),
    ):
        validate_contract_payload(registry=registry, contract_name=name, payload=payload)
    assert report["status"] == "AUTHORIZED"
    assert authorization["execution_authorized"] is True
    assert authorization["executor_invoked"] is False
    assert authorization["production_writes"] == authorization["ubuntu_changes"] == 0


def test_ids_digests_json_and_inputs_are_deterministic_and_immutable() -> None:
    plan = _plan()
    original = copy.deepcopy(plan)
    request_a = _request(plan)
    request_b = _request(plan)
    decision_a = _decision(request_a)
    decision_b = _decision(request_b)
    authorization_a, report_a = _authorize(plan, request_a, decision_a)
    authorization_b, report_b = _authorize(plan, request_b, decision_b)
    assert request_a == request_b
    assert decision_a == decision_b
    assert authorization_a == authorization_b
    assert report_a["authorization_digest"] == report_b["authorization_digest"]
    assert canonical_json_bytes(report_a) == canonical_json_bytes(report_b)
    assert plan == original


@pytest.mark.parametrize(
    ("decision_value", "now", "status", "reason"),
    [
        ("REJECTED", NOW, "DENIED", "DECISION_NOT_APPROVED"),
        ("APPROVED", EXPIRES, "EXPIRED", "AUTHORIZATION_EXPIRED"),
        ("APPROVED", "2026-07-29T00:59:59Z", "DENIED", "ISSUED_IN_FUTURE"),
    ],
)
def test_rejected_expired_and_future_issued_denial(
    decision_value: str, now: str, status: str, reason: str
) -> None:
    request = _request()
    decision = _decision(request, decision=decision_value)
    authorization, report = _authorize(request=request, decision=decision, now=now)
    assert authorization is None
    assert report["status"] == status
    assert reason in report["reason_codes"]


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("package_digest", "PACKAGE_DIGEST_MISMATCH"),
        ("plan_digest", "PLAN_DIGEST_MISMATCH"),
        ("target_identity", "TARGET_IDENTITY_MISMATCH"),
        ("action_scope", "ACTION_SCOPE_MISMATCH"),
    ],
)
def test_binding_mismatch_denied(field: str, reason: str) -> None:
    request = _request()
    decision = _decision(request)
    decision[field] = (
        ["act-" + "0" * 24] if field == "action_scope"
        else ("sha256:" + "0" * 64 if "digest" in field else "other-target")
    )
    authorization, report = _authorize(request=request, decision=decision)
    assert authorization is None
    assert reason in report["reason_codes"]


@pytest.mark.parametrize(
    ("factory", "override"),
    [
        (_request, {"environment": "production"}),
        (_request, {"production_requested": True}),
        (_request, {"maximum_uses": 2}),
        (_request, {"nonce": ""}),
        (_decision, {"production_authorized": True}),
        (_decision, {"maximum_uses": 2}),
        (_decision, {"nonce": ""}),
    ],
)
def test_schema_enforces_nonproduction_nonce_and_one_use(factory, override) -> None:
    with pytest.raises((DeploymentContractValidationError, AuthorizationInputError)):
        factory(**override)


def test_replay_and_requester_approver_separation() -> None:
    authorization, report = _authorize(replay_guard=FakeReplayGuard(True))
    assert authorization is None
    assert report["status"] == "REPLAYED"
    request = _request(approver_identity="requester-a")
    decision = _decision(request, approver_identity="requester-a")
    authorization, report = _authorize(request=request, decision=decision)
    assert authorization is None
    assert "REQUESTER_APPROVER_SEPARATION_FAILED" in report["reason_codes"]


def test_plan_readiness_and_critical_risk_are_default_denials() -> None:
    plan = _plan()
    plan["overall_status"] = "BLOCKED"
    semantic = copy.deepcopy(plan)
    semantic.pop("plan_digest")
    plan["plan_digest"] = sha256_digest(semantic)
    request = _request(plan)
    decision = _decision(request)
    authorization, report = _authorize(plan=plan, request=request, decision=decision)
    assert authorization is None
    assert "PLAN_NOT_READY_FOR_APPROVAL" in report["reason_codes"]
    plan = _plan()
    plan["actions"][0]["risk"] = "CRITICAL"
    plan["overall_status"] = "BLOCKED"
    plan["risk_level"] = "CRITICAL"
    semantic = copy.deepcopy(plan)
    semantic.pop("plan_digest")
    plan["plan_digest"] = sha256_digest(semantic)
    request = _request(plan)
    decision = _decision(request)
    authorization, report = _authorize(plan=plan, request=request, decision=decision)
    assert authorization is None
    assert "PLAN_CONTAINS_CRITICAL_RISK" in report["reason_codes"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("command", "unsafe"), ("shell", "unsafe"), ("argv", ["unsafe"]),
        ("script", "unsafe"), ("artifact_path", "/absolute/secret"),
        ("artifact_path", "../secret"), ("api_token", "must-not-leak"),
    ],
)
def test_command_path_unknown_and_secret_fields_are_rejected_and_redacted(
    field: str, value
) -> None:
    plan = _plan()
    plan[field] = value
    with pytest.raises(AuthorizationInputError) as error:
        _request(plan)
    assert "must-not-leak" not in str(error.value)


def test_missing_and_deterministic_fake_ports_default_deny() -> None:
    authorization, report = _authorize(verifier=None)
    assert authorization is None
    assert report["status"] == "INCOMPLETE"
    assert "VERIFIER_UNAVAILABLE" in report["reason_codes"]
    authorization, report = _authorize(replay_guard=None)
    assert authorization is None
    assert report["status"] == "INCOMPLETE"
    assert "REPLAY_GUARD_UNAVAILABLE" in report["reason_codes"]
    verifier, guard = FakeVerifier(), FakeReplayGuard()
    first = _authorize(verifier=verifier, replay_guard=guard)
    second = _authorize(verifier=FakeVerifier(), replay_guard=FakeReplayGuard())
    assert first == second
    assert verifier.calls == guard.calls == 1


def test_no_persistence_executor_network_or_runtime_command_imports() -> None:
    forbidden = {
        "core.api", "core.worker", "core.deployment.apply",
        "core.deployment.execution", "core.deployment.inspect", "subprocess",
        "socket", "requests", "paramiko", "sqlite3",
    }
    imported: set[str] = set()
    source = ""
    for path in (ROOT / "core/deployment/authorization").glob("*.py"):
        source += path.read_text("utf-8")
        tree = ast.parse(path.read_text("utf-8"))
        imported.update(
            node.module or "" for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        imported.update(
            alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        )
    assert not any(
        module == item or module.startswith(item + ".")
        for module in imported for item in forbidden
    )
    assert "UbuntuWorkerClient" not in source
    assert ".consume(" not in source


def test_dependency_policy_compatibility_and_namespace_collision_prevention() -> None:
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    authorization = importlib.import_module("core.deployment.authorization")
    legacy = importlib.import_module("core.deployment.approval")
    planning = importlib.import_module("core.deployment.planning")
    assert Path(authorization.__file__).name == "__init__.py"
    assert authorization is not legacy
    assert hasattr(planning, "DeploymentPlanBuilder")
