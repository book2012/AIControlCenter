"""Governance operation application orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Type
from uuid import UUID

from ..domain.events import (
    ErrorInfo,
    EventType,
    ExecutionEvent,
    Operation,
    failed_event,
    scheduled_event,
    started_event,
    succeeded_event,
)
from ..domain.ports import (
    Clock,
    ExecutionEventRepository,
)
from ..domain.severity import (
    NotificationSignal,
    OperationalCondition,
    build_signal,
)
from ..domain.state import (
    detect_missed_run,
    project_execution_state,
)
from .identity import event_id_for, run_id_for
from .models import (
    DispatchCommand,
    DispatchResult,
    MissedRunObservationCommand,
    MissedRunObservationResult,
)
from .ports import BackupVerifier, SnapshotExecutor


class ScheduledEventPersistenceError(
    RuntimeError
):
    """Scheduled event could not be persisted."""


class StartedEventPersistenceError(
    RuntimeError
):
    """Started event could not be persisted."""


class TerminalEventPersistenceError(
    RuntimeError
):
    """Terminal event could not be persisted."""


class OperationsApplicationService:
    def __init__(
        self,
        repository: ExecutionEventRepository,
        clock: Clock,
        snapshot_executor: SnapshotExecutor,
        backup_verifier: BackupVerifier,
        *,
        missed_grace_seconds: int = 300,
    ) -> None:
        if missed_grace_seconds < 1:
            raise ValueError(
                "missed_grace_seconds must be positive"
            )

        self.repository = repository
        self.clock = clock
        self.snapshot_executor = snapshot_executor
        self.backup_verifier = backup_verifier
        self.missed_grace_seconds = (
            missed_grace_seconds
        )


    def dispatch(
        self,
        command: DispatchCommand,
    ) -> DispatchResult:
        run_id = run_id_for(
            command.operation,
            command.scheduled_for,
            command.attempt,
        )

        existing = tuple(
            self.repository.events_for_run(run_id)
        )

        if existing:
            return DispatchResult(
                run_id=run_id,
                state=project_execution_state(
                    existing
                ),
                events=existing,
                events_appended=0,
                duplicate_dispatch=True,
            )

        scheduled = scheduled_event(
            command.operation,
            command.scheduled_for,
            occurred_at=command.scheduled_for,
            recorded_at=command.scheduled_for,
            event_id=event_id_for(
                run_id,
                EventType.RUN_SCHEDULED,
            ),
            run_id=run_id,
            attempt=command.attempt,
            evidence={
                "automatic_retry": False,
                "dispatch_id": str(
                    command.dispatch_id
                ),
                "job_id": command.job_id,
            },
        )

        scheduled_inserted = self._append_or_raise(
            scheduled,
            ScheduledEventPersistenceError,
        )

        started_at = self.clock.now()
        started = started_event(
            scheduled,
            started_at,
            event_id=event_id_for(
                run_id,
                EventType.RUN_STARTED,
            ),
            evidence={
                "automatic_retry": False,
            },
        )

        started_inserted = self._append_or_raise(
            started,
            StartedEventPersistenceError,
        )

        try:
            if (
                command.operation
                is Operation.GOVERNANCE_AUDIT_SNAPSHOT
            ):
                execution_result = (
                    self.snapshot_executor.execute(
                        run_id=run_id,
                        scheduled_for=(
                            command.scheduled_for
                        ),
                    )
                )
            elif (
                command.operation
                is Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
            ):
                execution_result = (
                    self.backup_verifier.verify(
                        run_id=run_id,
                        scheduled_for=(
                            command.scheduled_for
                        ),
                    )
                )
            else:
                raise RuntimeError(
                    "unsupported operation"
                )

        except Exception as error:
            return self._record_failure(
                command=command,
                scheduled=scheduled,
                started=started,
                error=error,
                events_appended=(
                    int(scheduled_inserted)
                    + int(started_inserted)
                ),
            )

        finished_at = self.clock.now()
        succeeded = succeeded_event(
            started,
            finished_at,
            event_id=event_id_for(
                run_id,
                EventType.RUN_SUCCEEDED,
            ),
            evidence=dict(
                execution_result.to_evidence()
            ),
        )

        terminal_inserted = self._append_or_raise(
            succeeded,
            TerminalEventPersistenceError,
        )

        signal = self._signal(
            condition=OperationalCondition.SUCCESS,
            event=succeeded,
            evidence={
                "automatic_remediation": False,
            },
        )

        events = (
            scheduled,
            started,
            succeeded,
        )

        return DispatchResult(
            run_id=run_id,
            state=project_execution_state(events),
            events=events,
            events_appended=(
                int(scheduled_inserted)
                + int(started_inserted)
                + int(terminal_inserted)
            ),
            duplicate_dispatch=False,
            notification_signals=(signal,),
        )


    def _record_failure(
        self,
        *,
        command: DispatchCommand,
        scheduled: ExecutionEvent,
        started: ExecutionEvent,
        error: Exception,
        events_appended: int,
    ) -> DispatchResult:
        finished_at = self.clock.now()
        message = str(error).strip()

        if not message:
            message = error.__class__.__name__

        failed = failed_event(
            started,
            finished_at,
            ErrorInfo(
                code=(
                    "backup-verification-failed"
                    if (
                        command.operation
                        is Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
                    )
                    else "snapshot-execution-failed"
                ),
                message=message,
                details={
                    "automatic_remediation": False,
                    "automatic_retry": False,
                    "exception_type": (
                        error.__class__.__name__
                    ),
                    "model_write": False,
                },
            ),
            event_id=event_id_for(
                scheduled.run_id,
                EventType.RUN_FAILED,
            ),
        )

        terminal_inserted = self._append_or_raise(
            failed,
            TerminalEventPersistenceError,
        )

        condition = (
            OperationalCondition.BACKUP_VERIFICATION_FAILURE
            if (
                command.operation
                is Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
            )
            else OperationalCondition.EXECUTION_FAILURE
        )

        signal = self._signal(
            condition=condition,
            event=failed,
            evidence={
                "automatic_retry": False,
            },
        )

        events = (
            scheduled,
            started,
            failed,
        )

        return DispatchResult(
            run_id=scheduled.run_id,
            state=project_execution_state(events),
            events=events,
            events_appended=(
                events_appended
                + int(terminal_inserted)
            ),
            duplicate_dispatch=False,
            notification_signals=(signal,),
        )


    def observe_missed_runs(
        self,
        command: MissedRunObservationCommand,
    ) -> MissedRunObservationResult:
        grouped: dict[
            UUID,
            list[ExecutionEvent],
        ] = {}

        for event in self.repository.iter_events(
            command.operation
        ):
            grouped.setdefault(
                event.run_id,
                [],
            ).append(event)

        missed_run_ids: list[UUID] = []
        signals: list[NotificationSignal] = []
        appended_count = 0

        for run_id, events in grouped.items():
            candidate = detect_missed_run(
                tuple(events),
                command.observed_at,
                grace_seconds=(
                    self.missed_grace_seconds
                ),
            )

            if candidate is None:
                continue

            candidate = replace(
                candidate,
                event_id=event_id_for(
                    run_id,
                    EventType.RUN_MISSED,
                ),
            )

            inserted = self._append_or_raise(
                candidate,
                TerminalEventPersistenceError,
            )

            if not inserted:
                continue

            appended_count += 1
            missed_run_ids.append(run_id)
            signals.append(
                self._signal(
                    condition=(
                        OperationalCondition.MISSED_RUN
                    ),
                    event=candidate,
                    evidence={
                        "automatic_catch_up": False,
                    },
                )
            )

        return MissedRunObservationResult(
            operation=command.operation,
            observed_at=command.observed_at,
            missed_run_ids=tuple(
                missed_run_ids
            ),
            events_appended=appended_count,
            notification_signals=tuple(signals),
        )


    def _append_or_raise(
        self,
        event: ExecutionEvent,
        exception_type: Type[RuntimeError],
    ) -> bool:
        try:
            result = self.repository.append(event)
        except Exception as error:
            raise exception_type(
                f"unable to persist "
                f"{event.event_type.value}"
            ) from error

        return result is not False


    def _signal(
        self,
        *,
        condition: OperationalCondition,
        event: ExecutionEvent,
        evidence: dict[str, object],
    ) -> NotificationSignal:
        deduplication_key = (
            f"{event.operation.value}:"
            f"{event.scheduled_for.isoformat()}:"
            f"{condition.value}"
        )

        return build_signal(
            condition,
            event.occurred_at,
            deduplication_key,
            operation=event.operation,
            run_id=event.run_id,
            evidence=evidence,
        )
