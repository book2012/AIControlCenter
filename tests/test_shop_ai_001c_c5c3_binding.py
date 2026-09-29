from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
    TwilioVerificationSid,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadAuthorizationError,
    TwilioAuthenticatedReadRequest,
    TwilioAuthorizationReason,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)


NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)

SERVICE_A = TwilioServiceSid("VA" + "a" * 32)
SERVICE_B = TwilioServiceSid("VA" + "b" * 32)

VERIFY_A = TwilioVerificationSid("VE" + "c" * 32)
VERIFY_B = TwilioVerificationSid("VE" + "d" * 32)


def authority():
    return TwilioAuthenticatedReadAuthority(
        clock=lambda: NOW,
        id_factory=lambda: "b" * 32,
    )


def identity(
    request_id="request-c3a-binding",
    correlation_id="correlation-c3a-binding",
):
    return ProviderRequestIdentity(
        request_id=request_id,
        correlation_id=correlation_id,
    )


def evidence_request(
    *,
    provider=TWILIO_PROVIDER_SOURCE,
    operation=ProviderOperation.READ_EVIDENCE,
    request_identity=None,
    service=SERVICE_A,
    verification=VERIFY_A,
):
    return TwilioAuthenticatedReadRequest(
        provider_source=provider,
        operation=operation,
        identity=request_identity or identity(),
        service_sid=service,
        verification_sid=verification,
    )


def fresh_decision(mutated_request):
    auth = authority()
    capability = auth.issue(evidence_request())

    return auth, capability, auth.authorize_once(
        mutated_request,
        capability=capability,
    )


def test_exact_binding_authorizes_once() -> None:
    auth = authority()
    original = evidence_request()
    capability = auth.issue(original)

    decision = auth.authorize_once(
        original,
        capability=capability,
    )

    assert decision.allowed is True
    assert (
        decision.reason
        is TwilioAuthorizationReason.AUTHORIZED
    )


def test_provider_binding_is_exact() -> None:
    _, _, decision = fresh_decision(
        evidence_request(provider="future.provider")
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.PROVIDER_BINDING_REJECTED
    )


def test_operation_binding_is_exact() -> None:
    _, _, decision = fresh_decision(
        TwilioAuthenticatedReadRequest(
            provider_source=TWILIO_PROVIDER_SOURCE,
            operation=ProviderOperation.READ_HEALTH,
            identity=identity(),
            service_sid=SERVICE_A,
        )
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.OPERATION_BINDING_REJECTED
    )


@pytest.mark.parametrize(
    "changed_identity",
    [
        identity(request_id="request-c3a-other"),
        identity(correlation_id="correlation-c3a-other"),
    ],
)
def test_identity_binding_is_exact(
    changed_identity,
) -> None:
    _, _, decision = fresh_decision(
        evidence_request(
            request_identity=changed_identity,
        )
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.IDENTITY_BINDING_REJECTED
    )


def test_service_binding_is_exact() -> None:
    _, _, decision = fresh_decision(
        evidence_request(service=SERVICE_B)
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.SERVICE_BINDING_REJECTED
    )


def test_verification_binding_is_exact() -> None:
    _, _, decision = fresh_decision(
        evidence_request(verification=VERIFY_B)
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.VERIFICATION_BINDING_REJECTED
    )


def test_health_request_rejects_verification_sid() -> None:
    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ):
        TwilioAuthenticatedReadRequest(
            provider_source=TWILIO_PROVIDER_SOURCE,
            operation=ProviderOperation.READ_HEALTH,
            identity=identity(),
            service_sid=SERVICE_A,
            verification_sid=VERIFY_A,
        )


def test_evidence_request_requires_verification_sid() -> None:
    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ):
        TwilioAuthenticatedReadRequest(
            provider_source=TWILIO_PROVIDER_SOURCE,
            operation=ProviderOperation.READ_EVIDENCE,
            identity=identity(),
            service_sid=SERVICE_A,
        )


def test_read_lookup_is_not_legal_c5c3_operation() -> None:
    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ):
        TwilioAuthenticatedReadRequest(
            provider_source=TWILIO_PROVIDER_SOURCE,
            operation=ProviderOperation.READ_LOOKUP,
            identity=identity(),
            service_sid=SERVICE_A,
        )
