from datetime import datetime, timezone

import pytest

from core.governance.operations.domain.events import (
    DomainValidationError,
)
from core.governance.operations.domain.metrics import (
    duration_ms,
    observation_age_ms,
    scheduling_latency_ms,
)


def utc(second: int) -> datetime:
    return datetime(
        2026,
        7,
        21,
        1,
        0,
        second,
        tzinfo=timezone.utc,
    )


def test_metrics_are_non_negative_milliseconds():
    assert duration_ms(utc(1), utc(4)) == 3000
    assert scheduling_latency_ms(utc(1), utc(6)) == 5000
    assert observation_age_ms(utc(1), utc(11)) == 10000


def test_negative_metric_is_rejected():
    with pytest.raises(
        DomainValidationError,
        match="non-negative",
    ):
        duration_ms(utc(5), utc(4))
