"""WooCommerce read-only capability integration."""

from .adapter import WooCommerceAdapter, WooCommerceConfiguration
from .composition import build_woocommerce_status_service

__all__ = ("WooCommerceAdapter", "WooCommerceConfiguration", "build_woocommerce_status_service")
