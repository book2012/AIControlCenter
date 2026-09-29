"""Explicit, non-activating Mac composition for the C5 provider boundary.

This module owns composition metadata only.  It deliberately has no network,
socket, SDK, Keychain, subprocess, or environment-secret delivery dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from core.secrets.ports import SecretReference, SecretResolverPort
from core.shopping.governance.provider_network_authorization import (
    ProviderNetworkAuthorizationGate,
)
from core.shopping.ports.provider_activation import (
    AuthenticatedReadCapability, ProviderActivationError, ProviderActivationState,
    SecretDeliveryContract,
)
from core.shopping.ports.provider_authenticated_read import (
    AuthenticatedProviderReadPort,
)


@runtime_checkable
class ProviderSpecificTransportFactory(Protocol):
    """Future provider-specific factory at the outer Mac composition seam."""

    def create_authenticated_read_transport(
        self,
        *,
        secret_reference: SecretReference,
        secret_resolver: SecretResolverPort,
        capability: AuthenticatedReadCapability,
    ) -> AuthenticatedProviderReadPort:
        """
        Construct a provider-specific transport.

        The factory is the only future composition boundary that may receive
        the resolver.  Generic shopping services never call ``resolve``.
        """
        ...


@dataclass(frozen=True, slots=True)
class ProviderSelection:
    """Deferred provider-selection metadata, isolated from business logic."""

    provider_profile: str

    def __post_init__(self) -> None:
        if type(self.provider_profile) is not str or not self.provider_profile:
            raise ValueError("provider profile is invalid")

    def __repr__(self) -> str:
        return "ProviderSelection(<deferred provider profile>)"


@dataclass(frozen=True, slots=True)
class ProviderIntegrationComposition:
    """Immutable, inert snapshot of the C5-B provider boundary.

    This validation is deliberately on the value object itself.  A caller
    cannot bypass builder rules by directly constructing a composition with a
    resolver, transport, network-enabled flag, or credential activity.
    """

    activation_state: ProviderActivationState
    authorization_gate: ProviderNetworkAuthorizationGate
    provider_selection: ProviderSelection | None = None
    authenticated_read_port: AuthenticatedProviderReadPort | None = None
    secret_resolver: SecretResolverPort | None = None
    transport_constructed: bool = False
    credential_resolution_performed: bool = False

    def __post_init__(self) -> None:
        if type(self.activation_state) is not ProviderActivationState:
            raise TypeError("activation state is invalid")
        if type(self.authorization_gate) is not ProviderNetworkAuthorizationGate:
            raise TypeError("authorization gate is required")
        if self.authorization_gate.activation_state is not self.activation_state:
            raise ProviderActivationError("AUTHORIZATION_GATE_STATE_MISMATCH")
        if self.provider_selection is not None and type(self.provider_selection) is not ProviderSelection:
            raise TypeError("provider selection is invalid")
        if type(self.transport_constructed) is not bool:
            raise TypeError("transport construction flag is invalid")
        if type(self.credential_resolution_performed) is not bool:
            raise TypeError("credential resolution flag is invalid")
        if (
            self.authenticated_read_port is not None
            or self.secret_resolver is not None
            or self.transport_constructed
            or self.credential_resolution_performed
        ):
            raise ProviderActivationError("INACTIVE_COMPOSITION_REJECTS_RUNTIME_DEPENDENCIES")
        if self.activation_state is ProviderActivationState.CONTROLLED_NONPROD_WRITE:
            raise ProviderActivationError("CONTROLLED_WRITE_DEFERRED")

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def provider_transport(self) -> AuthenticatedProviderReadPort | None:
        return self.authenticated_read_port

    def secret_delivery_contract(self, reference: SecretReference) -> SecretDeliveryContract:
        """Return metadata only; this method never resolves a secret."""

        if type(reference) is not SecretReference:
            raise TypeError("secret reference is required")
        return SecretDeliveryContract(reference=reference)

    def __repr__(self) -> str:
        return (
            "ProviderIntegrationComposition("
            f"activation_state={self.activation_state.value!r}, "
            f"transport_constructed={self.transport_constructed!r}, "
            f"credential_resolution_performed={self.credential_resolution_performed!r})"
        )


def build_provider_integration_composition(
    *,
    activation_state: ProviderActivationState = ProviderActivationState.DISABLED,
    authorization_gate: ProviderNetworkAuthorizationGate | None = None,
    provider_selection: ProviderSelection | None = None,
    authenticated_read_port: AuthenticatedProviderReadPort | None = None,
    secret_resolver: SecretResolverPort | None = None,
    transport_factory: ProviderSpecificTransportFactory | None = None,
) -> ProviderIntegrationComposition:
    """Build an offline composition snapshot without constructing a transport.

    DISABLED and CONTRACT_ONLY are the only C5-B runtime compositions.  A
    future authenticated composition may inject an already constructed,
    provider-specific read port, but C5-B never invokes a factory or resolver.
    """

    if type(activation_state) is not ProviderActivationState:
        raise TypeError("activation state is invalid")
    gate = authorization_gate or ProviderNetworkAuthorizationGate(
        activation_state=activation_state,
    )
    if type(gate) is not ProviderNetworkAuthorizationGate:
        raise TypeError("authorization gate is required")
    if gate.activation_state is not activation_state:
        raise ProviderActivationError("AUTHORIZATION_GATE_STATE_MISMATCH")
    if transport_factory is not None and not isinstance(transport_factory, ProviderSpecificTransportFactory):
        raise TypeError("transport factory is invalid")
    if provider_selection is not None and type(provider_selection) is not ProviderSelection:
        raise TypeError("provider selection is invalid")
    if activation_state is ProviderActivationState.AUTHENTICATED_READ_ONLY and (
        authenticated_read_port is not None or secret_resolver is not None
    ):
        raise ProviderActivationError("INACTIVE_COMPOSITION_REJECTS_RUNTIME_DEPENDENCIES")
    if activation_state in {
        ProviderActivationState.DISABLED,
        ProviderActivationState.CONTRACT_ONLY,
    }:
        if authenticated_read_port is not None or secret_resolver is not None:
            raise ProviderActivationError("INACTIVE_COMPOSITION_REJECTS_RUNTIME_DEPENDENCIES")
        # The factory is intentionally ignored, never called, and never used
        # to construct a provider transport in C5-B.
        return ProviderIntegrationComposition(
            activation_state=activation_state,
            authorization_gate=gate,
            provider_selection=provider_selection,
        )
    if activation_state in {
        ProviderActivationState.AUTHENTICATED_READ_ONLY,
        ProviderActivationState.CONTROLLED_NONPROD_WRITE,
    }:
        if activation_state is ProviderActivationState.CONTROLLED_NONPROD_WRITE:
            raise ProviderActivationError("CONTROLLED_WRITE_DEFERRED")
        # The state remains available for the authorization contract, but C5-B
        # never constructs an authenticated runtime dependency.
        return ProviderIntegrationComposition(
            activation_state=activation_state,
            authorization_gate=gate,
            provider_selection=provider_selection,
        )
    raise ProviderActivationError("AUTHORIZATION_GATE_STATE_MISMATCH")


def build_disabled_provider_integration() -> ProviderIntegrationComposition:
    return build_provider_integration_composition()


def build_contract_only_provider_integration(
    provider_selection: ProviderSelection | None = None,
) -> ProviderIntegrationComposition:
    return build_provider_integration_composition(
        activation_state=ProviderActivationState.CONTRACT_ONLY,
        provider_selection=provider_selection,
    )


__all__ = [
    "ProviderIntegrationComposition", "ProviderSelection",
    "ProviderSpecificTransportFactory", "build_contract_only_provider_integration",
    "build_disabled_provider_integration", "build_provider_integration_composition",
]
