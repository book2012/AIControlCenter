from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from core.governance.operations.domain.events import (
    DomainValidationError,
    ErrorInfo,
    EventType,
    Operation,
    failed_event,
    scheduled_event,
    started_event,
    succeeded_event,
)


def utc(second: int) -> datetime:
    return datetime(
        2026,
        7,
        21,
        1,
        0,
        second,
        tzinfo=timezone.utc,
    )


def test_events_are_immutable_and_calculate_metrics():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(0),
    )
    started = started_event(scheduled, utc(5))
    succeeded = succeeded_event(started, utc(9))

    assert scheduled.event_type is EventType.RUN_SCHEDULED
    assert started.scheduling_latency_ms == 5000
    assert succeeded.duration_ms == 4000

    with pytest.raises(FrozenInstanceError):
        succeeded.duration_ms = 1


def test_failed_event_records_structured_error():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(0),
    )
    started = started_event(scheduled, utc(1))
    error = ErrorInfo(
        code="snapshot-failed",
        message="snapshot failed",
        details={"automatic_retry": False},
    )
    failed = failed_event(started, utc(3), error)

    assert failed.event_type is EventType.RUN_FAILED
    assert failed.duration_ms == 2000
    assert failed.error == error
    assert failed.error.details["automatic_retry"] is False


def test_naive_datetime_is_rejected():
    with pytest.raises(
        DomainValidationError,
        match="timezone-aware UTC",
    ):
        scheduled_event(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT,
            datetime(2026, 7, 21, 1),
        )
