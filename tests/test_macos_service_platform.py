from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from core.runtime.service_platform import (
    ServiceDefinition, ServiceDefinitionError, inspect_service, lifecycle_dry_run,
)
from core.runtime.service_topology import ServiceTopology
from core.runtime.service_topology import TopologyConfigurationError
from core.runtime.service_health import ServiceHealth
from ops.macos.runtime.service_platform import (
    inspect_filesystem, inspect_immutable_runtime, inspect_platform_services,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config/services/mac-standalone-production.json"
SCHEMA = ROOT / "config/schemas/mac-service-manifest.schema.json"


def definition(*, required: bool = True, health: str = "launchd") -> ServiceDefinition:
    return ServiceDefinition.from_mapping({
        "service_id": "example", "launchd_label": "com.example.service",
        "required": required, "runtime": "python-immutable-venv", "lifecycle": "launchd",
        "service_platform": {
            "application_entrypoint": "core.example", "logs": [
                {"path": "/logs/example.log", "type": "file", "mode": 0o640, "owner": "root", "group": "wheel"},
            ],
            "log_parent": {"path": "/logs", "type": "directory", "mode": 0o755, "owner": "root", "group": "wheel"},
            "health_observation": health, "lifecycle_capabilities": ["inspect"],
            "lifecycle_planning": {"bounded_action": "bootstrap", "eligible_statuses": ["NOT_DEPLOYED"]},
            "immutable_runtime": {"runtime_root": "/runtime"},
        },
    })


def inspect(defn: ServiceDefinition, state: str = "RUNNING", *, fresh: bool = True, fs=True, runtime=True):
    return inspect_service(
        defn, launchd_observer=lambda _label: state,
        filesystem_observer=lambda _logs: {"ready": fs},
        runtime_observer=lambda _contract: {"ready": runtime},
        freshness_observer=lambda _definition: {"fresh": fresh},
    )


def test_canonical_manifest_exposes_reference_service_contracts() -> None:
    services = {item.service_id: item for item in ServiceTopology(MANIFEST, SCHEMA).platform_services()}
    assert set(services) == {"aicontrolcenter-api", "application-scheduler"}
    assert services["aicontrolcenter-api"].application_entrypoint == "ops.macos.runtime.application:app"
    scheduler = services["application-scheduler"]
    assert scheduler.health_observation == "heartbeat"
    assert [item["path"] for item in scheduler.logs] == [
        "/var/log/aicontrolcenter/application-scheduler.stdout.log",
        "/var/log/aicontrolcenter/application-scheduler.stderr.log",
    ]


def test_manifest_platform_identity_mismatch_fails_closed(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text())
    manifest["services"][0]["service_platform"]["launchd_label"] = "com.example.wrong"
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(manifest))
    with pytest.raises(TopologyConfigurationError):
        ServiceTopology(path, SCHEMA).platform_services()


@pytest.mark.parametrize("change", [
    lambda platform: platform.update(unexpected=True),
    lambda platform: platform["log_parent"].update(mode=4096),
    lambda platform: platform["logs"][0].update(path="relative.log"),
    lambda platform: platform.update(lifecycle_planning={"bounded_action": "kickstart", "eligible_statuses": ["STOPPED"]}),
    lambda platform: platform.update(lifecycle_planning={"bounded_action": "bootstrap", "eligible_statuses": ["STOPPED", "STOPPED"]}),
    lambda platform: platform.update(logs=[platform["logs"][0], platform["logs"][0]]),
])
def test_schema_rejects_malformed_platform_shapes(change, tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text())
    change(manifest["services"][0]["service_platform"])
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(manifest))
    with pytest.raises(TopologyConfigurationError):
        ServiceTopology(path, SCHEMA).platform_services()


def test_outer_macos_contract_matches_canonical_api_entrypoint() -> None:
    from ops.macos.launchd.canonical_api_daemon import validate_contract
    service = ServiceTopology(MANIFEST, SCHEMA).platform_services()[0]
    assert service.application_entrypoint == validate_contract(ROOT)["installation"]["application"]
    assert service.application_entrypoint == "ops.macos.runtime.application:app"
    assert service.application_entrypoint != "core.api.shadow:app"


