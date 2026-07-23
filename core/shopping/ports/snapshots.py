"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    PageRequest,
    ReadContext,
    SnapshotEnvelope,
    SnapshotEnvelopePage,
)

__all__ = ('SnapshotRepositoryPort',)


class SnapshotRepositoryPort(Protocol):
    """Read-only or compute-only application port."""

    async def get_latest_snapshot(
        self,
        *,
        context: ReadContext,
        snapshot_type: str,
        external_id: str,
    ) -> SnapshotEnvelope | None:
        ...

    async def list_snapshots(
        self,
        *,
        context: ReadContext,
        snapshot_type: str,
        page: PageRequest,
    ) -> SnapshotEnvelopePage:
        ...
