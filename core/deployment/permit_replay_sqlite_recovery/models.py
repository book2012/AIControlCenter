"""Immutable contracts for permit/replay backup, restore, and validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from core.deployment.contracts import sha256_digest


class PermitReplayRecoveryStatus(StrEnum):
    VALID = "VALID"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class PermitReplayBackupConfig:
    source_path: Path
    backup_root: Path
    repository_root: Path
    user_home: Path

    def __post_init__(self) -> None:
        for name in ("source_path", "backup_root", "repository_root", "user_home"):
            object.__setattr__(self, name, Path(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class PermitReplayBackupRequest:
    backup_path: Path
    manifest_path: Path
    created_at: str
    production_authorized: bool = False
    operational_backup: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "backup_path", Path(self.backup_path))
        object.__setattr__(self, "manifest_path", Path(self.manifest_path))


@dataclass(frozen=True, slots=True)
class PermitReplayRestoreConfig:
    restore_root: Path
    repository_root: Path
    user_home: Path

    def __post_init__(self) -> None:
        for name in ("restore_root", "repository_root", "user_home"):
            object.__setattr__(self, name, Path(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class PermitReplayRestoreRequest:
    backup_path: Path
    manifest_path: Path
    restore_path: Path
    restored_at: str
    production_authorized: bool = False

    def __post_init__(self) -> None:
        for name in ("backup_path", "manifest_path", "restore_path"):
            object.__setattr__(self, name, Path(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class PermitReplayBackupManifest:
    backup_id: str
    source_path_identity_digest: str
    backup_path_identity_digest: str
    schema_version: str
    event_count: int
    permit_count: int
    reserved_count: int
    consumed_count: int
    failed_closed_count: int
    invalid_count: int
    first_sequence: int | None
    last_sequence: int | None
    first_event_hash: str | None
    last_event_hash: str | None
    database_byte_digest: str
    logical_event_ledger_digest: str
    derived_permit_state_digest: str
    source_inspection_report_id: str
    source_inspection_report_digest: str
    created_at: str
    production_authorized: bool
    operational_backup: bool
    manifest_digest: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def build(cls, **values: Any) -> "PermitReplayBackupManifest":
        digest = sha256_digest(values)
        backup_id = "permit-replay-backup-" + digest[7:39]
        return cls(**values, backup_id=backup_id, manifest_digest=digest)


@dataclass(frozen=True, slots=True)
class PermitReplayBackupReceipt:
    backup_id: str
    backup_path_identity_digest: str
    manifest_path_identity_digest: str
    database_byte_digest: str
    logical_event_ledger_digest: str
    derived_permit_state_digest: str
    manifest_digest: str
    source_unchanged: bool
    production_authorized: bool
    operational_backup: bool
    receipt_digest: str


@dataclass(frozen=True, slots=True)
class PermitReplayRestoreReceipt:
    backup_id: str
    restore_path_identity_digest: str
    manifest_digest: str
    database_byte_digest: str
    logical_event_ledger_digest: str
    derived_permit_state_digest: str
    restored_at: str
    selected_operationally: bool
    production_authorized: bool
    receipt_digest: str


@dataclass(frozen=True, slots=True, order=True)
class PermitReplayRecoveryFinding:
    code: str
    severity: str = "ERROR"
    detail: str = "recovery validation denied"


@dataclass(frozen=True, slots=True)
class PermitReplayRecoveryValidationReport:
    status: PermitReplayRecoveryStatus
    findings: tuple[PermitReplayRecoveryFinding, ...]
    source_path_identity_digest: str
    recovered_path_identity_digest: str
    exact_event_equality: bool
    exact_permit_state_equality: bool
    source_unchanged: bool
    recovered_healthy: bool
    replay_violations: int
    production_authorized: bool
    report_digest: str


@dataclass(frozen=True, slots=True)
class PermitReplayConcurrencyValidationReport:
    status: PermitReplayRecoveryStatus
    reservation_commits: int
    reservation_idempotent: int
    terminal_commits: int
    terminal_denials: int
    duplicate_sequences: int
    duplicate_event_ids: int
    final_healthy: bool
    replay_violations: int
    production_authorized: bool
    report_digest: str


class PermitReplayRecoveryError(RuntimeError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
