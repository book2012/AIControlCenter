"""Operational health projection policy."""

from dataclasses import dataclass
from enum import Enum


class HealthState(str, Enum):
    UNKNOWN = "UNKNOWN"
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


class FreshnessState(str, Enum):
    UNKNOWN = "UNKNOWN"
    FRESH = "FRESH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class OperationalHealthInput:
    has_completed_observation: bool
    freshness: FreshnessState
    latest_execution_failed: bool = False
    warning_metric_exceeded: bool = False
    critical_condition: bool = False
    missed_run: bool = False
    backup_verification_failed: bool = False
    persistence_unavailable: bool = False
    append_only_violation: bool = False


def calculate_health(
    state: OperationalHealthInput,
) -> HealthState:
    if any(
        (
            state.critical_condition,
            state.missed_run,
            state.backup_verification_failed,
            state.persistence_unavailable,
            state.append_only_violation,
            state.freshness is FreshnessState.CRITICAL,
        )
    ):
        return HealthState.UNHEALTHY

    if (
        not state.has_completed_observation
        or state.freshness is FreshnessState.UNKNOWN
    ):
        return HealthState.UNKNOWN

    if any(
        (
            state.latest_execution_failed,
            state.warning_metric_exceeded,
            state.freshness is FreshnessState.WARNING,
        )
    ):
        return HealthState.DEGRADED

    return HealthState.HEALTHY
