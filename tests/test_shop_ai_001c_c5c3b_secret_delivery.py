from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.secrets.ports import SecretReference
from core.shopping.adapters.twilio_authenticated_read_secret_delivery import (
    TWILIO_SECRET_BACKEND,
    TwilioCredentialReferences,
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

SERVICE = TwilioServiceSid("VA" + "a" * 32)


def authority():
    return TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "a" * 32,
    )


def request():
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id="request-c3b-secret",
            correlation_id="correlation-c3b-secret",
        ),
        service_sid=SERVICE,
    )


def credentials():
    return TwilioCredentialReferences(
        api_key_sid_reference=SID_REF,
        api_key_secret_reference=SECRET_REF,
    )


def test_existing_secret_reference_contract_is_reused() -> None:
    value = credentials()

    assert type(value.api_key_sid_reference) is SecretReference
    assert type(value.api_key_secret_reference) is SecretReference
    assert TWILIO_SECRET_BACKEND == "macos.keychain"


def test_two_independent_references_are_required() -> None:
    with pytest.raises(TwilioSecretDeliveryError) as caught:
        TwilioCredentialReferences(
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SID_REF,
        )

    assert (
        caught.value.reason
        is TwilioSecretDeliveryReason.DUPLICATE_REFERENCE
    )


def test_non_mac_secret_backend_is_rejected() -> None:
    other = SecretReference(
        backend="future.backend",
        key_name="shopping.twilio.other",
    )

    with pytest.raises(TwilioSecretDeliveryError) as caught:
        TwilioCredentialReferences(
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=other,
        )

    assert (
        caught.value.reason
        is TwilioSecretDeliveryReason.BACKEND_REJECTED
    )


def test_delivery_contracts_are_metadata_only() -> None:
    contracts = credentials().delivery_contracts

    assert len(contracts) == 2

    assert contracts[0].reference == SID_REF
    assert contracts[1].reference == SECRET_REF

    for contract in contracts:
        assert contract.lease_required is True
        assert contract.lease_type == "EphemeralSecretLease"
        assert (
            contract.consumer_boundary
            == "PROVIDER_SPECIFIC_TRANSPORT_ONLY"
        )


def test_reference_wrapper_repr_redacts_key_names() -> None:
    rendered = repr(credentials())

    assert SID_REF.key_name not in rendered
    assert SECRET_REF.key_name not in rendered
    assert "metadata-only" in rendered


def test_authorization_must_succeed_before_plan_exists() -> None:
    auth = authority()

    composition = (
        build_twilio_authenticated_read_secret_composition(
            authority=auth,
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SECRET_REF,
        )
    )

    result = composition.prepare(
        request(),
        capability=object(),
    )

    assert result.prepared is False
    assert result.plan is None
    assert result.authorization.allowed is False


def test_authorized_request_produces_metadata_plan_only() -> None:
    auth = authority()
    req = request()

    capability = auth.issue(req)

    composition = (
        build_twilio_authenticated_read_secret_composition(
            authority=auth,
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SECRET_REF,
        )
    )

    result = composition.prepare(
        req,
        capability=capability,
    )

    assert result.prepared is True
    assert result.plan is not None

    assert result.plan.network_enabled is False
    assert (
        result.plan.credential_resolution_performed
        is False
    )
    assert result.plan.transport_constructed is False

    assert (
        result.plan.resolver_contract
        == "SecretResolverPort"
    )
    assert (
        result.plan.lease_contract
        == "EphemeralSecretLease"
    )


def test_c3a_one_shot_still_applies_to_c3b_prepare() -> None:
    auth = authority()
    req = request()

    capability = auth.issue(req)

    composition = (
        build_twilio_authenticated_read_secret_composition(
            authority=auth,
            api_key_sid_reference=SID_REF,
            api_key_secret_reference=SECRET_REF,
        )
    )

    first = composition.prepare(
        req,
        capability=capability,
    )

    second = composition.prepare(
        req,
        capability=capability,
    )

    assert first.prepared is True
    assert second.prepared is False
    assert second.plan is None
