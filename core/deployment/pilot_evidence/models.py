"""Immutable M2-P3 evidence and controlled rollback contracts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class PilotEvidenceError(ValueError):
    """Raised without reflecting unsafe evidence input."""


class PilotRollbackStatus(StrEnum):
    EVIDENCE_VALID = "EVIDENCE_VALID"
    EVIDENCE_INVALID = "EVIDENCE_INVALID"
    ROLLED_BACK = "ROLLED_BACK"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    REPLAYED = "REPLAYED"


ACTIVATION_STEPS = (
    "VERIFY_SANDBOX_TARGET",
    "PREPARE_SANDBOX",
    "COLLECT_EXECUTION_EVIDENCE",
)
ROLLBACK_STEPS = (
    "VERIFY_ROLLBACK_TARGET",
    "VERIFY_ACTIVATION_EVIDENCE",
    "REMOVE_CONTROLLED_TEST_ARTIFACTS",
    "VERIFY_PRE_ACTIVATION_STATE",
    "COLLECT_ROLLBACK_EVIDENCE",
)
SAFETY_COUNTERS = (
    "production_writes", "repository_runtime_writes", "ubuntu_changes",
    "network_accesses", "runtime_commands", "service_restarts",
)
_FORBIDDEN = {
    "password", "api_key", "access_token", "token", "private_key", "cookie",
    "cookies", "authorization_header", "raw_environment",
    "environment_variables", "shell", "command", "argv", "script",
}


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise PilotEvidenceError("evidence keys must be strings")
            normalized = key.lower()
            if normalized in _FORBIDDEN or any(
                marker in normalized for marker in (
                    "password", "api_key", "access_token", "private_key",
                    "cookie", "authorization_header",
                )
            ):
                raise PilotEvidenceError("unsafe evidence field rejected")
            validate_safe(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            validate_safe(child)
    elif isinstance(value, StrEnum):
        return
    elif not isinstance(value, (str, int, bool, type(None))):
        raise PilotEvidenceError("unsupported evidence value")


def _thaw(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return _thaw(value.to_dict())
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


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True)
class PilotEvidenceManifest:
    before_state_manifest_digest: str
    after_activation_manifest_digest: str
    artifact_paths: tuple[str, ...]
    artifact_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifact_paths", tuple(sorted(self.artifact_paths)))
        object.__setattr__(self, "artifact_digests", tuple(sorted(self.artifact_digests)))
        if len(set(self.artifact_paths)) != len(self.artifact_paths):
            raise PilotEvidenceError("duplicate artifact path")
        if len(set(self.artifact_digests)) != len(self.artifact_digests):
            raise PilotEvidenceError("duplicate evidence digest")
        validate_safe(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "before_state_manifest_digest": self.before_state_manifest_digest,
            "after_activation_manifest_digest": self.after_activation_manifest_digest,
            "artifact_paths": list(self.artifact_paths),
            "artifact_digests": list(self.artifact_digests),
        }


@dataclass(frozen=True)
class PilotEvidenceBundle:
    bundle_id: str
    permit_id: str
    permit_digest: str
    execution_authorization_id: str
    readiness_report_id: str
    readiness_report_digest: str
    activation_id: str
    activation_receipt_id: str
    activation_receipt_digest: str
    package_digest: str
    plan_digest: str
    target_identity: str
    environment: str
    sandbox_root_identity_digest: str
    requester_identity: str
    operator_identity: str
    approver_identity: str
    ordered_activation_steps: tuple[str, ...]
    ordered_executor_result_ids: tuple[str, ...]
    ordered_executor_result_digests: tuple[str, ...]
    manifest: PilotEvidenceManifest
    safety_counters: Mapping[str, int]
    recorded_at: str
    controlled_test_sandbox: bool
    persistent_host_activation: bool
    production_authorized: bool
    evidence_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ordered_activation_steps", tuple(self.ordered_activation_steps))
        object.__setattr__(self, "ordered_executor_result_ids", tuple(self.ordered_executor_result_ids))
        object.__setattr__(self, "ordered_executor_result_digests", tuple(self.ordered_executor_result_digests))
        object.__setattr__(self, "safety_counters", MappingProxyType(dict(sorted(self.safety_counters.items()))))
        validate_safe(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id, "permit_id": self.permit_id,
            "permit_digest": self.permit_digest,
            "execution_authorization_id": self.execution_authorization_id,
            "readiness_report_id": self.readiness_report_id,
            "readiness_report_digest": self.readiness_report_digest,
            "activation_id": self.activation_id,
            "activation_receipt_id": self.activation_receipt_id,
            "activation_receipt_digest": self.activation_receipt_digest,
            "package_digest": self.package_digest, "plan_digest": self.plan_digest,
            "target_identity": self.target_identity, "environment": self.environment,
            "sandbox_root_identity_digest": self.sandbox_root_identity_digest,
            "requester_identity": self.requester_identity,
            "operator_identity": self.operator_identity,
            "approver_identity": self.approver_identity,
            "ordered_activation_steps": list(self.ordered_activation_steps),
            "ordered_executor_result_ids": list(self.ordered_executor_result_ids),
            "ordered_executor_result_digests": list(self.ordered_executor_result_digests),
            "manifest": self.manifest.to_dict(),
            "safety_counters": dict(self.safety_counters),
            "recorded_at": self.recorded_at,
            "controlled_test_sandbox": self.controlled_test_sandbox,
            "persistent_host_activation": self.persistent_host_activation,
            "production_authorized": self.production_authorized,
            "evidence_digest": self.evidence_digest,
        }


@dataclass(frozen=True)
class PilotEvidenceFinding:
    code: str
    field: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "field": self.field}


@dataclass(frozen=True)
class PilotEvidenceValidationReport:
    status: PilotRollbackStatus
    findings: tuple[PilotEvidenceFinding, ...]
    validated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status.value, "findings": [x.to_dict() for x in self.findings], "validated_at": self.validated_at}


@dataclass(frozen=True)
class PilotRollbackRequest:
    evidence_bundle_id: str
    evidence_digest: str
    operator_identity: str
    rollback_approver_identity: str
    rollback_approver_role: str
    reason_category: str
    requested_at: str
    expires_at: str
    production_authorized: bool = False
    persistent_host_rollback: bool = False

    def __post_init__(self) -> None:
        validate_safe(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class PilotRollbackStep:
    sequence: int
    operation: str

    def to_dict(self) -> dict[str, Any]:
        return {"sequence": self.sequence, "operation": self.operation}


@dataclass(frozen=True)
class PilotRollbackPlan:
    plan_id: str
    evidence_bundle_id: str
    evidence_digest: str
    activation_id: str
    activation_receipt_digest: str
    permit_id: str
    sandbox_root_identity_digest: str
    before_state_manifest_digest: str
    after_activation_manifest_digest: str
    artifact_paths: tuple[str, ...]
    operator_identity: str
    rollback_approver_identity: str
    reason_category: str
    requested_at: str
    steps: tuple[PilotRollbackStep, ...]
    production_authorized: bool = False
    persistent_host_rollback: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = self.__dict__.copy()
        value["artifact_paths"] = list(self.artifact_paths)
        value["steps"] = [step.to_dict() for step in self.steps]
        return value


@dataclass(frozen=True)
class PilotRollbackReceipt:
    rollback_id: str
    evidence_bundle_id: str
    evidence_digest: str
    activation_id: str
    activation_receipt_digest: str
    permit_id: str
    target_identity: str
    environment: str
    sandbox_root_identity_digest: str
    before_state_manifest_digest: str
    after_activation_manifest_digest: str
    after_rollback_manifest_digest: str
    ordered_rollback_steps: tuple[str, ...]
    rollback_evidence_digests: tuple[str, ...]
    rollback_status: PilotRollbackStatus
    rollback_request_consumed: bool
    controlled_test_sandbox: bool
    persistent_host_rollback: bool
    production_authorized: bool
    safety_counters: Mapping[str, int]
    receipt_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "safety_counters", MappingProxyType(dict(sorted(self.safety_counters.items()))))

    def to_dict(self) -> dict[str, Any]:
        value = self.__dict__.copy()
        value["ordered_rollback_steps"] = list(self.ordered_rollback_steps)
        value["rollback_evidence_digests"] = list(self.rollback_evidence_digests)
        value["rollback_status"] = self.rollback_status.value
        value["safety_counters"] = dict(self.safety_counters)
        return value


@dataclass(frozen=True)
class PilotRollbackDecision:
    status: PilotRollbackStatus
    reason_codes: tuple[str, ...]
    plan: PilotRollbackPlan | None
    receipt: PilotRollbackReceipt | None


@dataclass(frozen=True)
class PilotRecoveryValidationReport:
    status: PilotRollbackStatus
    before_state_manifest_digest: str
    after_rollback_manifest_digest: str
    findings: tuple[PilotEvidenceFinding, ...]
