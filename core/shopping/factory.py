from __future__ import annotations

from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.adapters.woocommerce_rest import (
    WooCommerceRESTAdapter,
)
from core.shopping.ports import CommerceCatalogPort


class ShoppingAdapterConfigurationError(ValueError):
    pass


SUPPORTED_CATALOG_ADAPTERS = {
    "mock",
    "woocommerce",
}


def create_catalog_adapter(
    adapter_name: str,
    *,
    woocommerce_base_url: str | None = None,
    woocommerce_connect_base_url: str | None = None,
    woocommerce_consumer_key: str | None = None,
    woocommerce_consumer_secret: str | None = None,
    timeout_seconds: int = 10,
) -> CommerceCatalogPort:
    normalized_name = adapter_name.strip().lower()

    if normalized_name == "mock":
        return MockCommerceCatalogAdapter()

    if normalized_name == "woocommerce":
        missing = [
            name
            for name, value in {
                "woocommerce_base_url": woocommerce_base_url,
                "woocommerce_consumer_key": woocommerce_consumer_key,
                "woocommerce_consumer_secret": woocommerce_consumer_secret,
            }.items()
            if not value
        ]

        if missing:
            raise ShoppingAdapterConfigurationError(
                "Missing WooCommerce adapter settings: "
                + ", ".join(missing)
            )

        return WooCommerceRESTAdapter(
            base_url=woocommerce_base_url,
            consumer_key=woocommerce_consumer_key,
            consumer_secret=woocommerce_consumer_secret,
            timeout_seconds=timeout_seconds,
            connect_base_url=woocommerce_connect_base_url,
        )

    raise ShoppingAdapterConfigurationError(
        "Unsupported Shopping catalog adapter: "
        f"{adapter_name}. "
        "Supported adapters: "
        + ", ".join(sorted(SUPPORTED_CATALOG_ADAPTERS))
    )
