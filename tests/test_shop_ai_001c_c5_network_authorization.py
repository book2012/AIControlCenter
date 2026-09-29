from __future__ import annotations

import inspect

import pytest

from core.shopping.ports.destination_resolution import DestinationHandle
from core.shopping.ports.provider_activation import (
    AuthenticatedReadCapability, ControlledNonProductionWriteCapability,
    OpaqueDestinationAllowlist, OperationAllowlist, ProviderActivationState,
    ProviderAllowlist, ProviderEnvironment, ProviderOperation,
    ProviderRequestIdentity,
)
from core.shopping.governance.provider_network_authorization import (
    CONTROLLED_NONPRODUCTION_ENVIRONMENT, ProviderAuthorizationReason,
    ProviderNetworkAuthorizationError, ProviderNetworkAuthorizationGate,
    ProviderNetworkAuthorizationRequest,
)


def request(operation: ProviderOperation, **updates):
    values = dict(
        provider_source="future.provider", operation=operation,
        identity=ProviderRequestIdentity(request_id="request-1", correlation_id="correlation-1"),
    )
    values.update(updates)
    return ProviderNetworkAuthorizationRequest(**values)


class FakeCapabilityAuthority:
    def is_bound(self, capability, capability_type):
        return True


def test_c5_b_has_no_authority_injection_seam() -> None:
    assert "capability_authority" not in inspect.signature(
        ProviderNetworkAuthorizationGate,
    ).parameters
    with pytest.raises(TypeError):
        ProviderNetworkAuthorizationGate(capability_authority=FakeCapabilityAuthority())


def test_default_gate_is_deny_only_and_config_is_not_authorization() -> None:
    gate = ProviderNetworkAuthorizationGate()
    decision = gate.authorize(request(ProviderOperation.READ_HEALTH))
    assert decision.allowed is False
    assert decision.reason is ProviderAuthorizationReason.ACTIVATION_DISABLED


def test_forged_object_new_capabilities_cannot_authorize() -> None:
    read_capability = object.__new__(AuthenticatedReadCapability)
    write_capability = object.__new__(ControlledNonProductionWriteCapability)
    read_gate = ProviderNetworkAuthorizationGate(
        activation_state=ProviderActivationState.AUTHENTICATED_READ_ONLY,
        provider_allowlist=ProviderAllowlist(providers=("future.provider",)),
        read_operation_allowlist=OperationAllowlist(
            operations=(ProviderOperation.READ_HEALTH,),
        ),
    )
    write_gate = ProviderNetworkAuthorizationGate(
        activation_state=ProviderActivationState.CONTROLLED_NONPROD_WRITE,
        provider_allowlist=ProviderAllowlist(providers=("future.provider",)),
        write_operation_allowlist=OperationAllowlist(
            operations=(ProviderOperation.START_CHALLENGE,),
        ),
    )
    assert read_gate.authorize(
        request(ProviderOperation.READ_HEALTH), capability=read_capability,
    ).allowed is False
    assert write_gate.authorize(
        request(
            ProviderOperation.START_CHALLENGE,
            environment=CONTROLLED_NONPRODUCTION_ENVIRONMENT,
        ),
        capability=write_capability,
    ).allowed is False


def test_all_generic_read_and_write_requests_remain_denied() -> None:
    handle = DestinationHandle._issue()
    read_gate = ProviderNetworkAuthorizationGate(
        activation_state=ProviderActivationState.AUTHENTICATED_READ_ONLY,
        provider_allowlist=ProviderAllowlist(providers=("future.provider",)),
        read_operation_allowlist=OperationAllowlist(
            operations=(ProviderOperation.READ_HEALTH,),
        ),
    )
    write_gate = ProviderNetworkAuthorizationGate(
        activation_state=ProviderActivationState.CONTROLLED_NONPROD_WRITE,
        provider_allowlist=ProviderAllowlist(providers=("future.provider",)),
        write_operation_allowlist=OperationAllowlist(
            operations=(ProviderOperation.START_CHALLENGE,),
        ),
        destination_allowlist=OpaqueDestinationAllowlist((handle,)),
    )
    read_decision = read_gate.authorize(
        request(ProviderOperation.READ_HEALTH), capability=object(),
    )
    write_decision = write_gate.authorize(
        request(
            ProviderOperation.START_CHALLENGE,
            environment=CONTROLLED_NONPRODUCTION_ENVIRONMENT,
            destination_handle=handle,
        ),
        capability=object(),
    )
    assert read_decision.allowed is False
    assert read_decision.reason is ProviderAuthorizationReason.READ_CAPABILITY_REQUIRED
    assert write_decision.allowed is False
    assert write_decision.reason is ProviderAuthorizationReason.WRITE_CAPABILITY_REQUIRED
    with pytest.raises(ProviderNetworkAuthorizationError):
        read_gate.require(request(ProviderOperation.READ_HEALTH), capability=object())


def test_environment_is_closed_bounded_and_nonproduction_only() -> None:
    values = dict(
        provider_source="future.provider", operation=ProviderOperation.START_CHALLENGE,
        identity=ProviderRequestIdentity(request_id="request-1", correlation_id="correlation-1"),
    )
    assert CONTROLLED_NONPRODUCTION_ENVIRONMENT is ProviderEnvironment.CONTROLLED_NONPRODUCTION
    assert "PRODUCTION" not in {item.name for item in ProviderEnvironment}
    for value in ("PRODUCTION", "+821012345678", "provider-secret", {"payload": "x"}):
        with pytest.raises((TypeError, ValueError)):
            ProviderNetworkAuthorizationRequest(**dict(values, environment=value))
    bounded = ProviderNetworkAuthorizationRequest(**values)
    rendered = repr(bounded)
    assert "CONTROLLED_NON_PRODUCTION" in rendered
    assert "+821012345678" not in rendered
    assert "provider-secret" not in rendered
