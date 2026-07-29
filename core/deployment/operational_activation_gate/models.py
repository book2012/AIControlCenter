"""Immutable contracts for the M3-A4A operational activation readiness gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping


class OperationalActivationError(ValueError):
    """Fail-closed validation error with no unsafe value reflection."""


class OperationalActivationStage(StrEnum):
    PRE_ACTIVATION_READINESS = "PRE_ACTIVATION_READINESS"


class ActivationReadinessStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


class ActivationReadinessDecision(StrEnum):
    READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP = (
        "READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP"
    )
    READY_WITH_RESTRICTIONS = "READY_WITH_RESTRICTIONS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


_FORBIDDEN_MARKERS = (
    "password", "api_key", "apikey", "access_token", "private_key", "cookie",
    "authorization_header", "raw_environment", "environment_variable",
    "raw_nonce", "shell", "command", "argv", "script",
)


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise OperationalActivationError("mapping keys must be strings")
            normalized = key.lower()
            if (normalized != "runtime_infrastructure_commands"
                    and any(marker in normalized for marker in _FORBIDDEN_MARKERS)):
                raise OperationalActivationError("unsafe evidence field rejected")
            validate_safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            validate_safe(child)
    elif not isinstance(value, (str, int, bool, type(None))):
        raise OperationalActivationError("unsupported evidence value")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {key: _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


def parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise OperationalActivationError("explicit timestamp is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OperationalActivationError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise OperationalActivationError("timestamp must include timezone")
    return parsed


@dataclass(frozen=True, slots=True)
class OperationalActivationGateConfig:
    stage: OperationalActivationStage
    repository_root: str
    user_home: str
    approved_branch: str = "feature/deployment-package"
    maximum_evidence_age_seconds: int = 86_400
    block_on_warnings: bool = False
    production_authorized: bool = False
    bootstrap_authorized: bool = False

    def __post_init__(self) -> None:
        if self.stage is not OperationalActivationStage.PRE_ACTIVATION_READINESS:
            raise OperationalActivationError("privileged or unknown stage rejected")
        if not self.repository_root.startswith("/") or not self.user_home.startswith("/"):
            raise OperationalActivationError("repository root and user home must be absolute")
        if self.maximum_evidence_age_seconds <= 0:
            raise OperationalActivationError("evidence age limit must be positive")
        if self.production_authorized or self.bootstrap_authorized:
            raise OperationalActivationError("authorization must remain false")


@dataclass(frozen=True, slots=True)
class OperationalActivationEvidence:
    evidence_id: str
    generated_at: str
    m2_readiness_closed: bool
    m2_pilot_closed: bool
    m3_a1a_closed: bool
    m3_a1b_closed: bool
    m3_a1c_closed: bool
    m3_a2a_closed: bool
    m3_a2b_closed: bool
    m3_a2c_closed: bool
    m3_a3a_closed: bool
    m3_a3b_closed: bool
    m3_a3c_closed: bool
    full_regression_passed: int
    full_regression_failed: int
    full_regression_deselected: int
    full_regression_warnings: int
    deployment_tests_passed: int
    deployment_tests_failed: int
    git_branch: str
    git_commit: str
    git_clean: bool
    upstream_ahead: int
    upstream_behind: int
    documentation_closed: bool
    architecture_closed: bool
    audit_recovery_drill_passed: bool
    replay_recovery_drill_passed: bool
    post_recovery_concurrency_passed: bool
    monitoring_alert_drill_passed: bool
    safety_counters: Mapping[str, int]
    operational_paths_exist: Mapping[str, bool]
    operational_writers_active: bool
    operational_monitoring_active: bool
    external_alert_dispatch_active: bool
    authorized_bootstrap_receipt: bool
    control_plane_owner: str = "AIControlCenter Mac"
    ubuntu_ownership_present: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        validate_safe(asdict(self))
        parse_timestamp(self.generated_at)
        if not self.evidence_id or not self.git_commit:
            raise OperationalActivationError("evidence identity and Git commit are required")
        counters = dict(self.safety_counters)
        paths = dict(self.operational_paths_exist)
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
               for value in counters.values()):
            raise OperationalActivationError("safety counters must be non-negative integers")
        if any(not isinstance(value, bool) for value in paths.values()):
            raise OperationalActivationError("path existence evidence must be boolean")
        object.__setattr__(self, "safety_counters", dict(sorted(counters.items())))
        object.__setattr__(self, "operational_paths_exist", dict(sorted(paths.items())))

    def as_dict(self) -> dict[str, Any]:
        return {
            field: _jsonable(getattr(self, field))
            for field in self.__dataclass_fields__
        }


@dataclass(frozen=True, slots=True)
class OperationalPathPlan:
    audit_database: str
    audit_backup_root: str
    permit_replay_database: str
    permit_replay_backup_root: str
    monitoring_evidence_root: str
    symlink_paths: tuple[str, ...] = ()
    mac_control_plane_owned: bool = True
    ubuntu_owned: bool = False
    network_or_removable: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalPermissionPlan:
    application_state_parent_mode: int = 0o700
    audit_directory_mode: int = 0o700
    security_directory_mode: int = 0o700
    monitoring_directory_mode: int = 0o700
    sqlite_database_mode: int = 0o600
    backup_database_mode: int = 0o600
    manifest_file_mode: int = 0o600
    owner: str = "AIControlCenter Mac operator"
    ubuntu_owned: bool = False
    network_filesystem: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in tuple(data):
            if key.endswith("_mode"):
                data[key] = format(data[key], "04o")
        return data


@dataclass(frozen=True, slots=True)
class OperationalBootstrapStep:
    sequence: int
    code: str
    description: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPlan:
    steps: tuple[OperationalBootstrapStep, ...]
    production_authorized: bool = False
    external_dispatch_authorized: bool = False
    ubuntu_participation: bool = False
    api_write_route: bool = False
    service_restart: bool = False
    writer_activation: bool = False
    activation_performed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalRollbackPlan:
    partial_audit_cleanup_defined: bool
    partial_replay_cleanup_defined: bool
    overwrite_preexisting_prohibited: bool
    backup_before_activation_required: bool
    restore_validation_required: bool
    writer_activation_can_be_withheld: bool
    monitoring_activation_can_be_withheld: bool
    external_dispatch_unavailable: bool
    failed_bootstrap_cannot_activate: bool
    operator_escalation_documented: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ActivationReadinessCheck:
    code: str
    status: ActivationReadinessStatus
    evidence_references: tuple[str, ...]
    reason_codes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))


@dataclass(frozen=True, slots=True, order=True)
class ActivationReadinessFinding:
    code: str
    severity: str
    summary: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True, order=True)
class ActivationRestriction:
    code: str
    summary: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ActivationReadinessReport:
    report_id: str
    operational_stage: OperationalActivationStage
    readiness_decision: ActivationReadinessDecision
    evaluated_at: str
    evidence_ids: tuple[str, ...]
    evidence_digests: tuple[str, ...]
    checks: tuple[ActivationReadinessCheck, ...]
    findings: tuple[ActivationReadinessFinding, ...]
    restrictions: tuple[ActivationRestriction, ...]
    path_plan: OperationalPathPlan
    permission_plan: OperationalPermissionPlan
    bootstrap_plan: OperationalBootstrapPlan
    rollback_plan_valid: bool
    failed_checks: tuple[str, ...]
    warning_checks: tuple[str, ...]
    passed_checks: tuple[str, ...]
    report_digest: str
    writes_performed: int = 0
    directories_created: int = 0
    databases_created: int = 0
    writers_activated: int = 0
    monitoring_activated: int = 0
    alerts_dispatched: int = 0
    bootstrap_authorized: bool = False
    writers_authorized: bool = False
    monitoring_activation_authorized: bool = False
    external_dispatch_authorized: bool = False
    production_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @property
    def canonical_json(self) -> str:
        return canonical_json(self)
