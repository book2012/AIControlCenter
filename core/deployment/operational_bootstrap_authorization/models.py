"""Pure immutable contracts for M3-A4B1 bootstrap authorization."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping

from core.deployment.operational_activation_gate import (
    ActivationReadinessDecision,
    ActivationReadinessReport,
)


class OperationalBootstrapAuthorizationError(ValueError):
    """Fail-closed contract error which never reflects unsafe input."""


class OperationalBootstrapAuthorizationStage(StrEnum):
    CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION = (
        "CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION"
    )


class OperationalBootstrapAuthorizationStatus(StrEnum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


class OperationalBootstrapAuthorizationDecisionValue(StrEnum):
    AUTHORIZED_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP = (
        "AUTHORIZED_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP"
    )
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_PLACEHOLDER = re.compile(r"^(anonymous|unknown|none|null|n/?a|operator|approver|requester)$", re.I)
_FORBIDDEN = (
    "password", "api_key", "apikey", "access_token", "token", "private_key",
    "cookie", "authorization_header", "environment_variable", "raw_environment",
    "raw_nonce", "shell", "command", "argv", "script", "webhook", "email",
    "phone", "destination",
)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return value.as_dict()
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


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise OperationalBootstrapAuthorizationError("explicit timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OperationalBootstrapAuthorizationError("invalid explicit timestamp") from exc
    if parsed.tzinfo is None:
        raise OperationalBootstrapAuthorizationError("timestamp timezone required")
    return parsed


def require_digest(value: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise OperationalBootstrapAuthorizationError("canonical sha256 digest required")


def require_identity(value: str) -> None:
    if (not isinstance(value, str) or not value.strip() or _PLACEHOLDER.fullmatch(value.strip())
            or "@" in value or "://" in value or re.search(r"\+?\d[\d ()-]{7,}", value)):
        raise OperationalBootstrapAuthorizationError("named internal identity required")


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            if (normalized != "runtime_infrastructure_commands"
                    and any(marker in normalized for marker in _FORBIDDEN)):
                raise OperationalBootstrapAuthorizationError("unsafe field rejected")
            validate_safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            validate_safe(child)
    elif not isinstance(value, (str, int, bool, type(None), StrEnum)):
        raise OperationalBootstrapAuthorizationError("unsupported contract value")


@dataclass(frozen=True, slots=True)
class OperationalBootstrapAuthorizationConfig:
    stage: OperationalBootstrapAuthorizationStage
    approved_branch: str = "feature/deployment-package"
    environment: str = "controlled non-production"
    maximum_uses: int = 1
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if self.stage is not OperationalBootstrapAuthorizationStage.CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION:
            raise OperationalBootstrapAuthorizationError("privileged or unknown stage rejected")
        if (self.approved_branch != "feature/deployment-package"
                or self.environment != "controlled non-production"
                or self.maximum_uses != 1 or self.production_authorized):
            raise OperationalBootstrapAuthorizationError("authorization configuration rejected")


@dataclass(frozen=True, slots=True, order=True)
class OperationalBootstrapRestrictionAcknowledgement:
    restriction_code: str
    restriction_digest: str
    restriction_text: str
    operator_identity: str
    approver_identity: str
    acknowledged_at: str

    def __post_init__(self) -> None:
        require_digest(self.restriction_digest)
        require_identity(self.operator_identity)
        require_identity(self.approver_identity)
        parse_timestamp(self.acknowledged_at)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapApproval:
    approved: bool
    operator_identity: str
    approver_identity: str
    approved_at: str
    branch: str
    commit: str
    environment: str = "controlled non-production"
    production_authorized: bool = False

    def __post_init__(self) -> None:
        require_identity(self.operator_identity)
        require_identity(self.approver_identity)
        parse_timestamp(self.approved_at)
        if self.operator_identity == self.approver_identity:
            raise OperationalBootstrapAuthorizationError("independent approver required")
        if not _COMMIT.fullmatch(self.commit):
            raise OperationalBootstrapAuthorizationError("exact commit required")


@dataclass(frozen=True, slots=True)
class OperationalBootstrapTargetBinding:
    audit_database_identity_digest: str
    audit_backup_root_identity_digest: str
    replay_database_identity_digest: str
    replay_backup_root_identity_digest: str
    monitoring_root_identity_digest: str
    target_nonexistence: Mapping[str, bool]

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if name.endswith("_digest"):
                require_digest(getattr(self, name))
        expected = {"audit_database", "audit_backup_root", "replay_database",
                    "replay_backup_root", "monitoring_root"}
        evidence = dict(self.target_nonexistence)
        if set(evidence) != expected or not all(value is True for value in evidence.values()):
            raise OperationalBootstrapAuthorizationError("all validated targets must be absent")
        object.__setattr__(self, "target_nonexistence", dict(sorted(evidence.items())))

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @property
    def binding_digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapSchemaBinding:
    audit_schema_expectation_digest: str
    audit_append_only_controls_digest: str
    replay_schema_expectation_digest: str
    replay_immutable_controls_digest: str
    audit_schema_version_digest: str
    replay_schema_version_digest: str

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            require_digest(getattr(self, name))

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def binding_digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPlanBinding:
    operational_path_plan_digest: str
    permission_plan_digest: str
    bootstrap_plan_digest: str
    rollback_plan_digest: str
    ordered_instruction_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if name.endswith("_digest"):
                require_digest(getattr(self, name))
        forbidden = ("ACTIVATE", "DISPATCH", "API_WRITE", "UBUNTU", "PRODUCTION",
                     "OVERWRITE", "RESTART", "SHELL", "COMMAND", "EXECUTE")
        if not self.ordered_instruction_codes or any(
                any(marker in code.upper() for marker in forbidden)
                for code in self.ordered_instruction_codes):
            raise OperationalBootstrapAuthorizationError("unsafe bootstrap plan rejected")

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @property
    def binding_digest(self) -> str:
        return canonical_digest(self)


_COUNTERS = (
    "operational_directories_created", "operational_databases_created",
    "operational_backup_files_created", "operational_audit_writes",
    "operational_replay_writes", "writers_activated", "monitoring_activated",
    "alerts_dispatched", "notifications_sent", "n8n_invocations", "ubuntu_changes",
    "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
    "bootstrap_executions", "production_activations",
)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapSafetySnapshot:
    counters: Mapping[str, int]
    git_clean: bool
    upstream_ahead: int
    upstream_behind: int
    full_regression_passed: int
    full_regression_failed: int
    full_regression_deselected: int
    full_regression_warnings: int
    operational_writers_inactive: bool
    monitoring_inactive: bool
    external_dispatch_inactive: bool
    captured_at: str

    def __post_init__(self) -> None:
        parse_timestamp(self.captured_at)
        counters = dict(self.counters)
        if set(counters) != set(_COUNTERS) or any(
                not isinstance(value, int) or isinstance(value, bool) or value != 0
                for value in counters.values()):
            raise OperationalBootstrapAuthorizationError("every safety counter must be zero")
        if (not self.git_clean or self.upstream_ahead or self.upstream_behind
                or self.full_regression_passed <= 0 or self.full_regression_failed
                or not self.operational_writers_inactive or not self.monitoring_inactive
                or not self.external_dispatch_inactive):
            raise OperationalBootstrapAuthorizationError("unsafe snapshot rejected")
        object.__setattr__(self, "counters", dict(sorted(counters.items())))

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @property
    def snapshot_digest(self) -> str:
        return canonical_digest(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapAuthorizationRequest:
    authorization_request_id: str
    branch: str
    commit: str
    readiness_report: ActivationReadinessReport
    readiness_report_digest: str
    target_binding: OperationalBootstrapTargetBinding
    schema_binding: OperationalBootstrapSchemaBinding
    plan_binding: OperationalBootstrapPlanBinding
    safety_snapshot: OperationalBootstrapSafetySnapshot
    requester_identity: str
    operator_identity: str
    approver_identity: str
    requested_at: str
    expires_at: str
    restriction_acknowledgements: tuple[OperationalBootstrapRestrictionAcknowledgement, ...] = ()
    maximum_uses: int = 1
    environment: str = "controlled non-production"
    production_authorized: bool = False

    def __post_init__(self) -> None:
        validate_safe({key: value for key, value in asdict(self).items()
                       if key != "readiness_report"})
        require_identity(self.requester_identity)
        require_identity(self.operator_identity)
        require_identity(self.approver_identity)
        require_digest(self.readiness_report_digest)
        requested = parse_timestamp(self.requested_at)
        expires = parse_timestamp(self.expires_at)
        if (not self.authorization_request_id or self.branch != "feature/deployment-package"
                or not _COMMIT.fullmatch(self.commit) or expires <= requested
                or self.maximum_uses != 1 or self.environment != "controlled non-production"
                or self.production_authorized):
            raise OperationalBootstrapAuthorizationError("request scope rejected")
        object.__setattr__(self, "restriction_acknowledgements",
                           tuple(sorted(self.restriction_acknowledgements)))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapAuthorizationDecision:
    decision_id: str
    status: OperationalBootstrapAuthorizationStatus
    decision: OperationalBootstrapAuthorizationDecisionValue
    reason_codes: tuple[str, ...]
    authorization_request_id: str
    request_digest: str
    decided_at: str
    production_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPermit:
    permit_id: str
    authorization_request_id: str
    authorization_decision_id: str
    stage: OperationalBootstrapAuthorizationStage
    branch: str
    commit: str
    readiness_report_id: str
    readiness_report_digest: str
    restriction_acknowledgement_digest: str
    target_binding_digest: str
    schema_binding_digest: str
    plan_binding_digest: str
    safety_snapshot_digest: str
    requester_identity: str
    operator_identity: str
    approver_identity: str
    issued_at: str
    expires_at: str
    maximum_uses: int
    environment: str
    bootstrap_authorized: bool
    writers_authorized: bool
    monitoring_authorized: bool
    external_dispatch_authorized: bool
    production_authorized: bool
    permit_digest: str

    def content(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("permit_digest")
        return _jsonable(data)

    def as_dict(self) -> dict[str, Any]:
        return {**self.content(), "permit_digest": self.permit_digest}

    @property
    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPermitValidationReport:
    report_id: str
    valid: bool
    reason_codes: tuple[str, ...]
    permit_id: str
    validated_at: str
    report_digest: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPermitUseClaim:
    claim_id: str
    permit_id: str
    permit_digest: str
    claimant_identity: str
    claimed_at: str
    maximum_uses: int = 1
    production_authorized: bool = False
