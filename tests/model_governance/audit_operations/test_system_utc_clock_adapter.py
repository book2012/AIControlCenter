from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone

from core.governance.operations.adapters.system_clock import (
    SystemUTCClock,
)


def test_system_utc_clock_returns_aware_utc_datetime() -> None:
    clock = SystemUTCClock()
    before = datetime.now(timezone.utc)
    value = clock.now()
    after = datetime.now(timezone.utc)

    assert before <= value <= after
    assert value.tzinfo is not None
    assert value.utcoffset() == timedelta(0)


def test_system_utc_clock_matches_clock_method_contract() -> None:
    signature = inspect.signature(
        SystemUTCClock.now
    )

    assert list(signature.parameters) == ["self"]
    assert isinstance(SystemUTCClock(), SystemUTCClock)
