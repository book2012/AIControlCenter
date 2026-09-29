from __future__ import annotations

import ast
import copy
import inspect
from datetime import datetime, timezone

import pytest

import core.shopping.governance.twilio_authenticated_read_authority as authority_module
import ops.macos.shopping.twilio_authenticated_read_authorization as composition_module

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
)
from core.shopping.governance.provider_network_authorization import (
    ProviderNetworkAuthorizationGate,
    ProviderNetworkAuthorizationRequest,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
)
from core.shopping.ports.provider_activation import (
    OperationAllowlist,
    ProviderActivationState,
    ProviderAllowlist,
    ProviderOperation,
    ProviderRequestIdentity,
)
from ops.macos.shopping.twilio_authenticated_read_authorization import (
    TwilioAuthenticatedReadAuthorizationComposition,
    build_twilio_authenticated_read_authorization,
)


NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
SERVICE = TwilioServiceSid("VA" + "a" * 32)


def request():
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id="request-c3a-privacy",
            correlation_id="correlation-c3a-privacy",
        ),
        service_sid=SERVICE,
    )


def test_capability_is_not_copyable() -> None:
    auth = TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "d" * 32,
    )

    capability = auth.issue(request())

    with pytest.raises(TypeError):
        copy.copy(capability)

    with pytest.raises(TypeError):
        copy.deepcopy(capability)


def test_request_and_decision_repr_hide_resource_ids() -> None:
    auth = TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "d" * 32,
    )

    req = request()
    capability = auth.issue(req)

    decision = auth.authorize_once(
        req,
        capability=capability,
    )

    rendered = " ".join([
        repr(req),
        repr(capability),
        repr(decision),
    ])

    assert str(SERVICE) not in rendered
    assert "resource=<bounded>" in rendered


def test_decision_log_is_bounded() -> None:
    auth = TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "d" * 32,
    )

    req = request()
    capability = auth.issue(req)

    decision = auth.authorize_once(
        req,
        capability=capability,
    )

    logged = decision.to_log_dict()

    assert "service_sid" not in logged
    assert "verification_sid" not in logged
    assert "credential" not in logged
    assert "payload" not in logged
    assert "to" not in logged

    assert set(logged).issubset({
        "allowed",
        "reason_code",
        "provider_source",
        "operation",
        "request_id",
        "correlation_id",
        "observed_at",
        "issuance_id",
        "expires_at",
    })


def test_c5c3_composition_is_offline_contract_only() -> None:
    composition = build_twilio_authenticated_read_authorization(
        clock=lambda: NOW,
        id_factory=lambda: "d" * 32,
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


def test_composition_rejects_authenticated_runtime_activation() -> None:
    authority = TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "d" * 32,
    )

    with pytest.raises(ValueError):
        TwilioAuthenticatedReadAuthorizationComposition(
            authority=authority,
            activation_state=(
                ProviderActivationState.AUTHENTICATED_READ_ONLY
            ),
        )


def test_generic_c5b_gate_remains_deny_only() -> None:
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

    generic_request = ProviderNetworkAuthorizationRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id="request-c3a-generic",
            correlation_id="correlation-c3a-generic",
        ),
    )

    decision = gate.authorize(
        generic_request,
        capability=object(),
    )

    assert decision.allowed is False


def test_c5c3_source_has_no_forbidden_runtime_imports() -> None:
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
        authority_module,
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
