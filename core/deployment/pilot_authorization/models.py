"""Immutable contracts for M2-P1 controlled sandbox pilot authorization."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class PilotAuthorizationError(ValueError):
    """Raised without reflecting unsafe input values."""


class PilotAuthorizationStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"


class PilotRestriction(StrEnum):
    MAC_CONTROL_PLANE_ONLY = "MAC_CONTROL_PLANE_ONLY"
    NON_PRODUCTION_ONLY = "NON_PRODUCTION_ONLY"
    ONE_TIME_USE = "ONE_TIME_USE"
    NO_PERSISTENT_AUDIT = "NO_PERSISTENT_AUDIT"
    NO_PILOT_ACTIVATION = "NO_PILOT_ACTIVATION"
    NO_PRODUCTION_AUTHORIZATION = "NO_PRODUCTION_AUTHORIZATION"


_FORBIDDEN_KEYS = {
    "password", "api_key", "access_token", "private_key", "cookie",
    "authorization_header", "authorization_headers", "raw_environment",
    "environment_variables", "shell", "command", "argv", "script",
}


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise PilotAuthorizationError("evidence keys must be strings")
            normalized = key.lower()
            if normalized in _FORBIDDEN_KEYS or any(
                marker in normalized
                for marker in (
                    "password", "api_key", "access_token", "private_key",
                    "cookie", "authorization_header",
                )
            ):
                raise PilotAuthorizationError("unsafe pilot authorization field rejected")
            validate_safe(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            validate_safe(child)
    elif not isinstance(value, (str, int, bool, type(None))):
        raise PilotAuthorizationError("unsupported pilot authorization value")


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
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    return prefix + sha256_digest(value)[7:39]


@dataclass(frozen=True)
class PilotAuthorizationRequest:
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
    nonce_reference: str
    issued_at: str
    expires_at: str
    max_uses: int = 1
    production_authorized: bool = False
    pilot_activation_requested: bool = False
    persistent_sqlite_audit_operational: bool = False
    safety_counters: Mapping[str, int] = MappingProxyType({})

    def __post_init__(self) -> None:
        validate_safe(self.to_dict())
        object.__setattr__(self, "operation_scope", tuple(sorted(set(self.operation_scope))))
        object.__setattr__(
            self, "safety_counters",
            MappingProxyType({key: self.safety_counters[key] for key in sorted(self.safety_counters)}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_authorization_id": self.execution_authorization_id,
            "readiness_report_id": self.readiness_report_id,
            "readiness_report_digest": self.readiness_report_digest,
            "package_digest": self.package_digest,
            "plan_digest": self.plan_digest,
            "target_identity": self.target_identity,
            "target_owner": self.target_owner,
            "environment": self.environment,
            "operation_scope": list(self.operation_scope),
            "sandbox_root_identity_digest": self.sandbox_root_identity_digest,
            "requester_identity": self.requester_identity,
            "operator_identity": self.operator_identity,
            "nonce_reference": self.nonce_reference,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "max_uses": self.max_uses,
            "production_authorized": self.production_authorized,
            "pilot_activation_requested": self.pilot_activation_requested,
            "persistent_sqlite_audit_operational": self.persistent_sqlite_audit_operational,
            "safety_counters": dict(self.safety_counters),
        }


@dataclass(frozen=True)
class PilotOperatorApproval:
    approver_identity: str
    approver_role: str
    operator_identity: str
    approved: bool
    issued_at: str
    expires_at: str

    def __post_init__(self) -> None:
        validate_safe(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "approver_identity": self.approver_identity,
            "approver_role": self.approver_role,
            "operator_identity": self.operator_identity,
            "approved": self.approved,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
        }


@dataclass(frozen=True)
class PilotPermit:
    permit_id: str
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
    approver_role: str
    nonce_reference: str
    issued_at: str
    expires_at: str
    max_uses: int
    production_authorized: bool
    pilot_activation_started: bool
    restrictions: tuple[PilotRestriction, ...]
    permit_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "permit_id": self.permit_id,
            "execution_authorization_id": self.execution_authorization_id,
            "readiness_report_id": self.readiness_report_id,
            "readiness_report_digest": self.readiness_report_digest,
            "package_digest": self.package_digest,
            "plan_digest": self.plan_digest,
            "target_identity": self.target_identity,
            "target_owner": self.target_owner,
            "environment": self.environment,
            "operation_scope": list(self.operation_scope),
            "sandbox_root_identity_digest": self.sandbox_root_identity_digest,
            "requester_identity": self.requester_identity,
            "operator_identity": self.operator_identity,
            "approver_identity": self.approver_identity,
            "approver_role": self.approver_role,
            "nonce_reference": self.nonce_reference,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "max_uses": self.max_uses,
            "production_authorized": self.production_authorized,
            "pilot_activation_started": self.pilot_activation_started,
            "restrictions": [item.value for item in self.restrictions],
            "permit_digest": self.permit_digest,
        }


@dataclass(frozen=True)
class PilotPermitValidationReport:
    status: PilotAuthorizationStatus
    reason_codes: tuple[str, ...]
    evaluated_at: str
    permit_id: str | None
    permit_digest: str | None
    production_authorized: bool = False
    pilot_activation_started: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "evaluated_at": self.evaluated_at,
            "permit_id": self.permit_id,
            "permit_digest": self.permit_digest,
            "production_authorized": self.production_authorized,
            "pilot_activation_started": self.pilot_activation_started,
        }


@dataclass(frozen=True)
class PilotAuthorizationDecision:
    status: PilotAuthorizationStatus
    reason_codes: tuple[str, ...]
    restrictions: tuple[PilotRestriction, ...]
    permit: PilotPermit | None
    validation_report: PilotPermitValidationReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "restrictions": [item.value for item in self.restrictions],
            "permit": self.permit.to_dict() if self.permit else None,
            "validation_report": self.validation_report.to_dict(),
        }
