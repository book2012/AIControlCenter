from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from core.deployment.application import MacInventoryService
from core.deployment.contracts import (
    canonical_json_bytes,
    load_schema_registry,
    validate_contract_payload,
)


class Source:
    def __init__(self, value):
        self.value = value

    def observe_git_identity(self):
        return self.value

    def observe_runtime_metadata(self):
        return self.value

    def observe_launchd(self):
        return self.value

    def observe_caddy_desired_state(self):
        return self.value

    def observe_colima_contract(self):
        return self.value

    def observe_compose_desired_state(self):
        return self.value


class Clock:
    def now_utc(self) -> str:
        return "2026-07-28T00:00:00Z"


def _service(**overrides) -> MacInventoryService:
    values = {
        "git": {"repository_id": "AIControlCenter", "branch": "feature/deployment-package", "commit": "0" * 40},
        "runtime": {"commit": "0" * 40, "runtime_mode": "shadow"},
        "launchd": {"services": [{"label": "com.aicontrolcenter.api.shadow", "desired": "loaded", "current": "running"}]},
        "caddy": {"owner": "host-caddy", "sole_public_edge": True, "application_exposure": "loopback-only"},
        "colima": {"public_ingress_owner": "host-caddy", "ubuntu_runtime_allowed": False},
        "compose": {
            "project": "ai-shopping",
            "wordpress": True,
            "woocommerce": True,
            "wordpress_exposure": "loopback-only",
            "direct_public_ports": False,
        },
    }
    values.update(overrides)
    return MacInventoryService(
        git=Source(values["git"]),
        runtime=Source(values["runtime"]),
        launchd=Source(values["launchd"]),
        caddy=Source(values["caddy"]),
        colima=Source(values["colima"]),
        compose=Source(values["compose"]),
        clock=Clock(),
    )


def test_inventory_is_deterministic_schema_valid_and_ordered() -> None:
    first = _service().collect()
    second = _service().collect()
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert [item["component_id"] for item in first["items"]] == [
        "git-repository",
        "runtime-metadata",
        "mac-production-profile",
        "launchd-services",
        "host-caddy",
        "colima-commerce",
        "compose-commerce",
        "wordpress",
        "woocommerce",
        "public-edge-policy",
    ]
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name="InventoryResult",
        payload=first,
    )


def test_ownership_loopback_and_sole_edge_policy() -> None:
    items = {item["component_id"]: item for item in _service().collect()["items"]}
    assert items["wordpress"]["details"]["business_logic_owner"] == "aicontrolcenter"
    assert items["woocommerce"]["details"]["business_logic_owner"] == "aicontrolcenter"
    assert items["wordpress"]["details"]["exposure"] == "loopback-only"
    assert items["public-edge-policy"]["details"] == {
        "owner": "host-caddy",
        "sole_public_edge": True,
        "direct_public_service_ports": False,
        "live_network_test_performed": False,
    }


def test_partial_failure_is_structured_and_redacted() -> None:
    class Failure(Source):
        def observe_runtime_metadata(self):
            raise RuntimeError("password=hunter2 token=abc /Users/private")

    result = _service(runtime={}).collect()
    service = _service()
    service._sources["runtime-metadata"] = ("runtime-metadata", Failure({}).observe_runtime_metadata)
    result = service.collect()
    item = next(value for value in result["items"] if value["component_id"] == "runtime-metadata")
    assert item["state"] == "unavailable"
    assert item["observed"] is False
    rendered = canonical_json_bytes(result).decode()
    assert "hunter2" not in rendered
    assert "token=abc" not in rendered
    assert "/Users/private" not in rendered


def test_malformed_adapter_data_becomes_unavailable() -> None:
    item = _service(git=["not", "an", "object"]).collect()["items"][0]
    assert item["state"] == "unavailable"


def test_input_objects_are_not_mutated() -> None:
    compose = {
        "wordpress": True,
        "woocommerce": True,
        "wordpress_exposure": "loopback-only",
        "direct_public_ports": False,
        "nested": {"values": [1, 2]},
    }
    original = copy.deepcopy(compose)
    _service(compose=compose).collect()
    assert compose == original


def test_degraded_edge_when_direct_public_ports_are_declared() -> None:
    result = _service(compose={
        "wordpress": True,
        "woocommerce": True,
        "wordpress_exposure": "public-prohibited",
        "direct_public_ports": True,
    }).collect()
    edge = result["items"][-1]
    assert edge["state"] == "degraded"
    assert edge["details"]["sole_public_edge"] is False


@pytest.mark.parametrize("name", ["subprocess", "socket", "requests", "paramiko"])
def test_application_layer_has_no_runtime_transport_import(name: str) -> None:
    root = Path("core/deployment/application")
    imported = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text("utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert name not in imported
