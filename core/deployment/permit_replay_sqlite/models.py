"""Immutable contracts for read-only durable permit/replay inspection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from core.deployment.contracts import canonical_json_bytes, sha256_digest


class PermitReplayStatus(StrEnum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"


class PermitUseEventType(StrEnum):
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    FAILED_CLOSED = "FAILED_CLOSED"


class PermitUseState(StrEnum):
    UNUSED = "UNUSED"
    RESERVED = "RESERVED"
    CONSUMED = "CONSUMED"
    FAILED_CLOSED = "FAILED_CLOSED"
    INVALID = "INVALID"


@dataclass(frozen=True, slots=True, order=True)
class PermitReplayInspectionFinding:
    code: str
    severity: str
    detail: str
    permit_identity_digest: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "detail": self.detail,
            "permit_identity_digest": self.permit_identity_digest,
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class PermitReplaySchemaExpectation:
    schema_version: str = "dpl/permit-replay-sqlite/v1"
    required_tables: tuple[str, ...] = ("permit_replay_meta", "permit_use_events")
    required_indexes: tuple[str, ...] = (
        "ux_permit_use_events_event_id",
        "ux_permit_use_events_ledger_sequence",
        "ux_permit_use_events_one_reservation",
        "ux_permit_use_events_one_terminal",
    )
    required_triggers: tuple[str, ...] = (
        "trg_permit_use_events_no_update",
        "trg_permit_use_events_no_delete",
    )
    event_fields: tuple[str, ...] = (
        "ledger_sequence", "event_id", "permit_id", "permit_digest",
        "activation_id", "activation_request_digest", "event_type", "event_at",
        "actor_identity", "target_identity", "environment", "canonical_payload",
        "payload_digest", "previous_event_hash", "event_hash",
        "production_authorized",
    )
    allowed_event_types: tuple[str, ...] = (
        "RESERVED", "CONSUMED", "FAILED_CLOSED",
    )
    immutable_events: bool = True
    append_only: bool = True

    def schema_sql_for_documentation(self) -> str:
        """Return inert future DDL. Runtime inspection never executes it."""
        fields = (
            "ledger_sequence INTEGER NOT NULL, event_id TEXT NOT NULL, "
            "permit_id TEXT NOT NULL, permit_digest TEXT NOT NULL, "
            "activation_id TEXT NOT NULL, activation_request_digest TEXT NOT NULL, "
            "event_type TEXT NOT NULL CHECK(event_type IN "
            "('RESERVED','CONSUMED','FAILED_CLOSED')), event_at TEXT NOT NULL, "
            "actor_identity TEXT NOT NULL, target_identity TEXT NOT NULL, "
            "environment TEXT NOT NULL CHECK(environment <> 'production'), "
            "canonical_payload TEXT NOT NULL, payload_digest TEXT NOT NULL, "
            "previous_event_hash TEXT NOT NULL, event_hash TEXT NOT NULL, "
            "production_authorized INTEGER NOT NULL CHECK(production_authorized = 0)"
        )
        return (
            "CREATE TABLE permit_replay_meta (schema_version TEXT NOT NULL);\n"
            f"CREATE TABLE permit_use_events ({fields});\n"
            "CREATE UNIQUE INDEX ux_permit_use_events_event_id "
            "ON permit_use_events(event_id);\n"
            "CREATE UNIQUE INDEX ux_permit_use_events_ledger_sequence "
            "ON permit_use_events(ledger_sequence);\n"
            "CREATE UNIQUE INDEX ux_permit_use_events_one_reservation "
            "ON permit_use_events(permit_id) WHERE event_type='RESERVED';\n"
            "CREATE UNIQUE INDEX ux_permit_use_events_one_terminal "
            "ON permit_use_events(permit_id) "
            "WHERE event_type IN ('CONSUMED','FAILED_CLOSED');\n"
            "CREATE TRIGGER trg_permit_use_events_no_update BEFORE UPDATE "
            "ON permit_use_events BEGIN SELECT RAISE(ABORT,'immutable'); END;\n"
            "CREATE TRIGGER trg_permit_use_events_no_delete BEFORE DELETE "
            "ON permit_use_events BEGIN SELECT RAISE(ABORT,'immutable'); END;"
        )


@dataclass(frozen=True, slots=True)
class PermitReplayInspectionReport:
    status: PermitReplayStatus
    database_path_identity_digest: str
    file_exists: bool
    connection_mode: str
    query_only: bool
    schema_version: str | None
    schema_findings: tuple[PermitReplayInspectionFinding, ...]
    event_count: int
    permit_count: int
    unused_count: int
    reserved_count: int
    consumed_count: int
    failed_closed_count: int
    invalid_count: int
    permit_states: tuple[tuple[str, PermitUseState], ...]
    replay_violations: int
    chain_result: str
    privacy_result: str
    production_violations: int
    restrictions: tuple[str, ...]
    inspected_at: str
    report_id: str
    report_digest: str
    writes_performed: int = 0
    reservations_performed: int = 0
    consumptions_performed: int = 0
    migrations_performed: int = 0
    repairs_performed: int = 0
    production_authorized: bool = False

    def _content(self) -> dict[str, Any]:
        return {
            "chain_result": self.chain_result,
            "connection_mode": self.connection_mode,
            "consumed_count": self.consumed_count,
            "consumptions_performed": self.consumptions_performed,
            "database_path_identity_digest": self.database_path_identity_digest,
            "event_count": self.event_count,
            "failed_closed_count": self.failed_closed_count,
            "file_exists": self.file_exists,
            "inspected_at": self.inspected_at,
            "invalid_count": self.invalid_count,
            "migrations_performed": self.migrations_performed,
            "permit_count": self.permit_count,
            "permit_states": [
                {"permit_identity_digest": identity, "state": state.value}
                for identity, state in self.permit_states
            ],
            "privacy_result": self.privacy_result,
            "production_authorized": self.production_authorized,
            "production_violations": self.production_violations,
            "query_only": self.query_only,
            "repairs_performed": self.repairs_performed,
            "replay_violations": self.replay_violations,
            "reservations_performed": self.reservations_performed,
            "reserved_count": self.reserved_count,
            "restrictions": list(self.restrictions),
            "schema_findings": [item.as_dict() for item in self.schema_findings],
            "schema_version": self.schema_version,
            "status": self.status.value,
            "unused_count": self.unused_count,
            "writes_performed": self.writes_performed,
        }

    def as_dict(self) -> dict[str, Any]:
        return {**self._content(), "report_digest": self.report_digest,
                "report_id": self.report_id}

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode("utf-8")

    @classmethod
    def build(cls, **values: Any) -> "PermitReplayInspectionReport":
        content = dict(values)
        content["schema_findings"] = tuple(sorted(content["schema_findings"]))
        content["permit_states"] = tuple(sorted(content["permit_states"]))
        digestable = {
            **content,
            "schema_findings": [item.as_dict() for item in content["schema_findings"]],
            "permit_states": [
                (identity, state.value) for identity, state in content["permit_states"]
            ],
            "status": content["status"].value,
        }
        digest = sha256_digest(digestable)
        return cls(**content, report_id="permit-replay-inspection-" + digest[7:39],
                   report_digest=digest)
