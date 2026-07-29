"""Immutable M2-P2 controlled sandbox pilot activation contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from core.deployment.pilot_authorization import PilotPermit


class PilotActivationError(ValueError):
    """Raised without reflecting unsafe activation input."""


class PilotActivationStatus(StrEnum):
    ACTIVATED = "ACTIVATED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    REPLAYED = "REPLAYED"


_FORBIDDEN = {
    "password", "api_key", "access_token", "token", "private_key", "cookie",
    "cookies", "authorization_header", "raw_environment",
    "environment_variables", "shell", "command", "argv", "script",
}


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise PilotActivationError("activation keys must be strings")
            normalized = key.lower()
            if normalized in _FORBIDDEN or any(
                marker in normalized
                for marker in (
                    "password", "api_key", "access_token", "private_key",
                    "cookie", "authorization_header",
                )
            ):
                raise PilotActivationError("unsafe activation field rejected")
            validate_safe(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            validate_safe(child)
    elif isinstance(value, StrEnum):
        return
    elif not isinstance(value, (str, int, bool, type(None))):
        raise PilotActivationError("unsupported activation value")


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    if isinstance(value, StrEnum):
        return value.value
    return value


def canonical_json(value: Any) -> str:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return json.dumps(_thaw(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class PilotActivationRequest:
    permit: PilotPermit
    permit_id: str
    permit_digest: str
    execution_authorization_id: str
    readiness_report_id: str
    readiness_report_digest: str
    package_digest: str
    plan_digest: str
    target_identity: str
    target_owner: str
    environment: str
    operation_scope: tuple[str, ...]
    sandbox_root_identity_digest: str
    requester_identity: str
    operator_identity: str
    approver_identity: str
    activation_id: str
    activation_timestamp: str
    production_authorized: bool = False
    persistent_audit_operational: bool = False
    safety_counters: Mapping[str, int] = MappingProxyType({})

    def __post_init__(self) -> None:
        object.__setattr__(self, "operation_scope", tuple(sorted(set(self.operation_scope))))
        object.__setattr__(
            self, "safety_counters",
            MappingProxyType({key: self.safety_counters[key] for key in sorted(self.safety_counters)}),
        )
        validate_safe(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "permit": self.permit.to_dict(), "permit_id": self.permit_id,
            "permit_digest": self.permit_digest,
            "execution_authorization_id": self.execution_authorization_id,
            "readiness_report_id": self.readiness_report_id,
            "readiness_report_digest": self.readiness_report_digest,
            "package_digest": self.package_digest, "plan_digest": self.plan_digest,
            "target_identity": self.target_identity, "target_owner": self.target_owner,
            "environment": self.environment, "operation_scope": list(self.operation_scope),
            "sandbox_root_identity_digest": self.sandbox_root_identity_digest,
            "requester_identity": self.requester_identity,
            "operator_identity": self.operator_identity,
            "approver_identity": self.approver_identity,
            "activation_id": self.activation_id,
            "activation_timestamp": self.activation_timestamp,
            "production_authorized": self.production_authorized,
            "persistent_audit_operational": self.persistent_audit_operational,
            "safety_counters": dict(self.safety_counters),
        }


@dataclass(frozen=True)
class PilotActivationStep:
    sequence: int
    operation: str
    request_id: str
    capability_id: str
    result_digest: str
    status: str
    evidence_digests: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence, "operation": self.operation,
            "request_id": self.request_id, "capability_id": self.capability_id,
            "result_digest": self.result_digest, "status": self.status,
            "evidence_digests": list(self.evidence_digests),
        }


@dataclass(frozen=True)
class PilotActivationEvidence:
    ordered_steps: tuple[PilotActivationStep, ...]
    executor_result_digests: tuple[str, ...]
    evidence_digests: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ordered_steps": [step.to_dict() for step in self.ordered_steps],
            "executor_result_digests": list(self.executor_result_digests),
            "evidence_digests": list(self.evidence_digests),
        }


@dataclass(frozen=True)
class PilotActivationValidationReport:
    status: PilotActivationStatus
    reason_codes: tuple[str, ...]
    evaluated_at: str
    permit_consumed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value, "reason_codes": list(self.reason_codes),
            "evaluated_at": self.evaluated_at, "permit_consumed": self.permit_consumed,
        }


@dataclass(frozen=True)
class PilotActivationReceipt:
    activation_id: str
    permit_id: str
    permit_digest: str
    execution_authorization_id: str
    readiness_report_id: str
    package_digest: str
    plan_digest: str
    target_identity: str
    environment: str
    sandbox_root_identity_digest: str
    evidence: PilotActivationEvidence
    activation_status: PilotActivationStatus
    permit_consumed: bool
    controlled_test_sandbox: bool
    production_authorized: bool
    production_writes: int
    repository_runtime_writes: int
    ubuntu_changes: int
    network_accesses: int
    runtime_commands: int
    service_restarts: int
    receipt_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation_id": self.activation_id, "permit_id": self.permit_id,
            "permit_digest": self.permit_digest,
            "execution_authorization_id": self.execution_authorization_id,
            "readiness_report_id": self.readiness_report_id,
            "package_digest": self.package_digest, "plan_digest": self.plan_digest,
            "target_identity": self.target_identity, "environment": self.environment,
            "sandbox_root_identity_digest": self.sandbox_root_identity_digest,
            "evidence": self.evidence.to_dict(),
            "activation_status": self.activation_status.value,
            "permit_consumed": self.permit_consumed,
            "controlled_test_sandbox": self.controlled_test_sandbox,
            "production_authorized": self.production_authorized,
            "production_writes": self.production_writes,
            "repository_runtime_writes": self.repository_runtime_writes,
            "ubuntu_changes": self.ubuntu_changes,
            "network_accesses": self.network_accesses,
            "runtime_commands": self.runtime_commands,
            "service_restarts": self.service_restarts,
            "receipt_digest": self.receipt_digest,
        }


@dataclass(frozen=True)
class PilotActivationDecision:
    status: PilotActivationStatus
    reason_codes: tuple[str, ...]
    receipt: PilotActivationReceipt | None
    validation_report: PilotActivationValidationReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value, "reason_codes": list(self.reason_codes),
            "receipt": self.receipt.to_dict() if self.receipt else None,
            "validation_report": self.validation_report.to_dict(),
        }