@pytest.mark.parametrize("change", [
    lambda value: value["service_platform"].update(extra=True),
    lambda value: value.update(required="yes"),
    lambda value: value["service_platform"].update(health_observation="guess"),
    lambda value: value["service_platform"].update(lifecycle_capabilities=["bootstrap"]),
    lambda value: value["service_platform"].update(lifecycle_planning={"bounded_action": "bootstrap", "eligible_statuses": ["STOPPED"]}),
    lambda value: value["service_platform"]["log_parent"].update(mode=0o10000),
    lambda value: value["service_platform"]["immutable_runtime"].update(runtime_root="relative"),
])
def test_malformed_definitions_fail_closed(change) -> None:
    value = definition().__dict__
    value = {
        "service_id": value["service_id"], "launchd_label": value["launchd_label"],
        "required": value["required"], "runtime": value["runtime_type"], "lifecycle": "launchd",
        "service_platform": {
            "application_entrypoint": value["application_entrypoint"],
            "immutable_runtime": dict(value["immutable_runtime"]),
            "log_parent": dict(value["log_parent"]), "logs": [dict(item) for item in value["logs"]],
            "health_observation": value["health_observation"], "lifecycle_capabilities": ["inspect"],
            "lifecycle_planning": {"bounded_action": "bootstrap", "eligible_statuses": ["NOT_DEPLOYED"]},
        },
    }
    change(value)
    with pytest.raises(ServiceDefinitionError):
        ServiceDefinition.from_mapping(value)


@pytest.mark.parametrize("state", ["RUNNING", "STOPPED", "UNAVAILABLE", "NOT_DEPLOYED"])
def test_generic_states_are_preserved(state: str) -> None:
    assert inspect(definition(), state)["status"] == state


def test_indeterminate_state_fails_closed_and_stale_is_projected() -> None:
    result = inspect_service(
        definition(), launchd_observer=lambda _label: "MAYBE",
        filesystem_observer=lambda _logs: {"ready": True},
        runtime_observer=lambda _contract: {"ready": True},
    )
    assert result["status"] == "UNAVAILABLE" and result["ready"] is False
    assert inspect(definition(health="heartbeat"), fresh=False)["status"] == "STALE"


def test_required_and_optional_aggregate_semantics() -> None:
    assert inspect(definition(required=True), "STOPPED")["healthy"] is False
    optional = inspect(definition(required=False), "NOT_DEPLOYED")
    assert optional["healthy"] is False and optional["ready"] is False
    assert optional["fails_platform_health"] is False


def test_filesystem_contract_is_strict_under_umask_077(tmp_path: Path) -> None:
    old = os.umask(0o077)
    try:
        path = tmp_path / "service.log"
        path.touch(); path.chmod(0o640)
    finally:
        os.umask(old)
    metadata = path.lstat()
    import grp
    import pwd
    spec = ({"path": str(path), "type": "file", "mode": 0o640, "owner": pwd.getpwuid(metadata.st_uid).pw_name, "group": grp.getgrgid(metadata.st_gid).gr_name},)
    assert inspect_filesystem(spec)["ready"] is True
    path.chmod(0o600)
    assert inspect_filesystem(spec)["ready"] is False
    path.unlink(); path.symlink_to(tmp_path / "target")
    assert inspect_filesystem(spec)["paths"][0]["symlink"] is True
    assert inspect_filesystem(spec)["ready"] is False


