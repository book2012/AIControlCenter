from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from core.deployment.contracts import (
    DeploymentContractValidationError,
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)
from core.deployment.planning import (
    DeploymentPlanBuilder,
    PlanGraphError,
    PlanInputError,
    stable_topological_order,
    validate_action_graph,
    validate_deployment_plan,
    validate_deployment_plan_report,
)

FIXTURES = Path("tests/fixtures/deployment")
ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text("utf-8"))


def _inputs() -> dict:
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
            "git-repository",
            "runtime-metadata",
            "mac-production-profile",
            "launchd-services",
            "host-caddy",
            "public-edge-policy",
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
    return {
        "package": package,
        "package_digest": sha256_digest(package),
        "mac_inventory": inventory,
        "ingress_readiness": _load("ingress-readiness-report.json"),
        "dependency_policy": policy,
        "target_profile": {
            "target_id": "mac-mini-m4",
            "platform": "macos",
            "role": "control-plane",
            "profile": "mac-standalone-production",
            "control_plane_owner": "aicontrolcenter",
            "public_edge_owner": "host-caddy",
            "cms_owner": "wordpress",
            "commerce_owner": "woocommerce",
        },
        "actor_identity": "test-actor",
        "context_identity": "dpl-03b-test",
    }


def _build(values: dict | None = None) -> dict:
    return DeploymentPlanBuilder().build(**(values or _inputs()))


def test_legacy_plan_module_and_pure_planning_package_resolve_independently() -> None:
    legacy = importlib.import_module("core.deployment.plan")
    planning = importlib.import_module("core.deployment.planning")

    assert Path(legacy.__file__).resolve() == ROOT / "core/deployment/plan.py"
    assert Path(planning.__file__).resolve() == (
        ROOT / "core/deployment/planning/__init__.py"
    )
    assert legacy is importlib.import_module("core.deployment.plan")
    assert hasattr(legacy, "build_deployment_plan")
    assert hasattr(planning, "DeploymentPlanBuilder")


def test_valid_plan_and_report_contracts() -> None:
    report = _build()
    validate_deployment_plan(report["plan"])
    validate_deployment_plan_report(report)
    registry = load_schema_registry()
    validate_contract_payload(
        registry=registry, contract_name="DeploymentPlanAction",
        payload=report["plan"]["actions"][0],
    )
    assert report["overall_status"] == "READY_FOR_APPROVAL"
    assert report["plan"]["execution_authorized"] is False
    assert report["plan"]["production_authorized"] is False


def test_deterministic_identity_order_and_canonical_serialization() -> None:
    first, second = _build(), _build()
    assert first == second
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert first["plan"]["plan_id"] == second["plan"]["plan_id"]
    assert first["plan"]["plan_digest"] == second["plan"]["plan_digest"]
    assert [item["action_id"] for item in first["plan"]["actions"]] == [
        item["action_id"] for item in second["plan"]["actions"]
    ]


def test_inputs_are_not_mutated() -> None:
    values = _inputs()
    original = copy.deepcopy(values)
    _build(values)
    assert values == original


def test_graph_cycle_duplicate_missing_and_order_rejection() -> None:
    actions = copy.deepcopy(_build()["plan"]["actions"])
    actions[0]["dependency_ids"] = [actions[-1]["action_id"]]
    with pytest.raises(PlanGraphError, match="cycle"):
        stable_topological_order(actions)
    duplicate = [actions[0], actions[0]]
    with pytest.raises(PlanGraphError, match="unique"):
        stable_topological_order(duplicate)
    missing = copy.deepcopy(_build()["plan"]["actions"])
    missing[0]["dependency_ids"] = ["act-" + "0" * 24]
    with pytest.raises(PlanGraphError, match="unknown"):
        stable_topological_order(missing)
    reversed_actions = list(reversed(_build()["plan"]["actions"]))
    with pytest.raises(PlanGraphError, match="order"):
        validate_action_graph(reversed_actions)


def test_stable_topological_tie_breaking() -> None:
    actions = [
        {"action_id": "b", "dependency_ids": []},
        {"action_id": "a", "dependency_ids": []},
        {"action_id": "c", "dependency_ids": ["a", "b"]},
    ]
    assert stable_topological_order(actions) == ("a", "b", "c")


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("dependency_policy", "FAIL", "DEPENDENCY_POLICY_NOT_PASS"),
        ("ingress_readiness", "NOT_READY", "INGRESS_NOT_READY"),
        ("ingress_readiness", "INVALID", "INGRESS_INVALID"),
        ("ingress_readiness", "UNAVAILABLE", "INGRESS_UNAVAILABLE"),
    ],
)
def test_read_evidence_statuses_block(field: str, value: str, reason: str) -> None:
    inputs = _inputs()
    key = "overall_result" if field == "dependency_policy" else "overall_status"
    inputs[field][key] = value
    plan = _build(inputs)["plan"]
    assert plan["overall_status"] == "BLOCKED"
    assert reason in plan["blocking_reasons"]
    assert plan["actions"][-1]["action_type"] == "RECORD_BLOCKER"


