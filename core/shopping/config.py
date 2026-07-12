"""Configuration for the AI Shopping Platform."""

import os
from dataclasses import dataclass

from core.config.loader import ConfigLoader


TRUE_VALUES = {"1", "true", "yes", "on"}

SUPPORTED_WRITE_MODES = {
    "read_only",
    "draft",
    "approval_required",
    "controlled_write",
    "automated",
}

SUPPORTED_CATALOG_ADAPTERS = {
    "mock",
    "woocommerce",
}


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in TRUE_VALUES


def _env_int(
    name: str,
    default: int,
    minimum: int = 1,
) -> int:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(
            f"{name} must be an integer"
        ) from error

    if value < minimum:
        raise ValueError(
            f"{name} must be greater than or equal to {minimum}"
        )

    return value


@dataclass(frozen=True)
class ShoppingSettings:
    enabled: bool
    environment: str
    runtime: str
    deployment_target: str
    write_mode: str
    approval_required: bool
    automation_enabled: bool
    ai_enabled: bool

    catalog_adapter: str = "mock"
    woocommerce_base_url: str | None = None
    woocommerce_connect_base_url: str | None = None
    woocommerce_consumer_key: str | None = None
    woocommerce_consumer_secret: str | None = None
    woocommerce_timeout_seconds: int = 10

    @property
    def write_mode_supported(self) -> bool:
        return self.write_mode in SUPPORTED_WRITE_MODES

    @property
    def catalog_adapter_supported(self) -> bool:
        return self.catalog_adapter in SUPPORTED_CATALOG_ADAPTERS


def load_shopping_settings() -> ShoppingSettings:
    ConfigLoader().load()

    catalog_adapter = os.getenv(
        "SHOPPING_CATALOG_ADAPTER",
        "mock",
    ).strip().lower()

    return ShoppingSettings(
        enabled=_env_bool(
            "SHOPPING_ENABLED",
            True,
        ),
        environment=os.getenv(
            "SHOPPING_ENVIRONMENT",
            "development",
        ),
        runtime=os.getenv(
            "SHOPPING_RUNTIME",
            "virtual",
        ),
        deployment_target=os.getenv(
            "SHOPPING_DEPLOYMENT_TARGET",
            "mac-mini-m4",
        ),
        write_mode=os.getenv(
            "SHOPPING_WRITE_MODE",
            "read_only",
        ),
        approval_required=_env_bool(
            "SHOPPING_APPROVAL_REQUIRED",
            True,
        ),
        automation_enabled=_env_bool(
            "SHOPPING_AUTOMATION_ENABLED",
            False,
        ),
        ai_enabled=_env_bool(
            "SHOPPING_AI_ENABLED",
            False,
        ),
        catalog_adapter=catalog_adapter,
        woocommerce_base_url=os.getenv(
            "WOOCOMMERCE_BASE_URL",
        ),
        woocommerce_connect_base_url=os.getenv(
            "WOOCOMMERCE_INTERNAL_BASE_URL",
        ),
        woocommerce_consumer_key=os.getenv(
            "WOOCOMMERCE_CONSUMER_KEY",
        ),
        woocommerce_consumer_secret=os.getenv(
            "WOOCOMMERCE_CONSUMER_SECRET",
        ),
        woocommerce_timeout_seconds=_env_int(
            "WOOCOMMERCE_TIMEOUT_SECONDS",
            10,
        ),
    )
