"""Governance audit operations application API."""

from .identity import event_id_for, run_id_for
from .models import (
    BackupExecutionResult,
    DispatchCommand,
    DispatchResult,
    MissedRunObservationCommand,
    MissedRunObservationResult,
    SnapshotExecutionResult,
)
from .projection import (
    OperationalProjection,
    project_operation,
)
from .scheduler import (
    BACKUP_JOB_ID,
    MISSED_OBSERVER_JOB_ID,
    SNAPSHOT_JOB_ID,
    SchedulerContractError,
    SchedulerDispatchAdapter,
)
from .service import (
    OperationsApplicationService,
    ScheduledEventPersistenceError,
    StartedEventPersistenceError,
    TerminalEventPersistenceError,
)

__all__ = [
    "BACKUP_JOB_ID",
    "BackupExecutionResult",
    "DispatchCommand",
    "DispatchResult",
    "MISSED_OBSERVER_JOB_ID",
    "MissedRunObservationCommand",
    "MissedRunObservationResult",
    "OperationalProjection",
    "OperationsApplicationService",
    "SNAPSHOT_JOB_ID",
    "ScheduledEventPersistenceError",
    "SchedulerContractError",
    "SchedulerDispatchAdapter",
    "SnapshotExecutionResult",
    "StartedEventPersistenceError",
    "TerminalEventPersistenceError",
    "event_id_for",
    "project_operation",
    "run_id_for",
]
