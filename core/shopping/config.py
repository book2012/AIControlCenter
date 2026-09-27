"""Configuration for the AI Shopping Platform."""

import os
from dataclasses import dataclass

from core.config.loader import ConfigLoader
from core.secrets.ports import SecretReference


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


def _env_bounded_float(
    name: str,
    default: float,
    *,
    minimum: float,
    maximum: float,
) -> float:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error

    if not minimum < value <= maximum:
        raise ValueError(
            f"{name} must be greater than {minimum} and less than or equal to {maximum}"
        )

    return value


def _optional_secret_reference() -> SecretReference | None:
    backend = os.getenv("SHOPPING_PHONE_VERIFICATION_SECRET_BACKEND")
    key_name = os.getenv("SHOPPING_PHONE_VERIFICATION_SECRET_KEY_NAME")
    if backend is None and key_name is None:
        return None
    if backend is None or key_name is None:
        raise ValueError(
            "phone verification secret reference requires backend and key name"
        )
    try:
        return SecretReference(backend=backend, key_name=key_name)
    except ValueError:
        raise ValueError("phone verification secret reference is invalid") from None


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

    # C2 metadata only.  Disabled and unprofiled are both default-safe.
    phone_verification_enabled: bool = False
    phone_verification_profile: str | None = None
    phone_verification_secret_reference: SecretReference | None = None
    phone_verification_timeout_seconds: float = 10.0

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
    phone_profile = os.getenv("SHOPPING_PHONE_VERIFICATION_PROFILE")
    if phone_profile is not None:
        phone_profile = phone_profile.strip()
        if phone_profile.lower() in {"", "disabled", "off", "none"}:
            phone_profile = None

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
        phone_verification_enabled=_env_bool(
            "SHOPPING_PHONE_VERIFICATION_ENABLED",
            False,
        ),
        phone_verification_profile=phone_profile,
        phone_verification_secret_reference=_optional_secret_reference(),
        phone_verification_timeout_seconds=_env_bounded_float(
            "SHOPPING_PHONE_VERIFICATION_TIMEOUT_SECONDS",
            10.0,
            minimum=0.0,
            maximum=30.0,
        ),
    )
