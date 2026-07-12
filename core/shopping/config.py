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


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in TRUE_VALUES


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

    @property
    def write_mode_supported(self) -> bool:
        return self.write_mode in SUPPORTED_WRITE_MODES


def load_shopping_settings() -> ShoppingSettings:
    ConfigLoader().load()

    return ShoppingSettings(
        enabled=_env_bool("SHOPPING_ENABLED", True),
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
    )
