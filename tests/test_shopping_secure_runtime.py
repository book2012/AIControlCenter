from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.shopping.secure_runtime import (
    SHOPPING_RUNTIME_PROFILE_ENV,
    ShoppingSecureRuntimeError,
    WooCommerceReadSecretFileProvider,
    build_default_shopping_service,
    load_secure_woocommerce_read_settings,
    secure_runtime_contract_manifest,
)
from core.shopping.product_drafts.deployment.live import (
    WooCommerceControlledWriteAdapter,
)


def write_secret(
    root: Path,
    *,
    permission: str = "read_only",
) -> Path:
    root.mkdir(mode=0o700)

    path = root / "shopping-woocommerce-read.env"

    path.write_text(
        "\n".join(
            [
                (
                    "SHOPPING_WOOCOMMERCE_BASE_URL="
                    "https://commerce.example.test"
                ),
                (
                    "SHOPPING_WOOCOMMERCE_CONSUMER_KEY="
                    "ck_test"
                ),
                (
                    "SHOPPING_WOOCOMMERCE_CONSUMER_SECRET="
                    "cs_test"
                ),
                (
                    "SHOPPING_WOOCOMMERCE_API_KEY_PERMISSION="
                    f"{permission}"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    path.chmod(0o600)
    return path


def clear_shopping_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "SHOPPING_ENABLED",
        "SHOPPING_ENVIRONMENT",
        "SHOPPING_RUNTIME",
        "SHOPPING_DEPLOYMENT_TARGET",
        "SHOPPING_CATALOG_ADAPTER",
        "SHOPPING_WRITE_MODE",
        "SHOPPING_APPROVAL_REQUIRED",
        "SHOPPING_AUTOMATION_ENABLED",
        "SHOPPING_AI_ENABLED",
        "WOOCOMMERCE_BASE_URL",
        "WOOCOMMERCE_INTERNAL_BASE_URL",
        "WOOCOMMERCE_CONSUMER_KEY",
        "WOOCOMMERCE_CONSUMER_SECRET",
        "WOOCOMMERCE_TIMEOUT_SECONDS",
        SHOPPING_RUNTIME_PROFILE_ENV,
    ):
        monkeypatch.delenv(name, raising=False)


def test_secure_provider_loads_read_only_secret(
    tmp_path: Path,
) -> None:
    path = write_secret(tmp_path / "woocommerce")

    secret = WooCommerceReadSecretFileProvider(
        path
    ).load()

    assert secret.base_url == (
        "https://commerce.example.test"
    )
    assert secret.consumer_key == "ck_test"
    assert secret.consumer_secret == "cs_test"
    assert secret.permission == "READ_ONLY"


def test_secure_provider_rejects_insecure_file_mode(
    tmp_path: Path,
) -> None:
    path = write_secret(tmp_path / "woocommerce")
    path.chmod(0o644)

    with pytest.raises(
        ShoppingSecureRuntimeError,
        match="credential_mode_0600_required",
    ):
        WooCommerceReadSecretFileProvider(
            path
        ).load()


def test_secure_provider_rejects_write_permission(
    tmp_path: Path,
) -> None:
    path = write_secret(
        tmp_path / "woocommerce",
        permission="read_write",
    )

    with pytest.raises(
        ShoppingSecureRuntimeError,
        match="woocommerce_permission_read_only_required",
    ):
        WooCommerceReadSecretFileProvider(
            path
        ).load()


def test_secure_settings_do_not_mutate_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_shopping_environment(monkeypatch)
    path = write_secret(tmp_path / "woocommerce")

    before = dict(os.environ)

    settings = load_secure_woocommerce_read_settings(
        secret_path=path,
    )

    assert dict(os.environ) == before
    assert settings.enabled is True
    assert settings.catalog_adapter == "woocommerce"
    assert settings.write_mode == "read_only"
    assert settings.approval_required is True
    assert settings.automation_enabled is False
    assert settings.ai_enabled is False
    assert settings.woocommerce_consumer_key == (
        "ck_test"
    )


def test_default_profile_preserves_mock_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_shopping_environment(monkeypatch)

    service = build_default_shopping_service(
        environment={},
    )

    assert service.integration_status()[
        "catalog_adapter"
    ] == "mock"


def test_default_runtime_does_not_construct_live_write_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_constructor(*args, **kwargs):
        raise AssertionError("live write adapter constructed")

    monkeypatch.setattr(
        WooCommerceControlledWriteAdapter,
        "__init__",
        forbidden_constructor,
    )

    service = build_default_shopping_service(environment={})

    assert service.capabilities()["write_executor_available"] is False


def test_woocommerce_profile_uses_secure_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_shopping_environment(monkeypatch)
    path = write_secret(tmp_path / "woocommerce")

    service = build_default_shopping_service(
        environment={
            SHOPPING_RUNTIME_PROFILE_ENV: (
                "woocommerce_read_only"
            )
        },
        secret_path=path,
    )

    integration = service.integration_status()
    capabilities = service.capabilities()

    assert integration["catalog_adapter"] == (
        "woocommerce"
    )
    assert integration["read_only"] is True
    assert capabilities["write_catalog"] is False
    assert capabilities["approval_required"] is True


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(
        ShoppingSecureRuntimeError,
        match="runtime_profile_unsupported",
    ):
        build_default_shopping_service(
            environment={
                SHOPPING_RUNTIME_PROFILE_ENV: (
                    "production_write"
                )
            }
        )


def test_secure_runtime_contract_freezes_safety() -> None:
    contract = secure_runtime_contract_manifest()

    assert contract["profile_contains_secret"] is False
    assert (
        contract["credential_values_in_plist_allowed"]
        is False
    )
    assert (
        contract["process_environment_secret_mutation"]
        is False
    )
    assert contract["write_mode"] == "read_only"
    assert contract["approval_required"] is True
    assert contract["automation_enabled"] is False
    assert contract["ai_enabled"] is False
    assert contract["write_methods_added"] is False
    assert contract["write_executor_available"] is False
    assert contract["production_mutation_authorized"] is False
    assert (
        contract["persistent_activation_authorized"]
        is False
    )
