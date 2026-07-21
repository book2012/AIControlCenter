"""Read-only operational projection from domain events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable
from uuid import UUID

from ..domain.events import (
    EventType,
    ExecutionEvent,
    Operation,
    require_utc,
)
from ..domain.health import (
    FreshnessState,
    HealthState,
    OperationalHealthInput,
    calculate_health,
)
from ..domain.ports import (
    ExecutionEventRepository,
)
from ..domain.severity import NotificationSignal
from ..domain.state import (
    ExecutionState,
    last_failure,
    last_success,
    project_execution_state,
)


@dataclass(frozen=True, slots=True)
class OperationalProjection:
    schema_version: str
    generated_at: datetime
    operation: Operation
    schedule_owner: str
    overall_health: HealthState
    freshness_state: FreshnessState
    latest_state: ExecutionState | None
    latest_run_id: UUID | None
    last_scheduled_at: datetime | None
    last_started_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_missed_at: datetime | None
    duration_ms: int | None
    scheduling_latency_ms: int | None
    missed_run: bool
    backup_verification: dict[str, object] | None
    severity_signals: tuple[
        NotificationSignal,
        ...,
    ]

    def to_dict(self) -> dict[str, object]:
        def iso(
            value: datetime | None,
        ) -> str | None:
            return (
                value.isoformat()
                if value is not None
                else None
            )

        return {
            "backup_verification": (
                self.backup_verification
            ),
            "duration_ms": self.duration_ms,
            "freshness_state": (
                self.freshness_state.value
            ),
            "generated_at": (
                self.generated_at.isoformat()
            ),
            "last_failure_at": iso(
                self.last_failure_at
            ),
            "last_missed_at": iso(
                self.last_missed_at
            ),
            "last_scheduled_at": iso(
                self.last_scheduled_at
            ),
            "last_started_at": iso(
                self.last_started_at
            ),
            "last_success_at": iso(
                self.last_success_at
            ),
            "latest_run_id": (
                str(self.latest_run_id)
                if self.latest_run_id
                else None
            ),
            "latest_state": (
                self.latest_state.value
                if self.latest_state
                else None
            ),
            "missed_run": self.missed_run,
            "operation": self.operation.value,
            "overall_health": (
                self.overall_health.value
            ),
            "schedule_owner": (
                self.schedule_owner
            ),
            "schema_version": (
                self.schema_version
            ),
            "scheduling_latency_ms": (
                self.scheduling_latency_ms
            ),
            "severity_signals": [
                {
                    "condition": (
                        signal.condition.value
                    ),
                    "deduplication_key": (
                        signal.deduplication_key
                    ),
                    "observed_at": (
                        signal.observed_at.isoformat()
                    ),
                    "severity": (
                        signal.severity.value
                    ),
                }
                for signal in self.severity_signals
            ],
        }


def project_operation(
    repository: ExecutionEventRepository,
    operation: Operation,
    generated_at: datetime,
    *,
    freshness_warning_seconds: int = 900,
    freshness_critical_seconds: int = 3600,
    severity_signals: Iterable[
        NotificationSignal
    ] = (),
) -> OperationalProjection:
    now = require_utc(
        generated_at,
        "generated_at",
    )

    if freshness_warning_seconds < 1:
        raise ValueError(
            "freshness warning must be positive"
        )

    if (
        freshness_critical_seconds
        <= freshness_warning_seconds
    ):
        raise ValueError(
            "critical freshness must exceed warning"
        )

    events = tuple(
        repository.iter_events(operation)
    )

    if not events:
        return OperationalProjection(
            schema_version="1.0.0",
            generated_at=now,
            operation=operation,
            schedule_owner=(
                "AIControlCenter Scheduler"
            ),
            overall_health=HealthState.UNKNOWN,
            freshness_state=FreshnessState.UNKNOWN,
            latest_state=None,
            latest_run_id=None,
            last_scheduled_at=None,
            last_started_at=None,
            last_success_at=None,
            last_failure_at=None,
            last_missed_at=None,
            duration_ms=None,
            scheduling_latency_ms=None,
            missed_run=False,
            backup_verification=None,
            severity_signals=tuple(
                severity_signals
            ),
        )

    grouped: dict[
        UUID,
        list[ExecutionEvent],
    ] = {}

    for event in events:
        grouped.setdefault(
            event.run_id,
            [],
        ).append(event)

    latest_sequence = max(
        grouped.values(),
        key=lambda sequence: (
            sequence[0].scheduled_for,
            sequence[-1].recorded_at,
        ),
    )
    latest_state = project_execution_state(
        tuple(latest_sequence)
    )
    latest_terminal = latest_sequence[-1]

    successful = last_success(
        events,
        operation,
    )
    failed = last_failure(
        events,
        operation,
    )

    scheduled_events = [
        event
        for event in events
        if (
            event.event_type
            is EventType.RUN_SCHEDULED
        )
    ]
    started_events = [
        event
        for event in events
        if (
            event.event_type
            is EventType.RUN_STARTED
        )
    ]
    missed_events = [
        event
        for event in events
        if (
            event.event_type
            is EventType.RUN_MISSED
        )
    ]

    last_scheduled_event = max(
        scheduled_events,
        key=lambda event: event.occurred_at,
    )
    last_started_event = (
        max(
            started_events,
            key=lambda event: event.occurred_at,
        )
        if started_events
        else None
    )
    last_missed_event = (
        max(
            missed_events,
            key=lambda event: event.occurred_at,
        )
        if missed_events
        else None
    )

    if successful is None:
        freshness = FreshnessState.UNKNOWN
    else:
        age_seconds = (
            now - successful.occurred_at
        ).total_seconds()

        if age_seconds < 0:
            raise ValueError(
                "generated_at precedes last success"
            )

        if (
            age_seconds
            < freshness_warning_seconds
        ):
            freshness = FreshnessState.FRESH
        elif (
            age_seconds
            < freshness_critical_seconds
        ):
            freshness = FreshnessState.WARNING
        else:
            freshness = FreshnessState.CRITICAL

    has_completed_observation = any(
        event.event_type
        in {
            EventType.RUN_SUCCEEDED,
            EventType.RUN_FAILED,
            EventType.RUN_MISSED,
        }
        for event in events
    )

    overall_health = calculate_health(
        OperationalHealthInput(
            has_completed_observation=(
                has_completed_observation
            ),
            freshness=freshness,
            latest_execution_failed=(
                latest_state
                is ExecutionState.FAILED
            ),
            missed_run=(
                latest_state
                is ExecutionState.MISSED
            ),
            backup_verification_failed=(
                operation
                is Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
                and latest_state
                is ExecutionState.FAILED
            ),
        )
    )

    backup_verification = None

    if (
        operation
        is Operation.SQLITE_ONLINE_BACKUP_VERIFICATION
        and successful is not None
    ):
        backup_verification = dict(
            successful.evidence
        )

    return OperationalProjection(
        schema_version="1.0.0",
        generated_at=now,
        operation=operation,
        schedule_owner=(
            "AIControlCenter Scheduler"
        ),
        overall_health=overall_health,
        freshness_state=freshness,
        latest_state=latest_state,
        latest_run_id=latest_sequence[0].run_id,
        last_scheduled_at=(
            last_scheduled_event.occurred_at
        ),
        last_started_at=(
            last_started_event.occurred_at
            if last_started_event
            else None
        ),
        last_success_at=(
            successful.occurred_at
            if successful
            else None
        ),
        last_failure_at=(
            failed.occurred_at
            if failed
            else None
        ),
        last_missed_at=(
            last_missed_event.occurred_at
            if last_missed_event
            else None
        ),
        duration_ms=latest_terminal.duration_ms,
        scheduling_latency_ms=(
            next(
                (
                    event.scheduling_latency_ms
                    for event in latest_sequence
                    if (
                        event.event_type
                        is EventType.RUN_STARTED
                    )
                ),
                None,
            )
        ),
        missed_run=(
            latest_state
            is ExecutionState.MISSED
        ),
        backup_verification=backup_verification,
        severity_signals=tuple(
            severity_signals
        ),
    )
