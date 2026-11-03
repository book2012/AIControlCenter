"""Host-owned legacy composition bridge; product behavior lives in the plugin.

Configuration loading and real provider/secret selection stay outside the plugin.
"""
from dataclasses import fields
from core.shopping.config import ShoppingSettings, load_shopping_settings
from core.shopping.factory import create_catalog_adapter
from aicc_plugin_shopping.catalog_settings import CatalogSettings
from aicc_plugin_shopping.catalog_service import ShoppingService as CatalogService, ProductNotFoundError


class ShoppingService(CatalogService):
    def __init__(self, settings: ShoppingSettings | None = None, catalog=None, *, read_telemetry=None):
        host_settings = settings or load_shopping_settings()
        reader = catalog or create_catalog_adapter(
            host_settings.catalog_adapter,
            woocommerce_base_url=host_settings.woocommerce_base_url,
            woocommerce_connect_base_url=host_settings.woocommerce_connect_base_url,
            woocommerce_consumer_key=host_settings.woocommerce_consumer_key,
            woocommerce_consumer_secret=host_settings.woocommerce_consumer_secret,
            timeout_seconds=host_settings.woocommerce_timeout_seconds,
        )
        public_settings = CatalogSettings(**{item.name: getattr(host_settings, item.name)
                                           for item in fields(CatalogSettings)})
        super().__init__(public_settings, reader, read_telemetry=read_telemetry)
