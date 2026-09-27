from __future__ import annotations

from types import SimpleNamespace

from core.shopping.config import ShoppingSettings
from core.shopping.runtime_composition import (
    FutureProviderComposition, build_shopping_runtime,
)
from ops.macos.shopping.provider_destination_resolver import ProviderDestinationResolver
from ops.macos.shopping.provider_secret_resolver import ProviderSecretResolver


def settings() -> ShoppingSettings:
    return ShoppingSettings(
        enabled=True, environment="test", runtime="virtual",
        deployment_target="mac-mini-m4", write_mode="read_only",
        approval_required=True, automation_enabled=False, ai_enabled=False,
        phone_verification_enabled=True, phone_verification_profile="synthetic.mock",
    )


def test_default_runtime_remains_inert_and_does_not_construct_resolvers() -> None:
    runtime = build_shopping_runtime()
    assert runtime.phone_verification is None
    assert runtime.destination_resolution is None
    assert runtime.secret_resolver is None


def test_explicit_resolvers_are_injected_without_resolving_secret_material() -> None:
    calls = []
    destination = ProviderDestinationResolver()
    secret = ProviderSecretResolver(lambda reference: calls.append(reference) or "secret")
    transport = SimpleNamespace(start=lambda request: None, verify=lambda request: None)
    runtime = build_shopping_runtime(
        settings(), phone_verification_transport=transport,
        destination_resolution=destination, secret_resolver=secret,
    )
    assert runtime.destination_resolution is destination
    assert runtime.secret_resolver is secret
    assert not hasattr(runtime.phone_verification, "secret_resolver")
    assert calls == []


def test_future_provider_bundle_is_explicit_and_non_activating() -> None:
    destination = ProviderDestinationResolver()
    secret = ProviderSecretResolver()
    transport = SimpleNamespace(start=lambda request: None, verify=lambda request: None)
    bundle = FutureProviderComposition(
        provider_profile="future.provider",
        provider_transport=transport,
        destination_resolution=destination,
        secret_resolver=secret,
    )
    runtime = build_shopping_runtime(future_provider_composition=bundle)
    assert runtime.future_provider_composition is bundle
    assert runtime.phone_verification is None
