"""Immutable, evidence-only contracts for M3-A4B2B0."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping


class OperationalBootstrapPreflightError(ValueError):
    """Fail-closed error which never reflects supplied evidence."""


class OperationalBootstrapPreflightStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


class OperationalBootstrapPreflightDecision(StrEnum):
    READY_FOR_OPERATIONAL_PERMIT_REVIEW = "READY_FOR_OPERATIONAL_PERMIT_REVIEW"
    READY_WITH_RESTRICTIONS = "READY_WITH_RESTRICTIONS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell.?command|argv|script|executable|https?://",
    re.I,
)
_SECRET_PATH = re.compile(r"(^|[/_.-])(secret|password|token|credential|private.?key)([/_.-]|$)", re.I)


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _FORBIDDEN.search(str(key)):
                raise OperationalBootstrapPreflightError("UNSAFE_EVIDENCE_REJECTED")
            validate_safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            validate_safe(child)
    elif isinstance(value, str):
        if _FORBIDDEN.search(value):
            raise OperationalBootstrapPreflightError("UNSAFE_EVIDENCE_REJECTED")
    elif not isinstance(value, (int, bool, type(None), StrEnum)):
        raise OperationalBootstrapPreflightError("UNSUPPORTED_EVIDENCE_REJECTED")


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise OperationalBootstrapPreflightError("EXPLICIT_TIMESTAMP_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise OperationalBootstrapPreflightError("TIMESTAMP_TIMEZONE_REQUIRED")
    return parsed


def _jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    if hasattr(value, "as_dict"):
        value = value.as_dict()
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class OperationalBootstrapHostPreflightConfig:
    approved_commit: str
    application_support_root: str
    repository_root: str
    expected_targets: Mapping[str, str]
    minimum_available_bytes: int
    minimum_available_percentage: int
    estimated_audit_database_allocation: int
    estimated_replay_database_allocation: int
    estimated_baseline_backup_allocation: int
    estimated_restore_validation_allocation: int
    safety_reserve: int
    supported_architectures: tuple[str, ...] = ("arm64",)
    approved_branch: str = "feature/deployment-package"
    acknowledged_warning_count: int = 427
    production_authorized: bool = False
    bootstrap_authorized: bool = False
    permit_issuance_requested: bool = False
    bootstrap_execution_requested: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{40}", self.approved_commit):
            raise OperationalBootstrapPreflightError("APPROVED_COMMIT_REQUIRED")
        paths = (self.application_support_root, self.repository_root, *self.expected_targets.values())
        if any(not item.startswith("/") or ".." in item.split("/") for item in paths):
            raise OperationalBootstrapPreflightError("ABSOLUTE_NORMALIZED_PATH_REQUIRED")
        if any(_SECRET_PATH.search(item) for item in paths):
            raise OperationalBootstrapPreflightError("SECRET_BEARING_PATH_REJECTED")
        capacities = (
            self.minimum_available_bytes, self.minimum_available_percentage,
            self.estimated_audit_database_allocation,
            self.estimated_replay_database_allocation,
            self.estimated_baseline_backup_allocation,
            self.estimated_restore_validation_allocation, self.safety_reserve,
        )
        if any(not isinstance(v, int) or isinstance(v, bool) or not 0 < v <= 2**63 - 1
               for v in capacities) or self.minimum_available_percentage > 100:
            raise OperationalBootstrapPreflightError("CAPACITY_CONFIGURATION_INVALID")
        if (self.production_authorized or self.bootstrap_authorized
                or self.permit_issuance_requested or self.bootstrap_execution_requested):
            raise OperationalBootstrapPreflightError("AUTHORIZATION_OR_EXECUTION_REJECTED")
        object.__setattr__(self, "expected_targets", dict(sorted(self.expected_targets.items())))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapHostEvidence:
    evidence_id: str
    collected_at: str
    operating_system: str
    machine_architecture: str
    user_id: int
    user_home: str
    repository_root: str
    repository_branch: str
    repository_commit: str
    working_tree_clean: bool
    upstream_ahead: int
    upstream_behind: int
    full_regression_passed: int
    full_regression_failed: int
    full_regression_warnings: int
    deployment_tests_passed: int
    deployment_tests_failed: int
    safety_counters: Mapping[str, int]

    def __post_init__(self) -> None:
        parse_timestamp(self.collected_at)
        validate_safe(asdict(self))
        if not self.evidence_id or not self.user_home.startswith("/"):
            raise OperationalBootstrapPreflightError("HOST_EVIDENCE_INVALID")
        if any(not isinstance(v, int) or isinstance(v, bool) or v < 0
               for v in self.safety_counters.values()):
            raise OperationalBootstrapPreflightError("SAFETY_COUNTER_INVALID")
        object.__setattr__(self, "safety_counters", dict(sorted(self.safety_counters.items())))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapTargetEvidence:
    responsibility: str
    normalized_identity: str
    exists: bool
    symlink: bool
    parent_component_symlink: bool
    filesystem_identity: str
    local_filesystem: bool
    removable: bool
    network: bool
    repository_overlap: bool
    ubuntu_linux_owned: bool
    protected_path: bool
    permission_mode: int
    expected_owner_identity: str
    authorized_prior_bootstrap_receipt: bool = False


@dataclass(frozen=True, slots=True)
class OperationalBootstrapFilesystemEvidence:
    filesystem_identity: str
    local: bool
    removable: bool
    network: bool


@dataclass(frozen=True, slots=True)
class OperationalBootstrapCapacityEvidence:
    filesystem_identity: str
    total_bytes: int
    available_bytes: int

    @property
    def available_percentage(self) -> int:
        return self.available_bytes * 100 // self.total_bytes if self.total_bytes else 0


@dataclass(frozen=True, slots=True)
class OperationalBootstrapClosedTrackEvidence:
    m3_a4a_status: str
    m3_a4b1_status: str
    m3_a4b2a_status: str
    readiness_decision: str
    authorization_capability_available: bool
    executor_test_only_validation_passed: bool
    audit_bootstrap_validation_passed: bool
    replay_bootstrap_validation_passed: bool
    backup_restore_validation_passed: bool
    failure_cleanup_validation_passed: bool
    warning_restriction_acknowledged: bool
    operational_permit_issued: bool = False
    operational_authorization_granted: bool = False
    operational_bootstrap_executed: bool = False


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPreflightCheck:
    code: str
    status: OperationalBootstrapPreflightStatus
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, order=True)
class OperationalBootstrapPreflightFinding:
    code: str
    severity: str


@dataclass(frozen=True, slots=True, order=True)
class OperationalBootstrapPreflightRestriction:
    code: str
    summary: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapPreflightReport:
    report_id: str
    decision: OperationalBootstrapPreflightDecision
    evaluated_at: str
    checks: tuple[OperationalBootstrapPreflightCheck, ...]
    findings: tuple[OperationalBootstrapPreflightFinding, ...]
    restrictions: tuple[OperationalBootstrapPreflightRestriction, ...]
    report_digest: str
    permit_issued: bool = False
    permit_claimed: bool = False
    bootstrap_authorized: bool = False
    bootstrap_executed: bool = False
    writers_authorized: bool = False
    monitoring_authorized: bool = False
    external_dispatch_authorized: bool = False
    production_authorized: bool = False
    filesystem_writes: int = 0
    database_writes: int = 0

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @property
    def canonical_json(self) -> str:
        return canonical_json(self)
