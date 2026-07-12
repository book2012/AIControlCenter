import pytest

from core.shopping.adapters.mock_commerce import (
    MockCommerceCatalogAdapter,
)
from core.shopping.adapters.woocommerce_rest import (
    WooCommerceRESTAdapter,
)
from core.shopping.config import load_shopping_settings
from core.shopping.service import ShoppingService


SHOPPING_ENV_NAMES = [
    "SHOPPING_CATALOG_ADAPTER",
    "WOOCOMMERCE_BASE_URL",
    "WOOCOMMERCE_INTERNAL_BASE_URL",
    "WOOCOMMERCE_CONSUMER_KEY",
    "WOOCOMMERCE_CONSUMER_SECRET",
    "WOOCOMMERCE_TIMEOUT_SECONDS",
]


@pytest.fixture(autouse=True)
def clean_shopping_env(monkeypatch):
    for name in SHOPPING_ENV_NAMES:
        monkeypatch.delenv(
            name,
            raising=False,
        )


def test_settings_default_to_mock_adapter():
    settings = load_shopping_settings()

    assert settings.catalog_adapter == "mock"
    assert settings.catalog_adapter_supported is True
    assert settings.woocommerce_timeout_seconds == 10


def test_service_uses_mock_adapter_by_default():
    service = ShoppingService()

    assert isinstance(
        service.catalog,
        MockCommerceCatalogAdapter,
    )


def test_settings_load_woocommerce_values(
    monkeypatch,
):
    monkeypatch.setenv(
        "SHOPPING_CATALOG_ADAPTER",
        "woocommerce",
    )
    monkeypatch.setenv(
        "WOOCOMMERCE_BASE_URL",
        "http://bokstory.iptime.org:58088",
    )
    monkeypatch.setenv(
        "WOOCOMMERCE_INTERNAL_BASE_URL",
        "http://127.0.0.1:8088",
    )
    monkeypatch.setenv(
        "WOOCOMMERCE_CONSUMER_KEY",
        "ck_test",
    )
    monkeypatch.setenv(
        "WOOCOMMERCE_CONSUMER_SECRET",
        "cs_test",
    )
    monkeypatch.setenv(
        "WOOCOMMERCE_TIMEOUT_SECONDS",
        "15",
    )

    service = ShoppingService()

    assert isinstance(
        service.catalog,
        WooCommerceRESTAdapter,
    )
    assert service.catalog.base_url == (
        "http://bokstory.iptime.org:58088"
    )
    assert service.catalog.connect_base_url == (
        "http://127.0.0.1:8088"
    )
    assert service.catalog.timeout_seconds == 15


def test_invalid_timeout_is_rejected(
    monkeypatch,
):
    monkeypatch.setenv(
        "WOOCOMMERCE_TIMEOUT_SECONDS",
        "invalid",
    )

    with pytest.raises(
        ValueError,
        match="must be an integer",
    ):
        load_shopping_settings()


def test_unsupported_adapter_marks_not_ready(
    monkeypatch,
):
    monkeypatch.setenv(
        "SHOPPING_CATALOG_ADAPTER",
        "shopify",
    )

    settings = load_shopping_settings()

    assert settings.catalog_adapter_supported is False
