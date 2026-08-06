
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
)


FIXTURES = (
    Path(__file__).parents[1]
    / "fixtures"
    / "deployment"
)

CONTRACT_FIXTURES = {
    "ActivationInspectionPolicy":
        "activation-inspection-policy.json",
    "ActivationRouteManifest":
        "activation-route-manifest.json",
    "ActivationInspectionReport":
        "activation-inspection-report.json",
}


def fixture(contract_name: str) -> dict:
    path = FIXTURES / CONTRACT_FIXTURES[contract_name]

    return json.loads(
        path.read_text(encoding="utf-8")
    )


def reject(
    contract_name: str,
    payload: dict,
) -> DeploymentContractValidationError:
    with pytest.raises(
        DeploymentContractValidationError
    ) as caught:
        validate_contract_payload(
            registry=load_schema_registry(),
            contract_name=contract_name,
            payload=payload,
        )

    return caught.value


def test_contracts_are_registered_and_meta_valid() -> None:
    registry = load_schema_registry()

    assert set(CONTRACT_FIXTURES).issubset(
        registry.contracts
    )

    for contract_name in CONTRACT_FIXTURES:
        binding = registry.contracts[contract_name]
        schema = registry.schemas_by_id[
            binding.schema_id
        ]

        Draft202012Validator.check_schema(
            dict(schema)
        )


@pytest.mark.parametrize(
    "contract_name",
    tuple(CONTRACT_FIXTURES),
)
def test_valid_contract_fixtures(
    contract_name: str,
) -> None:
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name=contract_name,
        payload=fixture(contract_name),
    )


def test_fixture_digest_bindings() -> None:
    policy = fixture(
        "ActivationInspectionPolicy"
    )

    manifest = fixture(
        "ActivationRouteManifest"
    )

    report = fixture(
        "ActivationInspectionReport"
    )

    assert (
        policy["route_manifest"]["manifest_digest"]
        == sha256_digest(manifest)
    )

    assert (
        report["policy_digest"]
        == sha256_digest(policy)
    )

    assert (
        report["route_manifest_digest"]
        == sha256_digest(manifest)
    )

    semantic_report = copy.deepcopy(report)

    supplied_digest = semantic_report.pop(
        "report_digest"
    )

    assert supplied_digest == sha256_digest(
        semantic_report
    )


def test_policy_is_strict_and_fail_closed() -> None:
    payload = fixture(
        "ActivationInspectionPolicy"
    )

    payload["unexpected"] = True

    reject(
        "ActivationInspectionPolicy",
        payload,
    )

    payload = fixture(
        "ActivationInspectionPolicy"
    )

    payload["safety"][
        "production_authorized"
    ] = True

    reject(
        "ActivationInspectionPolicy",
        payload,
    )

    payload = fixture(
        "ActivationInspectionPolicy"
    )

    payload["runtime"]["python"][
        "probe_arguments"
    ] = [
        "--version",
    ]

    reject(
        "ActivationInspectionPolicy",
        payload,
    )


def test_route_manifest_rejects_unsafe_post() -> None:
    payload = fixture(
        "ActivationRouteManifest"
    )

    payload["probes"][2]["path"] = (
        "/shopping/products"
    )

    reject(
        "ActivationRouteManifest",
        payload,
    )

    payload = fixture(
        "ActivationRouteManifest"
    )

    payload["probes"][2][
        "expected_status"
    ] = 200

    reject(
        "ActivationRouteManifest",
        payload,
    )

    payload = fixture(
        "ActivationRouteManifest"
    )

    payload["probes"][2][
        "attempt_count"
    ] = 2

    reject(
        "ActivationRouteManifest",
        payload,
    )


def test_report_status_contract_is_closed() -> None:
    payload = fixture(
        "ActivationInspectionReport"
    )

    payload["overall_status"] = "AUTHORIZED"

    reject(
        "ActivationInspectionReport",
        payload,
    )

    payload = fixture(
        "ActivationInspectionReport"
    )

    payload["overall_status"] = "BLOCKED"

    reject(
        "ActivationInspectionReport",
        payload,
    )

    payload = fixture(
        "ActivationInspectionReport"
    )

    payload["production_authorized"] = True

    reject(
        "ActivationInspectionReport",
        payload,
    )


def test_secret_shaped_fields_are_rejected() -> None:
    payload = fixture(
        "ActivationInspectionReport"
    )

    payload["runtime"]["token"] = (
        "must-not-enter"
    )

    error = reject(
        "ActivationInspectionReport",
        payload,
    )

    assert any(
        issue.validator == "secret_field"
        for issue in error.issues
    )


def test_validation_is_deterministic() -> None:
    first = fixture(
        "ActivationInspectionReport"
    )

    second = copy.deepcopy(first)

    second["git"] = {
        key: second["git"][key]
        for key in reversed(
            list(second["git"])
        )
    }

    assert canonical_json_bytes(
        first
    ) == canonical_json_bytes(
        second
    )

    assert sha256_digest(
        first
    ) == sha256_digest(
        second
    )


def test_pure_validation_uses_no_host_runtime(
    monkeypatch,
) -> None:
    calls: list[str] = []

    def prohibited(*args, **kwargs):
        calls.append("prohibited")

        raise AssertionError(
            "runtime dependency used"
        )

    monkeypatch.setattr(
        "subprocess.run",
        prohibited,
    )

    monkeypatch.setattr(
        "socket.create_connection",
        prohibited,
    )

    monkeypatch.setattr(
        "pathlib.Path.is_symlink",
        prohibited,
    )

    monkeypatch.setattr(
        "os.system",
        prohibited,
    )

    registry = load_schema_registry()

    for contract_name in CONTRACT_FIXTURES:
        validate_contract_payload(
            registry=registry,
            contract_name=contract_name,
            payload=fixture(contract_name),
        )

    assert calls == []
