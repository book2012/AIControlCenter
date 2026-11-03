"""Identity-preserving compatibility exports for the optional shopping domain."""
from aicc_plugin_shopping.order_core import (
    OrderContractError,
    OrderLineItem,
    OrderListQuery,
    OrderNotFoundError,
    OrderReadPort,
    OrderService,
    OrderSnapshot,
)

__all__ = ('OrderContractError', 'OrderLineItem', 'OrderListQuery', 'OrderNotFoundError', 'OrderReadPort', 'OrderService', 'OrderSnapshot')
