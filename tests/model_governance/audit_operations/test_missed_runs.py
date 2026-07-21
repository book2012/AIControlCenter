from datetime import datetime, timezone

from core.governance.operations.domain.events import (
    EventType,
    Operation,
    scheduled_event,
    started_event,
)
from core.governance.operations.domain.state import (
    detect_missed_run,
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


def test_run_is_not_missed_before_grace_boundary():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(0),
    )

    assert (
        detect_missed_run(
            [scheduled],
            utc(9),
            grace_seconds=10,
        )
        is None
    )


def test_run_is_missed_at_grace_boundary():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(0),
    )

    missed = detect_missed_run(
        [scheduled],
        utc(10),
        grace_seconds=10,
    )

    assert missed is not None
    assert missed.event_type is EventType.RUN_MISSED
    assert missed.run_id == scheduled.run_id
    assert missed.evidence["automatic_catch_up"] is False


def test_started_run_is_not_marked_missed():
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(0),
    )
    started = started_event(scheduled, utc(2))

    assert (
        detect_missed_run(
            [scheduled, started],
            utc(20),
            grace_seconds=10,
        )
        is None
    )
