"""Governance audit operations metric calculations."""

from datetime import datetime

from .events import elapsed_milliseconds


def duration_ms(
    started_at: datetime,
    finished_at: datetime,
) -> int:
    return elapsed_milliseconds(
        started_at,
        finished_at,
        field_name="duration_ms",
    )


def scheduling_latency_ms(
    scheduled_for: datetime,
    started_at: datetime,
) -> int:
    return elapsed_milliseconds(
        scheduled_for,
        started_at,
        field_name="scheduling_latency_ms",
    )


def observation_age_ms(
    last_success_at: datetime,
    observed_at: datetime,
) -> int:
    return elapsed_milliseconds(
        last_success_at,
        observed_at,
        field_name="observation_age_ms",
    )
