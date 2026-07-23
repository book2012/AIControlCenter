"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    ContentSnapshot,
    ContentSnapshotPage,
    PageRequest,
    ReadContext,
)

__all__ = ('CmsReadPort',)


class CmsReadPort(Protocol):
    """Read-only or compute-only application port."""

    async def get_content(
        self,
        *,
        context: ReadContext,
        content_id: str,
    ) -> ContentSnapshot | None:
        ...

    async def list_content(
        self,
        *,
        context: ReadContext,
        page: PageRequest,
    ) -> ContentSnapshotPage:
        ...
