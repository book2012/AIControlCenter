"""Immutable contracts for the controlled operational coordinator entrypoint."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class ControlledOperationalBootstrapError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ControlledOperationalBootstrapStage(StrEnum):
    CONTROLLED_OPERATIONAL_COORDINATION = "CONTROLLED_OPERATIONAL_COORDINATION"


class ControlledOperationalBootstrapScope(StrEnum):
    CONTROLLED_NON_PRODUCTION = "CONTROLLED_NON_PRODUCTION"


class ControlledOperationalBootstrapStatus(StrEnum):
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTITY = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{2,127}$")
_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|url|destination|"
    r"ubuntu|worker|production.?root", re.I)


def parse_timestamp(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ControlledOperationalBootstrapError("EXPLICIT_TIMESTAMP_REQUIRED") from exc
    if result.tzinfo is None:
        raise ControlledOperationalBootstrapError("TIMEZONE_REQUIRED")
    return result


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _FORBIDDEN.search(str(key)):
                raise ControlledOperationalBootstrapError("UNSAFE_FIELD_REJECTED")
            validate_safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            validate_safe(child)
    elif isinstance(value, str) and (
            _FORBIDDEN.search(value) or "://" in value):
        raise ControlledOperationalBootstrapError("UNSAFE_VALUE_REJECTED")


@dataclass(frozen=True, slots=True)
class ControlledOperationalBootstrapConfig:
    repository_root: Path
    approved_branch: str
    approved_commit: str
    stage: ControlledOperationalBootstrapStage = (
        ControlledOperationalBootstrapStage.CONTROLLED_OPERATIONAL_COORDINATION)
    scope: ControlledOperationalBootstrapScope = (
        ControlledOperationalBootstrapScope.CONTROLLED_NON_PRODUCTION)
    production_authorized: bool = False

    def __post_init__(self) -> None:
        root = Path(self.repository_root).resolve()
        if (self.approved_branch != "feature/deployment-package"
                or not _COMMIT.fullmatch(self.approved_commit)
                or self.production_authorized):
            raise ControlledOperationalBootstrapError("CONFIGURATION_REJECTED")
        object.__setattr__(self, "repository_root", root)


@dataclass(frozen=True, slots=True)
class ControlledOperationalBootstrapArtifactPaths:
    approval_input: Path
    shared_parent_preflight_evidence: Path
    activation_authorization_request_output: Path
    activation_authorization_output: Path
    activation_authorization_evidence_output: Path
    operational_permit_output: Path
    permit_issuance_evidence_output: Path
    permit_claim_output: Path
    bootstrap_receipt_output: Path
    bootstrap_evidence_output: Path
    post_bootstrap_validation_output: Path

    def __post_init__(self) -> None:
        values: list[Path] = []
        for name in self.__dataclass_fields__:
            path = Path(getattr(self, name))
            if not path.is_absolute() or ".." in path.parts:
                raise ControlledOperationalBootstrapError("ABSOLUTE_ARTIFACT_PATH_REQUIRED")
            values.append(path)
            object.__setattr__(self, name, path)
        if len(set(values)) != len(values):
            raise ControlledOperationalBootstrapError("ARTIFACT_PATH_COLLISION")


@dataclass(frozen=True, slots=True)
class ControlledOperationalBootstrapTimePolicy:
    requested_at: str
    approval_maximum_age_seconds: int
    activation_not_before: str
    activation_expires_at: str
    permit_not_before: str
    permit_expires_at: str
    bootstrap_execution_deadline: str
    maximum_uses: int = 1

    def __post_init__(self) -> None:
        times = tuple(parse_timestamp(getattr(self, name)) for name in (
            "requested_at", "activation_not_before", "activation_expires_at",
            "permit_not_before", "permit_expires_at", "bootstrap_execution_deadline"))
        requested, activation_start, activation_end, permit_start, permit_end, deadline = times
        if (not isinstance(self.approval_maximum_age_seconds, int)
                or isinstance(self.approval_maximum_age_seconds, bool)
                or not 0 < self.approval_maximum_age_seconds <= 86400
                or self.maximum_uses != 1
                or not requested <= activation_start < permit_start <= deadline
                or not deadline <= permit_end <= activation_end):
            raise ControlledOperationalBootstrapError("TIME_POLICY_INVALID")


@dataclass(frozen=True, slots=True)
class ControlledOperationalBootstrapRequest:
    request_id: str
    branch: str
    commit: str
    trusted_operational_root: Path
    requester_identity: str
    operator_identity: str
    independent_approver_identity: str
    artifacts: ControlledOperationalBootstrapArtifactPaths
    time_policy: ControlledOperationalBootstrapTimePolicy
    restriction_acknowledgement_digests: tuple[str, ...]
    active_restriction_digests: tuple[str, ...]
    scope: ControlledOperationalBootstrapScope
    maximum_uses: int = 1
    production_authorized: bool = False
    writers_authorized: bool = False
    monitoring_authorized: bool = False
    external_dispatch_authorized: bool = False

    def __post_init__(self) -> None:
        root = Path(self.trusted_operational_root)
        identities = (self.requester_identity, self.operator_identity,
                      self.independent_approver_identity)
        if (not self.request_id or self.branch != "feature/deployment-package"
                or not _COMMIT.fullmatch(self.commit) or not root.is_absolute()
                or ".." in root.parts or any(not _IDENTITY.fullmatch(item) for item in identities)
                or self.operator_identity == self.independent_approver_identity
                or self.maximum_uses != 1 or self.time_policy.maximum_uses != 1
                or self.production_authorized or self.writers_authorized
                or self.monitoring_authorized or self.external_dispatch_authorized):
            raise ControlledOperationalBootstrapError("REQUEST_BINDING_INVALID")
        for digest in (*self.restriction_acknowledgement_digests,
                       *self.active_restriction_digests):
            if not _DIGEST.fullmatch(digest):
                raise ControlledOperationalBootstrapError("CANONICAL_DIGEST_REQUIRED")
        if (not self.active_restriction_digests
                or len(self.restriction_acknowledgement_digests)
                < 2 * len(self.active_restriction_digests)):
            raise ControlledOperationalBootstrapError(
                "DUAL_RESTRICTION_ACKNOWLEDGEMENT_REQUIRED")
        object.__setattr__(self, "trusted_operational_root", root)
        object.__setattr__(self, "restriction_acknowledgement_digests",
                           tuple(sorted(self.restriction_acknowledgement_digests)))
        object.__setattr__(self, "active_restriction_digests",
                           tuple(sorted(self.active_restriction_digests)))
        validate_safe(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class ControlledOperationalBootstrapCheck:
    code: str
    passed: bool


@dataclass(frozen=True, slots=True, order=True)
class ControlledOperationalBootstrapFinding:
    code: str
    severity: str = "ERROR"


@dataclass(frozen=True, slots=True)
class ControlledOperationalBootstrapResult:
    result_id: str
    status: ControlledOperationalBootstrapStatus
    request_digest: str | None
    checks: tuple[ControlledOperationalBootstrapCheck, ...]
    findings: tuple[ControlledOperationalBootstrapFinding, ...]
    activation_authorization_id: str | None = None
    permit_id: str | None = None
    claim_id: str | None = None
    bootstrap_receipt_id: str | None = None
    production_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


ControlledOperationalBootstrapApprovalBinding = Mapping[str, Any]
ControlledOperationalBootstrapPreflightBinding = Mapping[str, Any]
ControlledOperationalBootstrapGitBinding = Mapping[str, Any]
ControlledOperationalBootstrapArtifactManifest = Mapping[str, Any]
ControlledOperationalBootstrapValidationReport = ControlledOperationalBootstrapResult
