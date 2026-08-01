from __future__ import annotations

import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core.shopping.config import load_shopping_settings
from core.shopping.service import ShoppingService


SHOPPING_RUNTIME_PROFILE_ENV = (
    "AICONTROLCENTER_SHOPPING_PROFILE"
)

WOOCOMMERCE_READ_ONLY_PROFILE = (
    "woocommerce_read_only"
)

DEFAULT_WOOCOMMERCE_READ_SECRET_PATH = (
    Path.home()
    / "Library/Application Support/AIControlCenter"
    / "secrets/woocommerce"
    / "shopping-woocommerce-read.env"
)


class ShoppingSecureRuntimeError(ValueError):
    """Raised when the secure Shopping runtime boundary is invalid."""


@dataclass(frozen=True, slots=True)
class WooCommerceReadSecret:
    base_url: str
    consumer_key: str
    consumer_secret: str
    permission: str


class WooCommerceReadSecretFileProvider:
    """Loads a read-only WooCommerce credential from a protected file."""

    _BASE_URL = "SHOPPING_WOOCOMMERCE_BASE_URL"
    _CONSUMER_KEY = "SHOPPING_WOOCOMMERCE_CONSUMER_KEY"
    _CONSUMER_SECRET = (
        "SHOPPING_WOOCOMMERCE_CONSUMER_SECRET"
    )
    _PERMISSION = (
        "SHOPPING_WOOCOMMERCE_API_KEY_PERMISSION"
    )

    _REQUIRED_KEYS = frozenset(
        {
            _BASE_URL,
            _CONSUMER_KEY,
            _CONSUMER_SECRET,
            _PERMISSION,
        }
    )

    _ASSIGNMENT = re.compile(
        r"^(?:export\s+)?"
        r"([A-Za-z_][A-Za-z0-9_]*)"
        r"\s*=\s*(.*)$"
    )

    def __init__(
        self,
        path: Path | str = (
            DEFAULT_WOOCOMMERCE_READ_SECRET_PATH
        ),
    ) -> None:
        self._path = Path(path).expanduser()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> WooCommerceReadSecret:
        self._validate_boundary()
        values = self._parse()

        permission = (
            values[self._PERMISSION]
            .strip()
            .lower()
            .replace("-", "_")
        )

        if permission not in {
            "read",
            "read_only",
            "readonly",
        }:
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "woocommerce_permission_read_only_required"
            )

        base_url = values[self._BASE_URL]
        parsed_url = urlparse(base_url)

        if (
            parsed_url.scheme not in {"http", "https"}
            or not parsed_url.hostname
        ):
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "woocommerce_base_url_invalid"
            )

        return WooCommerceReadSecret(
            base_url=base_url,
            consumer_key=values[self._CONSUMER_KEY],
            consumer_secret=values[
                self._CONSUMER_SECRET
            ],
            permission="READ_ONLY",
        )

    def descriptor(self) -> dict[str, Any]:
        return {
            "provider": type(self).__name__,
            "path_role": (
                "WOOCOMMERCE_READ_ONLY_CREDENTIAL_FILE"
            ),
            "expected_file_mode": "0o600",
            "expected_parent_mode": "0o700",
            "symlink_allowed": False,
            "secret_values_exposed": False,
        }

    def _validate_boundary(self) -> None:
        path = self._path

        if not path.exists():
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_file_not_found"
            )

        if path.is_symlink() or not path.is_file():
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_regular_file_required"
            )

        metadata = path.lstat()

        if metadata.st_uid != os.getuid():
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_owner_invalid"
            )

        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_mode_0600_required"
            )

        parent = path.parent

        if parent.is_symlink() or not parent.is_dir():
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_parent_directory_required"
            )

        parent_metadata = parent.lstat()

        if parent_metadata.st_uid != os.getuid():
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_parent_owner_invalid"
            )

        if (
            stat.S_IMODE(parent_metadata.st_mode)
            != 0o700
        ):
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_parent_mode_0700_required"
            )

    def _parse(self) -> dict[str, str]:
        values: dict[str, str] = {}

        for line_number, raw_line in enumerate(
            self._path.read_text(
                encoding="utf-8",
            ).splitlines(),
            start=1,
        ):
            line = raw_line.strip()

            if not line or line.startswith("#"):
                continue

            match = self._ASSIGNMENT.match(line)

            if not match:
                raise ShoppingSecureRuntimeError(
                    "shopping.secure_runtime."
                    "credential_line_malformed"
                )

            key = match.group(1)

            if key not in self._REQUIRED_KEYS:
                raise ShoppingSecureRuntimeError(
                    "shopping.secure_runtime."
                    "credential_key_unsupported"
                )

            if key in values:
                raise ShoppingSecureRuntimeError(
                    "shopping.secure_runtime."
                    "credential_key_duplicate"
                )

            value = self._normalize_value(
                match.group(2)
            )

            if not value:
                raise ShoppingSecureRuntimeError(
                    "shopping.secure_runtime."
                    "credential_value_required"
                )

            values[key] = value

        missing = self._REQUIRED_KEYS - values.keys()

        if missing:
            raise ShoppingSecureRuntimeError(
                "shopping.secure_runtime."
                "credential_keys_missing"
            )

        return values

    @staticmethod
    def _normalize_value(raw: str) -> str:
        value = raw.strip()

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            return value[1:-1]

        return value


