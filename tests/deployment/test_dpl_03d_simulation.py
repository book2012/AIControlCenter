from __future__ import annotations

import ast
import copy
import importlib
from pathlib import Path

import pytest

from core.deployment.contracts import (
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.policy import validate_dependency_boundaries
from core.deployment.simulation import (
    FakeDeploymentExecutor,
    InMemoryReplayGuard,
    SimulationApplyService,
)
from tests.deployment.test_dpl_03c_authorization import _authorize, _plan

ROOT = Path(__file__).resolve().parents[2]
STARTED = "2026-07-29T01:30:00Z"
COMPLETED = "2026-07-29T01:30:01Z"


class CountingExecutor(FakeDeploymentExecutor):
    def __init__(self, fail: bool = False):
        self.calls = 0
        self.fail = fail

    def execute(self, intents):
        self.calls += 1
        if self.fail:
            raise RuntimeError("deterministic fake failure")
        return super().execute(intents)


def _inputs():
    plan = _plan()
    authorization, report = _authorize(plan=plan)
    assert report["status"] == "AUTHORIZED"
    return {
        "authorization": authorization,
        "plan": plan,
        "package_digest": plan["package_digest"],
        "target_identity": plan["target_identity"],
        "environment": authorization["environment"],
        "action_scope": list(authorization["action_scope"]),
        "started_timestamp": STARTED,
        "completed_timestamp": COMPLETED,
    }


def _apply(values=None, *, guard=None, executor=None):
    guard = guard if guard is not None else InMemoryReplayGuard()
    executor = executor if executor is not None else CountingExecutor()
    return SimulationApplyService(
        replay_guard=guard, executor=executor
    ).apply(**(values or _inputs()))


def test_authorized_simulation_receipt_report_and_determinism() -> None:
    values = _inputs()
    original = copy.deepcopy(values)
    first, first_report = _apply(values)
    second, second_report = _apply(values)
    assert first == second
    assert first_report == second_report
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert sha256_digest({key: value for key, value in first.items() if key != "receipt_digest"}) == first["receipt_digest"]
    registry = load_schema_registry()
    validate_contract_payload(registry=registry, contract_name="SimulationExecutionReceipt", payload=first)
    validate_contract_payload(registry=registry, contract_name="SimulationExecutionReport", payload=first_report)
    assert first["result_status"] == first_report["status"] == "SIMULATED"
    assert first["execution_mode"] == "simulation"
    assert first["executor_type"] == "fake"
    assert first["production_writes"] == first["ubuntu_changes"] == 0
    assert "nonce" not in first
    assert values == original


def test_replay_second_consumption_and_single_fake_invocation() -> None:
    guard, executor = InMemoryReplayGuard(), CountingExecutor()
    first, first_report = _apply(guard=guard, executor=executor)
    second, second_report = _apply(guard=guard, executor=executor)
    assert first is not None and first_report["status"] == "SIMULATED"
    assert second is None and second_report["status"] == "REPLAYED"
    assert executor.calls == 1


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("package_digest", "sha256:" + "0" * 64, "PACKAGE_DIGEST_MISMATCH"),
        ("target_identity", "other-target", "TARGET_IDENTITY_MISMATCH"),
        ("environment", "production", "ENVIRONMENT_MISMATCH"),
        ("action_scope", ["act-" + "0" * 24], "ACTION_SCOPE_MISMATCH"),
    ],
)
def test_exact_binding_denials(field, value, reason) -> None:
    values = _inputs()
    values[field] = value
    executor = CountingExecutor()
    receipt, report = _apply(values, executor=executor)
    assert receipt is None
    assert reason in report["reason_codes"]
    assert executor.calls == 0


def test_expired_missing_ports_and_fail_closed_consumption() -> None:
    values = _inputs()
    values["started_timestamp"] = values["authorization"]["expiry_timestamp"]
    values["completed_timestamp"] = values["authorization"]["expiry_timestamp"]
    assert _apply(values)[1]["status"] == "EXPIRED"
    valid = _inputs()
    report = SimulationApplyService(
        replay_guard=None, executor=CountingExecutor()
    ).apply(**valid)[1]
    assert "REPLAY_GUARD_UNAVAILABLE" in report["reason_codes"]
    report = SimulationApplyService(
        replay_guard=InMemoryReplayGuard(), executor=None
    ).apply(**valid)[1]
    assert "FAKE_EXECUTOR_UNAVAILABLE" in report["reason_codes"]
    guard, failing = InMemoryReplayGuard(), CountingExecutor(True)
    assert _apply(valid, guard=guard, executor=failing)[1]["status"] == "FAILED"
    retry = _apply(valid, guard=guard, executor=CountingExecutor())[1]
    assert retry["status"] == "REPLAYED"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("command", "whoami"),
        ("argv", ["unsafe"]),
        ("script", "unsafe"),
        ("artifact_path", "../escape"),
        ("artifact_path", "/absolute"),
        ("api_token", "must-not-leak"),
    ],
)
def test_unsafe_fields_are_rejected_without_leakage(field, value) -> None:
    values = _inputs()
    values["plan"][field] = value
    receipt, report = _apply(values)
    assert receipt is None and report["status"] == "INVALID"
    assert "must-not-leak" not in str(report)


def test_invalid_plan_graphs_and_tampered_authorization_are_denied() -> None:
    for mutation in ("duplicate", "cycle"):
        values = _inputs()
        if mutation == "duplicate":
            values["plan"]["actions"].append(copy.deepcopy(values["plan"]["actions"][0]))
        else:
            values["plan"]["actions"][0]["dependency_ids"] = [
                values["plan"]["actions"][-1]["action_id"]
            ]
        assert _apply(values)[1]["status"] == "INVALID"
    values = _inputs()
    values["authorization"]["maximum_uses"] = 2
    assert _apply(values)[1]["status"] == "INVALID"


def test_dependency_architecture_namespace_and_no_runtime_imports() -> None:
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    assert not (ROOT / "core/deployment/simulation.py").exists()
    module = importlib.import_module("core.deployment.simulation")
    assert Path(module.__file__).name == "__init__.py"
    forbidden = {
        "core.api", "core.worker", "core.deployment.inspect", "subprocess",
        "socket", "requests", "paramiko", "sqlite3",
    }
    imports = set()
    source = ""
    for path in (ROOT / "core/deployment/simulation").glob("*.py"):
        text = path.read_text("utf-8")
        source += text
        tree = ast.parse(text)
        imports.update(
            node.module or "" for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        imports.update(
            alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
            for alias in node.names
        )
    assert not any(
        module == item or module.startswith(item + ".")
        for module in imports for item in forbidden
    )
    for forbidden_text in (
        "UbuntuWorkerClient", "SSHRunner", "launchctl", "docker compose",
        "Caddy", "Colima",
    ):
        assert forbidden_text not in source
