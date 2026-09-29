from __future__ import annotations

import copy
import pickle

import pytest

import core.shopping.ports.provider_activation as provider_activation
from core.shopping.ports.destination_resolution import DestinationHandle
from core.shopping.ports.provider_activation import (
    AuthenticatedReadCapability, ControlledNonProductionWriteCapability,
    OpaqueDestinationAllowlist, OperationAllowlist, ProviderActivationError,
    ProviderActivationState,
    ProviderAllowlist, ProviderOperation, ProviderRequestIdentity,
)


def test_activation_states_are_exact_and_production_is_absent() -> None:
    assert tuple(state.value for state in ProviderActivationState) == (
        "DISABLED", "CONTRACT_ONLY", "AUTHENTICATED_READ_ONLY",
        "CONTROLLED_NONPROD_WRITE",
    )
    assert all("PRODUCTION" not in state.value for state in ProviderActivationState)


@pytest.mark.parametrize("capability_type", [
    AuthenticatedReadCapability, ControlledNonProductionWriteCapability,
])
def test_capabilities_are_opaque_and_not_caller_constructible(capability_type) -> None:
    with pytest.raises(TypeError):
        capability_type()
    assert not hasattr(capability_type, "issue")
    assert not hasattr(capability_type, "issue_for_control_plane")
    capability = object.__new__(capability_type)
    assert "opaque" in repr(capability).lower()
    with pytest.raises(TypeError):
        copy.copy(capability)
    with pytest.raises(TypeError):
        copy.deepcopy(capability)
    with pytest.raises(TypeError):
        pickle.dumps(capability)


def test_c5_b_exposes_contracts_but_no_capability_issuer() -> None:
    assert not hasattr(provider_activation, "compose_provider_capability_bundle")
    assert not hasattr(provider_activation, "ProviderCapabilityBundle")
    assert not hasattr(provider_activation, "ProviderCapabilityAuthority")
    assert not any(
        any(word in name.lower() for word in ("issue", "mint", "create"))
        for name in dir(provider_activation)
    )


def test_activation_errors_have_bounded_reason_codes() -> None:
    error = ProviderActivationError("raw provider exception")
    assert error.reason_code == "AUTHORIZATION_REQUIRED"
    assert "raw provider exception" not in repr(error)


def test_identity_and_allowlists_are_bounded_and_explicit() -> None:
    identity = ProviderRequestIdentity(request_id="request-1", correlation_id="correlation-1")
    assert identity.request_id == "request-1"
    with pytest.raises(ValueError):
        ProviderRequestIdentity(request_id="has space", correlation_id="correlation-1")
    assert ProviderAllowlist(providers=("synthetic.mock",)).contains("synthetic.mock")
    assert OperationAllowlist(operations=(ProviderOperation.READ_HEALTH,)).contains(
        ProviderOperation.READ_HEALTH,
    )


def test_destination_allowlist_accepts_only_opaque_handles() -> None:
    handle = DestinationHandle._issue()
    allowlist = OpaqueDestinationAllowlist((handle,))
    assert allowlist.contains(handle)
    assert not allowlist.contains("+821012345678")
    assert "+821012345678" not in repr(allowlist)
