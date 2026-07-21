"""Append-only execution sequence validation and projection."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, Sequence
from uuid import UUID

from .events import (
    DomainValidationError,
    EventType,
    ExecutionEvent,
    Operation,
    missed_event,
    require_utc,
)


class InvalidEventSequenceError(DomainValidationError):
    """Raised when events violate append-only ordering."""


class DuplicateTerminalEventError(
    InvalidEventSequenceError
):
    """Raised when a run receives a second terminal event."""


class ExecutionState(str, Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    MISSED = "MISSED"


def validate_event_sequence(
    events: Sequence[ExecutionEvent],
) -> tuple[ExecutionEvent, ...]:
    sequence = tuple(events)

    if not sequence:
        raise InvalidEventSequenceError(
            "execution event sequence must not be empty"
        )

    first = sequence[0]

    if first.event_type is not EventType.RUN_SCHEDULED:
        raise InvalidEventSequenceError(
            "first event must be run_scheduled"
        )

    event_ids: set[UUID] = set()
    previous_recorded_at: datetime | None = None
    started = False
    terminal = False

    for index, event in enumerate(sequence):
        if event.event_id in event_ids:
            raise InvalidEventSequenceError(
                "event_id must be unique"
            )

        event_ids.add(event.event_id)

        if event.run_id != first.run_id:
            raise InvalidEventSequenceError(
                "all events must share run_id"
            )
        if event.operation is not first.operation:
            raise InvalidEventSequenceError(
                "all events must share operation"
            )
        if event.scheduled_for != first.scheduled_for:
            raise InvalidEventSequenceError(
                "all events must share scheduled_for"
            )
        if event.attempt != first.attempt:
            raise InvalidEventSequenceError(
                "all events must share attempt"
            )

        if (
            previous_recorded_at is not None
            and event.recorded_at < previous_recorded_at
        ):
            raise InvalidEventSequenceError(
                "recorded_at must be append ordered"
            )

        previous_recorded_at = event.recorded_at

        if index == 0:
            continue

        if terminal:
            raise DuplicateTerminalEventError(
                "event cannot follow terminal event"
            )

        if event.event_type is EventType.RUN_SCHEDULED:
            raise InvalidEventSequenceError(
                "run_scheduled may appear only once"
            )

        if event.event_type is EventType.RUN_STARTED:
            if started:
                raise InvalidEventSequenceError(
                    "run_started may appear only once"
                )
            started = True
            continue

        if event.event_type in {
            EventType.RUN_SUCCEEDED,
            EventType.RUN_FAILED,
        }:
            if not started:
                raise InvalidEventSequenceError(
                    "success or failure requires run_started"
                )
            terminal = True
            continue

        if event.event_type is EventType.RUN_MISSED:
            if started:
                raise InvalidEventSequenceError(
                    "started run cannot become missed"
                )
            terminal = True
            continue

        raise InvalidEventSequenceError(
            f"unsupported event type: {event.event_type}"
        )

    return sequence


def project_execution_state(
    events: Sequence[ExecutionEvent],
) -> ExecutionState:
    sequence = validate_event_sequence(events)

    return {
        EventType.RUN_SCHEDULED: ExecutionState.SCHEDULED,
        EventType.RUN_STARTED: ExecutionState.RUNNING,
        EventType.RUN_SUCCEEDED: ExecutionState.SUCCEEDED,
        EventType.RUN_FAILED: ExecutionState.FAILED,
        EventType.RUN_MISSED: ExecutionState.MISSED,
    }[sequence[-1].event_type]


def last_success(
    events: Iterable[ExecutionEvent],
    operation: Operation | None = None,
) -> ExecutionEvent | None:
    matching = [
        event
        for event in events
        if (
            event.event_type is EventType.RUN_SUCCEEDED
            and (
                operation is None
                or event.operation is operation
            )
        )
    ]

    return (
        max(matching, key=lambda item: item.occurred_at)
        if matching
        else None
    )


def last_failure(
    events: Iterable[ExecutionEvent],
    operation: Operation | None = None,
) -> ExecutionEvent | None:
    matching = [
        event
        for event in events
        if (
            event.event_type is EventType.RUN_FAILED
            and (
                operation is None
                or event.operation is operation
            )
        )
    ]

    return (
        max(matching, key=lambda item: item.occurred_at)
        if matching
        else None
    )


def detect_missed_run(
    events: Sequence[ExecutionEvent],
    now: datetime,
    *,
    grace_seconds: int,
) -> ExecutionEvent | None:
    if grace_seconds < 1:
        raise DomainValidationError(
            "grace_seconds must be at least one"
        )

    sequence = validate_event_sequence(events)

    if (
        project_execution_state(sequence)
        is not ExecutionState.SCHEDULED
    ):
        return None

    observed_at = require_utc(now, "now")
    scheduled = sequence[0]
    boundary = scheduled.scheduled_for + timedelta(
        seconds=grace_seconds
    )

    if observed_at < boundary:
        return None

    return missed_event(
        scheduled,
        observed_at,
        evidence={
            "automatic_catch_up": False,
            "decision": "missed-run",
            "grace_seconds": grace_seconds,
        },
    )
