from dataclasses import replace
from datetime import datetime, timezone
import sqlite3

import pytest

from core.governance.operations.adapters.sqlite import (
    IdempotencyConflictError,
    REQUIRED_OBJECTS,
    SQLiteOperationsEventRepository,
)
from core.governance.operations.domain.events import (
    ErrorInfo,
    Operation,
    failed_event,
    scheduled_event,
    started_event,
    succeeded_event,
)
from core.governance.operations.domain.state import (
    ExecutionState,
    InvalidEventSequenceError,
    project_execution_state,
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


def repository(tmp_path):
    instance = SQLiteOperationsEventRepository(
        tmp_path / "operations.sqlite3"
    )
    instance.initialize_schema()
    return instance


def append_success(instance, hour: int):
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(hour),
    )
    started = started_event(
        scheduled,
        utc(hour, 1),
    )
    succeeded = succeeded_event(
        started,
        utc(hour, 4),
    )

    for event in (scheduled, started, succeeded):
        assert instance.append(event) is True

    return scheduled, started, succeeded


def append_failure(instance, hour: int):
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(hour),
    )
    started = started_event(
        scheduled,
        utc(hour, 1),
    )
    failed = failed_event(
        started,
        utc(hour, 3),
        ErrorInfo(
            code="snapshot-failed",
            message="snapshot failed",
        ),
    )

    for event in (scheduled, started, failed):
        assert instance.append(event) is True

    return scheduled, started, failed


def test_schema_uses_wal_and_required_objects(
    tmp_path,
):
    instance = repository(tmp_path)

    assert instance.journal_mode().lower() == "wal"
    assert REQUIRED_OBJECTS.issubset(
        instance.schema_objects()
    )


def test_identical_duplicate_is_idempotent(
    tmp_path,
):
    instance = repository(tmp_path)
    event = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
    )

    assert instance.append(event) is True
    assert instance.append(event) is False
    assert instance.count() == 1


def test_conflicting_duplicate_is_rejected(
    tmp_path,
):
    instance = repository(tmp_path)
    event = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
    )
    conflict = replace(
        event,
        evidence={"different": True},
    )

    assert instance.append(event) is True

    with pytest.raises(IdempotencyConflictError):
        instance.append(conflict)

    assert instance.count() == 1


def test_run_sequence_is_append_ordered_and_projectable(
    tmp_path,
):
    instance = repository(tmp_path)
    scheduled, started, succeeded = append_success(
        instance,
        2,
    )

    events = instance.events_for_run(
        scheduled.run_id
    )

    assert events == (
        scheduled,
        started,
        succeeded,
    )
    assert (
        project_execution_state(events)
        is ExecutionState.SUCCEEDED
    )


def test_invalid_sequence_is_rejected_before_insert(
    tmp_path,
):
    instance = repository(tmp_path)
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(3),
    )
    started = started_event(
        scheduled,
        utc(3, 1),
    )

    with pytest.raises(InvalidEventSequenceError):
        instance.append(started)

    assert instance.count() == 0


def test_update_and_delete_are_denied(tmp_path):
    instance = repository(tmp_path)
    event = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(4),
    )
    instance.append(event)

    connection = sqlite3.connect(
        instance.database_path
    )

    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                UPDATE governance_audit_operation_events
                SET evidence_json = '{}'
                WHERE event_id = ?
                """,
                (str(event.event_id),),
            )

        connection.rollback()

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                DELETE FROM governance_audit_operation_events
                WHERE event_id = ?
                """,
                (str(event.event_id),),
            )

        connection.rollback()

    finally:
        connection.close()

    assert instance.count() == 1


def test_last_success_and_failure_queries(
    tmp_path,
):
    instance = repository(tmp_path)
    _, _, succeeded = append_success(instance, 5)
    _, _, failed = append_failure(instance, 6)

    assert (
        instance.last_success(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT
        )
        == succeeded
    )
    assert (
        instance.last_failure(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT
        )
        == failed
    )


def test_iter_events_filters_by_operation(
    tmp_path,
):
    instance = repository(tmp_path)

    audit = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(7),
    )
    backup = scheduled_event(
        Operation.SQLITE_ONLINE_BACKUP_VERIFICATION,
        utc(8),
    )

    instance.append(audit)
    instance.append(backup)

    assert tuple(
        instance.iter_events(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT
        )
    ) == (audit,)

    assert tuple(instance.iter_events()) == (
        audit,
        backup,
    )
