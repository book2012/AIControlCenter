from core.governance.operations.domain.health import (
    FreshnessState,
    HealthState,
    OperationalHealthInput,
    calculate_health,
)


def test_unknown_is_not_silently_healthy():
    state = OperationalHealthInput(
        has_completed_observation=False,
        freshness=FreshnessState.UNKNOWN,
    )

    assert calculate_health(state) is HealthState.UNKNOWN


def test_warning_condition_is_degraded():
    state = OperationalHealthInput(
        has_completed_observation=True,
        freshness=FreshnessState.FRESH,
        warning_metric_exceeded=True,
    )

    assert calculate_health(state) is HealthState.DEGRADED


def test_critical_condition_takes_precedence():
    state = OperationalHealthInput(
        has_completed_observation=True,
        freshness=FreshnessState.WARNING,
        warning_metric_exceeded=True,
        missed_run=True,
    )

    assert calculate_health(state) is HealthState.UNHEALTHY


def test_fresh_success_is_healthy():
    state = OperationalHealthInput(
        has_completed_observation=True,
        freshness=FreshnessState.FRESH,
    )

    assert calculate_health(state) is HealthState.HEALTHY
