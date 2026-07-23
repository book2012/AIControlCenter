"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    AdapterHealth,
    ReadContext,
)

__all__ = ('AdapterHealthPort',)


class AdapterHealthPort(Protocol):
    """Read-only or compute-only application port."""

    async def get_health(
        self,
        *,
        context: ReadContext,
        adapter_name: str,
    ) -> AdapterHealth:
        ...