def test_optional_degraded_ingress_is_warning() -> None:
    inputs = _inputs()
    inputs["ingress_readiness"]["overall_status"] = "DEGRADED"
    report = _build(inputs)
    assert report["overall_status"] == "READY_FOR_APPROVAL"
    assert "INGRESS_OPTIONAL_OBSERVATION_DEGRADED" in report["warnings"]


def test_required_inventory_unavailable_blocks() -> None:
    inputs = _inputs()
    inputs["mac_inventory"]["items"][0]["state"] = "unavailable"
    report = _build(inputs)
    assert report["overall_status"] == "BLOCKED"
    assert any(reason.startswith("REQUIRED_INVENTORY_UNAVAILABLE") for reason in report["blocking_reasons"])


def test_package_digest_mismatch_and_invalid_package_block() -> None:
    inputs = _inputs()
    inputs["package_digest"] = "sha256:" + "0" * 64
    assert "PACKAGE_DIGEST_MISMATCH" in _build(inputs)["blocking_reasons"]
    inputs = _inputs()
    inputs["package"]["read_only"] = False
    inputs["package_digest"] = sha256_digest(inputs["package"])
    assert "PACKAGE_INVALID" in _build(inputs)["blocking_reasons"]


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("platform", "ubuntu"),
        ("control_plane_owner", "ubuntu"),
        ("public_edge_owner", "nginx"),
        ("cms_owner", "ubuntu"),
        ("commerce_owner", "ubuntu"),
    ],
)
def test_unsafe_target_profiles_block(key: str, value: str) -> None:
    inputs = _inputs()
    inputs["target_profile"][key] = value
    assert _build(inputs)["overall_status"] == "BLOCKED"


@pytest.mark.parametrize("flag", ["execution_authorized", "production_authorized"])
def test_authorization_true_is_rejected(flag: str) -> None:
    inputs = _inputs()
    inputs[flag] = True
    with pytest.raises(PlanInputError):
        _build(inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("command", "unsafe"),
        ("shell", "unsafe"),
        ("argv", ["unsafe"]),
        ("artifact_path", "../secret"),
        ("artifact_path", "/absolute/secret"),
        ("api_token", "must-not-leak"),
    ],
)
def test_command_path_and_secret_bearing_inputs_are_rejected(field: str, value) -> None:
    inputs = _inputs()
    inputs["package"]["components"][0][field] = value
    with pytest.raises(PlanInputError) as error:
        _build(inputs)
    assert "must-not-leak" not in str(error.value)


def test_evidence_warning_content_is_redacted() -> None:
    inputs = _inputs()
    inputs["ingress_readiness"]["warnings"] = ["sensitive implementation detail"]
    report = _build(inputs)
    assert report["warnings"] == ["INGRESS_EVIDENCE_WARNING_PRESENT"]
    assert "sensitive implementation detail" not in canonical_json_bytes(report).decode()


def test_plan_digest_mismatch_and_critical_risk_are_rejected() -> None:
    plan = copy.deepcopy(_build()["plan"])
    plan["plan_digest"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="digest"):
        validate_deployment_plan(plan)
    plan = copy.deepcopy(_build()["plan"])
    plan["actions"][0]["risk"] = "CRITICAL"
    semantic = copy.deepcopy(plan)
    semantic.pop("plan_digest")
    plan["plan_digest"] = sha256_digest(semantic)
    with pytest.raises(PlanGraphError, match="critical"):
        validate_deployment_plan(plan)


def test_contract_rejects_arbitrary_action_payload_and_unsupported_type() -> None:
    action = copy.deepcopy(_build()["plan"]["actions"][0])
    action["shell"] = "unsafe"
    with pytest.raises(DeploymentContractValidationError):
        validate_contract_payload(
            registry=load_schema_registry(), contract_name="DeploymentPlanAction",
            payload=action,
        )
    action.pop("shell")
    action["action_type"] = "EXECUTE"
    with pytest.raises(DeploymentContractValidationError):
        validate_contract_payload(
            registry=load_schema_registry(), contract_name="DeploymentPlanAction",
            payload=action,
        )


def test_plan_zone_has_no_execution_or_network_imports() -> None:
    import ast

    imported: set[str] = set()
    for path in (ROOT / "core/deployment/planning").glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        imported.update(
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        )
        imported.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
    forbidden = (
        "core.api", "core.worker", "core.deployment.apply", "core.deployment.execution",
        "core.deployment.inspect", "SSHRunner", "UbuntuWorkerClient", "subprocess",
        "socket", "requests", "paramiko",
    )
    assert not any(
        module == item or module.startswith(item + ".")
        for module in imported for item in forbidden
    )


def test_builder_executes_no_runtime_command(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket
    import subprocess

    calls: list[str] = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append("command"))
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: calls.append("network"))
    _build()
    assert calls == []
