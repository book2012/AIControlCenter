from uuid import uuid4

import pytest

from core.governance.operations.application.identity import (
    run_id_for,
)
from core.governance.operations.application.models import (
    DispatchCommand,
)
from core.governance.operations.application.service import (
    OperationsApplicationService,
    ScheduledEventPersistenceError,
    StartedEventPersistenceError,
    TerminalEventPersistenceError,
)
from core.governance.operations.domain.events import (
    EventType,
    Operation,
)
from core.governance.operations.domain.severity import (
    Severity,
)
from core.governance.operations.domain.state import (
    ExecutionState,
    project_execution_state,
)

from .application_helpers import (
    FailingAppendRepository,
    FakeBackupVerifier,
    FakeSnapshotExecutor,
    SequenceClock,
    temporary_repository,
    utc,
)


def command(
    operation,
    scheduled_for,
):
    return DispatchCommand(
        job_id="test-job",
        operation=operation,
        scheduled_for=scheduled_for,
        dispatch_id=uuid4(),
    )


def test_snapshot_success_records_sequence_and_info_signal(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    snapshot = FakeSnapshotExecutor()
    backup = FakeBackupVerifier()
    service = OperationsApplicationService(
        repository,
        SequenceClock(
            utc(1, 0, 2),
            utc(1, 0, 7),
        ),
        snapshot,
        backup,
    )

    result = service.dispatch(
        command(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT,
            utc(1),
        )
    )

    assert result.state is ExecutionState.SUCCEEDED
    assert result.events_appended == 3
    assert result.duplicate_dispatch is False
    assert [
        event.event_type
        for event in result.events
    ] == [
        EventType.RUN_SCHEDULED,
        EventType.RUN_STARTED,
        EventType.RUN_SUCCEEDED,
    ]
    assert result.events[-1].duration_ms == 5000
    assert (
        result.events[-1].evidence["snapshot_id"]
        == "snapshot-001"
    )
    assert len(snapshot.calls) == 1
    assert (
        result.notification_signals[0].severity
        is Severity.INFO
    )


def test_duplicate_dispatch_does_not_reinvoke_executor(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    snapshot = FakeSnapshotExecutor()
    service = OperationsApplicationService(
        repository,
        SequenceClock(
            utc(2, 0, 1),
            utc(2, 0, 3),
        ),
        snapshot,
        FakeBackupVerifier(),
    )
    dispatch = command(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(2),
    )

    first = service.dispatch(dispatch)
    second = service.dispatch(dispatch)

    assert first.state is ExecutionState.SUCCEEDED
    assert second.state is ExecutionState.SUCCEEDED
    assert second.duplicate_dispatch is True
    assert second.events_appended == 0
    assert len(snapshot.calls) == 1
    assert repository.count() == 3


def test_snapshot_failure_records_failed_and_warning_signal(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    snapshot = FakeSnapshotExecutor(
        error=RuntimeError("snapshot failed")
    )
    service = OperationsApplicationService(
        repository,
        SequenceClock(
            utc(3, 0, 2),
            utc(3, 0, 5),
        ),
        snapshot,
        FakeBackupVerifier(),
    )

    result = service.dispatch(
        command(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT,
            utc(3),
        )
    )

    assert result.state is ExecutionState.FAILED
    assert result.events[-1].error is not None
    assert (
        result.events[-1].error.details[
            "automatic_retry"
        ]
        is False
    )
    assert (
        result.notification_signals[0].severity
        is Severity.WARNING
    )
    assert len(snapshot.calls) == 1


def test_backup_success_records_verification_evidence(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    backup = FakeBackupVerifier()
    service = OperationsApplicationService(
        repository,
        SequenceClock(
            utc(4, 0, 1),
            utc(4, 0, 4),
        ),
        FakeSnapshotExecutor(),
        backup,
    )

    result = service.dispatch(
        command(
            Operation.SQLITE_ONLINE_BACKUP_VERIFICATION,
            utc(4),
        )
    )

    assert result.state is ExecutionState.SUCCEEDED
    assert (
        result.events[-1].evidence["quick_check"]
        == ["ok"]
    )
    assert (
        result.events[-1].evidence[
            "automatic_restore"
        ]
        is False
    )
    assert len(backup.calls) == 1


def test_scheduled_persistence_failure_prevents_executor(
    tmp_path,
):
    delegate = temporary_repository(tmp_path)
    repository = FailingAppendRepository(
        delegate,
        fail_on_append=1,
    )
    snapshot = FakeSnapshotExecutor()
    service = OperationsApplicationService(
        repository,
        SequenceClock(),
        snapshot,
        FakeBackupVerifier(),
    )

    with pytest.raises(
        ScheduledEventPersistenceError
    ):
        service.dispatch(
            command(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT,
                utc(5),
            )
        )

    assert snapshot.calls == []
    assert delegate.count() == 0


def test_started_persistence_failure_prevents_executor(
    tmp_path,
):
    delegate = temporary_repository(tmp_path)
    repository = FailingAppendRepository(
        delegate,
        fail_on_append=2,
    )
    snapshot = FakeSnapshotExecutor()
    service = OperationsApplicationService(
        repository,
        SequenceClock(utc(6, 0, 1)),
        snapshot,
        FakeBackupVerifier(),
    )

    with pytest.raises(
        StartedEventPersistenceError
    ):
        service.dispatch(
            command(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT,
                utc(6),
            )
        )

    assert snapshot.calls == []
    assert delegate.count() == 1


def test_terminal_persistence_failure_does_not_retry_executor(
    tmp_path,
):
    delegate = temporary_repository(tmp_path)
    repository = FailingAppendRepository(
        delegate,
        fail_on_append=3,
    )
    snapshot = FakeSnapshotExecutor()
    service = OperationsApplicationService(
        repository,
        SequenceClock(
            utc(7, 0, 1),
            utc(7, 0, 4),
        ),
        snapshot,
        FakeBackupVerifier(),
    )
    scheduled_for = utc(7)

    with pytest.raises(
        TerminalEventPersistenceError
    ):
        service.dispatch(
            command(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT,
                scheduled_for,
            )
        )

    run_id = run_id_for(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        scheduled_for,
        1,
    )
    events = delegate.events_for_run(run_id)

    assert len(snapshot.calls) == 1
    assert (
        project_execution_state(events)
        is ExecutionState.RUNNING
    )
