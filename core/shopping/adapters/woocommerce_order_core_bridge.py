from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from core.shopping.order_core.domain import (
    OrderContractError,
    OrderListQuery,
    OrderSnapshot,
)


class ExistingWooCommerceOrderReadStack(
    Protocol
):
    def get_order_summary(
        self,
        context: Any,
        order_id: str,
    ) -> Any | None:
        ...


class WooCommerceOrderCoreBridgeError(
    RuntimeError
):
    def __init__(
        self,
        reason_code: str,
    ) -> None:
        self._reason_code = str(
            reason_code
        )

        super().__init__(
            self._reason_code
        )

    @property
    def reason_code(self) -> str:
        return self._reason_code


OrderSummaryProjector = Callable[
    [Any],
    OrderSnapshot,
]

ReadContextProvider = Callable[
    [],
    Any,
]


@dataclass(frozen=True, slots=True)
class WooCommerceExistingStackOrderReadBridge:
    """
    Thin OrderReadPort bridge over the existing
    WooCommerceCommerceReadAdapter boundary.

    This class intentionally owns no HTTP,
    credentials, retry policy or provider
    authorization implementation.
    """

    existing_read_stack: (
        ExistingWooCommerceOrderReadStack
    )

    read_context_provider: (
        ReadContextProvider
    )

    order_summary_projector: (
        OrderSummaryProjector
    )

    def list_orders(
        self,
        query: OrderListQuery,
    ) -> Sequence[OrderSnapshot]:
        if type(query) is not OrderListQuery:
            raise OrderContractError(
                "query:TYPE"
            )

        raise WooCommerceOrderCoreBridgeError(
            "LIST_ORDERS_NOT_SUPPORTED_BY_"
            "EXISTING_WOO_READ_STACK"
        )

    def read_order(
        self,
        provider_order_id: int,
    ) -> OrderSnapshot | None:
        if (
            type(provider_order_id)
            is not int
            or provider_order_id <= 0
        ):
            raise OrderContractError(
                "provider_order_id:INVALID"
            )

        context = (
            self.read_context_provider()
        )

        summary = (
            self.existing_read_stack
            .get_order_summary(
                context,
                str(provider_order_id),
            )
        )

        if summary is None:
            return None

        snapshot = (
            self.order_summary_projector(
                summary
            )
        )

        if type(snapshot) is not OrderSnapshot:
            raise WooCommerceOrderCoreBridgeError(
                "PROJECTOR_RESULT_INVALID"
            )

        if (
            snapshot.provider
            != "woocommerce"
        ):
            raise WooCommerceOrderCoreBridgeError(
                "PROJECTOR_PROVIDER_MISMATCH"
            )

        if (
            snapshot.provider_order_id
            != provider_order_id
        ):
            raise WooCommerceOrderCoreBridgeError(
                "PROJECTOR_ORDER_ID_MISMATCH"
            )

        return snapshot

    @property
    def provider(self) -> str:
        return "woocommerce"

    @property
    def read_order_enabled(self) -> bool:
        return True

    @property
    def list_orders_enabled(self) -> bool:
        return False

    @property
    def owns_network_transport(self) -> bool:
        return False

    @property
    def owns_credentials(self) -> bool:
        return False

    @property
    def writes_enabled(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "WooCommerceExistingStackOrderReadBridge("
            "provider=woocommerce,"
            "read_order_enabled=True,"
            "list_orders_enabled=False,"
            "owns_network_transport=False,"
            "owns_credentials=False,"
            "writes_enabled=False)"
        )
