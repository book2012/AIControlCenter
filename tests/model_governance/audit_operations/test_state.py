from datetime import datetime, timezone

import pytest

from core.governance.operations.domain.events import (
    ErrorInfo,
    Operation,
    failed_event,
    scheduled_event,
    started_event,
    succeeded_event,
)
from core.governance.operations.domain.state import (
    DuplicateTerminalEventError,
    ExecutionState,
    last_failure,
    last_success,
    project_execution_state,
    validate_event_sequence,
)


def utc(hour: int, second: int = 0) -> datetime:
    return datetime(
        2026,
        7,
        21,
        hour,
        0,
        second,
        tzinfo=timezone.utc,
    )


def test_state_is_projected_without_mutable_state_row():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
    )
    started = started_event(scheduled, utc(1, 1))
    succeeded = succeeded_event(started, utc(1, 4))

    assert (
        project_execution_state([scheduled])
        is ExecutionState.SCHEDULED
    )
    assert (
        project_execution_state([scheduled, started])
        is ExecutionState.RUNNING
    )
    assert (
        project_execution_state(
            [scheduled, started, succeeded]
        )
        is ExecutionState.SUCCEEDED
    )


def test_second_terminal_event_is_rejected():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(2),
    )
    started = started_event(scheduled, utc(2, 1))
    succeeded = succeeded_event(started, utc(2, 2))
    failed = failed_event(
        started,
        utc(2, 3),
        ErrorInfo(
            code="late-failure",
            message="late failure",
        ),
    )

    with pytest.raises(DuplicateTerminalEventError):
        validate_event_sequence(
            [scheduled, started, succeeded, failed]
        )


def test_last_success_and_failure_are_independent():
    first = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(3),
    )
    first_started = started_event(first, utc(3, 1))
    first_success = succeeded_event(
        first_started,
        utc(3, 2),
    )

    second = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(4),
    )
    second_started = started_event(second, utc(4, 1))
    second_failure = failed_event(
        second_started,
        utc(4, 2),
        ErrorInfo(
            code="failure",
            message="failure",
        ),
    )

    events = [
        first,
        first_started,
        first_success,
        second,
        second_started,
        second_failure,
    ]

    assert last_success(events) is first_success
    assert last_failure(events) is second_failure
