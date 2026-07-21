"""Deterministic execution event SQLite serialization."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Any
from uuid import UUID

from ...domain.events import (
    ErrorInfo,
    EventType,
    ExecutionEvent,
    Operation,
)


class PayloadIntegrityError(ValueError):
    """Raised when stored event payload integrity fails."""


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        allow_nan=False,
    )


def event_payload(
    event: ExecutionEvent,
) -> dict[str, Any]:
    error_json = None

    if event.error is not None:
        error_json = canonical_json(
            {
                "code": event.error.code,
                "details": dict(event.error.details),
                "message": event.error.message,
            }
        )

    return {
        "attempt": event.attempt,
        "duration_ms": event.duration_ms,
        "error_json": error_json,
        "event_id": str(event.event_id),
        "event_type": event.event_type.value,
        "evidence_json": canonical_json(
            dict(event.evidence)
        ),
        "occurred_at": event.occurred_at.isoformat(),
        "operation": event.operation.value,
        "producer": event.producer,
        "recorded_at": event.recorded_at.isoformat(),
        "run_id": str(event.run_id),
        "scheduled_for": (
            event.scheduled_for.isoformat()
        ),
        "schema_version": event.schema_version,
        "scheduling_latency_ms": (
            event.scheduling_latency_ms
        ),
    }


def event_payload_sha256(
    event: ExecutionEvent,
) -> str:
    encoded = canonical_json(
        event_payload(event)
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def event_to_parameters(
    event: ExecutionEvent,
) -> tuple[object, ...]:
    payload = event_payload(event)

    return (
        payload["event_id"],
        payload["run_id"],
        payload["operation"],
        payload["event_type"],
        payload["scheduled_for"],
        payload["occurred_at"],
        payload["recorded_at"],
        payload["attempt"],
        payload["producer"],
        payload["schema_version"],
        payload["duration_ms"],
        payload["scheduling_latency_ms"],
        payload["error_json"],
        payload["evidence_json"],
        event_payload_sha256(event),
    )


def event_from_row(
    row: sqlite3.Row,
) -> ExecutionEvent:
    error = None

    if row["error_json"] is not None:
        parsed_error = json.loads(row["error_json"])
        error = ErrorInfo(
            code=parsed_error["code"],
            message=parsed_error["message"],
            details=parsed_error.get("details", {}),
        )

    event = ExecutionEvent(
        event_id=UUID(row["event_id"]),
        run_id=UUID(row["run_id"]),
        operation=Operation(row["operation"]),
        event_type=EventType(row["event_type"]),
        scheduled_for=datetime.fromisoformat(
            row["scheduled_for"]
        ),
        occurred_at=datetime.fromisoformat(
            row["occurred_at"]
        ),
        recorded_at=datetime.fromisoformat(
            row["recorded_at"]
        ),
        attempt=row["attempt"],
        producer=row["producer"],
        schema_version=row["schema_version"],
        duration_ms=row["duration_ms"],
        scheduling_latency_ms=(
            row["scheduling_latency_ms"]
        ),
        error=error,
        evidence=json.loads(row["evidence_json"]),
    )

    if (
        event_payload_sha256(event)
        != row["payload_sha256"]
    ):
        raise PayloadIntegrityError(
            "stored operation event payload checksum "
            "does not match"
        )

    return event
