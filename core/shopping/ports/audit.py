"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    AuditEvent,
    AuditEventPage,
    PageRequest,
    ReadContext,
)

__all__ = ('AuditPort',)


class AuditPort(Protocol):
    """Read-only or compute-only application port."""

    async def get_event(
        self,
        *,
        context: ReadContext,
        event_id: str,
    ) -> AuditEvent | None:
        ...

    async def list_events(
        self,
        *,
        context: ReadContext,
        correlation_id: str | None,
        page: PageRequest,
    ) -> AuditEventPage:
        ...
