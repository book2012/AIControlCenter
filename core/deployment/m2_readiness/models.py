"""Immutable contracts for the DPL-04D M2 operational readiness gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


class M2ReadinessDecision(str, Enum):
    READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX = (
        "READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX"
    )
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"


class M2ReadinessEvidenceError(ValueError):
    """Raised without reflecting unsafe evidence values."""


_FORBIDDEN_KEYS = {
    "password", "access_token", "api_key", "private_key", "cookie",
    "authorization_header", "authorization", "shell", "command", "argv",
    "script", "raw_environment", "environment_variables",
}


def _validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise M2ReadinessEvidenceError("evidence keys must be strings")
            normalized = key.lower()
            if normalized in _FORBIDDEN_KEYS or any(
                marker in normalized
                for marker in ("password", "access_token", "api_key", "private_key")
            ):
                raise M2ReadinessEvidenceError("unsafe evidence field rejected")
            _validate_safe(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _validate_safe(child)
    elif not isinstance(value, (str, int, bool, type(None))):
        raise M2ReadinessEvidenceError("unsupported evidence value")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(value[key]) for key in sorted(value)})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return json.dumps(_thaw(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class M2ReadinessEvidence:
    schema_version: str
    observed_at: str
    checks: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "M2ReadinessEvidence":
        _validate_safe(value)
        if set(value) != {"schema_version", "observed_at", "checks"}:
            raise M2ReadinessEvidenceError("evidence envelope is malformed")
        if value["schema_version"] != "dpl/m2-readiness/v1":
            raise M2ReadinessEvidenceError("unsupported evidence schema")
        if not isinstance(value["observed_at"], str) or not value["observed_at"]:
            raise M2ReadinessEvidenceError("observed_at is required")
        if not isinstance(value["checks"], Mapping):
            raise M2ReadinessEvidenceError("checks must be an object")
        return cls(
            schema_version=value["schema_version"],
            observed_at=value["observed_at"],
            checks=_freeze(value["checks"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "observed_at": self.observed_at,
            "checks": _thaw(self.checks),
        }


@dataclass(frozen=True)
class M2ReadinessCheck:
    category: str
    passed: bool
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "passed": self.passed,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class M2ReadinessFinding:
    category: str
    severity: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "category": self.category,
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
        }


@dataclass(frozen=True)
class M2ReadinessReport:
    schema_version: str
    report_id: str
    report_digest: str
    evaluated_at: str
    evidence_digest: str
    decision: M2ReadinessDecision
    checks: tuple[M2ReadinessCheck, ...]
    findings: tuple[M2ReadinessFinding, ...]
    restrictions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "report_id": self.report_id,
            "report_digest": self.report_digest,
            "evaluated_at": self.evaluated_at,
            "evidence_digest": self.evidence_digest,
            "decision": self.decision.value,
            "checks": [item.to_dict() for item in self.checks],
            "findings": [item.to_dict() for item in self.findings],
            "restrictions": list(self.restrictions),
        }
