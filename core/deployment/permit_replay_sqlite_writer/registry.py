"""Existing-file-only SQLite permit reservation and terminal registry."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.permit_replay_sqlite import (
    PermitReplayPathPolicy,
    PermitReplaySchemaExpectation,
)
from core.deployment.permit_replay_sqlite_writer.models import (
    PermitReplayWriteFinding,
    PermitReplayWriteStatus,
    PermitReplayWriteValidationReport,
    PermitReplayWriterConfig,
    PermitReservationReceipt,
    PermitReservationRequest,
    PermitTerminalReceipt,
    PermitTerminalRequest,
    PermitTerminalState,
    build_receipt,
)

GENESIS = "GENESIS"
_FORBIDDEN = (
    "nonce", "password", "secret", "token", "credential", "cookie",
    "private_key", "api_key", "authorization", "environment_variables",
    "raw_environment", "shell", "command", "argv", "script",
)


def _secret_bearing(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            any(marker in str(key).lower().replace("-", "_") for marker in _FORBIDDEN)
            or _secret_bearing(child)
            for key, child in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_secret_bearing(child) for child in value)
    if isinstance(value, str):
        normalized = value.lower().replace("-", "_")
        return any(marker in normalized for marker in _FORBIDDEN)
    return False


def _semantic(row: Mapping[str, Any], payload: Any) -> dict[str, Any]:
    return {
        "ledger_sequence": row["ledger_sequence"], "event_id": row["event_id"],
        "permit_id": row["permit_id"], "permit_digest": row["permit_digest"],
        "activation_id": row["activation_id"],
        "activation_request_digest": row["activation_request_digest"],
        "event_type": row["event_type"], "event_at": row["event_at"],
        "actor_identity": row["actor_identity"],
        "target_identity": row["target_identity"], "environment": row["environment"],
        "canonical_payload": payload, "payload_digest": row["payload_digest"],
        "previous_event_hash": row["previous_event_hash"],
        "production_authorized": bool(row["production_authorized"]),
    }


class _Denied(Exception):
    def __init__(self, status: PermitReplayWriteStatus, code: str) -> None:
        self.status, self.code = status, code


class SQLitePermitReplayRegistry:
    """Fail-closed registry; construction alone never opens or creates state."""

    def __init__(
        self, *, config: PermitReplayWriterConfig,
        path_policy: PermitReplayPathPolicy,
        schema: PermitReplaySchemaExpectation | None = None,
    ) -> None:
        if config is None or path_policy is None:
            raise ValueError("validated configuration and path policy are required")
        self._config = config
        self._policy = path_policy
        self._schema = schema or PermitReplaySchemaExpectation()

    def _path_digest(self) -> str:
        return self._policy.identity_digest(self._config.database_path)

    def _report(
        self, status: PermitReplayWriteStatus, code: str,
        committed: bool = False,
    ) -> PermitReplayWriteValidationReport:
        findings = () if committed else (PermitReplayWriteFinding(code),)
        return PermitReplayWriteValidationReport(
            status, findings, self._path_digest(), committed,
        )

    def _connect(self) -> sqlite3.Connection:
        path = self._config.database_path
        violations = self._policy.validate(path)
        if violations:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, violations[0])
        if not path.is_file():
            raise _Denied(PermitReplayWriteStatus.UNAVAILABLE, "DATABASE_UNAVAILABLE")
        try:
            with path.open("rb") as stream:
                if stream.read(16) != b"SQLite format 3\x00":
                    raise _Denied(PermitReplayWriteStatus.INVALID, "INVALID_SQLITE_HEADER")
        except OSError as exc:
            raise _Denied(PermitReplayWriteStatus.UNAVAILABLE, "DATABASE_UNREADABLE") from exc
        uri = "file:" + quote(str(path), safe="/") + "?mode=rw"
        connection = sqlite3.connect(
            uri, uri=True, timeout=self._config.busy_timeout_seconds,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        connection.execute(
            f"PRAGMA busy_timeout={int(self._config.busy_timeout_seconds * 1000)}"
        )
        return connection

    def _validate_database(self, connection: sqlite3.Connection) -> list[dict[str, Any]]:
        if str(connection.execute("PRAGMA journal_mode").fetchone()[0]).lower() != "wal":
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "WAL_REQUIRED")
        if not bool(connection.execute("PRAGMA foreign_keys").fetchone()[0]):
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "FOREIGN_KEYS_INACTIVE")
        synchronous = int(connection.execute("PRAGMA synchronous").fetchone()[0])
        if synchronous < 2:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "SYNCHRONOUS_FULL_REQUIRED")
        integrity = str(connection.execute("PRAGMA quick_check").fetchone()[0])
        if integrity.lower() != "ok":
            raise _Denied(PermitReplayWriteStatus.INVALID, "INTEGRITY_CHECK_FAILED")
        objects = defaultdict(set)
        for row in connection.execute("SELECT type,name FROM sqlite_schema"):
            objects[str(row["type"])].add(str(row["name"]))
        if not set(self._schema.required_tables) <= objects["table"]:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "MISSING_TABLE")
        if not set(self._schema.required_indexes) <= objects["index"]:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "MISSING_INDEX")
        if not set(self._schema.required_triggers) <= objects["trigger"]:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "MISSING_TRIGGER")
        columns = {row[1] for row in connection.execute(
            "PRAGMA table_info(permit_use_events)"
        )}
        if not set(self._schema.event_fields) <= columns:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "MISSING_COLUMN")
        versions = connection.execute(
            "SELECT schema_version FROM permit_replay_meta"
        ).fetchall()
        if len(versions) != 1 or versions[0][0] != self._schema.schema_version:
            raise _Denied(PermitReplayWriteStatus.BLOCKED, "SCHEMA_VERSION_MISMATCH")
        fields = ",".join(self._schema.event_fields)
        rows = [dict(row) for row in connection.execute(
            f"SELECT {fields} FROM permit_use_events ORDER BY ledger_sequence,event_id"
        )]
        self._validate_chain(rows)
        return rows

    @staticmethod
    def _validate_chain(rows: list[dict[str, Any]]) -> None:
        previous, histories = GENESIS, defaultdict(list)
        for ordinal, row in enumerate(rows, 1):
            if row["ledger_sequence"] != ordinal or row["previous_event_hash"] != previous:
                raise _Denied(PermitReplayWriteStatus.INVALID, "INVALID_HASH_CHAIN")
            try:
                payload = json.loads(row["canonical_payload"])
            except (TypeError, ValueError):
                raise _Denied(PermitReplayWriteStatus.INVALID, "INVALID_PAYLOAD")
            if canonical_json_bytes(payload).decode() != row["canonical_payload"]:
                raise _Denied(PermitReplayWriteStatus.INVALID, "NON_CANONICAL_PAYLOAD")
            if _secret_bearing(payload):
                raise _Denied(PermitReplayWriteStatus.INVALID, "SECRET_BEARING_PAYLOAD")
            if sha256_digest(payload) != row["payload_digest"]:
                raise _Denied(PermitReplayWriteStatus.INVALID, "INVALID_PAYLOAD_DIGEST")
            if sha256_digest(_semantic(row, payload)) != row["event_hash"]:
                raise _Denied(PermitReplayWriteStatus.INVALID, "INVALID_EVENT_HASH")
            if row["event_type"] not in ("RESERVED", "CONSUMED", "FAILED_CLOSED"):
                raise _Denied(PermitReplayWriteStatus.INVALID, "UNKNOWN_EVENT_TYPE")
            if bool(row["production_authorized"]) or str(row["environment"]).lower() == "production":
                raise _Denied(PermitReplayWriteStatus.INVALID, "PRODUCTION_PROHIBITED")
            if "ubuntu" in str(row["target_identity"]).lower():
                raise _Denied(PermitReplayWriteStatus.INVALID, "UBUNTU_PROHIBITED")
            histories[row["permit_id"]].append(row)
            previous = row["event_hash"]
        for history in histories.values():
            types = [row["event_type"] for row in history]
            if types not in (["RESERVED"], ["RESERVED", "CONSUMED"],
                             ["RESERVED", "FAILED_CLOSED"]):
                raise _Denied(PermitReplayWriteStatus.INVALID, "INVALID_LIFECYCLE")
            bound = ("permit_digest", "activation_id", "activation_request_digest",
                     "target_identity", "environment")
            if any(len({row[field] for row in history}) != 1 for field in bound):
                raise _Denied(PermitReplayWriteStatus.INVALID, "LIFECYCLE_BINDING_CHANGED")

    @staticmethod
    def _request_dict(request: Any) -> dict[str, Any]:
        return {
            name: getattr(request, name)
            for name in request.__dataclass_fields__
            if name not in ("terminal_state",)
        }

    @staticmethod
    def _validate_common(request: Any) -> None:
        values = SQLitePermitReplayRegistry._request_dict(request)
        if any(value is None or value == "" for value in values.values()):
            raise _Denied(PermitReplayWriteStatus.DENIED, "INCOMPLETE_BINDING")
        if request.production_authorized or request.environment.lower() == "production":
            raise _Denied(PermitReplayWriteStatus.DENIED, "PRODUCTION_PROHIBITED")
        if "ubuntu" in request.target_identity.lower() or request.target_identity.lower().startswith("linux"):
            raise _Denied(PermitReplayWriteStatus.DENIED, "UBUNTU_PROHIBITED")
        if _secret_bearing(values):
            raise _Denied(PermitReplayWriteStatus.DENIED, "SECRET_BEARING_REQUEST")

    def _receipt(self, receipt_type: type, row: Mapping[str, Any], retry: bool):
        return build_receipt(
            receipt_type, event_id=row["event_id"],
            ledger_sequence=row["ledger_sequence"], permit_id=row["permit_id"],
            permit_digest=row["permit_digest"], activation_id=row["activation_id"],
            activation_request_digest=row["activation_request_digest"],
            event_type=row["event_type"], payload_digest=row["payload_digest"],
            previous_event_hash=row["previous_event_hash"], event_hash=row["event_hash"],
            database_path_identity_digest=self._path_digest(),
            transaction_committed=True, idempotent_retry=retry,
            event_at=row["event_at"], production_authorized=False,
        )

    def reserve(
        self, request: PermitReservationRequest, *, evaluated_at: str | None = None,
    ) -> tuple[PermitReplayWriteValidationReport, PermitReservationReceipt | None]:
        connection = None
        try:
            self._validate_common(request)
            now = datetime.fromisoformat(evaluated_at or request.reserved_at)
            if now >= datetime.fromisoformat(request.expires_at):
                raise _Denied(PermitReplayWriteStatus.DENIED, "PERMIT_EXPIRED")
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            rows = self._validate_database(connection)
            existing = [row for row in rows if row["permit_id"] == request.permit_id]
            payload = self._request_dict(request)
            if existing:
                row = existing[0]
                if row["event_type"] == "RESERVED" and json.loads(row["canonical_payload"]) == payload:
                    connection.rollback()
                    return self._report(PermitReplayWriteStatus.IDEMPOTENT, "", True), self._receipt(
                        PermitReservationReceipt, row, True
                    )
                raise _Denied(PermitReplayWriteStatus.DENIED, "RESERVATION_CONFLICT")
            row = self._insert(connection, rows, request, "RESERVED", request.reserved_at, payload,
                               request.operator_identity)
            connection.commit()
            return self._report(PermitReplayWriteStatus.COMMITTED, "", True), self._receipt(
                PermitReservationReceipt, row, False
            )
        except _Denied as exc:
            if connection is not None:
                connection.rollback()
            return self._report(exc.status, exc.code), None
        except sqlite3.Error:
            if connection is not None:
                connection.rollback()
            return self._report(PermitReplayWriteStatus.UNAVAILABLE, "SQLITE_WRITE_FAILURE"), None
        finally:
            if connection is not None:
                connection.close()

    def transition_terminal(
        self, request: PermitTerminalRequest,
    ) -> tuple[PermitReplayWriteValidationReport, PermitTerminalReceipt | None]:
        connection = None
        try:
            self._validate_common(request)
            if request.terminal_state not in (
                PermitTerminalState.CONSUMED, PermitTerminalState.FAILED_CLOSED
            ):
                raise _Denied(PermitReplayWriteStatus.DENIED, "INVALID_TERMINAL_STATE")
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            rows = self._validate_database(connection)
            history = [row for row in rows if row["permit_id"] == request.permit_id]
            if not history:
                raise _Denied(PermitReplayWriteStatus.DENIED, "TERMINAL_WITHOUT_RESERVATION")
            reservation = history[0]
            binding = {
                "permit_digest": request.permit_digest,
                "activation_id": request.activation_id,
                "activation_request_digest": request.activation_request_digest,
                "target_identity": request.target_identity,
                "environment": request.environment,
            }
            if any(reservation[key] != value for key, value in binding.items()):
                raise _Denied(PermitReplayWriteStatus.DENIED, "TERMINAL_BINDING_CONFLICT")
            payload = self._request_dict(request)
            payload["terminal_state"] = request.terminal_state.value
            if len(history) == 2:
                row = history[1]
                if row["event_type"] == request.terminal_state.value and json.loads(
                    row["canonical_payload"]
                ) == payload:
                    connection.rollback()
                    return self._report(PermitReplayWriteStatus.IDEMPOTENT, "", True), self._receipt(
                        PermitTerminalReceipt, row, True
                    )
                raise _Denied(PermitReplayWriteStatus.DENIED, "TERMINAL_CONFLICT")
            row = self._insert(
                connection, rows, request, request.terminal_state.value,
                request.event_at, payload, request.actor_identity,
            )
            connection.commit()
            return self._report(PermitReplayWriteStatus.COMMITTED, "", True), self._receipt(
                PermitTerminalReceipt, row, False
            )
        except _Denied as exc:
            if connection is not None:
                connection.rollback()
            return self._report(exc.status, exc.code), None
        except sqlite3.Error:
            if connection is not None:
                connection.rollback()
            return self._report(PermitReplayWriteStatus.UNAVAILABLE, "SQLITE_WRITE_FAILURE"), None
        finally:
            if connection is not None:
                connection.close()

    def consume(self, request: PermitTerminalRequest):
        if request.terminal_state is not PermitTerminalState.CONSUMED:
            return self._report(PermitReplayWriteStatus.DENIED, "INVALID_TERMINAL_STATE"), None
        return self.transition_terminal(request)

    def fail_closed(self, request: PermitTerminalRequest):
        if request.terminal_state is not PermitTerminalState.FAILED_CLOSED:
            return self._report(PermitReplayWriteStatus.DENIED, "INVALID_TERMINAL_STATE"), None
        return self.transition_terminal(request)

    def _insert(
        self, connection: sqlite3.Connection, rows: list[dict[str, Any]], request: Any,
        event_type: str, event_at: str, payload: dict[str, Any], actor: str,
    ) -> dict[str, Any]:
        canonical_payload = canonical_json_bytes(payload).decode()
        payload_digest = sha256_digest(payload)
        sequence = len(rows) + 1
        previous = rows[-1]["event_hash"] if rows else GENESIS
        event_id = "permit-event-" + sha256_digest({
            "permit_id": request.permit_id, "event_type": event_type,
            "payload_digest": payload_digest,
        })[7:39]
        row = {
            "ledger_sequence": sequence, "event_id": event_id,
            "permit_id": request.permit_id, "permit_digest": request.permit_digest,
            "activation_id": request.activation_id,
            "activation_request_digest": request.activation_request_digest,
            "event_type": event_type, "event_at": event_at, "actor_identity": actor,
            "target_identity": request.target_identity, "environment": request.environment,
            "canonical_payload": canonical_payload, "payload_digest": payload_digest,
            "previous_event_hash": previous, "production_authorized": 0,
        }
        row["event_hash"] = sha256_digest(_semantic(row, payload))
        fields = self._schema.event_fields
        connection.execute(
            f"INSERT INTO permit_use_events ({','.join(fields)}) VALUES "
            f"({','.join('?' for _ in fields)})",
            tuple(row[field] for field in fields),
        )
        stored = dict(connection.execute(
            f"SELECT {','.join(fields)} FROM permit_use_events WHERE event_id=?",
            (event_id,),
        ).fetchone())
        if stored != row:
            raise _Denied(PermitReplayWriteStatus.INVALID, "READ_BACK_MISMATCH")
        self._validate_chain(rows + [stored])
        return stored
