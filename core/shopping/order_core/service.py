"""Identity-preserving compatibility exports for the optional shopping domain."""
from aicc_plugin_shopping.order_core.service import (
    OrderNotFoundError,
    OrderService,
)

__all__ = ('OrderNotFoundError', 'OrderService')
