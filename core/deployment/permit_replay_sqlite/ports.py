"""Read-only port for durable permit/replay state inspection."""

from typing import Protocol

from core.deployment.permit_replay_sqlite.models import PermitReplayInspectionReport


class PermitReplayReadOnlyPort(Protocol):
    def inspect(self, *, inspected_at: str) -> PermitReplayInspectionReport: ...
