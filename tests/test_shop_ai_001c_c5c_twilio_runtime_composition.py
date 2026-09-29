from __future__ import annotations

import ast
import inspect

import pytest

import core.shopping.adapters.twilio_verify_read as twilio_adapter
import ops.macos.shopping.twilio_verify_read_composition as twilio_composition

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
    TwilioVerificationSid,
)
from core.shopping.governance.provider_network_authorization import (
    ProviderNetworkAuthorizationGate,
    ProviderNetworkAuthorizationRequest,
)
from core.shopping.ports.provider_activation import (
    OperationAllowlist,
    ProviderActivationState,
    ProviderAllowlist,
    ProviderOperation,
    ProviderRequestIdentity,
)
from ops.macos.shopping.twilio_verify_read_composition import (
    TwilioVerifyReadComposition,
    build_twilio_verify_read_composition,
)


SERVICE = "VA" + "a" * 32
VERIFY = "VE" + "b" * 32


def identity() -> ProviderRequestIdentity:
    return ProviderRequestIdentity(
        request_id="request-runtime-1",
        correlation_id="correlation-runtime-1",
    )


def test_runtime_composition_is_inert_contract_only() -> None:
    composition = build_twilio_verify_read_composition(
        service_sid=SERVICE,
    )

    assert composition.provider_source == "twilio.verify.v2"
    assert composition.authorization_model == "OFFLINE_DENY_ONLY"
    assert (
        composition.activation_state
        is ProviderActivationState.CONTRACT_ONLY
    )
    assert composition.network_enabled is False
    assert composition.transport_constructed is False
    assert composition.credential_resolution_performed is False

    service = composition.service_request()
    verify = composition.verification_request(
        TwilioVerificationSid(VERIFY)
    )

    assert service.method == "GET"
    assert verify.method == "GET"


def test_runtime_rejects_authenticated_activation() -> None:
    with pytest.raises(ValueError):
        TwilioVerifyReadComposition(
            service_sid=TwilioServiceSid(SERVICE),
            activation_state=(
                ProviderActivationState.AUTHENTICATED_READ_ONLY
            ),
        )


def test_c5_b_generic_gate_remains_deny_only() -> None:
    gate = ProviderNetworkAuthorizationGate(
        activation_state=(
            ProviderActivationState.AUTHENTICATED_READ_ONLY
        ),
        provider_allowlist=ProviderAllowlist(
            providers=(TWILIO_PROVIDER_SOURCE,),
        ),
        read_operation_allowlist=OperationAllowlist(
            operations=(ProviderOperation.READ_HEALTH,),
        ),
    )

    request = ProviderNetworkAuthorizationRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=identity(),
    )

    decision = gate.authorize(
        request,
        capability=object(),
    )

    assert decision.allowed is False


def test_c5c_modules_have_no_forbidden_runtime_imports() -> None:
    forbidden = {
        "socket",
        "requests",
        "httpx",
        "urllib",
        "twilio",
        "sqlite3",
        "keyring",
        "subprocess",
    }

    for module in (
        twilio_adapter,
        twilio_composition,
    ):
        source = inspect.getsource(module)
        tree = ast.parse(source)

        roots = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(
                    item.name.split(".", 1)[0]
                    for item in node.names
                )

            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(
                    node.module.split(".", 1)[0]
                )

        assert roots.isdisjoint(forbidden)