def test_filesystem_enoent_differs_from_other_errors(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    spec = ({"path": str(missing), "type": "file", "mode": 0o640, "owner": "root", "group": "wheel"},)
    assert inspect_filesystem(spec)["paths"][0]["inspection_error"] is None
    original = Path.lstat
    def denied(path):
        if str(path) == str(missing):
            raise PermissionError(13, "hidden")
        return original(path)
    monkeypatch.setattr(Path, "lstat", denied)
    result = inspect_filesystem(spec)
    assert result["ready"] is False
    assert result["paths"][0]["inspection_error"] == {"error_type": "PermissionError", "errno": "EACCES"}
    assert "hidden" not in repr(result)


def test_owner_and_group_mismatch_fail() -> None:
    spec = ({"path": __file__, "type": "file", "mode": 0o644, "owner": "root", "group": "wheel"},)
    result = inspect_filesystem(spec)
    assert result["ready"] is False
    assert result["paths"][0]["owner_matches"] is False
    assert result["paths"][0]["group_matches"] is False


def test_identity_lookup_error_fails_closed_without_lookup_value(monkeypatch) -> None:
    import pwd
    monkeypatch.setattr(pwd, "getpwnam", lambda _name: (_ for _ in ()).throw(OSError("private lookup detail")))
    spec = ({"path": __file__, "type": "file", "mode": 0o644, "owner": "secret-owner", "group": "wheel"},)
    result = inspect_filesystem(spec)
    assert result["ready"] is False
    assert result["paths"][0]["inspection_error"] == {"error_type": "OSError"}
    assert "private lookup detail" not in repr(result)
    assert "secret-owner" not in repr(result)


def test_existing_service_health_launchd_observer_is_reused() -> None:
    observer = ServiceHealth(launchd_inspector=lambda _label: "RUNNING").launchd_inspector
    assert inspect_service(
        definition(), launchd_observer=observer,
        filesystem_observer=lambda _specs: {"ready": True},
        runtime_observer=lambda _contract: {"ready": True},
    )["status"] == "RUNNING"


def test_outer_composition_inspects_reference_services_with_fakes() -> None:
    heartbeat = type("Heartbeat", (), {"latest": lambda self: None})()
    health = ServiceHealth(heartbeat=heartbeat, launchd_inspector=lambda _label: "RUNNING")
    result = inspect_platform_services(
        topology=ServiceTopology(MANIFEST, SCHEMA), service_health=health,
        filesystem_observer=lambda _specs: {"ready": True},
        runtime_observer=lambda _contract: {"ready": True},
    )
    assert "ready" not in result
    assert set(result["services"]) == {"aicontrolcenter-api", "application-scheduler"}
    assert result["services"]["aicontrolcenter-api"]["ready"] is True
    scheduler = result["services"]["application-scheduler"]
    assert scheduler["freshness"]["required"] is True and scheduler["ready"] is False


def test_immutable_runtime_uses_current_and_source_validator(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"; release = runtime / "venvs" / "012345abcdef"
    source = runtime / "sources" / release.name
    release.mkdir(parents=True); source.mkdir(parents=True)
    (runtime / "current").symlink_to(release)
    calls = []
    result = inspect_immutable_runtime(
        {"runtime_root": str(runtime)},
        source_validator=lambda path: calls.append(path) or {"immutable_source_context_valid": True},
    )
    assert result["ready"] is True and calls == [source]
    bad = inspect_immutable_runtime(
        {"runtime_root": str(runtime)},
        source_validator=lambda _path: {"immutable_source_context_valid": False},
    )
    assert bad["ready"] is False


def test_immutable_runtime_rejects_non_symlink_and_release_outside_venvs(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    (runtime / "current").mkdir(parents=True)
    assert inspect_immutable_runtime({"runtime_root": str(runtime)}, source_validator=lambda _path: {})["ready"] is False
    (runtime / "current").rmdir()
    outside = tmp_path / "outside"; outside.mkdir()
    (runtime / "current").symlink_to(outside)
    assert inspect_immutable_runtime({"runtime_root": str(runtime)}, source_validator=lambda _path: {"immutable_source_context_valid": True})["ready"] is False


def test_canonical_runtime_reuses_authoritative_source_validator(monkeypatch, tmp_path: Path) -> None:
    import ops.macos.launchd.canonical_api_daemon_refresh as validator
    from ops.macos.runtime.service_platform import inspect_canonical_immutable_runtime
    runtime = tmp_path / "runtime"; release = runtime / "venvs" / "012345abcdef"
    release.mkdir(parents=True); (runtime / "current").symlink_to(release)
    calls = []
    monkeypatch.setattr(validator, "validate_immutable_source_context", lambda source: calls.append(source) or {"immutable_source_context_valid": False})
    assert inspect_canonical_immutable_runtime({"runtime_root": str(runtime)})["ready"] is False
    assert calls == [runtime / "sources" / release.name]


def test_canonical_runtime_rejects_missing_source_validation(tmp_path: Path) -> None:
    from ops.macos.runtime.service_platform import inspect_canonical_immutable_runtime
    runtime = tmp_path / "runtime"; release = runtime / "venvs" / "012345abcdef"
    release.mkdir(parents=True); (runtime / "current").symlink_to(release)
    result = inspect_canonical_immutable_runtime({"runtime_root": str(runtime)})
    assert result["ready"] is False
    assert result["validation"]["immutable_source_context_valid"] is False


def test_dry_run_is_json_compatible_bounded_and_never_mutates() -> None:
    plan = lifecycle_dry_run(definition(), inspect(definition(), "NOT_DEPLOYED"))
    json.dumps(plan)
    assert plan["eligible"] is True and plan["bounded_action"] == "bootstrap"
    assert plan["capabilities"] == ["inspect"]
    assert plan["authorization_included"] is False and plan["mutation_performed"] is False
    assert all(plan[key] == 0 for key in (
        "write_operations_executed", "launchctl_mutations_executed", "retry_operations_executed",
        "rollback_operations_executed", "kickstart_operations_executed",
    ))


@pytest.mark.parametrize("observation", [
    {}, {"status": "STOPPED", "ready": False},
    {"status": "STOPPED", "ready": False, "launchd": {"status": "STOPPED", "inspection_error": {}}, "filesystem": {"ready": True}, "immutable_runtime": {"ready": True}},
])
def test_dry_run_fails_closed_on_malformed_or_indeterminate_inspection(observation) -> None:
    plan = lifecycle_dry_run(definition(), observation)
    assert plan["eligible"] is False and plan["bounded_action"] is None


def test_duplicate_filesystem_paths_fail_closed() -> None:
    service = json.loads(MANIFEST.read_text())["services"][0]
    service["service_platform"]["logs"][1]["path"] = service["service_platform"]["logs"][0]["path"]
    with pytest.raises(ServiceDefinitionError):
        ServiceDefinition.from_mapping(service)
