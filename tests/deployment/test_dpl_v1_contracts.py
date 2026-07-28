from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from core.deployment.contracts import (
    DeploymentContractValidationError,
    canonical_json_bytes,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
    verify_digest,
)
from core.deployment.contracts.canonical import CanonicalJSONError

FIXTURES = Path(__file__).parents[1] / "fixtures" / "deployment"
CONTRACT_FIXTURES = {
    "ImmutableDeploymentPackage": "immutable-deployment-package.json",
    "InventoryResult": "inventory-result.json",
    "IngressContract": "ingress-contract.json",
    "IngressReadinessReport": "ingress-readiness-report.json",
    "ValidationReport": "validation-report.json",
    "DesiredCurrentDiff": "desired-current-diff.json",
    "DeterministicDryRunPlan": "deterministic-dry-run-plan.json",
    "ReadinessReport": "readiness-report.json",
    "ErrorEnvelope": "error-envelope.json",
}


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / CONTRACT_FIXTURES[name]).read_text("utf-8"))


def _reject(payload: dict, contract: str = "ImmutableDeploymentPackage") -> None:
    with pytest.raises(DeploymentContractValidationError):
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name=contract,
            payload=payload,
        )


def test_registry_discovery_and_meta_schema() -> None:
    registry = load_schema_registry()
    assert set(registry.contracts).issuperset(CONTRACT_FIXTURES)
    assert {"DeploymentAuditEvidence", "DeploymentApiResponse"}.issubset(
        registry.contracts
    )
    assert registry.manifest["network_resolution"] is False
    assert len(registry.schemas_by_id) == 1 + len(registry.contracts)
    for schema in registry.schemas_by_id.values():
        Draft202012Validator.check_schema(dict(schema))


@pytest.mark.parametrize("contract", CONTRACT_FIXTURES)
def test_valid_schema_fixtures(contract: str) -> None:
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name=contract,
        payload=_fixture(contract),
    )


def test_unknown_schema_version_and_contract_are_rejected() -> None:
    payload = _fixture("ImmutableDeploymentPackage")
    payload["schema_version"] = "dpl/v2"
    _reject(payload)
    _reject(payload, "UnknownContract")


def test_canonical_json_and_digest_are_deterministic_and_utf8() -> None:
    first = {"한글": "값", "b": [2, 1], "a": {"y": True}}
    second = {"a": {"y": True}, "b": [2, 1], "한글": "값"}
    assert canonical_json_bytes(first) == canonical_json_bytes(second)
    assert canonical_json_bytes(first) == (
        '{"a":{"y":true},"b":[2,1],"한글":"값"}'.encode("utf-8")
    )
    assert sha256_digest(first) == sha256_digest(second)
    assert sha256_digest({"a": 1}) == (
        "sha256:015abd7f5cc57a2dd94b7590f04ad8084273905ee33e"
        "c5cebeae62276a97f862"
    )


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_canonical_json_rejects_non_finite_numbers(value: float) -> None:
    with pytest.raises(CanonicalJSONError):
        canonical_json_bytes({"value": value})


def test_digest_tampering_and_input_immutability() -> None:
    payload = _fixture("ImmutableDeploymentPackage")
    original = copy.deepcopy(payload)
    digest = sha256_digest(payload)
    assert verify_digest(payload, digest)
    payload["package_version"] = "1.0.1"
    assert not verify_digest(payload, digest)
    payload = original
    canonical_json_bytes(payload)
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name="ImmutableDeploymentPackage",
        payload=payload,
    )
    assert payload == original


def test_package_security_policy_rejections() -> None:
    mutations = [
        ("read_only", False),
        ("target", {"platform": "ubuntu", "role": "control-plane",
                    "profile": "mac-standalone-production"}),
        ("public_edge", {"owner": "nginx", "direct_application_ports": False}),
        ("artifact_digest", "sha256:bad"),
    ]
    for key, value in mutations:
        payload = _fixture("ImmutableDeploymentPackage")
        payload[key] = value
        _reject(payload)


def test_git_sha_mutable_image_and_additional_property_rejections() -> None:
    payload = _fixture("ImmutableDeploymentPackage")
    payload["source"]["git_commit"] = "abc123"
    _reject(payload)
    payload = _fixture("ImmutableDeploymentPackage")
    payload["components"][0]["image_reference"] = "vendor/app:latest"
    _reject(payload)
    payload = _fixture("ImmutableDeploymentPackage")
    payload["policies"]["unexpected"] = True
    _reject(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("password", "value"),
        ("token", "value"),
        ("secret", "value"),
        ("private_key", "value"),
        ("credential", "value"),
    ],
)
def test_embedded_secret_fields_are_rejected(field: str, value: str) -> None:
    payload = _fixture("ImmutableDeploymentPackage")
    payload["components"][0][field] = value
    error = pytest.raises(
        DeploymentContractValidationError,
        validate_contract_payload,
        registry=load_schema_registry(),
        contract_name="ImmutableDeploymentPackage",
        payload=payload,
    )
    assert any(issue.validator == "secret_field" for issue in error.value.issues)


@pytest.mark.parametrize("operation", ["apply", "execute", "install", "restart", "bootstrap"])
def test_forbidden_operations_are_rejected(operation: str) -> None:
    payload = _fixture("DeterministicDryRunPlan")
    payload["steps"][0]["operation"] = operation
    _reject(payload, "DeterministicDryRunPlan")


def test_path_traversal_is_rejected() -> None:
    payload = _fixture("ImmutableDeploymentPackage")
    payload["components"][0]["artifact_path"] = "../secret"
    error = pytest.raises(
        DeploymentContractValidationError,
        validate_contract_payload,
        registry=load_schema_registry(),
        contract_name="ImmutableDeploymentPackage",
        payload=payload,
    )
    assert any(issue.validator == "path_traversal" for issue in error.value.issues)
