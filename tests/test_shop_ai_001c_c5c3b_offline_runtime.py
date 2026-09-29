from __future__ import annotations

import ast
import inspect
from datetime import datetime, timezone

import pytest

import core.shopping.adapters.twilio_authenticated_read_secret_delivery as delivery_module
import ops.macos.shopping.twilio_authenticated_read_secret_composition as composition_module

from core.secrets.ports import (
    SecretReference,
    SecretResolverPort,
)
from core.shopping.adapters.twilio_authenticated_read_secret_delivery import (
    TwilioCredentialReferences,
    TwilioOfflineAuthenticatedReadTransportFactory,
    TwilioSecretDeliveryError,
    TwilioSecretDeliveryReason,
)
from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import (
    ProviderActivationState,
    ProviderOperation,
    ProviderRequestIdentity,
)
from ops.macos.shopping.twilio_authenticated_read_secret_composition import (
    build_twilio_authenticated_read_secret_composition,
)


NOW = datetime(2026, 9, 30, 0, 0, tzinfo=timezone.utc)

SID_REF = SecretReference(
    backend="macos.keychain",
    key_name="shopping.twilio.api-key-sid",
)

SECRET_REF = SecretReference(
    backend="macos.keychain",
    key_name="shopping.twilio.api-key-secret",
)

SERVICE = TwilioServiceSid("VA" + "b" * 32)


class ResolverSpy:
    def __init__(self):
        self.calls = 0

    def resolve(self, reference):
        self.calls += 1
        raise AssertionError(
            "C5-C3B must never resolve a secret"
        )


def authority():
    return TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "b" * 32,
    )


def request():
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id="request-c3b-runtime",
            correlation_id="correlation-c3b-runtime",
        ),
        service_sid=SERVICE,
    )


def credentials():
    return TwilioCredentialReferences(
        api_key_sid_reference=SID_REF,
        api_key_secret_reference=SECRET_REF,
    )


def test_existing_secret_resolver_protocol_is_reused() -> None:
    resolver = ResolverSpy()

    assert isinstance(
        resolver,
        SecretResolverPort,
    )


def test_offline_factory_never_resolves_or_constructs() -> None:
    resolver = ResolverSpy()
    auth = authority()
    req = request()

    capability = auth.issue(req)

    factory = TwilioOfflineAuthenticatedReadTransportFactory()

    with pytest.raises(TwilioSecretDeliveryError) as caught:
        factory.create_authenticated_read_transport(
            credentials=credentials(),
            secret_resolver=resolver,
            capability=capability,
        )

    assert (
        caught.value.reason
        is TwilioSecretDeliveryReason.OFFLINE_TRANSPORT_DISABLED
    )

    assert resolver.calls == 0
    assert factory.network_enabled is False
    assert (
        factory.credential_resolution_performed
        is False
    )
    assert factory.transport_constructed is False


def test_composition_remains_contract_only_and_inert() -> None:
    composition = (
        build_twilio_authenticated_read_secret_composition(
            authority=authority(),
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SECRET_REF,
        )
    )

    assert (
        composition.activation_state
        is ProviderActivationState.CONTRACT_ONLY
    )

    assert (
        composition.generic_authorization_model
        == "OFFLINE_DENY_ONLY"
    )

    assert composition.network_enabled is False
    assert (
        composition.credential_resolution_performed
        is False
    )
    assert composition.keychain_accessed is False
    assert composition.transport_constructed is False
    assert composition.provider_transport is None
    assert composition.secret_resolver is None


def test_c3b_has_no_network_or_keychain_runtime_imports() -> None:
    forbidden = {
        "socket",
        "requests",
        "httpx",
        "urllib",
        "twilio",
        "keyring",
        "subprocess",
    }

    for module in (
        delivery_module,
        composition_module,
    ):
        tree = ast.parse(
            inspect.getsource(module)
        )

        roots = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(
                    item.name.split(".", 1)[0]
                    for item in node.names
                )

            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
            ):
                roots.add(
                    node.module.split(".", 1)[0]
                )

        assert roots.isdisjoint(forbidden)


def test_c3b_source_never_calls_resolve_or_consume() -> None:
    for module in (
        delivery_module,
        composition_module,
    ):
        tree = ast.parse(
            inspect.getsource(module)
        )

        called_attributes = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
        }

        assert "resolve" not in called_attributes
        assert "consume" not in called_attributes


def test_c3b_does_not_import_concrete_mac_secret_resolver() -> None:
    source = "\n".join([
        inspect.getsource(delivery_module),
        inspect.getsource(composition_module),
    ])

    assert "provider_secret_resolver" not in source
    assert "MacOSKeychain" not in source
    assert "security find-generic-password" not in source


def test_runtime_repr_has_no_reference_key_names() -> None:
    composition = (
        build_twilio_authenticated_read_secret_composition(
            authority=authority(),
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SECRET_REF,
        )
    )

    rendered = " ".join([
        repr(composition),
        repr(composition.credentials),
        repr(composition.transport_factory),
    ])

    assert SID_REF.key_name not in rendered
    assert SECRET_REF.key_name not in rendered
    assert "api-key-secret" not in rendered
