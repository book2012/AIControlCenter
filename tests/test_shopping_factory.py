import pytest

from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.adapters.woocommerce_rest import (
    WooCommerceRESTAdapter,
)
from core.shopping.factory import (
    ShoppingAdapterConfigurationError,
    create_catalog_adapter,
)


def test_factory_creates_mock_adapter():
    adapter = create_catalog_adapter("mock")

    assert isinstance(
        adapter,
        MockCommerceCatalogAdapter,
    )


def test_factory_normalizes_adapter_name():
    adapter = create_catalog_adapter("  MOCK  ")

    assert isinstance(
        adapter,
        MockCommerceCatalogAdapter,
    )


def test_factory_creates_woocommerce_adapter():
    adapter = create_catalog_adapter(
        "woocommerce",
        woocommerce_base_url="http://bokstory.iptime.org:58088",
        woocommerce_connect_base_url="http://127.0.0.1:8088",
        woocommerce_consumer_key="ck_test",
        woocommerce_consumer_secret="cs_test",
        timeout_seconds=15,
    )

    assert isinstance(
        adapter,
        WooCommerceRESTAdapter,
    )
    assert adapter.base_url == "http://bokstory.iptime.org:58088"
    assert adapter.connect_base_url == "http://127.0.0.1:8088"
    assert adapter.consumer_key == "ck_test"
    assert adapter.consumer_secret == "cs_test"
    assert adapter.timeout_seconds == 15


@pytest.mark.parametrize(
    "missing_name,settings",
    [
        (
            "woocommerce_base_url",
            {
                "woocommerce_base_url": None,
                "woocommerce_consumer_key": "ck_test",
                "woocommerce_consumer_secret": "cs_test",
            },
        ),
        (
            "woocommerce_consumer_key",
            {
                "woocommerce_base_url": "http://127.0.0.1:8088",
                "woocommerce_consumer_key": None,
                "woocommerce_consumer_secret": "cs_test",
            },
        ),
        (
            "woocommerce_consumer_secret",
            {
                "woocommerce_base_url": "http://127.0.0.1:8088",
                "woocommerce_consumer_key": "ck_test",
                "woocommerce_consumer_secret": None,
            },
        ),
    ],
)
def test_factory_rejects_missing_woocommerce_settings(
    missing_name,
    settings,
):
    with pytest.raises(
        ShoppingAdapterConfigurationError,
        match=missing_name,
    ):
        create_catalog_adapter(
            "woocommerce",
            **settings,
        )


def test_factory_rejects_unsupported_adapter():
    with pytest.raises(
        ShoppingAdapterConfigurationError,
        match="Unsupported Shopping catalog adapter",
    ):
        create_catalog_adapter("shopify")
