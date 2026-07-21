"""AIControlCenter scheduler command adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from uuid import UUID, uuid4

from ..domain.events import Operation
from .models import (
    DispatchCommand,
    MissedRunObservationCommand,
)

SNAPSHOT_JOB_ID = "governance-audit-snapshot"
BACKUP_JOB_ID = (
    "governance-audit-sqlite-backup-verification"
)
MISSED_OBSERVER_JOB_ID = (
    "governance-audit-missed-run-observer"
)


class SchedulerContractError(ValueError):
    """Raised for an unsupported scheduler job."""


@dataclass(frozen=True, slots=True)
class ScheduledJobDefinition:
    job_id: str
    operation: Operation | None
    command_type: str


JOB_DEFINITIONS = MappingProxyType(
    {
        SNAPSHOT_JOB_ID: ScheduledJobDefinition(
            job_id=SNAPSHOT_JOB_ID,
            operation=(
                Operation.GOVERNANCE_AUDIT_SNAPSHOT
            ),
            command_type="dispatch",
        ),
        BACKUP_JOB_ID: ScheduledJobDefinition(
            job_id=BACKUP_JOB_ID,
            operation=(
                Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
            ),
            command_type="dispatch",
        ),
        MISSED_OBSERVER_JOB_ID: (
            ScheduledJobDefinition(
                job_id=MISSED_OBSERVER_JOB_ID,
                operation=None,
                command_type="missed-observation",
            )
        ),
    }
)


class SchedulerDispatchAdapter:
    def build_dispatch(
        self,
        job_id: str,
        scheduled_for: datetime,
        *,
        dispatch_id: UUID | None = None,
    ) -> DispatchCommand:
        definition = JOB_DEFINITIONS.get(job_id)

        if (
            definition is None
            or definition.command_type
            != "dispatch"
            or definition.operation is None
        ):
            raise SchedulerContractError(
                f"unsupported dispatch job: {job_id}"
            )

        return DispatchCommand(
            job_id=job_id,
            operation=definition.operation,
            scheduled_for=scheduled_for,
            dispatch_id=(
                dispatch_id or uuid4()
            ),
            attempt=1,
        )


    def build_missed_observation(
        self,
        job_id: str,
        observed_at: datetime,
        *,
        operation: Operation,
    ) -> MissedRunObservationCommand:
        definition = JOB_DEFINITIONS.get(job_id)

        if (
            definition is None
            or definition.command_type
            != "missed-observation"
        ):
            raise SchedulerContractError(
                f"unsupported observer job: {job_id}"
            )

        return MissedRunObservationCommand(
            operation=operation,
            observed_at=observed_at,
        )
