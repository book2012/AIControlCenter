"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    ReadContext,
    SchemaDiscoveryResult,
)

__all__ = ('SchemaDiscoveryPort',)


class SchemaDiscoveryPort(Protocol):
    """Read-only or compute-only application port."""

    async def discover_schema(
        self,
        *,
        context: ReadContext,
        adapter_name: str,
    ) -> SchemaDiscoveryResult:
        ...
