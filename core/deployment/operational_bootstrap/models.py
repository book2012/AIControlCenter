"""Immutable M3-A4B2A test-only bootstrap contracts."""

from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from core.deployment.contracts import sha256_digest


class OperationalBootstrapError(RuntimeError):
    """Fail-closed bootstrap error with a non-sensitive reason code."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class OperationalBootstrapExecutionMode(StrEnum):
    TEST_ONLY_BOOTSTRAP_VALIDATION = "TEST_ONLY_BOOTSTRAP_VALIDATION"


class OperationalBootstrapStatus(StrEnum):
    COMPLETE = "COMPLETE"
    FAILED_CLOSED = "FAILED_CLOSED"


ORDERED_STEPS = (
    "VALIDATE_EXECUTION_CONFIGURATION",
    "VALIDATE_TEST_ONLY_TARGET_ROOT",
    "VALIDATE_SYNTHETIC_PERMIT",
    "CLAIM_SYNTHETIC_PERMIT",
    "REVALIDATE_TARGET_NONEXISTENCE",
    "CREATE_APPLICATION_STATE_DIRECTORIES",
    "VERIFY_DIRECTORY_PERMISSIONS",
    "CREATE_AUDIT_DATABASE",
    "APPLY_AUDIT_SCHEMA_AND_PROTECTIONS",
    "VERIFY_AUDIT_DATABASE_READ_ONLY",
    "CREATE_REPLAY_DATABASE",
    "APPLY_REPLAY_SCHEMA_AND_PROTECTIONS",
    "VERIFY_REPLAY_DATABASE_READ_ONLY",
    "CREATE_BASELINE_AUDIT_BACKUP",
    "VALIDATE_AUDIT_RESTORE",
    "CREATE_BASELINE_REPLAY_BACKUP",
    "VALIDATE_REPLAY_RESTORE",
    "CREATE_PRE_ACTIVATION_MONITORING_SNAPSHOT",
    "VERIFY_WRITERS_REMAIN_INACTIVE",
    "RETURN_EVIDENCE_BUNDLE",
)

_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script",
    re.I,
)


def _safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _FORBIDDEN.search(str(key)):
                raise OperationalBootstrapError("UNSAFE_FIELD_REJECTED")
            _safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _safe(child)
    elif not isinstance(value, (str, int, bool, type(None), StrEnum)):
        raise OperationalBootstrapError("UNSAFE_VALUE_REJECTED")


@dataclass(frozen=True, slots=True)
class OperationalBootstrapExecutorConfig:
    test_root: Path
    repository_root: Path
    mode: OperationalBootstrapExecutionMode
    busy_timeout_ms: int = 2000
    cleanup_restore_targets: bool = True
    failure_step: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "test_root", Path(self.test_root))
        object.__setattr__(self, "repository_root", Path(self.repository_root))
        if self.mode is not OperationalBootstrapExecutionMode.TEST_ONLY_BOOTSTRAP_VALIDATION:
            raise OperationalBootstrapError("PRIVILEGED_EXECUTION_MODE_REJECTED")
        if not 1 <= self.busy_timeout_ms <= 5000:
            raise OperationalBootstrapError("BUSY_TIMEOUT_UNBOUNDED")
        if self.failure_step is not None and self.failure_step not in ORDERED_STEPS:
            raise OperationalBootstrapError("UNKNOWN_FAILURE_STEP")


@dataclass(frozen=True, slots=True)
class OperationalBootstrapTargetPaths:
    root: Path
    application_state: Path
    audit_directory: Path
    audit_database: Path
    audit_backup_root: Path
    security_directory: Path
    replay_database: Path
    replay_backup_root: Path
    monitoring_directory: Path
    restore_validation_root: Path

    @classmethod
    def under(cls, root: Path) -> "OperationalBootstrapTargetPaths":
        root = Path(root)
        state = root / "application-state"
        audit = state / "audit"
        security = state / "security"
        return cls(
            root, state, audit, audit / "audit-ledger.sqlite3", audit / "backups",
            security, security / "permit-replay.sqlite3", security / "backups",
            state / "monitoring", root / "restore-validation",
        )


@dataclass(frozen=True, slots=True)
class OperationalBootstrapSchemaPlan:
    audit_schema_version: str = "dpl/audit-sqlite/v1"
    replay_schema_version: str = "dpl/permit-replay-sqlite/v1"
    production_authorized: bool = False

    @property
    def plan_digest(self) -> str:
        return sha256_digest(asdict(self))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapExecutionStep:
    sequence: int
    code: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapExecutionPlan:
    steps: tuple[OperationalBootstrapExecutionStep, ...]
    plan_digest: str

    @classmethod
    def build(cls) -> "OperationalBootstrapExecutionPlan":
        steps = tuple(OperationalBootstrapExecutionStep(i, code)
                      for i, code in enumerate(ORDERED_STEPS, 1))
        return cls(steps, sha256_digest(
            [{"sequence": step.sequence, "code": step.code} for step in steps]))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapRequest:
    request_id: str
    branch: str
    commit: str
    started_at: str
    completed_at: str
    claimant_identity: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.request_id or not re.fullmatch(r"[0-9a-f]{40}", self.commit):
            raise OperationalBootstrapError("INVALID_REQUEST_BINDING")
        _safe(self.metadata)
        object.__setattr__(self, "metadata", dict(sorted(self.metadata.items())))


@dataclass(frozen=True, slots=True)
class OperationalBootstrapStepReceipt:
    sequence: int
    code: str
    completed: bool
    evidence_digest: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class OperationalBootstrapReceipt:
    receipt_id: str
    request_id: str
    permit_id: str
    execution_mode: OperationalBootstrapExecutionMode
    branch: str
    commit: str
    status: OperationalBootstrapStatus
    completed_steps: tuple[str, ...]
    created_directory_count: int
    created_database_count: int
    created_backup_count: int
    validated_restore_count: int
    transaction_committed: bool
    complete: bool
    receipt_digest: str
    test_only: bool = True
    operational_bootstrap: bool = False
    writers_activated: bool = False
    monitoring_activated: bool = False
    external_dispatch_activated: bool = False
    production_authorized: bool = False


@dataclass(frozen=True, slots=True, order=True)
class OperationalBootstrapFinding:
    code: str
    severity: str
    detail: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapValidationReport:
    status: OperationalBootstrapStatus
    findings: tuple[OperationalBootstrapFinding, ...]
    report_digest: str


@dataclass(frozen=True, slots=True)
class OperationalBootstrapEvidenceBundle:
    evidence_bundle_id: str
    receipt: OperationalBootstrapReceipt
    receipt_id: str
    receipt_digest: str
    permit_id: str
    permit_digest: str
    permit_use_claim_id: str
    permit_use_claim_digest: str
    branch: str
    commit: str
    execution_mode: OperationalBootstrapExecutionMode
    target_root_identity_digest: str
    step_receipts: tuple[OperationalBootstrapStepReceipt, ...]
    directory_permission_evidence: tuple[tuple[str, str], ...]
    audit_database_path_identity_digest: str
    audit_schema_digest: str
    audit_inspection_digest: str
    replay_database_path_identity_digest: str
    replay_schema_digest: str
    replay_inspection_digest: str
    audit_backup_digest: str
    audit_restore_digest: str
    replay_backup_digest: str
    replay_restore_digest: str
    monitoring_snapshot_id: str
    monitoring_snapshot_digest: str
    artifact_inventory: tuple[tuple[str, str], ...]
    started_at: str
    completed_at: str
    evidence_digest: str
    writers_activated: int = 0
    monitoring_activated: int = 0
    alerts_dispatched: int = 0
    production_authorized: bool = False


def path_identity(path: Path) -> str:
    return "sha256:" + __import__("hashlib").sha256(os.fsencode(path)).hexdigest()
