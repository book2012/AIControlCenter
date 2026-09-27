from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from core.secrets.ports import SecretReference
from core.shopping.config import load_shopping_settings


def test_secret_reference_is_frozen_closed_and_value_free() -> None:
    reference = SecretReference(backend="macos.keychain", key_name="shopping.provider")
    assert reference.to_dict() == {
        "backend": "macos.keychain",
        "key_name": "shopping.provider",
    }
    assert set(reference.model_dump()) == {"backend", "key_name"}
    assert "api-value" not in repr(reference)
    with pytest.raises((ValidationError, TypeError, ValueError)):
        reference.backend = "changed"  # type: ignore[misc]
    with pytest.raises((ValidationError, TypeError, ValueError)):
        SecretReference(backend="macos.keychain", key_name="shopping.provider", extra="x")


@pytest.mark.parametrize(
    ("backend", "key_name"),
    [
        ("", "valid.name"),
        ("has space", "valid.name"),
        ("macos.keychain", ""),
        ("macos.keychain", "has space"),
        ("macos/keychain", "valid.name"),
        ("macos.keychain", "../credential"),
    ],
)
def test_secret_reference_rejects_malformed_identifiers(backend: str, key_name: str) -> None:
    with pytest.raises((ValidationError, ValueError, TypeError)):
        SecretReference(backend=backend, key_name=key_name)


def test_c2_settings_are_disabled_by_default_and_do_not_read_secret_values(monkeypatch) -> None:
    before = dict(os.environ)
    settings = load_shopping_settings()
    after = dict(os.environ)
    assert settings.phone_verification_enabled is False
    assert settings.phone_verification_profile is None
    assert settings.phone_verification_secret_reference is None
    assert after == before


def test_c2_settings_accept_metadata_reference_only(monkeypatch) -> None:
    monkeypatch.setenv("SHOPPING_PHONE_VERIFICATION_SECRET_BACKEND", "macos.keychain")
    monkeypatch.setenv("SHOPPING_PHONE_VERIFICATION_SECRET_KEY_NAME", "shopping.provider")
    monkeypatch.setenv("SHOPPING_PHONE_VERIFICATION_TIMEOUT_SECONDS", "30")
    settings = load_shopping_settings()
    assert settings.phone_verification_secret_reference is not None
    assert settings.phone_verification_secret_reference.to_dict() == {
        "backend": "macos.keychain",
        "key_name": "shopping.provider",
    }
    assert settings.phone_verification_timeout_seconds == 30.0


@pytest.mark.parametrize("value", ["0", "31", "-1", "not-a-number"])
def test_c2_timeout_is_positive_and_bounded(monkeypatch, value: str) -> None:
    monkeypatch.setenv("SHOPPING_PHONE_VERIFICATION_TIMEOUT_SECONDS", value)
    with pytest.raises(ValueError):
        load_shopping_settings()
