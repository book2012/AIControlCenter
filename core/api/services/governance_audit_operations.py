"""Read-only governance audit operations presentation."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from core.api.dependencies.audit import DATABASE_FILENAME
from core.governance.operations.adapters.sqlite import (
    SQLiteOperationsEventRepository,
    TABLE_NAME,
)
from core.governance.operations.application.projection import (
    project_operation,
)
from core.governance.operations.domain.events import (
    Operation,
)

SCHEMA_VERSION = "1.0.0"
SCHEDULE_OWNER = "AIControlCenter Scheduler"
DATABASE_OVERRIDE_ENV = (
    "AICONTROLCENTER_GOVERNANCE_AUDIT_DB"
)

ENUM_VALUE_FIELDS = frozenset(
    {
        "freshness_state",
        "latest_state",
        "overall_health",
    }
)
SIGNAL_ENUM_VALUE_FIELDS = frozenset(
    {
        "condition",
        "severity",
    }
)


def resolve_governance_audit_database_path() -> Path:
    override = os.environ.get(DATABASE_OVERRIDE_ENV)

    if override:
        return Path(override).expanduser()

    return (
        Path.home()
        / "Library"
        / "Application Support"
        / "AIControlCenter"
        / "data"
        / DATABASE_FILENAME
    )


def _utc_time(
    generated_at: datetime | None,
) -> datetime:
    now = generated_at or datetime.now(timezone.utc)

    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError(
            "generated_at must be timezone-aware"
        )

    return now.astimezone(timezone.utc)


def _lowercase_enum_value(
    value: object,
) -> object:
    if isinstance(value, str):
        return value.lower()

    return value


def _normalize_projection_payload(
    payload: dict[str, object],
) -> dict[str, object]:
    normalized = dict(payload)

    for field in ENUM_VALUE_FIELDS:
        normalized[field] = _lowercase_enum_value(
            normalized.get(field)
        )

    signals = normalized.get("severity_signals")

    if isinstance(signals, list):
        normalized_signals = []

        for signal in signals:
            if not isinstance(signal, dict):
                normalized_signals.append(signal)
                continue

            normalized_signal = dict(signal)

            for field in SIGNAL_ENUM_VALUE_FIELDS:
                normalized_signal[field] = (
                    _lowercase_enum_value(
                        normalized_signal.get(field)
                    )
                )

            normalized_signals.append(
                normalized_signal
            )

        normalized["severity_signals"] = (
            normalized_signals
        )

    return normalized


def _unknown_operation(
    operation: Operation,
    generated_at: datetime,
    reason: str,
) -> dict[str, object]:
    return {
        "availability": "unavailable",
        "backup_verification": None,
        "duration_ms": None,
        "freshness_state": "unknown",
        "generated_at": generated_at.isoformat(),
        "last_failure_at": None,
        "last_missed_at": None,
        "last_scheduled_at": None,
        "last_started_at": None,
        "last_success_at": None,
        "latest_run_id": None,
        "latest_state": None,
        "missed_run": False,
        "operation": operation.value,
        "overall_health": "unknown",
        "schedule_owner": SCHEDULE_OWNER,
        "schema_version": SCHEMA_VERSION,
        "scheduling_latency_ms": None,
        "severity_signals": [],
        "unavailable_reason": reason,
    }


def _unavailable_payload(
    generated_at: datetime,
    reason: str,
) -> dict[str, object]:
    return {
        "generated_at": generated_at.isoformat(),
        "operations": [
            _unknown_operation(
                operation,
                generated_at,
                reason,
            )
            for operation in (
                Operation.GOVERNANCE_AUDIT_SNAPSHOT,
                Operation.SQLITE_ONLINE_BACKUP_VERIFICATION,
            )
        ],
        "overall_health": "unknown",
        "production_database_migrated": False,
        "read_only": True,
        "schedule_owner": SCHEDULE_OWNER,
        "schema_version": SCHEMA_VERSION,
        "write_actions": [],
    }


def _operations_table_exists(
    database_path: Path,
) -> bool:
    if not database_path.is_file():
        return False

    uri = (
        "file:"
        + quote(
            str(database_path),
            safe="/",
        )
        + "?mode=ro"
    )

    connection = sqlite3.connect(
        uri,
        uri=True,
        timeout=1.0,
    )

    try:
        connection.execute(
            "PRAGMA query_only = ON"
        )

        return (
            connection.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
                LIMIT 1
                """,
                (TABLE_NAME,),
            ).fetchone()
            is not None
        )
    finally:
        connection.close()


def _overall_health(
    operations: list[dict[str, object]],
) -> str:
    values = {
        str(
            operation.get(
                "overall_health",
                "unknown",
            )
        ).lower()
        for operation in operations
    }

    for candidate in (
        "unhealthy",
        "degraded",
        "unknown",
        "healthy",
    ):
        if candidate in values:
            return candidate

    return "unknown"


def build_governance_audit_operations_payload(
    database_path: str | Path | None = None,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    now = _utc_time(generated_at)
    resolved_path = (
        Path(database_path)
        if database_path is not None
        else resolve_governance_audit_database_path()
    ).expanduser()

    if not _operations_table_exists(resolved_path):
        reason = (
            "database-not-found"
            if not resolved_path.is_file()
            else "operations-schema-not-migrated"
        )

        return _unavailable_payload(now, reason)

    repository_adapter = (
        SQLiteOperationsEventRepository(
            resolved_path
        )
    )

    operations = [
        _normalize_projection_payload(
            project_operation(
                repository_adapter,
                operation,
                now,
            ).to_dict()
        )
        for operation in (
            Operation.GOVERNANCE_AUDIT_SNAPSHOT,
            Operation.SQLITE_ONLINE_BACKUP_VERIFICATION,
        )
    ]

    for operation in operations:
        operation["availability"] = "available"
        operation["unavailable_reason"] = None

    return {
        "generated_at": now.isoformat(),
        "operations": operations,
        "overall_health": _overall_health(
            operations
        ),
        "production_database_migrated": True,
        "read_only": True,
        "schedule_owner": SCHEDULE_OWNER,
        "schema_version": SCHEMA_VERSION,
        "write_actions": [],
    }


def build_governance_audit_operations_dashboard_payload(
    database_path: str | Path | None = None,
    *,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    now = _utc_time(generated_at)

    try:
        return build_governance_audit_operations_payload(
            database_path,
            generated_at=now,
        )
    except Exception:
        return _unavailable_payload(
            now,
            "presentation-error",
        )
