"""SQLite URI mode=ro permit/replay inspection with no mutation capability."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

from core.deployment.contracts import sha256_digest
from core.deployment.permit_replay_sqlite.models import (
    PermitReplayInspectionFinding,
    PermitReplayInspectionReport,
    PermitReplaySchemaExpectation,
    PermitReplayStatus,
    PermitUseEventType,
    PermitUseState,
)
from core.deployment.permit_replay_sqlite.path_policy import PermitReplayPathPolicy

GENESIS_PREVIOUS_HASH = "GENESIS"
_FORBIDDEN_KEYS = frozenset({
    "api_key", "access_token", "argv", "authorization", "authorization_header",
    "command", "cookie", "credential", "credentials", "environment_variables",
    "nonce", "password", "private_key", "raw_environment", "script", "secret",
    "shell", "token",
})


@dataclass(frozen=True, slots=True)
class PermitReplayStorageConfig:
    configured_path: Path
    timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "configured_path", Path(self.configured_path))
        if not 0 < self.timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be bounded")


def _secret_bearing(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_KEYS or any(marker in normalized for marker in (
                "password", "secret", "token", "credential", "cookie", "nonce",
                "private_key", "api_key",
            )):
                return True
            if _secret_bearing(child):
                return True
    elif isinstance(value, list):
        return any(_secret_bearing(child) for child in value)
    return False


def _event_semantic(row: Mapping[str, Any], payload: Any) -> dict[str, Any]:
    return {
        "ledger_sequence": row["ledger_sequence"],
        "event_id": row["event_id"],
        "permit_id": row["permit_id"],
        "permit_digest": row["permit_digest"],
        "activation_id": row["activation_id"],
        "activation_request_digest": row["activation_request_digest"],
        "event_type": row["event_type"],
        "event_at": row["event_at"],
        "actor_identity": row["actor_identity"],
        "target_identity": row["target_identity"],
        "environment": row["environment"],
        "canonical_payload": payload,
        "payload_digest": row["payload_digest"],
        "previous_event_hash": row["previous_event_hash"],
        "production_authorized": bool(row["production_authorized"]),
    }


class PermitReplayReadOnlyInspector:
    def __init__(
        self, *, config: PermitReplayStorageConfig,
        path_policy: PermitReplayPathPolicy,
        schema: PermitReplaySchemaExpectation | None = None,
    ) -> None:
        self._config = config
        self._policy = path_policy
        self._schema = schema or PermitReplaySchemaExpectation()

    def _report(
        self, *, inspected_at: str, status: PermitReplayStatus, exists: bool,
        findings: list[PermitReplayInspectionFinding], **values: Any,
    ) -> PermitReplayInspectionReport:
        defaults: dict[str, Any] = {
            "status": status,
            "database_path_identity_digest":
                self._policy.identity_digest(self._config.configured_path),
            "file_exists": exists, "connection_mode": "mode=ro", "query_only": False,
            "schema_version": None, "schema_findings": tuple(findings),
            "event_count": 0, "permit_count": 0, "unused_count": 0,
            "reserved_count": 0, "consumed_count": 0, "failed_closed_count": 0,
            "invalid_count": 0, "permit_states": (), "replay_violations": 0,
            "chain_result": "NOT_RUN", "privacy_result": "NOT_RUN",
            "production_violations": 0,
            "restrictions": (
                "READ_ONLY", "NO_RESERVATION", "NO_CONSUMPTION", "NO_DDL",
                "NO_MIGRATION", "NO_REPAIR", "NO_JOURNAL_CHANGE",
                "NO_PRODUCTION", "EXPLICIT_PATH_REQUIRED",
            ),
            "inspected_at": inspected_at,
        }
        defaults.update(values)
        return PermitReplayInspectionReport.build(**defaults)

    @staticmethod
    def _finding(
        findings: list[PermitReplayInspectionFinding], code: str, detail: str,
        permit_id: str | None = None,
    ) -> None:
        identity = sha256_digest({"permit_id": permit_id}) if permit_id else None
        findings.append(PermitReplayInspectionFinding(
            code, "ERROR", detail, identity,
        ))

    def inspect(self, *, inspected_at: str) -> PermitReplayInspectionReport:
        path = self._config.configured_path
        violations = self._policy.validate(path)
        if violations:
            return self._report(
                inspected_at=inspected_at, status=PermitReplayStatus.BLOCKED,
                exists=path.is_file(),
                findings=[PermitReplayInspectionFinding(
                    code, "ERROR", "configured path rejected",
                ) for code in violations],
            )
        if not path.is_file():
            return self._report(
                inspected_at=inspected_at, status=PermitReplayStatus.UNAVAILABLE,
                exists=False, findings=[PermitReplayInspectionFinding(
                    "DATABASE_UNAVAILABLE", "ERROR",
                    "configured database is unavailable",
                )],
            )
        try:
            with path.open("rb") as stream:
                if stream.read(16) != b"SQLite format 3\x00":
                    return self._report(
                        inspected_at=inspected_at, status=PermitReplayStatus.INVALID,
                        exists=True, findings=[PermitReplayInspectionFinding(
                            "INVALID_SQLITE_HEADER", "ERROR", "SQLite header is invalid",
                        )],
                    )
        except OSError:
            return self._report(
                inspected_at=inspected_at, status=PermitReplayStatus.UNAVAILABLE,
                exists=True, findings=[PermitReplayInspectionFinding(
                    "DATABASE_UNREADABLE", "ERROR", "database is unreadable",
                )],
            )
        findings: list[PermitReplayInspectionFinding] = []
        rows: list[dict[str, Any]] = []
        schema_version: str | None = None
        query_only = False
        try:
            uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
            connection = sqlite3.connect(
                uri, uri=True, timeout=self._config.timeout_seconds,
                isolation_level=None,
            )
            connection.row_factory = sqlite3.Row
            try:
                connection.execute("PRAGMA query_only=ON")
                query_only = bool(connection.execute("PRAGMA query_only").fetchone()[0])
                integrity = str(connection.execute("PRAGMA quick_check").fetchone()[0])
                if integrity.lower() != "ok":
                    self._finding(findings, "INTEGRITY_CHECK_FAILED",
                                  "SQLite quick check failed")
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table'"
                )}
                indexes = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type='index'"
                )}
                triggers = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_schema WHERE type='trigger'"
                )}
                for table in self._schema.required_tables:
                    if table not in tables:
                        self._finding(findings, "MISSING_TABLE",
                                      f"required table missing: {table}")
                for index in self._schema.required_indexes:
                    if index not in indexes:
                        self._finding(findings, "MISSING_INDEX",
                                      f"required index missing: {index}")
                for trigger in self._schema.required_triggers:
                    if trigger not in triggers:
                        self._finding(findings, "MISSING_IMMUTABILITY_TRIGGER",
                                      f"required trigger missing: {trigger}")
                if "permit_replay_meta" in tables:
                    try:
                        meta = connection.execute(
                            "SELECT schema_version FROM permit_replay_meta LIMIT 1"
                        ).fetchone()
                        schema_version = str(meta[0]) if meta else None
                    except sqlite3.Error:
                        self._finding(findings, "UNREADABLE_SCHEMA_VERSION",
                                      "schema metadata is unreadable")
                if schema_version != self._schema.schema_version:
                    self._finding(findings, "SCHEMA_VERSION_MISMATCH",
                                  "schema version does not match expectation")
                if "permit_use_events" in tables:
                    columns = {row[1] for row in connection.execute(
                        "PRAGMA table_info(permit_use_events)"
                    )}
                    for field in self._schema.event_fields:
                        if field not in columns:
                            self._finding(findings, "MISSING_COLUMN",
                                          f"required event field missing: {field}")
                    if set(self._schema.event_fields).issubset(columns):
                        selection = ",".join(self._schema.event_fields)
                        rows = [dict(row) for row in connection.execute(
                            f"SELECT {selection} FROM permit_use_events "
                            "ORDER BY ledger_sequence,event_id"
                        )]
            finally:
                connection.close()
        except sqlite3.Error:
            return self._report(
                inspected_at=inspected_at, status=PermitReplayStatus.INVALID,
                exists=True, findings=[PermitReplayInspectionFinding(
                    "SQLITE_READ_FAILURE", "ERROR", "SQLite inspection failed",
                )],
            )
        if not query_only:
            self._finding(findings, "QUERY_ONLY_INACTIVE", "query_only is inactive")

        sequences = [row["ledger_sequence"] for row in rows]
        event_ids = [row["event_id"] for row in rows]
        if len(event_ids) != len(set(event_ids)):
            self._finding(findings, "DUPLICATE_EVENT_ID", "duplicate event ID detected")
        if len(sequences) != len(set(sequences)):
            self._finding(findings, "DUPLICATE_SEQUENCE", "duplicate sequence detected")
        if sequences and sorted(sequences) != list(range(1, max(sequences) + 1)):
            self._finding(findings, "MISSING_SEQUENCE_GAP", "sequence is not contiguous")

        histories: dict[str, list[dict[str, Any]]] = defaultdict(list)
        invalid_permits: set[str] = set()
        previous = GENESIS_PREVIOUS_HASH
        privacy_violations = production_violations = chain_violations = 0
        for ordinal, row in enumerate(rows, 1):
            permit_id = str(row["permit_id"])
            histories[permit_id].append(row)
            payload: Any = None
            try:
                payload = json.loads(str(row["canonical_payload"]))
            except (TypeError, ValueError, json.JSONDecodeError):
                self._finding(findings, "INVALID_CANONICAL_PAYLOAD",
                              "canonical payload is invalid", permit_id)
                invalid_permits.add(permit_id)
                privacy_violations += 1
            if payload is not None:
                if sha256_digest(payload) != row["payload_digest"]:
                    self._finding(findings, "INVALID_PAYLOAD_DIGEST",
                                  "payload digest mismatch", permit_id)
                    self._finding(findings, "MODIFIED_CANONICAL_PAYLOAD",
                                  "canonical payload was modified", permit_id)
                    invalid_permits.add(permit_id)
                if _secret_bearing(payload):
                    self._finding(findings, "SECRET_BEARING_PAYLOAD",
                                  "payload violates privacy policy", permit_id)
                    invalid_permits.add(permit_id)
                    privacy_violations += 1
                expected_hash = sha256_digest(_event_semantic(row, payload))
                if expected_hash != row["event_hash"]:
                    self._finding(findings, "INVALID_EVENT_HASH",
                                  "event hash mismatch", permit_id)
                    invalid_permits.add(permit_id)
                    chain_violations += 1
            if row["ledger_sequence"] != ordinal:
                self._finding(findings, "REORDERED_EVENT",
                              "event order does not match ledger sequence", permit_id)
                invalid_permits.add(permit_id)
                chain_violations += 1
            if row["previous_event_hash"] != previous:
                self._finding(findings, "BROKEN_PREVIOUS_EVENT_HASH",
                              "previous-event hash is broken", permit_id)
                invalid_permits.add(permit_id)
                chain_violations += 1
            previous = str(row["event_hash"])
            try:
                PermitUseEventType(str(row["event_type"]))
            except ValueError:
                self._finding(findings, "UNKNOWN_EVENT_TYPE",
                              "unknown permit event type", permit_id)
                invalid_permits.add(permit_id)
            if bool(row["production_authorized"]):
                self._finding(findings, "PRODUCTION_AUTHORIZED_VIOLATION",
                              "production authorization is prohibited", permit_id)
                invalid_permits.add(permit_id)
                production_violations += 1
            if str(row["environment"]).lower() == "production":
                self._finding(findings, "PRODUCTION_ENVIRONMENT",
                              "production environment is prohibited", permit_id)
                invalid_permits.add(permit_id)
                production_violations += 1
            target = str(row["target_identity"]).lower()
            if "ubuntu" in target or target.startswith("linux"):
                self._finding(findings, "UBUNTU_TARGET_OWNERSHIP",
                              "Ubuntu cannot own permit/replay state", permit_id)
                invalid_permits.add(permit_id)

        states: list[tuple[str, PermitUseState]] = []
        replay_codes = {
            "DUPLICATE_EVENT_ID", "DUPLICATE_SEQUENCE", "MISSING_SEQUENCE_GAP",
            "DUPLICATE_RESERVATION", "TERMINAL_WITHOUT_RESERVATION",
            "MULTIPLE_TERMINAL_EVENTS", "CONSUMED_AFTER_FAILED_CLOSED",
            "FAILED_CLOSED_AFTER_CONSUMED", "UNKNOWN_EVENT_TYPE",
            "ACTIVATION_ID_MISMATCH", "PERMIT_DIGEST_MISMATCH", "REORDERED_EVENT",
            "BROKEN_PREVIOUS_EVENT_HASH", "INVALID_EVENT_HASH",
        }
        for permit_id, history in sorted(histories.items()):
            types = [str(row["event_type"]) for row in history]
            reservations = types.count(PermitUseEventType.RESERVED.value)
            terminals = [value for value in types if value in (
                PermitUseEventType.CONSUMED.value,
                PermitUseEventType.FAILED_CLOSED.value,
            )]
            if reservations > 1:
                self._finding(findings, "DUPLICATE_RESERVATION",
                              "multiple reservation events", permit_id)
                invalid_permits.add(permit_id)
            if terminals and not reservations:
                self._finding(findings, "TERMINAL_WITHOUT_RESERVATION",
                              "terminal event lacks reservation", permit_id)
                invalid_permits.add(permit_id)
            if len(terminals) > 1:
                self._finding(findings, "MULTIPLE_TERMINAL_EVENTS",
                              "multiple terminal events", permit_id)
                invalid_permits.add(permit_id)
            if "FAILED_CLOSED" in types and types.index("FAILED_CLOSED") < len(types) - 1:
                if "CONSUMED" in types[types.index("FAILED_CLOSED") + 1:]:
                    self._finding(findings, "CONSUMED_AFTER_FAILED_CLOSED",
                                  "consumed follows failed-closed", permit_id)
                    invalid_permits.add(permit_id)
            if "CONSUMED" in types and types.index("CONSUMED") < len(types) - 1:
                if "FAILED_CLOSED" in types[types.index("CONSUMED") + 1:]:
                    self._finding(findings, "FAILED_CLOSED_AFTER_CONSUMED",
                                  "failed-closed follows consumed", permit_id)
                    invalid_permits.add(permit_id)
            if len({str(row["activation_id"]) for row in history}) > 1:
                self._finding(findings, "ACTIVATION_ID_MISMATCH",
                              "activation identity changed", permit_id)
                invalid_permits.add(permit_id)
            if len({str(row["permit_digest"]) for row in history}) > 1:
                self._finding(findings, "PERMIT_DIGEST_MISMATCH",
                              "permit digest changed", permit_id)
                invalid_permits.add(permit_id)
            if permit_id in invalid_permits:
                state = PermitUseState.INVALID
            elif terminals == ["CONSUMED"]:
                state = PermitUseState.CONSUMED
            elif terminals == ["FAILED_CLOSED"]:
                state = PermitUseState.FAILED_CLOSED
            elif reservations == 1:
                state = PermitUseState.RESERVED
            else:
                state = PermitUseState.UNUSED
            states.append((sha256_digest({"permit_id": permit_id}), state))

        counts = {state: 0 for state in PermitUseState}
        for _, state in states:
            counts[state] += 1
        replay_violations = sum(
            1 for finding in findings if finding.code in replay_codes
        )
        status = PermitReplayStatus.HEALTHY if not findings else PermitReplayStatus.INVALID
        return self._report(
            inspected_at=inspected_at, status=status, exists=True, findings=findings,
            query_only=query_only, schema_version=schema_version,
            event_count=len(rows), permit_count=len(histories),
            unused_count=counts[PermitUseState.UNUSED],
            reserved_count=counts[PermitUseState.RESERVED],
            consumed_count=counts[PermitUseState.CONSUMED],
            failed_closed_count=counts[PermitUseState.FAILED_CLOSED],
            invalid_count=counts[PermitUseState.INVALID], permit_states=tuple(states),
            replay_violations=replay_violations,
            chain_result="VALID" if not chain_violations else "INVALID",
            privacy_result="VALID" if not privacy_violations else "INVALID",
            production_violations=production_violations,
        )
