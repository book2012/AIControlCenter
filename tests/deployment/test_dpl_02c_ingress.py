from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from core.deployment.adapters.macos import (
    CaddyIngressAdapter,
    ColimaIngressAdapter,
    ComposeIngressAdapter,
    IngressContractFileAdapter,
    RepositoryFileReader,
)
from core.deployment.application import IngressReadinessService
from core.deployment.contracts import canonical_json_bytes, load_schema_registry, validate_contract_payload
from core.deployment.adapters.macos.caddy_sites import CaddySitePolicyError
from tests.support.caddy_site_fixtures import CaddyFixtureFiles, PRODUCTION, UNGUARDED

ROOT = Path(__file__).parents[2]


class Value:
    def __init__(self, value): self.value = value
    def read_ingress_contract(self): return copy.deepcopy(self.value)
    def observe(self): return copy.deepcopy(self.value)


def _contract():
    return json.loads((ROOT / "config/deployment/ingress.json").read_text("utf-8"))


def _observations():
    files = CaddyFixtureFiles(PRODUCTION)
    source_files = RepositoryFileReader(ROOT)
    return {
        "caddy": CaddyIngressAdapter(files, "ops/macos/caddy/Caddyfile").observe(),
        "colima": ColimaIngressAdapter(source_files, "ops/macos/colima/commerce-runtime.json").observe(),
        "compose": ComposeIngressAdapter(source_files, "deploy/shopping/compose.yaml").observe(),
    }


def _service(values=None, contract=None):
    values = values or _observations()
    return IngressReadinessService(
        contract=Value(contract or _contract()), caddy=Value(values["caddy"]),
        colima=Value(values["colima"]), compose=Value(values["compose"])
    )


def test_repository_configuration_cannot_claim_live_readiness():
    contract = IngressContractFileAdapter(
        RepositoryFileReader(ROOT), "config/deployment/ingress.json"
    ).read_ingress_contract()
    validate_contract_payload(
        registry=load_schema_registry(), contract_name="IngressContract", payload=contract
    )
    result = _service().evaluate()
    assert result["overall_status"] == "DEGRADED"
    assert result["normalized_endpoint_identities"]["caddy"] == "127.0.0.1:58082"
    assert result["warnings"] == [
        "caddy: Repository desired-state evidence cannot establish live ingress readiness."
    ]
    assert result["production_writes"] == result["ubuntu_changes"] == 0
    validate_contract_payload(
        registry=load_schema_registry(), contract_name="IngressReadinessReport", payload=result
    )


@pytest.mark.parametrize(
    ("component", "field", "value", "reason"),
    [
        ("caddy", "port", 58081, "caddy-commerce-port"),
        ("compose", "port_source", "OTHER_PORT", "commerce-compose-port"),
        ("caddy", "host", "192.168.1.2", "caddy-loopback"),
        ("compose", "host", "0.0.0.0", "wordpress-loopback"),
        ("compose", "database_host_published", True, "mariadb-not-published"),
        ("caddy", "owner", "nginx", "public-edge-owner"),
        ("compose", "direct_public_ports", True, "direct-public-ports-disabled"),
        ("colima", "ubuntu_runtime_allowed", True, "ubuntu-runtime-prohibited"),
        ("colima", "runtime_owner", "ubuntu", "mac-runtime-owner"),
    ],
)
def test_mismatches_are_not_ready(component, field, value, reason):
    values = _observations()
    values[component][field] = value
    result = _service(values).evaluate()
    assert result["overall_status"] == "NOT_READY"
    assert reason in result["mismatch_reasons"]


@pytest.mark.parametrize(
    ("adapter", "text"),
    [
        (CaddyIngressAdapter, "not a caddyfile"),
        (CaddyIngressAdapter, "x {\n reverse_proxy 127.0.0.1:1\n reverse_proxy 127.0.0.1:2\n}"),
        (ComposeIngressAdapter, "services: []"),
        (ColimaIngressAdapter, '{"schema_version": 2}'),
        (ComposeIngressAdapter, 'services: {wordpress: {ports: ["0.0.0.0:80:80"]}, database: {}}'),
    ],
)
def test_malformed_and_unsafe_inputs_are_rejected(adapter, text):
    class Reader:
        def read_text(self, path): return text
    with pytest.raises(ValueError):
        adapter(Reader(), "fixture").observe()


