"""Transport-neutral read-only Shopping port."""

from __future__ import annotations

from typing import Protocol

from core.shopping.contracts.provisional import (
    OrderSummary,
    PageRequest,
    ProductSnapshot,
    ProductSnapshotPage,
    ReadContext,
)

__all__ = ('CommerceReadPort',)


class CommerceReadPort(Protocol):
    """Read-only or compute-only application port."""

    async def get_product(
        self,
        *,
        context: ReadContext,
        product_id: str,
    ) -> ProductSnapshot | None:
        ...

    async def list_products(
        self,
        *,
        context: ReadContext,
        page: PageRequest,
    ) -> ProductSnapshotPage:
        ...

    async def get_order_summary(
        self,
        *,
        context: ReadContext,
        order_id: str,
    ) -> OrderSummary | None:
        ...