def load_secure_woocommerce_read_settings(
    *,
    secret_path: Path | str = (
        DEFAULT_WOOCOMMERCE_READ_SECRET_PATH
    ),
):
    """Builds safe WooCommerce settings without mutating os.environ."""

    base = load_shopping_settings()
    secret = WooCommerceReadSecretFileProvider(
        secret_path
    ).load()

    return replace(
        base,
        enabled=True,
        catalog_adapter="woocommerce",
        write_mode="read_only",
        approval_required=True,
        automation_enabled=False,
        ai_enabled=False,
        woocommerce_base_url=secret.base_url,
        woocommerce_consumer_key=secret.consumer_key,
        woocommerce_consumer_secret=(
            secret.consumer_secret
        ),
    )


def build_default_shopping_service(
    *,
    environment: Mapping[str, str] | None = None,
    secret_path: Path | str = (
        DEFAULT_WOOCOMMERCE_READ_SECRET_PATH
    ),
) -> ShoppingService:
    """Selects a safe Shopping runtime using a non-secret profile."""

    source = (
        environment
        if environment is not None
        else os.environ
    )

    profile = source.get(
        SHOPPING_RUNTIME_PROFILE_ENV,
        "",
    ).strip().lower()

    if profile in {
        "",
        "default",
        "mock",
    }:
        return ShoppingService()

    if profile == WOOCOMMERCE_READ_ONLY_PROFILE:
        return ShoppingService(
            settings=load_secure_woocommerce_read_settings(
                secret_path=secret_path,
            )
        )

    raise ShoppingSecureRuntimeError(
        "shopping.secure_runtime."
        "runtime_profile_unsupported"
    )


def secure_runtime_contract_manifest() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "activation_environment_variable": (
            SHOPPING_RUNTIME_PROFILE_ENV
        ),
        "woocommerce_profile": (
            WOOCOMMERCE_READ_ONLY_PROFILE
        ),
        "profile_contains_secret": False,
        "credential_values_in_git_allowed": False,
        "credential_values_in_plist_allowed": False,
        "credential_values_in_shell_history_allowed": False,
        "process_environment_secret_mutation": False,
        "secret_file_mode": "0o600",
        "secret_parent_mode": "0o700",
        "symlink_allowed": False,
        "write_mode": "read_only",
        "approval_required": True,
        "automation_enabled": False,
        "ai_enabled": False,
        "write_methods_added": False,
        "ubuntu_secret_loading_allowed": False,
        "persistent_activation_authorized": False,
    }


__all__ = (
    "DEFAULT_WOOCOMMERCE_READ_SECRET_PATH",
    "SHOPPING_RUNTIME_PROFILE_ENV",
    "WOOCOMMERCE_READ_ONLY_PROFILE",
    "ShoppingSecureRuntimeError",
    "WooCommerceReadSecret",
    "WooCommerceReadSecretFileProvider",
    "build_default_shopping_service",
    "load_secure_woocommerce_read_settings",
    "secure_runtime_contract_manifest",
)
