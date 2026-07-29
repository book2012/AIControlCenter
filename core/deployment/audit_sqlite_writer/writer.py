"""Existing-file-only, append-only SQLite durable audit adapter."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

from core.deployment.audit_contracts import (
    GENESIS_PREVIOUS_HASH,
    AuditAppendRequest,
    AuditContractError,
    AuditEvent,
    AuditEventType,
)
from core.deployment.audit_sqlite import SQLiteAuditPathPolicy
from core.deployment.contracts import canonical_json_bytes, sha256_digest

from .models import (
    SQLiteAuditAppendPolicy,
    SQLiteAuditAppendReceipt,
    SQLiteAuditAppendStatus,
    SQLiteAuditSchemaDefinition,
    SQLiteAuditSchemaValidationReport,
    SQLiteAuditWriterConfig,
    SQLiteAuditWriterError,
)


class SQLiteAuditWriter:
    """Append exactly one canonical event; exposes no mutation alternatives."""

    def __init__(
        self,
        *,
        config: SQLiteAuditWriterConfig,
        path_policy: SQLiteAuditPathPolicy,
        append_policy: SQLiteAuditAppendPolicy | None = None,
        schema: SQLiteAuditSchemaDefinition | None = None,
    ) -> None:
        if config is None or path_policy is None:
            raise ValueError("explicit writer configuration and path policy required")
        self._config = config
        self._path_policy = path_policy
        self._append_policy = append_policy or SQLiteAuditAppendPolicy()
        self._schema = schema or SQLiteAuditSchemaDefinition()

    def _deny(self, status: SQLiteAuditAppendStatus, code: str) -> None:
        raise SQLiteAuditWriterError(status, code)

    def _connect(self) -> sqlite3.Connection:
        path = self._config.database_path
        violations = self._path_policy.validate(path)
        if violations:
            self._deny(SQLiteAuditAppendStatus.BLOCKED, violations[0])
        if not path.is_file():
            self._deny(SQLiteAuditAppendStatus.UNAVAILABLE, "DATABASE_UNAVAILABLE")
        uri = "file:" + quote(str(path), safe="/") + "?mode=rw"
        try:
            connection = sqlite3.connect(
                uri, uri=True, timeout=self._config.timeout_seconds,
                isolation_level=None,
            )
            connection.execute(
                f"PRAGMA busy_timeout={int(self._config.timeout_seconds * 1000)}"
            )
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
            return connection
        except sqlite3.Error as error:
            raise SQLiteAuditWriterError(
                SQLiteAuditAppendStatus.UNAVAILABLE, "SQLITE_CONNECTION_FAILED"
            ) from error

    def _validate_schema(
        self, connection: sqlite3.Connection
    ) -> SQLiteAuditSchemaValidationReport:
        reasons: set[str] = set()
        try:
            quick_check = str(connection.execute("PRAGMA quick_check").fetchone()[0])
            journal = str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower()
            foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
            synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
            objects = list(connection.execute(
                "SELECT type,name FROM sqlite_schema "
                "WHERE type IN ('table','index','trigger')"
            ))
            names = {str(row[1]) for row in objects}
            for name in self._schema.required_tables:
                if name not in names:
                    reasons.add("MISSING_TABLE")
            for name in self._schema.required_indexes:
                if name not in names:
                    reasons.add("MISSING_INDEX")
            for name in self._schema.required_triggers:
                if name not in names:
                    reasons.add("MISSING_APPEND_ONLY_TRIGGER")
            schema_version = None
            if "audit_ledger_meta" in names:
                row = connection.execute(
                    "SELECT schema_version FROM audit_ledger_meta LIMIT 1"
                ).fetchone()
                schema_version = str(row[0]) if row else None
            if schema_version != self._schema.ledger_schema_version:
                reasons.add("SCHEMA_VERSION_MISMATCH")
            if "audit_events" in names:
                columns = {str(row[1]) for row in connection.execute(
                    "PRAGMA table_info(audit_events)"
                )}
                if not set(self._schema.event_fields).issubset(columns):
                    reasons.add("MISSING_COLUMN")
            if quick_check.lower() != "ok":
                reasons.add("INTEGRITY_CHECK_FAILED")
            if journal != self._append_policy.journal_mode:
                reasons.add("JOURNAL_MODE_NOT_WAL")
            if foreign_keys != self._append_policy.foreign_keys:
                reasons.add("FOREIGN_KEYS_INACTIVE")
            if synchronous != self._append_policy.synchronous:
                reasons.add("SYNCHRONOUS_NOT_FULL")
        except sqlite3.Error:
            reasons.add("SCHEMA_VALIDATION_FAILED")
            schema_version = None
            journal = None
        return SQLiteAuditSchemaValidationReport(
            valid=not reasons, reason_codes=tuple(sorted(reasons)),
            schema_version=schema_version, journal_mode=journal,
        )

    def validate_schema(self) -> SQLiteAuditSchemaValidationReport:
        connection = self._connect()
        try:
            return self._validate_schema(connection)
        finally:
            connection.close()

    def _event_from_row(self, row: tuple[object, ...]) -> tuple[AuditEvent, str]:
        sequence, event_id, schema_version, event_type, recorded_at, actor, raw, \
            payload_digest, previous_hash, event_hash, production = row
        try:
            semantic = json.loads(str(raw))
            if canonical_json_bytes(semantic).decode() != raw:
                self._deny(SQLiteAuditAppendStatus.BLOCKED, "NONCANONICAL_PAYLOAD")
            if sha256_digest(semantic) != payload_digest:
                self._deny(SQLiteAuditAppendStatus.BLOCKED, "MODIFIED_EXISTING_PAYLOAD")
            event = AuditEvent(
                event_id=str(event_id), event_type=AuditEventType(str(event_type)),
                sequence=int(sequence), previous_event_hash=str(previous_hash),
                event_hash=str(event_hash), recorded_at=str(recorded_at),
                actor_identity=str(actor), authorization_id=semantic.get("authorization_id"),
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
            )
        except (AuditContractError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            self._deny(SQLiteAuditAppendStatus.BLOCKED, "INVALID_EXISTING_EVENT")
        if schema_version != self._schema.event_schema_version:
            self._deny(SQLiteAuditAppendStatus.BLOCKED, "EVENT_SCHEMA_MISMATCH")
        expected_hash = sha256_digest({"event_id": event.event_id, **event.semantic()})
        if expected_hash != event.event_hash:
            self._deny(SQLiteAuditAppendStatus.BLOCKED, "INVALID_EXISTING_CHAIN")
        return event, str(payload_digest)

    def _receipt(
        self, event: AuditEvent, payload_digest: str, *,
        idempotent: bool, writes: int,
    ) -> SQLiteAuditAppendReceipt:
        return SQLiteAuditAppendReceipt.build(
            event_id=event.event_id, ledger_sequence=event.sequence,
            schema_version=self._schema.event_schema_version,
            event_type=event.event_type.value, payload_digest=payload_digest,
            previous_event_hash=event.previous_event_hash,
            event_hash=event.event_hash,
            database_path_identity_digest=self._path_policy.identity_digest(
                self._config.database_path
            ),
            transaction_committed=True, idempotent_retry=idempotent,
            recorded_at=event.recorded_at, production_authorized=False,
            writes_performed=writes,
            status=(SQLiteAuditAppendStatus.IDEMPOTENT if idempotent
                    else SQLiteAuditAppendStatus.COMMITTED),
        )

    def append(self, request: AuditAppendRequest) -> SQLiteAuditAppendReceipt:
        if not isinstance(request, AuditAppendRequest):
            self._deny(SQLiteAuditAppendStatus.BLOCKED, "MALFORMED_REQUEST")
        event = request.event
        if event.production_authorized:
            self._deny(SQLiteAuditAppendStatus.BLOCKED, "PRODUCTION_AUTHORIZED")
        connection = self._connect()
        transaction = False
        try:
            connection.execute("BEGIN IMMEDIATE")
            transaction = True
            report = self._validate_schema(connection)
            if not report.valid:
                self._deny(SQLiteAuditAppendStatus.BLOCKED, report.reason_codes[0])
            rows = list(connection.execute(
                "SELECT ledger_sequence,event_id,schema_version,event_type,recorded_at,"
                "actor_identity,canonical_payload,payload_digest,previous_event_hash,"
                "event_hash,production_authorized FROM audit_events "
                "ORDER BY ledger_sequence"
            ))
            parsed = [self._event_from_row(tuple(row)) for row in rows]
            previous = GENESIS_PREVIOUS_HASH
            for expected_sequence, (stored, _) in enumerate(parsed, 1):
                if (stored.sequence != expected_sequence or
                        stored.previous_event_hash != previous):
                    self._deny(SQLiteAuditAppendStatus.BLOCKED, "INVALID_EXISTING_CHAIN")
                previous = stored.event_hash
            duplicate = next(
                ((stored, digest) for stored, digest in parsed
                 if stored.event_id == event.event_id), None
            )
            requested_payload = canonical_json_bytes(event.semantic()).decode()
            requested_digest = sha256_digest(event.semantic())
            if duplicate:
                stored, digest = duplicate
                if stored != event or request.expected_previous_hash != event.previous_event_hash:
                    self._deny(SQLiteAuditAppendStatus.BLOCKED, "DUPLICATE_EVENT_CONFLICT")
                connection.execute("COMMIT")
                transaction = False
                return self._receipt(stored, digest, idempotent=True, writes=0)
            next_sequence = len(parsed) + 1
            if (event.sequence != next_sequence or event.previous_event_hash != previous or
                    request.expected_previous_hash != previous):
                self._deny(SQLiteAuditAppendStatus.BLOCKED, "APPEND_POSITION_MISMATCH")
            connection.execute(
                "INSERT INTO audit_events "
                "(ledger_sequence,event_id,schema_version,event_type,recorded_at,"
                "actor_identity,canonical_payload,payload_digest,previous_event_hash,"
                "event_hash,production_authorized) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (event.sequence, event.event_id, self._schema.event_schema_version,
                 event.event_type.value, event.recorded_at, event.actor_identity,
                 requested_payload, requested_digest, event.previous_event_hash,
                 event.event_hash, 0),
            )
            row = connection.execute(
                "SELECT ledger_sequence,event_id,schema_version,event_type,recorded_at,"
                "actor_identity,canonical_payload,payload_digest,previous_event_hash,"
                "event_hash,production_authorized FROM audit_events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if row is None:
                self._deny(SQLiteAuditAppendStatus.FAILED, "READBACK_FAILED")
            stored, stored_digest = self._event_from_row(tuple(row))
            if stored != event or stored_digest != requested_digest:
                self._deny(SQLiteAuditAppendStatus.FAILED, "READBACK_MISMATCH")
            connection.execute("COMMIT")
            transaction = False
            return self._receipt(event, requested_digest, idempotent=False, writes=1)
        except SQLiteAuditWriterError:
            if transaction:
                connection.execute("ROLLBACK")
            raise
        except sqlite3.Error as error:
            if transaction:
                connection.execute("ROLLBACK")
            raise SQLiteAuditWriterError(
                SQLiteAuditAppendStatus.FAILED, "APPEND_TRANSACTION_FAILED"
            ) from error
        finally:
            connection.close()

