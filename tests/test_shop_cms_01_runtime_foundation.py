from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from ops.macos.shopping.runtime_inspector import (
    CommandResult,
    _compose_rows,
    build_plan,
    inspect_runtime,
)

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


def test_wordpress_desired_port_is_loopback_only_and_not_control_plane_reserved() -> None:
    wordpress_port = int(
        (ROOT / "deploy/shopping/.env.example").read_text().split("SHOPPING_WORDPRESS_PORT=", 1)[1].splitlines()[0]
    )
    assert compose()["services"]["wordpress"]["ports"] == [
        "127.0.0.1:${SHOPPING_WORDPRESS_PORT}:80"
    ]
    services = json.loads((ROOT / "config/services/mac-standalone-production.json").read_text())["services"]
    reserved = {
        service["port"]
        for service in services
        if service.get("role") == "control-plane" and "port" in service
    }
    assert wordpress_port == 58082
    assert wordpress_port not in reserved


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


def test_compose_rows_accepts_array_object_ndjson_and_empty() -> None:
    database = {"Service": "database", "State": "running", "Health": "healthy"}
    wordpress = {"Service": "wordpress", "State": "running", "Health": "healthy"}
    assert _compose_rows(json.dumps([database, wordpress])) == [database, wordpress]
    assert _compose_rows(json.dumps(database)) == [database]
    assert _compose_rows(f"{json.dumps(database)}\n\n{json.dumps(wordpress)}\n") == [database, wordpress]
    assert _compose_rows(" \n\t") == []


def test_compose_rows_rejects_malformed_ndjson_scalar_and_non_object_row() -> None:
    malformed = '{"Service":"database"}\nnot-json\n{"Service":"wordpress"}'
    for stdout in (malformed, '"scalar"', '[{"Service":"database"}, 1]'):
        try:
            _compose_rows(stdout)
        except (json.JSONDecodeError, ValueError):
            pass
        else:
            raise AssertionError("malformed Compose output was accepted")


def test_stopped_service_fails_closed() -> None:
    def stopped(argv):
        if argv[0] == "colima":
            return CommandResult(0, "running")
        return CommandResult(0, json.dumps([
            {"Service": "database", "State": "running", "Health": "healthy"},
            {"Service": "wordpress", "State": "exited", "Health": ""},
        ]))
    result = inspect_runtime(stopped)
    assert result["error_type"] == "RuntimeNotHealthy"
    assert result["healthy"] is result["ready"] is False


def test_malformed_ndjson_fails_closed() -> None:
    def malformed(argv):
        stdout = "running" if argv[0] == "colima" else '{"Service":"database"}\nnot-json'
        return CommandResult(0, stdout)
    result = inspect_runtime(malformed)
    assert result["error_type"] == "MalformedDockerInspection"
    assert result["healthy"] is result["ready"] is False


def test_empty_compose_observation_is_valid_not_deployed_runtime() -> None:
    def runner(argv):
        return CommandResult(0, "running" if argv[0] == "colima" else " \n")
    result = inspect_runtime(runner)
    assert result["available"] is True
    assert result["healthy"] is result["ready"] is False
    assert result["error_type"] == "RuntimeNotDeployed"


def test_healthy_ndjson_runtime_is_ready_but_woocommerce_is_not() -> None:
    rows = (
        '{"Service":"database","State":"running","Health":"healthy"}\n'
        '{"Service":"wordpress","State":"running","Health":"healthy"}\n'
    )
    def runner(argv):
        return CommandResult(0, "running" if argv[0] == "colima" else rows)
    result = inspect_runtime(runner)
    assert result["database"] == {"present": True, "running": True, "healthy": True}
    assert result["wordpress"] == {"present": True, "running": True, "healthy": True}
    assert result["available"] is result["healthy"] is result["ready"] is True
    assert result["woocommerce"]["ready"] is False
    assert result["error_type"] is None


def test_healthy_runtime_on_reserved_control_plane_port_fails_ready_closed() -> None:
    services = json.loads((ROOT / "config/services/mac-standalone-production.json").read_text())["services"]
    reserved_port = next(service["port"] for service in services if service.get("role") == "control-plane")
    rows = [
        {"Service": "database", "State": "running", "Health": "healthy"},
        {
            "Service": "wordpress", "State": "running", "Health": "healthy",
            "Publishers": [{"URL": "127.0.0.1", "TargetPort": 80, "PublishedPort": reserved_port, "Protocol": "tcp"}],
        },
    ]
    def runner(argv):
        return CommandResult(0, "running" if argv[0] == "colima" else json.dumps(rows))
    result = inspect_runtime(runner)
    assert result["available"] is result["healthy"] is True
    assert result["ready"] is False
    assert result["error_type"] == "PortCollision"


def test_healthy_runtime_without_publisher_observation_does_not_invent_collision() -> None:
    rows = [
        {"Service": "database", "State": "running", "Health": "healthy"},
        {"Service": "wordpress", "State": "running", "Health": "healthy"},
    ]
    def runner(argv):
        return CommandResult(0, "running" if argv[0] == "colima" else json.dumps(rows))
    assert inspect_runtime(runner)["error_type"] is None


def test_compose_inspection_failure_precedes_stdout_parsing() -> None:
    def runner(argv):
        return CommandResult(0, "running") if argv[0] == "colima" else CommandResult(1, "not-json")
    assert inspect_runtime(runner)["error_type"] == "DockerInspectionUnavailable"


def test_plans_are_non_mutating_single_attempt_and_mac_owned() -> None:
    source = (ROOT / "ops/macos/shopping/runtime_inspector.py").read_text()
    assert "UbuntuWorkerClient" not in source and "ssh" not in source.lower()
    assert all(token not in source for token in ('"restart"', '"pull"', '"build"', '"up"', '"down"'))
    for kind in ("backup", "restore", "activation"):
        plan = build_plan(kind)
        assert plan["mutation_performed"] is False
        assert plan["automatic_retry"] is False
        assert plan["automatic_rollback"] is False
        assert plan["single_invocation"] is True
