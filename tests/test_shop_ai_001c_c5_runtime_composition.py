from __future__ import annotations

import pytest

from core.shopping.ports.provider_activation import (
    ProviderActivationError, ProviderActivationState,
)
from ops.macos.shopping.provider_integration_composition import (
    ProviderIntegrationComposition, ProviderSelection, build_contract_only_provider_integration,
    build_disabled_provider_integration, build_provider_integration_composition,
)
from core.shopping.governance.provider_network_authorization import ProviderNetworkAuthorizationGate


class NeverCalledFactory:
    def create_authenticated_read_transport(self, **kwargs):
        raise AssertionError("C5-B must not construct a provider transport")


def test_disabled_and_contract_only_compositions_are_inert() -> None:
    disabled = build_disabled_provider_integration()
    contract_only = build_contract_only_provider_integration(
        ProviderSelection("deferred-provider-profile"),
    )
    for composition in (disabled, contract_only):
        assert composition.network_enabled is False
        assert composition.authenticated_read_port is None
        assert composition.secret_resolver is None
        assert composition.transport_constructed is False
        assert composition.credential_resolution_performed is False


def test_inactive_composition_does_not_accept_runtime_dependencies() -> None:
    for state in (
        ProviderActivationState.DISABLED,
        ProviderActivationState.CONTRACT_ONLY,
        ProviderActivationState.AUTHENTICATED_READ_ONLY,
    ):
        with pytest.raises(ProviderActivationError):
            build_provider_integration_composition(
                activation_state=state,
                secret_resolver=object(),
            )
        with pytest.raises(ProviderActivationError):
            build_provider_integration_composition(
                activation_state=state,
                authenticated_read_port=object(),
            )
    composition = build_provider_integration_composition(
        activation_state=ProviderActivationState.CONTRACT_ONLY,
        transport_factory=NeverCalledFactory(),
    )
    assert composition.transport_constructed is False


def test_mac_composition_has_no_capability_authority_injection() -> None:
    with pytest.raises(TypeError):
        build_provider_integration_composition(capability_authority=object())


def test_controlled_write_composition_is_deferred() -> None:
    with pytest.raises(ProviderActivationError):
        build_provider_integration_composition(
            activation_state=ProviderActivationState.CONTROLLED_NONPROD_WRITE,
        )


def test_direct_composition_cannot_bypass_inert_runtime_invariants() -> None:
    gate = ProviderNetworkAuthorizationGate(
        activation_state=ProviderActivationState.DISABLED,
    )
    for values in (
        {"secret_resolver": object()},
        {"authenticated_read_port": object()},
        {"transport_constructed": True},
        {"credential_resolution_performed": True},
    ):
        with pytest.raises(ProviderActivationError):
            ProviderIntegrationComposition(
                activation_state=ProviderActivationState.DISABLED,
                authorization_gate=gate,
                **values,
            )

    for state in (
        ProviderActivationState.DISABLED,
        ProviderActivationState.CONTRACT_ONLY,
    ):
        with pytest.raises(TypeError):
            ProviderIntegrationComposition(
                activation_state=state,
                authorization_gate=ProviderNetworkAuthorizationGate(
                    activation_state=state,
                ),
                transport_constructed=1,
            )

    with pytest.raises(ProviderActivationError):
        ProviderIntegrationComposition(
            activation_state=ProviderActivationState.CONTROLLED_NONPROD_WRITE,
            authorization_gate=ProviderNetworkAuthorizationGate(
                activation_state=ProviderActivationState.CONTROLLED_NONPROD_WRITE,
            ),
        )
