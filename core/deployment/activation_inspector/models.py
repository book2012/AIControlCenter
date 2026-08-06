from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping
import re


CheckResult = Literal["PASS", "FAIL", "ERROR"]

_CHECK_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_]{2,99}$")
_ERROR_CODE_PATTERN = re.compile(r"^[A-Z0-9_]+$")


def freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {
                str(key): freeze_json(child)
                for key, child in value.items()
            }
        )

    if isinstance(value, (list, tuple)):
        return tuple(
            freeze_json(child)
            for child in value
        )

    if value is None or isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    raise TypeError(
        "Unsupported JSON value type: "
        + type(value).__name__
    )


def thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): thaw_json(child)
            for key, child in value.items()
        }

    if isinstance(value, tuple):
        return [
            thaw_json(child)
            for child in value
        ]

    return value


@dataclass(frozen=True, slots=True)
class CheckObservation:
    check_id: str
    expected: Any
    actual: Any
    result: CheckResult
    blocking: bool
    evidence_reference: str
    timestamp: str

    def __post_init__(self) -> None:
        if not _CHECK_ID_PATTERN.fullmatch(
            self.check_id
        ):
            raise ValueError(
                "Invalid check_id: "
                + self.check_id
            )

        if self.result not in {
            "PASS",
            "FAIL",
            "ERROR",
        }:
            raise ValueError(
                "Invalid check result: "
                + str(self.result)
            )

        if not self.evidence_reference:
            raise ValueError(
                "evidence_reference is required"
            )

        if not self.timestamp:
            raise ValueError(
                "timestamp is required"
            )

        object.__setattr__(
            self,
            "expected",
            freeze_json(self.expected),
        )

        object.__setattr__(
            self,
            "actual",
            freeze_json(self.actual),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "expected": thaw_json(self.expected),
            "actual": thaw_json(self.actual),
            "result": self.result,
            "blocking": self.blocking,
            "evidence_reference": (
                self.evidence_reference
            ),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True, slots=True)
class SanitizedError:
    code: str
    component: str
    message: str

    def __post_init__(self) -> None:
        if not _ERROR_CODE_PATTERN.fullmatch(
            self.code
        ):
            raise ValueError(
                "Invalid error code: "
                + self.code
            )

        if not self.component:
            raise ValueError(
                "Error component is required"
            )

        if not self.message:
            raise ValueError(
                "Error message is required"
            )

        if len(self.message) > 300:
            raise ValueError(
                "Error message exceeds 300 characters"
            )

    def to_payload(self) -> dict[str, str]:
        return {
            "code": self.code,
            "component": self.component,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class InspectionEvaluationRequest:
    policy: Mapping[str, Any]
    route_manifest: Mapping[str, Any]
    inspection_id: str
    started_at: str
    completed_at: str
    git: Mapping[str, Any]
    runtime: Mapping[str, Any]
    launchd: Mapping[str, Any]
    process: Mapping[str, Any]
    listener: Mapping[str, Any]
    http: Mapping[str, Any]
    checks: tuple[CheckObservation, ...]
    warnings: tuple[str, ...] = field(
        default_factory=tuple
    )
    errors: tuple[SanitizedError, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.inspection_id:
            raise ValueError(
                "inspection_id is required"
            )

        if not self.started_at:
            raise ValueError(
                "started_at is required"
            )

        if not self.completed_at:
            raise ValueError(
                "completed_at is required"
            )

        for field_name in (
            "policy",
            "route_manifest",
            "git",
            "runtime",
            "launchd",
            "process",
            "listener",
            "http",
        ):
            object.__setattr__(
                self,
                field_name,
                freeze_json(
                    getattr(self, field_name)
                ),
            )

        object.__setattr__(
            self,
            "checks",
            tuple(self.checks),
        )

        object.__setattr__(
            self,
            "warnings",
            tuple(self.warnings),
        )

        object.__setattr__(
            self,
            "errors",
            tuple(self.errors),
        )


@dataclass(frozen=True, slots=True)
class InspectionEvaluation:
    report: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "report",
            freeze_json(self.report),
        )

    def to_payload(self) -> dict[str, Any]:
        return thaw_json(self.report)


__all__ = (
    "CheckObservation",
    "CheckResult",
    "InspectionEvaluation",
    "InspectionEvaluationRequest",
    "SanitizedError",
    "freeze_json",
    "thaw_json",
)