def test_missing_evidence_is_degraded_and_all_missing_is_unavailable():
    class Missing:
        def observe(self): raise ValueError("password=do-not-leak")
    values = _observations()
    partial = IngressReadinessService(
        contract=Value(_contract()), caddy=Value(values["caddy"]),
        colima=Missing(), compose=Value(values["compose"])
    ).evaluate()
    assert partial["overall_status"] == "DEGRADED"
    assert "do-not-leak" not in json.dumps(partial)
    total = IngressReadinessService(
        contract=Value(_contract()), caddy=Missing(), colima=Missing(), compose=Missing()
    ).evaluate()
    assert total["overall_status"] == "UNAVAILABLE"


def test_current_repository_caddy_is_guarded_but_not_live_ready():
    files = RepositoryFileReader(ROOT)
    values = _observations()
    values["caddy"] = CaddyIngressAdapter(
        files, "ops/macos/caddy/Caddyfile"
    ).observe()
    caddy = values["caddy"]
    assert caddy["canonical_production_upstream"] == "127.0.0.1:58082"
    assert caddy["sites"]["production"]["role"] == "production"
    assert caddy["sites"]["preview"]["role"] == "preview"
    assert caddy["readiness_granted"] is False
    result = _service(values).evaluate()
    assert result["overall_status"] == "DEGRADED"
    assert result["normalized_endpoint_identities"]["caddy"] == "127.0.0.1:58082"
    rendered = json.dumps(result)
    assert "PRIVATE_GUARDS_REQUIRED" not in rendered
    assert "basic_auth" not in rendered


def test_unguarded_preview_fixture_fails_closed_with_sanitized_reporting():
    files = CaddyFixtureFiles(UNGUARDED)
    with pytest.raises(CaddySitePolicyError, match="^PRIVATE_GUARDS_REQUIRED$"):
        CaddyIngressAdapter(files, "ops/macos/caddy/Caddyfile").observe()
    values = _observations()
    values["caddy"] = CaddyIngressAdapter(
        files, "ops/macos/caddy/Caddyfile"
    ).observe
    result = IngressReadinessService(
        contract=IngressContractFileAdapter(files, "config/deployment/ingress.json"),
        caddy=type("Source", (), {"observe": values["caddy"]})(),
        colima=Value(values["colima"]),
        compose=Value(values["compose"]),
    ).evaluate()
    assert result["overall_status"] == "DEGRADED"
    assert result["overall_status"] != "READY"
    rendered = json.dumps(result)
    assert "PRIVATE_GUARDS_REQUIRED" not in rendered
    assert "basic_auth" not in rendered


def test_invalid_contract_determinism_and_input_immutability():
    invalid = _contract()
    invalid["public_edge"]["owner"] = "nginx"
    assert _service(contract=invalid).evaluate()["overall_status"] == "INVALID"
    values, contract = _observations(), _contract()
    original_values, original_contract = copy.deepcopy(values), copy.deepcopy(contract)
    first = _service(values, contract).evaluate()
    second = _service(values, contract).evaluate()
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert values == original_values and contract == original_contract


def test_path_traversal_and_layer_dependencies():
    with pytest.raises(ValueError):
        IngressContractFileAdapter(RepositoryFileReader(ROOT), "../secret").read_ingress_contract()
    imports = set()
    for path in Path("core/deployment/application").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text("utf-8"))):
            if isinstance(node, ast.Import): imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module: imports.add(node.module)
    prohibited = {"subprocess", "socket", "requests", "paramiko", "docker", "launchctl"}
    assert not imports.intersection(prohibited)
    adapter_text = "\n".join(
        path.read_text("utf-8") for path in Path("core/deployment/adapters/macos").glob("*.py")
    )
    assert "subprocess" not in adapter_text and "UbuntuWorkerClient" not in adapter_text
