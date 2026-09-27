from __future__ import annotations

from types import SimpleNamespace

from core.shopping.config import ShoppingSettings
from core.shopping.runtime_composition import (
    ShoppingRuntime, build_shopping_runtime,
)


def _settings(**updates) -> ShoppingSettings:
    values = dict(
        enabled=True,
        environment="test",
        runtime="virtual",
        deployment_target="mac-mini-m4",
        write_mode="read_only",
        approval_required=True,
        automation_enabled=False,
        ai_enabled=False,
    )
    values.update(updates)
    return ShoppingSettings(**values)


def test_default_runtime_phone_verification_is_disabled(monkeypatch) -> None:
    constructed = []

    def forbidden(*args, **kwargs):
        constructed.append((args, kwargs))
        raise AssertionError("provider adapter must not be constructed by default")

    monkeypatch.setattr(
        "core.shopping.runtime_composition.ProviderPhoneVerificationAdapter",
        forbidden,
    )
    runtime = build_shopping_runtime()
    assert isinstance(runtime, ShoppingRuntime)
    assert runtime.phone_verification_port is None
    assert runtime.phone_verification is None
    assert constructed == []


def test_missing_or_disabled_profile_does_not_construct_adapter_or_transport(monkeypatch) -> None:
    constructed = []

    def forbidden(*args, **kwargs):
        constructed.append((args, kwargs))
        raise AssertionError("provider adapter must not be constructed")

    monkeypatch.setattr(
        "core.shopping.runtime_composition.ProviderPhoneVerificationAdapter",
        forbidden,
    )
    transport = SimpleNamespace()
    assert build_shopping_runtime(
        settings=_settings(phone_verification_enabled=True),
        phone_verification_transport=transport,
    ).phone_verification_port is None
    assert build_shopping_runtime(
        settings=_settings(
            phone_verification_enabled=True,
            phone_verification_profile="disabled",
        ),
        phone_verification_transport=transport,
    ).phone_verification_port is None
    assert constructed == []


def test_explicit_future_composition_can_inject_transport() -> None:
    transport = SimpleNamespace(start=lambda request: None, verify=lambda request: None)
    runtime = build_shopping_runtime(
        settings=_settings(
            phone_verification_enabled=True,
            phone_verification_profile="synthetic.mock",
        ),
        phone_verification_transport=transport,
    )
    assert runtime.phone_verification_port is not None
