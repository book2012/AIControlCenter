"""Identity-preserving compatibility exports for the optional shopping domain."""
from aicc_plugin_shopping.order_core.domain import (
    OrderContractError,
    OrderLineItem,
    OrderListQuery,
    OrderSnapshot,
)

__all__ = ('OrderContractError', 'OrderLineItem', 'OrderListQuery', 'OrderSnapshot')
