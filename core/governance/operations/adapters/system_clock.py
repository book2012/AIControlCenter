from __future__ import annotations

from datetime import datetime, timezone

from core.governance.operations.domain.ports import Clock


class SystemUTCClock(Clock):
    """Production clock returning timezone-aware UTC timestamps."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)
