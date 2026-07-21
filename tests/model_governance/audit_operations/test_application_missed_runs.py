from core.governance.operations.application.models import (
    MissedRunObservationCommand,
)
from core.governance.operations.application.service import (
    OperationsApplicationService,
)
from core.governance.operations.domain.events import (
    EventType,
    Operation,
    scheduled_event,
)
from core.governance.operations.domain.severity import (
    Severity,
)

from .application_helpers import (
    FakeBackupVerifier,
    FakeSnapshotExecutor,
    SequenceClock,
    temporary_repository,
    utc,
)


def service(repository):
    return OperationsApplicationService(
        repository,
        SequenceClock(),
        FakeSnapshotExecutor(),
        FakeBackupVerifier(),
        missed_grace_seconds=300,
    )


def test_observer_does_not_mark_run_before_grace(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
    )
    repository.append(scheduled)

    result = service(
        repository
    ).observe_missed_runs(
        MissedRunObservationCommand(
            operation=(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT
            ),
            observed_at=utc(1, 4, 59),
        )
    )

    assert result.events_appended == 0
    assert repository.count() == 1


def test_observer_appends_missed_event_and_critical_signal(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(2),
    )
    repository.append(scheduled)

    result = service(
        repository
    ).observe_missed_runs(
        MissedRunObservationCommand(
            operation=(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT
            ),
            observed_at=utc(2, 5),
        )
    )

    events = repository.events_for_run(
        scheduled.run_id
    )

    assert result.events_appended == 1
    assert result.missed_run_ids == (
        scheduled.run_id,
    )
    assert (
        events[-1].event_type
        is EventType.RUN_MISSED
    )
    assert (
        events[-1].evidence[
            "automatic_catch_up"
        ]
        is False
    )
    assert (
        result.notification_signals[0].severity
        is Severity.CRITICAL
    )


def test_repeated_observation_is_idempotent(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(3),
    )
    repository.append(scheduled)
    application = service(repository)
    command = MissedRunObservationCommand(
        operation=(
            Operation.GOVERNANCE_AUDIT_SNAPSHOT
        ),
        observed_at=utc(3, 5),
    )

    first = application.observe_missed_runs(
        command
    )
    second = application.observe_missed_runs(
        command
    )

    assert first.events_appended == 1
    assert second.events_appended == 0
    assert second.notification_signals == ()
    assert repository.count() == 2
