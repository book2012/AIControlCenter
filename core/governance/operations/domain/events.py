"""Immutable governance audit operation events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4

CONTROL_PLANE_PRODUCER = "AIControlCenter"
SCHEMA_VERSION = "1.0.0"


class DomainValidationError(ValueError):
    """Raised when an operations domain value is invalid."""


class Operation(str, Enum):
    GOVERNANCE_AUDIT_SNAPSHOT = (
        "governance_audit_snapshot"
    )
    SQLITE_ONLINE_BACKUP_VERIFICATION = (
        "sqlite_online_backup_verification"
    )


class EventType(str, Enum):
    RUN_SCHEDULED = "run_scheduled"
    RUN_STARTED = "run_started"
    RUN_SUCCEEDED = "run_succeeded"
    RUN_FAILED = "run_failed"
    RUN_MISSED = "run_missed"


TERMINAL_EVENT_TYPES = frozenset(
    {
        EventType.RUN_SUCCEEDED,
        EventType.RUN_FAILED,
        EventType.RUN_MISSED,
    }
)


def require_utc(
    value: datetime,
    field_name: str,
) -> datetime:
    if not isinstance(value, datetime):
        raise DomainValidationError(
            f"{field_name} must be a datetime"
        )

    if (
        value.tzinfo is None
        or value.utcoffset() != timedelta(0)
    ):
        raise DomainValidationError(
            f"{field_name} must be timezone-aware UTC"
        )

    return value.astimezone(timezone.utc)


def elapsed_milliseconds(
    start: datetime,
    end: datetime,
    *,
    field_name: str,
) -> int:
    normalized_start = require_utc(start, "start")
    normalized_end = require_utc(end, "end")
    milliseconds = int(
        (
            normalized_end - normalized_start
        ).total_seconds()
        * 1000
    )

    if milliseconds < 0:
        raise DomainValidationError(
            f"{field_name} must be non-negative"
        )

    return milliseconds


def immutable_mapping(
    value: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    return MappingProxyType(dict(value or {}))


@dataclass(frozen=True, slots=True)
class ErrorInfo:
    code: str
    message: str
    details: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise DomainValidationError(
                "error code must not be empty"
            )

        if not self.message.strip():
            raise DomainValidationError(
                "error message must not be empty"
            )

        object.__setattr__(
            self,
            "details",
            immutable_mapping(self.details),
        )


@dataclass(frozen=True, slots=True)
class ExecutionEvent:
    event_id: UUID
    run_id: UUID
    operation: Operation
    event_type: EventType
    scheduled_for: datetime
    occurred_at: datetime
    recorded_at: datetime
    attempt: int = 1
    producer: str = CONTROL_PLANE_PRODUCER
    schema_version: str = SCHEMA_VERSION
    evidence: Mapping[str, Any] = field(
        default_factory=dict
    )
    duration_ms: int | None = None
    scheduling_latency_ms: int | None = None
    error: ErrorInfo | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, UUID):
            raise DomainValidationError(
                "event_id must be UUID"
            )
        if not isinstance(self.run_id, UUID):
            raise DomainValidationError(
                "run_id must be UUID"
            )
        if not isinstance(self.operation, Operation):
            raise DomainValidationError(
                "operation must be Operation"
            )
        if not isinstance(self.event_type, EventType):
            raise DomainValidationError(
                "event_type must be EventType"
            )
        if self.attempt < 1:
            raise DomainValidationError(
                "attempt must be at least one"
            )
        if self.producer != CONTROL_PLANE_PRODUCER:
            raise DomainValidationError(
                "producer must be AIControlCenter"
            )
        if self.schema_version != SCHEMA_VERSION:
            raise DomainValidationError(
                "unsupported schema version"
            )

        scheduled_for = require_utc(
            self.scheduled_for,
            "scheduled_for",
        )
        occurred_at = require_utc(
            self.occurred_at,
            "occurred_at",
        )
        recorded_at = require_utc(
            self.recorded_at,
            "recorded_at",
        )

        if recorded_at < occurred_at:
            raise DomainValidationError(
                "recorded_at must not precede occurred_at"
            )

        if (
            self.duration_ms is not None
            and self.duration_ms < 0
        ):
            raise DomainValidationError(
                "duration_ms must be non-negative"
            )

        if (
            self.scheduling_latency_ms is not None
            and self.scheduling_latency_ms < 0
        ):
            raise DomainValidationError(
                "scheduling_latency_ms must be non-negative"
            )

        object.__setattr__(
            self,
            "scheduled_for",
            scheduled_for,
        )
        object.__setattr__(
            self,
            "occurred_at",
            occurred_at,
        )
        object.__setattr__(
            self,
            "recorded_at",
            recorded_at,
        )
        object.__setattr__(
            self,
            "evidence",
            immutable_mapping(self.evidence),
        )

        if self.event_type is EventType.RUN_SCHEDULED:
            if any(
                value is not None
                for value in (
                    self.duration_ms,
                    self.scheduling_latency_ms,
                    self.error,
                )
            ):
                raise DomainValidationError(
                    "scheduled event cannot contain "
                    "metrics or error"
                )

        elif self.event_type is EventType.RUN_STARTED:
            if self.scheduling_latency_ms is None:
                raise DomainValidationError(
                    "started event requires "
                    "scheduling latency"
                )
            if (
                self.duration_ms is not None
                or self.error is not None
            ):
                raise DomainValidationError(
                    "started event cannot contain "
                    "duration or error"
                )

        elif self.event_type is EventType.RUN_SUCCEEDED:
            if self.duration_ms is None:
                raise DomainValidationError(
                    "succeeded event requires duration"
                )
            if self.error is not None:
                raise DomainValidationError(
                    "succeeded event cannot contain error"
                )

        elif self.event_type is EventType.RUN_FAILED:
            if self.duration_ms is None:
                raise DomainValidationError(
                    "failed event requires duration"
                )
            if self.error is None:
                raise DomainValidationError(
                    "failed event requires structured error"
                )

        elif self.event_type is EventType.RUN_MISSED:
            if occurred_at < scheduled_for:
                raise DomainValidationError(
                    "missed event cannot precede schedule"
                )
            if any(
                value is not None
                for value in (
                    self.duration_ms,
                    self.scheduling_latency_ms,
                    self.error,
                )
            ):
                raise DomainValidationError(
                    "missed event cannot contain "
                    "metrics or error"
                )


def scheduled_event(
    operation: Operation,
    scheduled_for: datetime,
    *,
    occurred_at: datetime | None = None,
    recorded_at: datetime | None = None,
    event_id: UUID | None = None,
    run_id: UUID | None = None,
    attempt: int = 1,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionEvent:
    event_time = occurred_at or scheduled_for

    return ExecutionEvent(
        event_id=event_id or uuid4(),
        run_id=run_id or uuid4(),
        operation=operation,
        event_type=EventType.RUN_SCHEDULED,
        scheduled_for=scheduled_for,
        occurred_at=event_time,
        recorded_at=recorded_at or event_time,
        attempt=attempt,
        evidence=evidence or {},
    )


def started_event(
    scheduled: ExecutionEvent,
    started_at: datetime,
    *,
    recorded_at: datetime | None = None,
    event_id: UUID | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionEvent:
    if scheduled.event_type is not EventType.RUN_SCHEDULED:
        raise DomainValidationError(
            "started event requires scheduled event"
        )

    latency = elapsed_milliseconds(
        scheduled.scheduled_for,
        started_at,
        field_name="scheduling_latency_ms",
    )

    return ExecutionEvent(
        event_id=event_id or uuid4(),
        run_id=scheduled.run_id,
        operation=scheduled.operation,
        event_type=EventType.RUN_STARTED,
        scheduled_for=scheduled.scheduled_for,
        occurred_at=started_at,
        recorded_at=recorded_at or started_at,
        attempt=scheduled.attempt,
        evidence=evidence or {},
        scheduling_latency_ms=latency,
    )


def succeeded_event(
    started: ExecutionEvent,
    finished_at: datetime,
    *,
    recorded_at: datetime | None = None,
    event_id: UUID | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionEvent:
    if started.event_type is not EventType.RUN_STARTED:
        raise DomainValidationError(
            "succeeded event requires started event"
        )

    return ExecutionEvent(
        event_id=event_id or uuid4(),
        run_id=started.run_id,
        operation=started.operation,
        event_type=EventType.RUN_SUCCEEDED,
        scheduled_for=started.scheduled_for,
        occurred_at=finished_at,
        recorded_at=recorded_at or finished_at,
        attempt=started.attempt,
        evidence=evidence or {},
        duration_ms=elapsed_milliseconds(
            started.occurred_at,
            finished_at,
            field_name="duration_ms",
        ),
    )


def failed_event(
    started: ExecutionEvent,
    finished_at: datetime,
    error: ErrorInfo,
    *,
    recorded_at: datetime | None = None,
    event_id: UUID | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionEvent:
    if started.event_type is not EventType.RUN_STARTED:
        raise DomainValidationError(
            "failed event requires started event"
        )

    return ExecutionEvent(
        event_id=event_id or uuid4(),
        run_id=started.run_id,
        operation=started.operation,
        event_type=EventType.RUN_FAILED,
        scheduled_for=started.scheduled_for,
        occurred_at=finished_at,
        recorded_at=recorded_at or finished_at,
        attempt=started.attempt,
        evidence=evidence or {},
        duration_ms=elapsed_milliseconds(
            started.occurred_at,
            finished_at,
            field_name="duration_ms",
        ),
        error=error,
    )


def missed_event(
    scheduled: ExecutionEvent,
    observed_at: datetime,
    *,
    recorded_at: datetime | None = None,
    event_id: UUID | None = None,
    evidence: Mapping[str, Any] | None = None,
) -> ExecutionEvent:
    if scheduled.event_type is not EventType.RUN_SCHEDULED:
        raise DomainValidationError(
            "missed event requires scheduled event"
        )

    return ExecutionEvent(
        event_id=event_id or uuid4(),
        run_id=scheduled.run_id,
        operation=scheduled.operation,
        event_type=EventType.RUN_MISSED,
        scheduled_for=scheduled.scheduled_for,
        occurred_at=observed_at,
        recorded_at=recorded_at or observed_at,
        attempt=scheduled.attempt,
        evidence=evidence or {},
    )
