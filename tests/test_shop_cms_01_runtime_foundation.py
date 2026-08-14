from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from ops.macos.shopping.runtime_inspector import CommandResult, build_plan, inspect_runtime

ROOT = Path(__file__).resolve().parents[1]


def compose() -> dict:
    return yaml.safe_load((ROOT / "deploy/shopping/compose.yaml").read_text())


def test_compose_isolated_persistent_and_fail_closed() -> None:
    data = compose()
    assert data["name"] == "ai-shopping"
    db = data["services"]["database"]
    wp = data["services"]["wordpress"]
    assert "ports" not in db
    assert db["healthcheck"] and wp["healthcheck"]
    assert wp["depends_on"]["database"]["condition"] == "service_healthy"
    assert db["volumes"] == ["shopping_database:/var/lib/mysql"]
    assert "shopping_wordpress:/var/www/html" in wp["volumes"]
    assert data["networks"]["shopping_internal"]["internal"] is True
    assert data["services"]["wordpress-cli"]["profiles"] == ["activation"]
    assert all(service["restart"] == "unless-stopped" for service in (db, wp))
    assert "utf8mb4" in " ".join(db["command"])


def test_compose_secret_references_are_value_free() -> None:
    for service in compose()["services"].values():
        for key, value in service.get("environment", {}).items():
            if "PASSWORD" in key:
                assert isinstance(value, str) and value.startswith("${") and value.endswith("}")


def test_canonical_runtime_and_capability_truth() -> None:
    services = json.loads((ROOT / "config/services/mac-standalone-production.json").read_text())["services"]
    runtime = [item for item in services if item["service_id"] == "shopping-runtime"]
    assert len(runtime) == 1
    assert runtime[0]["production_status"] == "NOT_DEPLOYED"
    assert runtime[0]["ubuntu_dependency"] is False
    assert not [item for item in services if item["service_id"] in {"wordpress", "shopping-db", "woocommerce"}]
    manifest = json.loads((ROOT / "config/capabilities/mac-standalone-production.json").read_text())
    schema = json.loads((ROOT / "config/schemas/capability-manifest.schema.json").read_text())
    assert not list(Draft202012Validator(schema).iter_errors(manifest))
    woo = manifest["capabilities"][0]
    assert woo == {
        "capability_id": "woocommerce", "host_service_id": "shopping-runtime",
        "kind": "wordpress-plugin-commerce-engine", "production_status": "NOT_DEPLOYED",
        "activation_authorized": False,
    }


def test_missing_runtime_fails_closed_without_docker_inspection() -> None:
    calls = []
    def runner(argv):
        calls.append(tuple(argv))
        return CommandResult(1)
    result = inspect_runtime(runner)
    assert result["healthy"] is result["ready"] is False
    assert result["error_type"] == "RuntimeUnavailable"
    assert len(calls) == 1 and calls[0][:2] == ("colima", "status")


def test_stopped_and_malformed_docker_inspection_fail_closed() -> None:
    def stopped(argv):
        if argv[0] == "colima":
            return CommandResult(0, "running")
        return CommandResult(0, json.dumps([
            {"Service": "database", "State": "running", "Health": "healthy"},
            {"Service": "wordpress", "State": "exited", "Health": ""},
        ]))
    assert inspect_runtime(stopped)["error_type"] == "RuntimeNotHealthy"
    def malformed(argv):
        return CommandResult(0, "running" if argv[0] == "colima" else "not-json")
    result = inspect_runtime(malformed)
    assert result["error_type"] == "MalformedDockerInspection"
    assert result["healthy"] is result["ready"] is False


def test_plans_are_non_mutating_single_attempt_and_mac_owned() -> None:
    source = (ROOT / "ops/macos/shopping/runtime_inspector.py").read_text()
    assert "UbuntuWorkerClient" not in source and "ssh" not in source.lower()
    for kind in ("backup", "restore", "activation"):
        plan = build_plan(kind)
        assert plan["mutation_performed"] is False
        assert plan["automatic_retry"] is False
        assert plan["automatic_rollback"] is False
        assert plan["single_invocation"] is True
