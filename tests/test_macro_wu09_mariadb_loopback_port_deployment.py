from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
import yaml

from ops.macos.shopping import mariadb_loopback_port_deployment as deployment


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/shopping-mariadb-loopback.json"
COMPOSE = ROOT / "deploy/shopping/mariadb-loopback/compose.yaml"
WRAPPER = ROOT / "ops/macos/shopping/mariadb_loopback_port_deployment.py"
FORBIDDEN_CREDENTIAL_IDENTIFIERS = {
    "_".join(("SHOPPING", "DB", suffix))
    for suffix in ("NAME", "USER", "PASSWORD", "ROOT_PASSWORD")
}


def test_json_is_exact_non_secret_transport_authority() -> None:
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert document == {
        "schema_version": "1.0",
        "service": "mariadb-loopback-adapter",
        "project": "ai-shopping-mariadb-loopback",
        "bind_host": "127.0.0.1",
        "host_port": 58083,
        "target_host": "database",
        "target_port": 3306,
        "external_network": "ai-shopping-internal",
    }
    assert not FORBIDDEN_CREDENTIAL_IDENTIFIERS & set(
        CONFIG.read_text(encoding="utf-8").split()
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "2.0"),
        ("service", "database"),
        ("project", "ai-shopping"),
        ("bind_host", "0.0.0.0"),
        ("host_port", "58083"),
        ("host_port", True),
        ("host_port", 0),
        ("target_host", "localhost"),
        ("target_port", 3307),
        ("external_network", "default"),
    ],
)
def test_validator_rejects_wrong_values_and_types(field: str, value: object) -> None:
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    document[field] = value
    with pytest.raises(deployment.ConfigurationError):
        deployment.validate_configuration(document)


def test_validator_rejects_missing_or_unexpected_fields() -> None:
    document = json.loads(CONFIG.read_text(encoding="utf-8"))
    missing = dict(document)
    missing.pop("bind_host")
    extra = {**document, "credential": "forbidden"}
    with pytest.raises(deployment.ConfigurationError):
        deployment.validate_configuration(missing)
    with pytest.raises(deployment.ConfigurationError):
        deployment.validate_configuration(extra)


def test_compose_is_dedicated_hardened_digest_pinned_adapter() -> None:
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert compose["name"] == "ai-shopping-mariadb-loopback"
    assert set(compose["services"]) == {"mariadb-loopback-adapter"}
    service = compose["services"]["mariadb-loopback-adapter"]
    image = service["image"]
    assert image.startswith("alpine/socat@sha256:")
    assert len(image.removeprefix("alpine/socat@sha256:")) == 64
    assert service["command"] == [
        "TCP-LISTEN:3306,fork,reuseaddr",
        "TCP:${MARIADB_LOOPBACK_TARGET_HOST:?WU09 target host required}:${MARIADB_LOOPBACK_TARGET_PORT:?WU09 target port required}",
    ]
    assert service["ports"] == [
        "${MARIADB_LOOPBACK_BIND_HOST:?WU09 bind host required}:${MARIADB_LOOPBACK_HOST_PORT:?WU09 host port required}:3306"
    ]
    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert service["security_opt"] == ["no-new-privileges:true"]
    for forbidden in ("volumes", "privileged", "network_mode", "environment"):
        assert forbidden not in service


def test_compose_references_only_existing_external_network() -> None:
    compose = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert compose["services"]["mariadb-loopback-adapter"]["networks"] == [
        "ai-shopping-internal"
    ]
    assert compose["networks"] == {
        "ai-shopping-internal": {
            "external": True,
            "name": "ai-shopping-internal",
        }
    }


def test_wrapper_produces_one_exact_non_secret_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[deployment.ComposeInvocation] = []
    monkeypatch.setattr(deployment, "CONFIG_PATH", CONFIG)

    def capability(invocation: deployment.ComposeInvocation) -> int:
        calls.append(invocation)
        return 19

    assert deployment.deploy(capability) == 19
    assert len(calls) == 1
    invocation = calls[0]
    assert invocation.argv == (
        "docker", "compose", "--project-name", "ai-shopping-mariadb-loopback",
        "--file", str(COMPOSE), "up", "--detach", "--no-deps",
        "--force-recreate", "mariadb-loopback-adapter",
    )
    assert dict(invocation.environment) == {
        "MARIADB_LOOPBACK_BIND_HOST": "127.0.0.1",
        "MARIADB_LOOPBACK_HOST_PORT": "58083",
        "MARIADB_LOOPBACK_TARGET_HOST": "database",
        "MARIADB_LOOPBACK_TARGET_PORT": "3306",
    }


def test_invalid_config_fails_before_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    invalid = tmp_path / "config.json"
    invalid.write_text('{"bind_host":"127.0.0.1"}', encoding="utf-8")
    monkeypatch.setattr(deployment, "CONFIG_PATH", invalid)
    calls = 0

    def capability(_: deployment.ComposeInvocation) -> int:
        nonlocal calls
        calls += 1
        return 0

    with pytest.raises(deployment.ConfigurationError):
        deployment.deploy(capability)
    assert calls == 0


def test_wrapper_has_no_runtime_adapter_or_forbidden_coupling() -> None:
    source = WRAPPER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imports.isdisjoint({"subprocess", "socket", "docker", "pymysql", "mysql"})
    combined = CONFIG.read_text() + COMPOSE.read_text() + source
    assert FORBIDDEN_CREDENTIAL_IDENTIFIERS.isdisjoint(combined.split())
    assert "secret_preflight" not in combined
    assert "deploy/shopping/compose.yaml" not in combined
    for token in ("rollback", "compensation", "claim recovery"):
        assert token not in source.lower()
