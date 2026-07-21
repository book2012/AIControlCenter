from uuid import uuid4

import pytest

from core.governance.operations.application.scheduler import (
    BACKUP_JOB_ID,
    MISSED_OBSERVER_JOB_ID,
    SNAPSHOT_JOB_ID,
    SchedulerContractError,
    SchedulerDispatchAdapter,
)
from core.governance.operations.domain.events import (
    Operation,
)

from .application_helpers import utc


def test_snapshot_job_maps_to_snapshot_dispatch():
    dispatch_id = uuid4()
    command = SchedulerDispatchAdapter().build_dispatch(
        SNAPSHOT_JOB_ID,
        utc(1),
        dispatch_id=dispatch_id,
    )

    assert (
        command.operation
        is Operation.GOVERNANCE_AUDIT_SNAPSHOT
    )
    assert command.dispatch_id == dispatch_id
    assert command.attempt == 1


def test_backup_job_maps_to_backup_dispatch():
    command = SchedulerDispatchAdapter().build_dispatch(
        BACKUP_JOB_ID,
        utc(2),
    )

    assert (
        command.operation
        is Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
    )


def test_missed_observer_job_builds_observation_command():
    command = (
        SchedulerDispatchAdapter()
        .build_missed_observation(
            MISSED_OBSERVER_JOB_ID,
            utc(3),
            operation=(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT
            ),
        )
    )

    assert (
        command.operation
        is Operation.GOVERNANCE_AUDIT_SNAPSHOT
    )
    assert command.observed_at == utc(3)


def test_unknown_scheduler_job_is_rejected():
    with pytest.raises(
        SchedulerContractError
    ):
        SchedulerDispatchAdapter().build_dispatch(
            "unknown-job",
            utc(4),
        )
