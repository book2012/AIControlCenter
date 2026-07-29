"""Pure DPL-04A non-production executor contract composition."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from datetime import datetime
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Any

from core.deployment.contracts import load_schema_registry, sha256_digest, validate_contract_payload


class ExecutorContractError(ValueError):
    """Raised without reflecting potentially sensitive input values."""


class ExecutorEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"


class ExecutorOperation(StrEnum):
    VERIFY_SANDBOX_TARGET = "VERIFY_SANDBOX_TARGET"
    VALIDATE_DEPLOYMENT_PACKAGE = "VALIDATE_DEPLOYMENT_PACKAGE"
    VALIDATE_DEPLOYMENT_PLAN = "VALIDATE_DEPLOYMENT_PLAN"
    VALIDATE_AUTHORIZATION = "VALIDATE_AUTHORIZATION"
    PREPARE_SANDBOX = "PREPARE_SANDBOX"
    SIMULATE_EXECUTION = "SIMULATE_EXECUTION"
    COLLECT_EXECUTION_EVIDENCE = "COLLECT_EXECUTION_EVIDENCE"


class ExecutorStatus(StrEnum):
    ALLOWED = "ALLOWED"
    DENIED = "DENIED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    INCOMPLETE = "INCOMPLETE"


ALLOWED_TARGET_OWNER = "mac-control-plane"
_FORBIDDEN_KEYS = {
    "argv", "command", "environment_variables", "executable", "filesystem_path",
    "password", "private_key", "raw_environment", "script", "secret", "shell",
    "ssh_command", "token",
}


def _security_check(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ExecutorContractError("unsafe or unsupported executor input")
            normalized = key.lower()
            if normalized in _FORBIDDEN_KEYS or any(
                marker in normalized
                for marker in ("credential", "password", "secret", "token")
            ):
                raise ExecutorContractError("unsafe or unsupported executor input")
            _security_check(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _security_check(child)
    elif isinstance(value, str):
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts:
            raise ExecutorContractError("unsafe or unsupported executor input")


def _validate_timestamp(value: str) -> None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ExecutorContractError("invalid timestamp input") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutorContractError("invalid timestamp input")


def _validate(name: str, value: Mapping[str, Any]) -> None:
    validate_contract_payload(
        registry=load_schema_registry(), contract_name=name, payload=value
    )


def _id(prefix: str, semantic: Mapping[str, Any]) -> str:
    return prefix + sha256_digest(semantic)[7:39]


def create_executor_capability(
    *,
    executor_type: str,
    environment: str,
    target_owner: str,
    operations: Sequence[str],
    capability_timestamp: str,
) -> dict[str, Any]:
    _security_check(locals())
    _validate_timestamp(capability_timestamp)
    operation_scope = sorted(set(operations))
    semantic = {
        "schema_version": "dpl/v1",
        "executor_type": executor_type,
        "environment": environment,
        "target_owner": target_owner,
        "operation_scope": operation_scope,
        "production_authorized": False,
    }
    capability = {
        "capability_id": _id("exc-", semantic),
        **semantic,
        "capability_timestamp": capability_timestamp,
    }
    _validate("ExecutorCapability", capability)
    return capability


def create_executor_request(
    *,
    authorization: Mapping[str, Any],
    capability: Mapping[str, Any],
    operation_scope: Sequence[str],
    actor_identity: str,
    nonce_reference: str,
    request_timestamp: str,
) -> dict[str, Any]:
    inputs = copy.deepcopy(
        {
            "authorization": dict(authorization),
            "capability": dict(capability),
            "operation_scope": list(operation_scope),
            "actor_identity": actor_identity,
            "nonce_reference": nonce_reference,
            "request_timestamp": request_timestamp,
        }
    )
    _security_check(inputs)
    _validate_timestamp(request_timestamp)
    _validate("ExecutionAuthorization", inputs["authorization"])
    _validate("ExecutorCapability", inputs["capability"])
    scope = sorted(set(inputs["operation_scope"]))
    auth = inputs["authorization"]
    cap = inputs["capability"]
    if (
        auth["production_authorized"] is not False
        or auth["environment"] != cap["environment"]
        or not set(scope).issubset(cap["operation_scope"])
    ):
        raise ExecutorContractError("authorization or capability binding mismatch")
    semantic = {
        "schema_version": "dpl/v1",
        "execution_authorization_id": auth["authorization_id"],
        "capability_id": cap["capability_id"],
        "package_digest": auth["package_digest"],
        "plan_digest": auth["plan_digest"],
        "target_identity": auth["target_identity"],
        "target_owner": cap["target_owner"],
        "environment": auth["environment"],
        "operation_scope": scope,
        "actor_identity": actor_identity,
        "nonce_reference": nonce_reference,
        "production_authorized": False,
    }
    request = {
        "request_id": _id("exr-", semantic),
        **semantic,
        "request_timestamp": request_timestamp,
    }
    _validate("ExecutorRequest", request)
    return request


def validate_executor_request(
    *,
    request: Mapping[str, Any],
    capability: Mapping[str, Any],
    authorization: Mapping[str, Any],
    validation_timestamp: str,
) -> dict[str, Any]:
    values = copy.deepcopy(
        {"request": dict(request), "capability": dict(capability), "authorization": dict(authorization)}
    )
    reasons: list[str] = []
    try:
        _security_check(values)
        _validate_timestamp(validation_timestamp)
        _validate("ExecutorRequest", values["request"])
        _validate("ExecutorCapability", values["capability"])
        _validate("ExecutionAuthorization", values["authorization"])
    except Exception:
        reasons.append("INVALID_INPUT")
    if not reasons:
        req, cap, auth = values["request"], values["capability"], values["authorization"]
        bindings = (
            ("CAPABILITY_MISMATCH", req["capability_id"], cap["capability_id"]),
            ("AUTHORIZATION_MISMATCH", req["execution_authorization_id"], auth["authorization_id"]),
            ("PACKAGE_DIGEST_MISMATCH", req["package_digest"], auth["package_digest"]),
            ("PLAN_DIGEST_MISMATCH", req["plan_digest"], auth["plan_digest"]),
            ("TARGET_MISMATCH", req["target_identity"], auth["target_identity"]),
            ("ENVIRONMENT_MISMATCH", req["environment"], auth["environment"]),
        )
        reasons.extend(code for code, left, right in bindings if left != right)
        if req["target_owner"] != cap["target_owner"]:
            reasons.append("TARGET_OWNER_MISMATCH")
        if not set(req["operation_scope"]).issubset(cap["operation_scope"]):
            reasons.append("OPERATION_SCOPE_MISMATCH")
    status = ExecutorStatus.ALLOWED if not reasons else ExecutorStatus.DENIED
    semantic = {
        "schema_version": "dpl/v1",
        "request_id": request.get("request_id", "exr-" + "0" * 32),
        "capability_id": capability.get("capability_id", "exc-" + "0" * 32),
        "status": status,
        "reason_codes": sorted(set(reasons)),
        "production_authorized": False,
    }
    report = {
        "report_id": _id("exv-", semantic),
        **semantic,
        "validation_timestamp": validation_timestamp,
    }
    _validate("ExecutorValidationReport", report)
    return report


def create_executor_result(
    *, request: Mapping[str, Any], capability: Mapping[str, Any],
    status: str, reason_codes: Sequence[str], result_timestamp: str,
) -> dict[str, Any]:
    _security_check({"request": request, "capability": capability})
    _validate_timestamp(result_timestamp)
    _validate("ExecutorRequest", request)
    _validate("ExecutorCapability", capability)
    semantic = {
        "schema_version": "dpl/v1",
        "request_id": request["request_id"],
        "capability_id": capability["capability_id"],
        "status": status,
        "executor_type": capability["executor_type"],
        "operation_results": [
            {"operation": operation, "status": status}
            for operation in sorted(request["operation_scope"])
        ],
        "evidence_digests": [],
        "reason_codes": sorted(set(reason_codes)),
        "production_authorized": False,
        "production_writes": 0,
        "ubuntu_changes": 0,
        "network_accesses": 0,
        "runtime_commands": 0,
        "real_executor_invocations": 0,
    }
    result = {
        "result_digest": sha256_digest(semantic),
        **semantic,
        "result_timestamp": result_timestamp,
    }
    _validate("ExecutorResult", result)
    return result


__all__ = (
    "ALLOWED_TARGET_OWNER", "ExecutorContractError", "ExecutorEnvironment",
    "ExecutorOperation", "ExecutorStatus", "create_executor_capability",
    "create_executor_request", "create_executor_result", "validate_executor_request",
)
