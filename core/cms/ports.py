from __future__ import annotations

from typing import Protocol

from core.cms.models import ContentSnapshot, ContentSnapshotPage, PageRequest, ReadContext


class CmsReadPort(Protocol):
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
