from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from core.api.app import create_app
from core.api.dependencies.deployment import (
    NullAuditEvidenceSink,
    get_deployment_api_composer,
    get_ingress_readiness_service,
    get_mac_inventory_service,
)
from core.deployment.application import DeploymentApiComposer
from core.deployment.contracts import (
    canonical_json_bytes,
    load_schema_registry,
    validate_contract_payload,
)

FIXTURES = Path("tests/fixtures/deployment")


class FixedClock:
    def now_utc(self) -> str:
        return "2026-07-28T00:00:00Z"


class MemorySink:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, evidence: dict[str, Any]) -> None:
        self.events.append(evidence)


class FakeInventory:
    calls = 0

    def collect(self) -> dict[str, Any]:
        self.calls += 1
        return json.loads((FIXTURES / "inventory-result.json").read_text("utf-8"))


class FakeIngress:
    calls = 0

    def __init__(self, status: str = "READY") -> None:
        self.status = status

    def evaluate(self) -> dict[str, Any]:
        self.calls += 1
        value = json.loads(
            (FIXTURES / "ingress-readiness-report.json").read_text("utf-8")
        )
        value["overall_status"] = self.status
        if self.status == "NOT_READY":
            value["mismatch_reasons"] = ["caddy-commerce-port"]
        return value


@pytest.fixture
def api() -> tuple[TestClient, MemorySink, FakeInventory, FakeIngress]:
    app = create_app()
    sink, inventory, ingress = MemorySink(), FakeInventory(), FakeIngress()
    app.dependency_overrides[get_deployment_api_composer] = lambda: DeploymentApiComposer(
        clock=FixedClock(), sink=sink
    )
    app.dependency_overrides[get_mac_inventory_service] = lambda: inventory
    app.dependency_overrides[get_ingress_readiness_service] = lambda: ingress
    return TestClient(app), sink, inventory, ingress


def _assert_response(payload: dict[str, Any], result_contract: str | None = None) -> None:
    registry = load_schema_registry()
    validate_contract_payload(
        registry=registry, contract_name="DeploymentApiResponse", payload=payload
    )
    validate_contract_payload(
        registry=registry,
        contract_name="DeploymentAuditEvidence",
        payload=payload["audit_evidence"],
    )
    if result_contract:
        validate_contract_payload(
            registry=registry, contract_name=result_contract, payload=payload["result"]
        )


def test_schema_discovery_success_and_determinism(api) -> None:
    client, sink, _, _ = api
    headers = {"x-actor-id": "lead", "x-context-id": "test", "x-request-id": "req-1"}
    first = client.get("/api/deployment/v1/schemas", headers=headers)
    second = client.get("/api/deployment/v1/schemas", headers=headers)
    assert first.status_code == 200
    assert canonical_json_bytes(first.json()) == canonical_json_bytes(second.json())
    _assert_response(first.json())
    assert first.json()["audit_evidence"]["actor_identity"] == "lead"
    assert sink.events[0] == sink.events[1]


def test_package_inspection_success_and_malformed_error(api) -> None:
    client, sink, _, _ = api
    package = json.loads(
        (FIXTURES / "immutable-deployment-package.json").read_text("utf-8")
    )
    response = client.get(
        "/api/deployment/v1/packages/inspect", params={"package": json.dumps(package)}
    )
    assert response.status_code == 200
    _assert_response(response.json())
    assert response.json()["result"]["valid"] is True

    package["components"][0]["token"] = "do-not-leak"
    bad = client.get(
        "/api/deployment/v1/packages/inspect", params={"package": json.dumps(package)}
    )
    assert bad.status_code == 422
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name="ErrorEnvelope",
        payload=bad.json(),
    )
    assert "do-not-leak" not in bad.text
    assert sink.events[-1]["error"]["message"].endswith("withheld.")


def test_inventory_and_ingress_success(api) -> None:
    client, _, _, _ = api
    inventory = client.get("/api/deployment/v1/inventory/mac")
    ingress = client.get("/api/deployment/v1/readiness/ingress")
    assert inventory.status_code == ingress.status_code == 200
    _assert_response(inventory.json(), "InventoryResult")
    _assert_response(ingress.json(), "IngressReadinessReport")


def test_inventory_unavailable_and_ingress_not_ready(api) -> None:
    client, _, inventory, ingress = api
    value = inventory.collect()
    for item in value["items"]:
        item.update(observed=False, state="unavailable", details={}, evidence=[])
        item["errors"] = [{"code": "unavailable", "message": "Withheld."}]
    inventory.collect = lambda: value
    ingress.status = "NOT_READY"
    assert (
        client.get("/api/deployment/v1/inventory/mac").json()["audit_evidence"][
            "result_classification"
        ]
        == "UNAVAILABLE"
    )
    assert (
        client.get("/api/deployment/v1/readiness/ingress").json()["audit_evidence"][
            "result_classification"
        ]
        == "NOT_READY"
    )


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
@pytest.mark.parametrize(
    "path",
    [
        "/api/deployment/v1/schemas",
        "/api/deployment/v1/packages/inspect",
        "/api/deployment/v1/inventory/mac",
        "/api/deployment/v1/readiness/ingress",
    ],
)
def test_write_methods_denied_without_dependencies(api, method: str, path: str) -> None:
    client, sink, inventory, ingress = api
    response = client.request(method.upper(), path, json={"token": "must-not-reach"})
    assert response.status_code == 405
    assert sink.events == []
    assert inventory.calls == 0
    assert ingress.calls == 0


def test_no_execution_routes_or_persistent_default() -> None:
    from core.api.routes.deployment import router

    dpl_routes = list(router.routes)
    assert dpl_routes
    assert all(route.methods == {"GET"} for route in dpl_routes)
    assert not any(
        word in route.path
        for route in dpl_routes
        for word in ("apply", "execute", "restart", "install", "rollback", "activate")
    )
    composer = get_deployment_api_composer()
    assert isinstance(composer._sink, NullAuditEvidenceSink)


def test_api_composition_has_no_forbidden_dependencies_or_absolute_leakage(api) -> None:
    text = "\n".join(
        Path(path).read_text("utf-8")
        for path in (
            "core/api/routes/deployment.py",
            "core/api/dependencies/deployment.py",
            "core/deployment/application/api_composition.py",
        )
    )
    forbidden = (
        "UbuntuWorkerClient",
        "SSHRunner",
        "subprocess",
        "socket.",
        "urllib",
        "SQLiteAuditRepository",
    )
    assert not any(name in text for name in forbidden)
    client, _, _, _ = api
    response = client.get("/api/deployment/v1/inventory/mac")
    assert "/Users/" not in response.text
