"""Immutable SQLite audit backup, restore, and recovery contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from core.deployment.contracts import sha256_digest


class SQLiteAuditRecoveryStatus(StrEnum):
    BACKUP_COMPLETE = "BACKUP_COMPLETE"
    RESTORE_COMPLETE = "RESTORE_COMPLETE"
    RECOVERY_VALID = "RECOVERY_VALID"
    DEGRADED = "DEGRADED"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    TAMPERED = "TAMPERED"


class SQLiteAuditRecoveryError(RuntimeError):
    def __init__(self, status: SQLiteAuditRecoveryStatus, code: str) -> None:
        self.status = status
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SQLiteAuditBackupConfig:
    source_path: Path
    backup_root: Path
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_path", Path(self.source_path))
        object.__setattr__(self, "backup_root", Path(self.backup_root))
        if not self.source_path.is_absolute() or not self.backup_root.is_absolute():
            raise ValueError("source_path and backup_root must be absolute")
        if not 0 < self.timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be bounded")


@dataclass(frozen=True, slots=True)
class SQLiteAuditBackupRequest:
    backup_path: Path
    manifest_path: Path
    created_at: str
    production_authorized: bool = False
    operational_backup: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "backup_path", Path(self.backup_path))
        object.__setattr__(self, "manifest_path", Path(self.manifest_path))
        if not self.backup_path.is_absolute() or not self.manifest_path.is_absolute():
            raise ValueError("backup_path and manifest_path must be absolute")
        if self.production_authorized or self.operational_backup:
            raise ValueError("operational or production backup is not authorized")


@dataclass(frozen=True, slots=True)
class SQLiteAuditBackupManifest:
    backup_id: str
    source_path_identity_digest: str
    backup_path_identity_digest: str
    schema_version: str
    event_count: int
    first_ledger_sequence: int | None
    last_ledger_sequence: int | None
    first_event_hash: str | None
    last_event_hash: str | None
    database_byte_digest: str
    logical_ledger_digest: str
    source_inspection_report_id: str
    source_inspection_report_digest: str
    created_at: str
    production_authorized: bool
    operational_backup: bool
    manifest_digest: str

    def content(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items()
                if key != "manifest_digest"}

    def as_dict(self) -> dict[str, Any]:
        return {**self.content(), "manifest_digest": self.manifest_digest}

    @classmethod
    def build(cls, **values: Any) -> "SQLiteAuditBackupManifest":
        return cls(**values, manifest_digest=sha256_digest(values))


@dataclass(frozen=True, slots=True)
class SQLiteAuditBackupReceipt:
    receipt_id: str
    backup_id: str
    backup_path_identity_digest: str
    manifest_digest: str
    database_byte_digest: str
    logical_ledger_digest: str
    event_count: int
    source_unchanged: bool
    idempotent_retry: bool
    status: SQLiteAuditRecoveryStatus
    production_authorized: bool
    operational_backup: bool
    receipt_digest: str

    @classmethod
    def build(cls, **values: Any) -> "SQLiteAuditBackupReceipt":
        digestable = {
            **values, "status": values["status"].value,
        }
        digest = sha256_digest(digestable)
        return cls(**values, receipt_id="sqlite-backup-" + digest[7:39],
                   receipt_digest=digest)


@dataclass(frozen=True, slots=True)
class SQLiteAuditRestoreConfig:
    restore_root: Path
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "restore_root", Path(self.restore_root))
        if not self.restore_root.is_absolute():
            raise ValueError("restore_root must be absolute")
        if not 0 < self.timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be bounded")


@dataclass(frozen=True, slots=True)
class SQLiteAuditRestoreRequest:
    backup_path: Path
    manifest_path: Path
    restore_path: Path
    restored_at: str
    production_authorized: bool = False
    operational_restore: bool = False

    def __post_init__(self) -> None:
        for name in ("backup_path", "manifest_path", "restore_path"):
            path = Path(getattr(self, name))
            object.__setattr__(self, name, path)
            if not path.is_absolute():
                raise ValueError(f"{name} must be absolute")
        if self.production_authorized or self.operational_restore:
            raise ValueError("operational or production restore is not authorized")


@dataclass(frozen=True, slots=True)
class SQLiteAuditRestoreReceipt:
    receipt_id: str
    backup_id: str
    restore_path_identity_digest: str
    manifest_digest: str
    database_byte_digest: str
    logical_ledger_digest: str
    event_count: int
    backup_unchanged: bool
    restored_at: str
    status: SQLiteAuditRecoveryStatus
    production_authorized: bool
    operational_restore: bool
    receipt_digest: str

    @classmethod
    def build(cls, **values: Any) -> "SQLiteAuditRestoreReceipt":
        digestable = {**values, "status": values["status"].value}
        digest = sha256_digest(digestable)
        return cls(**values, receipt_id="sqlite-restore-" + digest[7:39],
                   receipt_digest=digest)


@dataclass(frozen=True, slots=True, order=True)
class SQLiteAuditRecoveryFinding:
    code: str
    severity: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail, "severity": self.severity}


@dataclass(frozen=True, slots=True)
class SQLiteAuditRecoveryValidationReport:
    report_id: str
    status: SQLiteAuditRecoveryStatus
    backup_id: str
    source_path_identity_digest: str
    backup_path_identity_digest: str
    restore_path_identity_digest: str
    source_logical_ledger_digest: str
    backup_logical_ledger_digest: str
    restored_logical_ledger_digest: str
    schema_matches: bool
    event_count_matches: bool
    event_identity_matches: bool
    payload_digests_match: bool
    previous_hashes_match: bool
    event_hashes_match: bool
    source_unchanged: bool
    backup_unchanged: bool
    restored_inspection_healthy: bool
    production_authorization_violations: int
    secret_bearing_violations: int
    findings: tuple[SQLiteAuditRecoveryFinding, ...]
    validated_at: str
    operational_activation: bool
    production_authorized: bool
    report_digest: str

    @classmethod
    def build(cls, **values: Any) -> "SQLiteAuditRecoveryValidationReport":
        values["findings"] = tuple(sorted(values["findings"]))
        digestable = {
            **values,
            "status": values["status"].value,
            "findings": [item.as_dict() for item in values["findings"]],
        }
        digest = sha256_digest(digestable)
        return cls(**values, report_id="sqlite-recovery-" + digest[7:39],
                   report_digest=digest)
