from core.governance.operations.application.projection import (
    project_operation,
)
from core.governance.operations.domain.events import (
    ErrorInfo,
    Operation,
    failed_event,
    scheduled_event,
    started_event,
    succeeded_event,
)
from core.governance.operations.domain.health import (
    FreshnessState,
    HealthState,
)
from core.governance.operations.domain.state import (
    ExecutionState,
)

from .application_helpers import (
    temporary_repository,
    utc,
)


def test_empty_projection_is_unknown(tmp_path):
    repository = temporary_repository(tmp_path)

    projection = project_operation(
        repository,
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(1),
    )

    assert (
        projection.overall_health
        is HealthState.UNKNOWN
    )
    assert (
        projection.freshness_state
        is FreshnessState.UNKNOWN
    )
    assert projection.latest_state is None
    assert (
        projection.schedule_owner
        == "AIControlCenter Scheduler"
    )


def test_successful_projection_is_healthy(
    tmp_path,
):
    repository = temporary_repository(tmp_path)
    scheduled = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(2),
    )
    started = started_event(
        scheduled,
        utc(2, 0, 2),
    )
    succeeded = succeeded_event(
        started,
        utc(2, 0, 5),
    )

    for event in (
        scheduled,
        started,
        succeeded,
    ):
        repository.append(event)

    projection = project_operation(
        repository,
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(2, 5),
    )

    assert (
        projection.overall_health
        is HealthState.HEALTHY
    )
    assert (
        projection.latest_state
        is ExecutionState.SUCCEEDED
    )
    assert projection.duration_ms == 3000
    assert projection.scheduling_latency_ms == 2000


def test_latest_failure_after_success_is_degraded(
    tmp_path,
):
    repository = temporary_repository(tmp_path)

    first = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(3),
    )
    first_started = started_event(
        first,
        utc(3, 0, 1),
    )
    first_success = succeeded_event(
        first_started,
        utc(3, 0, 3),
    )

    second = scheduled_event(
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(3, 10),
    )
    second_started = started_event(
        second,
        utc(3, 10, 1),
    )
    second_failed = failed_event(
        second_started,
        utc(3, 10, 3),
        ErrorInfo(
            code="snapshot-failed",
            message="snapshot failed",
        ),
    )

    for event in (
        first,
        first_started,
        first_success,
        second,
        second_started,
        second_failed,
    ):
        repository.append(event)

    projection = project_operation(
        repository,
        Operation.GOVERNANCE_AUDIT_SNAPSHOT,
        utc(3, 12),
    )

    assert (
        projection.latest_state
        is ExecutionState.FAILED
    )
    assert (
        projection.overall_health
        is HealthState.DEGRADED
    )
    assert (
        projection.last_success_at
        == first_success.occurred_at
    )
    assert (
        projection.last_failure_at
        == second_failed.occurred_at
    )
