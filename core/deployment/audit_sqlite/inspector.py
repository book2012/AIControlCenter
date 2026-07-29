"""SQLite URI mode=ro inspector. It cannot create, migrate, repair or append."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from core.deployment.audit_contracts import (
    AuditContractError,
    AuditEvent,
    AuditEventType,
    verify_audit_chain,
)
from core.deployment.contracts import sha256_digest

from core.deployment.audit_sqlite.models import (
    SQLiteAuditInspectionReport,
    SQLiteAuditIntegrityFinding,
    SQLiteAuditSchemaExpectation,
    SQLiteAuditStatus,
)
from core.deployment.audit_sqlite.path_policy import SQLiteAuditPathPolicy


@dataclass(frozen=True, slots=True)
class SQLiteAuditStorageConfig:
    configured_path: Path
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "configured_path", Path(self.configured_path))
        if not 0 < self.timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be bounded")


class SQLiteAuditReadOnlyInspector:
    def __init__(
        self,
        *,
        config: SQLiteAuditStorageConfig,
        path_policy: SQLiteAuditPathPolicy,
        schema: SQLiteAuditSchemaExpectation | None = None,
    ) -> None:
        self._config = config
        self._policy = path_policy
        self._schema = schema or SQLiteAuditSchemaExpectation()

    def _report(self, *, inspected_at: str, status: SQLiteAuditStatus,
                exists: bool, findings: list[SQLiteAuditIntegrityFinding],
                **values: object) -> SQLiteAuditInspectionReport:
        defaults = {
            "configured_path_identity_digest":
                self._policy.identity_digest(self._config.configured_path),
            "file_exists": exists, "connection_mode": "mode=ro",
            "query_only": False, "schema_version": None,
            "schema_findings": tuple(findings), "integrity_result": "NOT_RUN",
            "event_count": 0, "first_sequence": None, "last_sequence": None,
            "chain_result": "NOT_RUN", "privacy_result": "NOT_RUN",
            "production_authorization_violations": 0, "journal_mode": None,
            "foreign_keys": None,
            "restrictions": (
                "READ_ONLY", "NO_APPEND", "NO_DDL", "NO_MIGRATION", "NO_REPAIR",
                "NO_VACUUM", "NO_CHECKPOINT", "PRODUCTION_NOT_AUTHORIZED",
            ),
            "inspected_at": inspected_at, "status": status,
        }
        defaults.update(values)
        return SQLiteAuditInspectionReport.build(**defaults)

    def inspect(self, *, inspected_at: str) -> SQLiteAuditInspectionReport:
        path = self._config.configured_path
        violations = self._policy.validate(path)
        if violations:
            findings = [
                SQLiteAuditIntegrityFinding(code, "ERROR", "configured path rejected")
                for code in violations
            ]
            return self._report(inspected_at=inspected_at,
                                status=SQLiteAuditStatus.BLOCKED,
                                exists=path.is_file(), findings=findings)
        if not path.is_file():
            return self._report(
                inspected_at=inspected_at, status=SQLiteAuditStatus.UNAVAILABLE,
                exists=False,
                findings=[SQLiteAuditIntegrityFinding(
                    "DATABASE_UNAVAILABLE", "ERROR", "configured database is unavailable"
                )],
            )
        try:
            with path.open("rb") as stream:
                if stream.read(16) != b"SQLite format 3\x00":
                    return self._report(
                        inspected_at=inspected_at, status=SQLiteAuditStatus.INVALID,
                        exists=True, integrity_result="INVALID_HEADER",
                        findings=[SQLiteAuditIntegrityFinding(
                            "INVALID_SQLITE_HEADER", "ERROR", "SQLite header is invalid"
                        )],
                    )
        except OSError:
            return self._report(
                inspected_at=inspected_at, status=SQLiteAuditStatus.UNAVAILABLE,
                exists=True, findings=[SQLiteAuditIntegrityFinding(
                    "DATABASE_UNREADABLE", "ERROR", "configured database is unreadable"
                )],
            )
        uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
        findings: list[SQLiteAuditIntegrityFinding] = []
        try:
            connection = sqlite3.connect(
                uri, uri=True, timeout=self._config.timeout_seconds,
                isolation_level=None,
            )
            try:
                connection.execute("PRAGMA query_only=ON")
                query_only = bool(connection.execute("PRAGMA query_only").fetchone()[0])
                journal_mode = str(connection.execute("PRAGMA journal_mode").fetchone()[0])
                foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
                integrity = str(connection.execute("PRAGMA quick_check").fetchone()[0])
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table'"
                )}
                indexes = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type='index'"
                )}
                for table in self._schema.required_tables:
                    if table not in tables:
                        findings.append(SQLiteAuditIntegrityFinding(
                            "MISSING_TABLE", "ERROR", f"required table missing: {table}"
                        ))
                for index in self._schema.required_indexes:
                    if index not in indexes:
                        findings.append(SQLiteAuditIntegrityFinding(
                            "MISSING_INDEX", "ERROR", f"required index missing: {index}"
                        ))
                schema_version = None
                rows: list[tuple[object, ...]] = []
                if "audit_ledger_meta" in tables:
                    try:
                        meta = connection.execute(
                            "SELECT schema_version FROM audit_ledger_meta LIMIT 1"
                        ).fetchone()
                        schema_version = str(meta[0]) if meta else None
                    except sqlite3.Error:
                        findings.append(SQLiteAuditIntegrityFinding(
                            "UNREADABLE_SCHEMA_VERSION", "ERROR",
                            "schema version metadata is unreadable",
                        ))
                if schema_version != self._schema.schema_version:
                    findings.append(SQLiteAuditIntegrityFinding(
                        "SCHEMA_VERSION_MISMATCH", "ERROR",
                        "schema version does not match expectation",
                    ))
                if "audit_events" in tables:
                    columns = {row[1] for row in connection.execute(
                        "PRAGMA table_info(audit_events)"
                    )}
                    for field in self._schema.event_fields:
                        if field not in columns:
                            findings.append(SQLiteAuditIntegrityFinding(
                                "MISSING_COLUMN", "ERROR",
                                f"required event field missing: {field}",
                            ))
                    if set(self._schema.event_fields).issubset(columns):
                        rows = list(connection.execute(
                            "SELECT ledger_sequence,event_id,schema_version,event_type,"
                            "recorded_at,actor_identity,canonical_payload,payload_digest,"
                            "previous_event_hash,event_hash,production_authorized "
                            "FROM audit_events ORDER BY ledger_sequence,event_id"
                        ))
            finally:
                connection.close()
        except sqlite3.Error:
            return self._report(
                inspected_at=inspected_at, status=SQLiteAuditStatus.INVALID,
                exists=True, findings=[SQLiteAuditIntegrityFinding(
                    "SQLITE_READ_FAILURE", "ERROR", "SQLite inspection failed"
                )],
            )
        if not query_only:
            findings.append(SQLiteAuditIntegrityFinding(
                "QUERY_ONLY_INACTIVE", "ERROR", "query_only is not active"
            ))
        if integrity.lower() != "ok":
            findings.append(SQLiteAuditIntegrityFinding(
                "INTEGRITY_CHECK_FAILED", "ERROR", "SQLite quick_check failed"
            ))
        events: list[AuditEvent] = []
        event_ids: list[str] = []
        sequences: list[int] = []
        privacy_violations = 0
        production_violations = 0
        for row in rows:
            sequence, event_id, row_schema, event_type, recorded_at, actor, raw_payload, \
                payload_digest, previous_hash, event_hash, production = row
            sequences.append(int(sequence))
            event_ids.append(str(event_id))
            production_violations += int(bool(production))
            try:
                payload = json.loads(str(raw_payload))
                if sha256_digest(payload) != payload_digest:
                    findings.append(SQLiteAuditIntegrityFinding(
                        "MODIFIED_PAYLOAD", "ERROR", "payload digest mismatch"
                    ))
                semantic = payload
                events.append(AuditEvent(
                    event_id=str(event_id), event_type=AuditEventType(str(event_type)),
                    sequence=int(sequence), previous_event_hash=str(previous_hash),
                    event_hash=str(event_hash), recorded_at=str(recorded_at),
                    actor_identity=str(actor),
                    authorization_id=semantic.get("authorization_id"),
                    package_digest=semantic.get("package_digest"),
                    plan_digest=semantic.get("plan_digest"),
                    target_identity=semantic.get("target_identity"),
                    environment=semantic["environment"],
                    executor_request_id=semantic.get("executor_request_id"),
                    executor_result_id=semantic.get("executor_result_id"),
                    evidence_digests=tuple(semantic.get("evidence_digests", ())),
                    policy_decision=semantic["policy_decision"],
                    payload=semantic.get("payload", {}),
                    production_authorized=bool(production),
                ))
                if row_schema != "dpl/audit/v1":
                    findings.append(SQLiteAuditIntegrityFinding(
                        "EVENT_SCHEMA_MISMATCH", "ERROR",
                        "event schema version does not match canonical contract",
                    ))
            except (AuditContractError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                privacy_violations += 1
                findings.append(SQLiteAuditIntegrityFinding(
                    "SECRET_OR_INVALID_PAYLOAD", "ERROR",
                    "payload violates canonical privacy contract",
                ))
        for code, values in (("DUPLICATE_EVENT_ID", event_ids),
                             ("DUPLICATE_SEQUENCE", sequences)):
            if len(values) != len(set(values)):
                findings.append(SQLiteAuditIntegrityFinding(
                    code, "ERROR", "duplicate ledger identity detected"
                ))
        if sequences and sequences != list(range(1, max(sequences) + 1)):
            findings.append(SQLiteAuditIntegrityFinding(
                "MISSING_SEQUENCE_GAP", "ERROR", "ledger sequence is not contiguous"
            ))
        chain = verify_audit_chain(events) if len(events) == len(rows) else None
        if chain and not chain.valid:
            for reason in chain.reason_codes:
                findings.append(SQLiteAuditIntegrityFinding(
                    reason, "ERROR", "canonical audit chain verification failed"
                ))
        if production_violations:
            findings.append(SQLiteAuditIntegrityFinding(
                "PRODUCTION_AUTHORIZED_VIOLATION", "ERROR",
                "production authorization is prohibited",
            ))
        status = SQLiteAuditStatus.HEALTHY if not findings else SQLiteAuditStatus.INVALID
        return self._report(
            inspected_at=inspected_at, status=status, exists=True, findings=findings,
            query_only=query_only, schema_version=schema_version,
            integrity_result=integrity.upper(), event_count=len(rows),
            first_sequence=min(sequences) if sequences else None,
            last_sequence=max(sequences) if sequences else None,
            chain_result="VALID" if chain and chain.valid else (
                "VALID" if not rows else "INVALID"),
            privacy_result="VALID" if not privacy_violations else "INVALID",
            production_authorization_violations=production_violations,
            journal_mode=journal_mode, foreign_keys=foreign_keys,
        )
