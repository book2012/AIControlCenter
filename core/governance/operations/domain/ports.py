"""Replaceable governance operations domain ports."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol, Sequence
from uuid import UUID

from .events import ExecutionEvent, Operation


class Clock(Protocol):
    def now(self) -> datetime:
        """Return timezone-aware UTC time."""


class ExecutionEventRepository(Protocol):
    def append(self, event: ExecutionEvent) -> None:
        """Append one immutable event."""

    def events_for_run(
        self,
        run_id: UUID,
    ) -> Sequence[ExecutionEvent]:
        """Return append-ordered events for one run."""

    def iter_events(
        self,
        operation: Operation | None = None,
    ) -> Iterable[ExecutionEvent]:
        """Iterate events without mutation access."""
