"""Immutable contracts for the reviewed operational activation boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping


class OperationalActivationAuthorizationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class OperationalActivationAuthorizationStage(StrEnum):
    CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION = (
        "CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION"
    )


class OperationalActivationAuthorizationScope(StrEnum):
    CONTROLLED_NON_PRODUCTION = "CONTROLLED_NON_PRODUCTION"


class OperationalActivationAuthorizationStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|https?://", re.I)


def parse_timestamp(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise OperationalActivationAuthorizationError("EXPLICIT_TIMESTAMP_REQUIRED") from exc
    if result.tzinfo is None:
        raise OperationalActivationAuthorizationError("TIMEZONE_REQUIRED")
    return result


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, (StrEnum, Path)):
        return str(value)
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


def _digest(value: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise OperationalActivationAuthorizationError("CANONICAL_DIGEST_REQUIRED")


def _safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) != "runtime_infrastructure_commands" and _FORBIDDEN.search(str(key)):
                raise OperationalActivationAuthorizationError("UNSAFE_INPUT_REJECTED")
            _safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _safe(child)
    elif isinstance(value, str) and _FORBIDDEN.search(value):
        raise OperationalActivationAuthorizationError("UNSAFE_INPUT_REJECTED")


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationConfig:
    approved_branch: str
    approved_commit: str
    trusted_operational_path: Path
    stage: OperationalActivationAuthorizationStage = (
        OperationalActivationAuthorizationStage.CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION)
    scope: OperationalActivationAuthorizationScope = (
        OperationalActivationAuthorizationScope.CONTROLLED_NON_PRODUCTION)
    production_authorized: bool = False

    def __post_init__(self) -> None:
        path = Path(self.trusted_operational_path)
        if (self.stage is not OperationalActivationAuthorizationStage.CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION
                or self.scope is not OperationalActivationAuthorizationScope.CONTROLLED_NON_PRODUCTION
                or self.approved_branch != "feature/deployment-package"
                or not _COMMIT.fullmatch(self.approved_commit)
                or not path.is_absolute() or ".." in path.parts
                or self.production_authorized):
            raise OperationalActivationAuthorizationError("CONFIGURATION_REJECTED")
        object.__setattr__(self, "trusted_operational_path", path)


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationIdentityBinding:
    requester_identity: str
    operator_identity: str
    independent_approver_identity: str
    synthetic: bool = False

    def __post_init__(self) -> None:
        values = (self.requester_identity, self.operator_identity,
                  self.independent_approver_identity)
        if any(not value or value in {"root", "unknown", "operator", "approver", "requester"}
               for value in values):
            raise OperationalActivationAuthorizationError("IDENTITY_INVALID")
        if self.operator_identity == self.independent_approver_identity:
            raise OperationalActivationAuthorizationError("INDEPENDENT_APPROVER_REQUIRED")
        _safe(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationRestrictionBinding:
    acknowledgement_digests: tuple[str, ...]
    active_restriction_digests: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.active_restriction_digests:
            raise OperationalActivationAuthorizationError("RESTRICTIONS_REQUIRED")
        for value in (*self.acknowledgement_digests, *self.active_restriction_digests):
            _digest(value)
        if tuple(sorted(self.acknowledgement_digests)) != self.acknowledgement_digests:
            raise OperationalActivationAuthorizationError("ACKNOWLEDGEMENTS_NOT_CANONICAL")
        if len(self.acknowledgement_digests) < 2 * len(self.active_restriction_digests):
            raise OperationalActivationAuthorizationError("RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE")


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationCommitBinding:
    branch: str
    commit: str
    git_clean: bool
    upstream_ahead: int
    upstream_behind: int

    def __post_init__(self) -> None:
        if (self.branch != "feature/deployment-package" or not _COMMIT.fullmatch(self.commit)
                or not self.git_clean or self.upstream_ahead or self.upstream_behind):
            raise OperationalActivationAuthorizationError("GIT_BINDING_INVALID")


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationWindow:
    approval_timestamp: str
    not_before: str
    expires_at: str
    maximum_permit_uses: int = 1

    def __post_init__(self) -> None:
        approved, start, end = map(parse_timestamp, (
            self.approval_timestamp, self.not_before, self.expires_at))
        if not approved <= start < end:
            raise OperationalActivationAuthorizationError("WINDOW_INVALID")
        if self.maximum_permit_uses != 1:
            raise OperationalActivationAuthorizationError("MAXIMUM_USES_MUST_EQUAL_ONE")


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationSafetyBinding:
    counters: Mapping[str, int]
    writers_authorized: bool = False
    monitoring_authorized: bool = False
    external_dispatch_authorized: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if (not self.counters or any(not isinstance(value, int) or isinstance(value, bool)
                                    or value != 0 for value in self.counters.values())
                or self.writers_authorized or self.monitoring_authorized
                or self.external_dispatch_authorized or self.production_authorized):
            raise OperationalActivationAuthorizationError("SAFETY_BINDING_INVALID")
        object.__setattr__(self, "counters", dict(sorted(self.counters.items())))


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationRequest:
    human_approval_report_id: str
    human_approval_report_digest: str
    permit_issuance_review_id: str
    permit_issuance_review_digest: str
    identity: OperationalActivationAuthorizationIdentityBinding
    restrictions: OperationalActivationAuthorizationRestrictionBinding
    git: OperationalActivationAuthorizationCommitBinding
    window: OperationalActivationAuthorizationWindow
    safety: OperationalActivationAuthorizationSafetyBinding
    approved_shared_parent_policy_digest: str
    operational_target_path: Path
    target_absence_evidence_digest: str
    runtime_plan_digest: str
    schema_digests: Mapping[str, str]
    test_evidence_digest: str
    environment: str = "CONTROLLED_NON_PRODUCTION"
    target_absent: bool = True

    def __post_init__(self) -> None:
        path = Path(self.operational_target_path)
        for value in (
            self.human_approval_report_digest, self.permit_issuance_review_digest,
            self.approved_shared_parent_policy_digest, self.target_absence_evidence_digest,
            self.runtime_plan_digest, self.test_evidence_digest, *self.schema_digests.values()):
            _digest(value)
        if (not self.human_approval_report_id or not self.permit_issuance_review_id
                or self.environment != "CONTROLLED_NON_PRODUCTION" or not self.target_absent
                or not path.is_absolute() or ".." in path.parts):
            raise OperationalActivationAuthorizationError("REQUEST_BINDING_INVALID")
        object.__setattr__(self, "operational_target_path", path)
        object.__setattr__(self, "schema_digests", dict(sorted(self.schema_digests.items())))
        _safe(self.as_dict())

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationDecision:
    decision_id: str
    status: OperationalActivationAuthorizationStatus
    reason_codes: tuple[str, ...]
    request_digest: str
    decided_at: str


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationPermit:
    authorization_id: str
    authorization_digest: str
    request: OperationalActivationAuthorizationRequest
    issued_at: str
    stage: OperationalActivationAuthorizationStage = (
        OperationalActivationAuthorizationStage.CONTROLLED_NON_PRODUCTION_OPERATIONAL_ACTIVATION)

    def content(self) -> dict[str, Any]:
        return {"authorization_id": self.authorization_id, "request": self.request.as_dict(),
                "issued_at": self.issued_at, "stage": self.stage}

    def as_dict(self) -> dict[str, Any]:
        return {**self.content(), "authorization_digest": self.authorization_digest}


@dataclass(frozen=True, slots=True)
class OperationalActivationAuthorizationValidationReport:
    status: OperationalActivationAuthorizationStatus
    reason_codes: tuple[str, ...]
    report_id: str
    report_digest: str
