"""Immutable contracts for the separately composed SQLite audit writer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from core.deployment.contracts import sha256_digest


class SQLiteAuditAppendStatus(StrEnum):
    COMMITTED = "COMMITTED"
    IDEMPOTENT = "IDEMPOTENT"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


class SQLiteAuditWriterError(RuntimeError):
    """Fail-closed writer error which never reflects payload values."""

    def __init__(self, status: SQLiteAuditAppendStatus, code: str) -> None:
        self.status = status
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SQLiteAuditWriterConfig:
    database_path: Path
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        path = Path(self.database_path)
        object.__setattr__(self, "database_path", path)
        if not path.is_absolute():
            raise ValueError("database_path must be absolute")
        if not 0 < self.timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be bounded")


@dataclass(frozen=True, slots=True)
class SQLiteAuditAppendPolicy:
    connection_mode: str = "mode=rw"
    journal_mode: str = "wal"
    synchronous: int = 2
    foreign_keys: int = 1
    production_authorized: bool = False


@dataclass(frozen=True, slots=True)
class SQLiteAuditSchemaDefinition:
    ledger_schema_version: str = "dpl/audit-sqlite/v1"
    event_schema_version: str = "dpl/audit/v1"
    required_tables: tuple[str, ...] = ("audit_events", "audit_ledger_meta")
    required_indexes: tuple[str, ...] = (
        "ux_audit_events_event_id",
        "ux_audit_events_ledger_sequence",
    )
    required_triggers: tuple[str, ...] = (
        "trg_audit_events_no_update",
        "trg_audit_events_no_delete",
    )
    event_fields: tuple[str, ...] = (
        "ledger_sequence", "event_id", "schema_version", "event_type",
        "recorded_at", "actor_identity", "canonical_payload", "payload_digest",
        "previous_event_hash", "event_hash", "production_authorized",
    )

    def ddl_for_test_bootstrap(self) -> str:
        """Return inert DDL. Runtime writer code never executes this value."""
        return """
CREATE TABLE audit_ledger_meta (schema_version TEXT NOT NULL);
CREATE TABLE audit_events (
 ledger_sequence INTEGER NOT NULL, event_id TEXT NOT NULL,
 schema_version TEXT NOT NULL, event_type TEXT NOT NULL,
 recorded_at TEXT NOT NULL, actor_identity TEXT NOT NULL,
 canonical_payload TEXT NOT NULL, payload_digest TEXT NOT NULL,
 previous_event_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
 production_authorized INTEGER NOT NULL CHECK(production_authorized = 0)
);
CREATE UNIQUE INDEX ux_audit_events_event_id ON audit_events(event_id);
CREATE UNIQUE INDEX ux_audit_events_ledger_sequence ON audit_events(ledger_sequence);
CREATE TRIGGER trg_audit_events_no_update BEFORE UPDATE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;
CREATE TRIGGER trg_audit_events_no_delete BEFORE DELETE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit_events are append-only'); END;
"""


@dataclass(frozen=True, slots=True)
class SQLiteAuditSchemaValidationReport:
    valid: bool
    reason_codes: tuple[str, ...]
    schema_version: str | None
    journal_mode: str | None


@dataclass(frozen=True, slots=True)
class SQLiteAuditAppendReceipt:
    receipt_id: str
    event_id: str
    ledger_sequence: int
    schema_version: str
    event_type: str
    payload_digest: str
    previous_event_hash: str
    event_hash: str
    database_path_identity_digest: str
    transaction_committed: bool
    idempotent_retry: bool
    recorded_at: str
    production_authorized: bool
    writes_performed: int
    receipt_digest: str
    status: SQLiteAuditAppendStatus

    def content(self) -> dict[str, Any]:
        return {
            "database_path_identity_digest": self.database_path_identity_digest,
            "event_hash": self.event_hash,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "idempotent_retry": self.idempotent_retry,
            "ledger_sequence": self.ledger_sequence,
            "payload_digest": self.payload_digest,
            "previous_event_hash": self.previous_event_hash,
            "production_authorized": False,
            "recorded_at": self.recorded_at,
            "schema_version": self.schema_version,
            "status": self.status.value,
            "transaction_committed": self.transaction_committed,
            "writes_performed": self.writes_performed,
        }

    @classmethod
    def build(cls, **values: Any) -> "SQLiteAuditAppendReceipt":
        digest = sha256_digest(values)
        return cls(
            **values,
            receipt_id="sqlite-append-" + digest[7:39],
            receipt_digest=digest,
        )

