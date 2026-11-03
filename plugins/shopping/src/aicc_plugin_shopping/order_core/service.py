from __future__ import annotations

from dataclasses import dataclass

from .domain import (
    OrderContractError,
    OrderListQuery,
    OrderSnapshot,
)
from .ports import OrderReadPort


class OrderNotFoundError(LookupError):
    def __init__(
        self,
        provider_order_id: int,
    ) -> None:
        self.provider_order_id = (
            provider_order_id
        )
        super().__init__(
            "ORDER_NOT_FOUND"
        )


@dataclass(frozen=True, slots=True)
class OrderService:
    order_reader: OrderReadPort

    def list_orders(
        self,
        query: OrderListQuery,
    ) -> tuple[OrderSnapshot, ...]:
        if type(query) is not OrderListQuery:
            raise OrderContractError(
                "query:TYPE"
            )

        result = tuple(
            self.order_reader.list_orders(
                query
            )
        )

        for order in result:
            if type(order) is not OrderSnapshot:
                raise OrderContractError(
                    "order_reader:INVALID_RESULT"
                )

        return result

    def read_order(
        self,
        provider_order_id: int,
    ) -> OrderSnapshot:
        if (
            type(provider_order_id)
            is not int
            or provider_order_id <= 0
        ):
            raise OrderContractError(
                "provider_order_id:INVALID"
            )

        result = (
            self.order_reader.read_order(
                provider_order_id
            )
        )

        if result is None:
            raise OrderNotFoundError(
                provider_order_id
            )

        if type(result) is not OrderSnapshot:
            raise OrderContractError(
                "order_reader:INVALID_RESULT"
            )

        if (
            result.provider_order_id
            != provider_order_id
        ):
            raise OrderContractError(
                "order_reader:ID_MISMATCH"
            )

        return result
