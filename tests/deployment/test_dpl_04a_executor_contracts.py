from __future__ import annotations

import ast
import copy
from pathlib import Path

import pytest

from core.deployment.contracts import (
    DeploymentContractValidationError,
    canonical_json_bytes,
    load_schema_registry,
    validate_contract_payload,
)
from core.deployment.executor_contracts import (
    ExecutorContractError,
    ExecutorOperation,
    create_executor_capability,
    create_executor_request,
    validate_executor_request,
)
from core.deployment.executor_ports import DenyOnlyNonProductionExecutor
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-07-29T03:00:00Z"
OPS = [item.value for item in ExecutorOperation]


def _authorization() -> dict:
    return {
        "schema_version": "dpl/v1", "authorization_id": "exa-" + "1" * 32,
        "request_id": "apr-" + "2" * 32, "decision_id": "apd-" + "3" * 32,
        "package_digest": "sha256:" + "4" * 64, "plan_digest": "sha256:" + "5" * 64,
        "target_identity": "mac-mini-m4", "environment": "staging",
        "action_scope": ["act-" + "6" * 24], "requester_identity": "actor-a",
        "approver_identity": "actor-b", "nonce": "authorization-nonce-01",
        "issued_timestamp": "2026-07-29T02:00:00Z",
        "expiry_timestamp": "2026-07-29T04:00:00Z", "maximum_uses": 1,
        "execution_authorized": True, "production_authorized": False,
        "executor_invoked": False, "production_writes": 0, "ubuntu_changes": 0,
    }


def _capability(**overrides) -> dict:
    values = {
        "executor_type": "deny-only-non-production", "environment": "staging",
        "target_owner": "mac-control-plane", "operations": OPS,
        "capability_timestamp": STAMP,
    }
    values.update(overrides)
    return create_executor_capability(**values)


def _request(authorization=None, capability=None, **overrides) -> dict:
    values = {
        "authorization": authorization or _authorization(),
        "capability": capability or _capability(),
        "operation_scope": ["VALIDATE_AUTHORIZATION", "SIMULATE_EXECUTION"],
        "actor_identity": "actor-a", "nonce_reference": "nonce-reference-0001",
        "request_timestamp": STAMP,
    }
    values.update(overrides)
    return create_executor_request(**values)


def test_all_schemas_determinism_and_input_immutability() -> None:
    authorization, capability = _authorization(), _capability()
    originals = copy.deepcopy((authorization, capability))
    request_a, request_b = _request(authorization, capability), _request(authorization, capability)
    report = validate_executor_request(
        request=request_a, capability=capability, authorization=authorization,
        validation_timestamp=STAMP,
    )
    result_a = DenyOnlyNonProductionExecutor(capability).execute(
        request_a, result_timestamp=STAMP
    )
    result_b = DenyOnlyNonProductionExecutor(capability).execute(
        request_b, result_timestamp=STAMP
    )
    registry = load_schema_registry()
    for name, payload in (
        ("ExecutorCapability", capability), ("ExecutorRequest", request_a),
        ("ExecutorValidationReport", report), ("ExecutorResult", result_a),
    ):
        validate_contract_payload(registry=registry, contract_name=name, payload=payload)
    assert request_a == request_b
    assert result_a["result_digest"] == result_b["result_digest"]
    assert canonical_json_bytes(result_a) == canonical_json_bytes(result_b)
    assert (authorization, capability) == originals
    assert report["status"] == "ALLOWED"


@pytest.mark.parametrize("environment", ["production", "prod", "live", "customer-production", "sandbox", "unknown"])
def test_production_and_unknown_environments_rejected(environment: str) -> None:
    with pytest.raises(DeploymentContractValidationError):
        _capability(environment=environment)


@pytest.mark.parametrize("owner", ["ubuntu-control-plane", "ubuntu-worker", "wordpress", "woocommerce", "external", "unknown"])
def test_non_mac_and_ubuntu_owners_rejected(owner: str) -> None:
    with pytest.raises(DeploymentContractValidationError):
        _capability(target_owner=owner)


def test_environment_and_operation_allowlists() -> None:
    for environment in ("development", "test", "staging"):
        assert _capability(environment=environment)["environment"] == environment
    for operation in OPS:
        assert _capability(operations=[operation])["operation_scope"] == [operation]
    with pytest.raises(DeploymentContractValidationError):
        _capability(operations=["RUN_COMMAND"])


@pytest.mark.parametrize("field", ["shell", "command", "argv", "script", "ssh_command", "token", "api_secret"])
def test_executable_and_secret_bearing_fields_rejected(field: str) -> None:
    capability = _capability()
    capability[field] = "sensitive-value"
    with pytest.raises(ExecutorContractError):
        _request(capability=capability)


@pytest.mark.parametrize("value", ["../escape", "/absolute/path"])
def test_traversal_and_absolute_paths_rejected(value: str) -> None:
    with pytest.raises(ExecutorContractError):
        _request(actor_identity=value)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("package_digest", "PACKAGE_DIGEST_MISMATCH"),
        ("plan_digest", "PLAN_DIGEST_MISMATCH"),
        ("execution_authorization_id", "AUTHORIZATION_MISMATCH"),
    ],
)
def test_digest_and_authorization_mismatch_denied(field: str, reason: str) -> None:
    request = _request()
    request[field] = "exa-" + "0" * 32 if field == "execution_authorization_id" else "sha256:" + "0" * 64
    report = validate_executor_request(
        request=request, capability=_capability(), authorization=_authorization(),
        validation_timestamp=STAMP,
    )
    assert report["status"] == "DENIED"
    assert reason in report["reason_codes"]


def test_default_deny_has_zero_side_effect_counters() -> None:
    result = DenyOnlyNonProductionExecutor(_capability()).execute(
        _request(), result_timestamp=STAMP
    )
    assert result["status"] == "DENIED"
    assert result["reason_codes"] == ["DEFAULT_DENY_NO_EXECUTOR"]
    for field in (
        "production_writes", "ubuntu_changes", "network_accesses",
        "runtime_commands", "real_executor_invocations",
    ):
        assert result[field] == 0


def test_dependency_policy_namespace_and_forbidden_imports() -> None:
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    assert (ROOT / "core/deployment/executor_contracts").is_dir()
    assert (ROOT / "core/deployment/executor_ports").is_dir()
    assert not (ROOT / "core/deployment/executor_contracts.py").exists()
    forbidden = {
        "subprocess", "socket", "requests", "paramiko", "core.worker",
    }
    for path in (
        ROOT / "core/deployment/executor_contracts",
        ROOT / "core/deployment/executor_ports",
    ):
        for source in path.glob("*.py"):
            tree = ast.parse(source.read_text("utf-8"))
            imports = {
                node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
                for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
            }
            assert not any(
                item == prefix or item.startswith(prefix + ".")
                for item in imports for prefix in forbidden
            )


def test_dpl03_authorization_schema_compatibility() -> None:
    validate_contract_payload(
        registry=load_schema_registry(),
        contract_name="ExecutionAuthorization",
        payload=_authorization(),
    )
