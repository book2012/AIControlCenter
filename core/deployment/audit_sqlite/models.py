"""Immutable contracts for deterministic, read-only SQLite inspection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from core.deployment.contracts import canonical_json_bytes, sha256_digest


class SQLiteAuditStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True, order=True)
class SQLiteAuditIntegrityFinding:
    code: str
    severity: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail, "severity": self.severity}


@dataclass(frozen=True, slots=True)
class SQLiteAuditSchemaExpectation:
    schema_version: str = "dpl/audit-sqlite/v1"
    required_tables: tuple[str, ...] = ("audit_events", "audit_ledger_meta")
    required_indexes: tuple[str, ...] = (
        "ux_audit_events_event_id",
        "ux_audit_events_ledger_sequence",
    )
    event_fields: tuple[str, ...] = (
        "ledger_sequence", "event_id", "schema_version", "event_type",
        "recorded_at", "actor_identity", "canonical_payload", "payload_digest",
        "previous_event_hash", "event_hash", "production_authorized",
    )
    append_only: bool = True
    immutable_events: bool = True

    def schema_sql_for_documentation(self) -> str:
        """Return inert expected DDL; runtime inspection never executes it."""
        return (
            "CREATE TABLE audit_ledger_meta (schema_version TEXT NOT NULL);\n"
            "CREATE TABLE audit_events (ledger_sequence INTEGER NOT NULL, "
            "event_id TEXT NOT NULL, schema_version TEXT NOT NULL, event_type TEXT NOT NULL, "
            "recorded_at TEXT NOT NULL, actor_identity TEXT NOT NULL, "
            "canonical_payload TEXT NOT NULL, payload_digest TEXT NOT NULL, "
            "previous_event_hash TEXT NOT NULL, event_hash TEXT NOT NULL, "
            "production_authorized INTEGER NOT NULL);\n"
            "CREATE UNIQUE INDEX ux_audit_events_event_id ON audit_events(event_id);\n"
            "CREATE UNIQUE INDEX ux_audit_events_ledger_sequence "
            "ON audit_events(ledger_sequence);"
        )


@dataclass(frozen=True, slots=True)
class SQLiteAuditInspectionReport:
    status: SQLiteAuditStatus
    configured_path_identity_digest: str
    file_exists: bool
    connection_mode: str
    query_only: bool
    schema_version: str | None
    schema_findings: tuple[SQLiteAuditIntegrityFinding, ...]
    integrity_result: str
    event_count: int
    first_sequence: int | None
    last_sequence: int | None
    chain_result: str
    privacy_result: str
    production_authorization_violations: int
    journal_mode: str | None
    foreign_keys: int | None
    restrictions: tuple[str, ...]
    inspected_at: str
    report_id: str
    report_digest: str
    writes_performed: int = 0
    migrations_performed: int = 0
    repairs_performed: int = 0
    production_authorized: bool = False

    def _content(self) -> dict[str, Any]:
        return {
            "chain_result": self.chain_result,
            "configured_path_identity_digest": self.configured_path_identity_digest,
            "connection_mode": self.connection_mode,
            "event_count": self.event_count,
            "file_exists": self.file_exists,
            "first_sequence": self.first_sequence,
            "foreign_keys": self.foreign_keys,
            "inspected_at": self.inspected_at,
            "integrity_result": self.integrity_result,
            "journal_mode": self.journal_mode,
            "last_sequence": self.last_sequence,
            "migrations_performed": self.migrations_performed,
            "privacy_result": self.privacy_result,
            "production_authorization_violations":
                self.production_authorization_violations,
            "production_authorized": self.production_authorized,
            "query_only": self.query_only,
            "repairs_performed": self.repairs_performed,
            "restrictions": list(self.restrictions),
            "schema_findings": [item.as_dict() for item in self.schema_findings],
            "schema_version": self.schema_version,
            "status": self.status.value,
            "writes_performed": self.writes_performed,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self._content(), "report_digest": self.report_digest,
                "report_id": self.report_id}

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode("utf-8")

    @classmethod
    def build(cls, **values: Any) -> "SQLiteAuditInspectionReport":
        content = dict(values)
        content["schema_findings"] = tuple(sorted(content["schema_findings"]))
        digestable = {
            **content,
            "schema_findings": [
                item.as_dict() for item in content["schema_findings"]
            ],
            "status": content["status"].value,
        }
        identity = sha256_digest(digestable)
        return cls(**content, report_id="sqlite-inspection-" + identity[7:39],
                   report_digest=identity)
