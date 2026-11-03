from __future__ import annotations

from typing import Protocol, Sequence

from .domain import (
    OrderListQuery,
    OrderSnapshot,
)


class OrderReadPort(Protocol):
    def list_orders(
        self,
        query: OrderListQuery,
    ) -> Sequence[OrderSnapshot]:
        ...

    def read_order(
        self,
        provider_order_id: int,
    ) -> OrderSnapshot | None:
        ...
