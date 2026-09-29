from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    MAX_CAPABILITY_TTL_SECONDS,
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadAuthorizationError,
    TwilioAuthenticatedReadCapability,
    TwilioAuthenticatedReadRequest,
    TwilioAuthorizationReason,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)


NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
SERVICE = TwilioServiceSid("VA" + "a" * 32)


def clock():
    return NOW


def request(
    *,
    provider_source=TWILIO_PROVIDER_SOURCE,
):
    return TwilioAuthenticatedReadRequest(
        provider_source=provider_source,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id="request-c3a-authority",
            correlation_id="correlation-c3a-authority",
        ),
        service_sid=SERVICE,
    )


def authority():
    return TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=lambda: "a" * 32,
    )


def test_capability_cannot_be_normally_constructed() -> None:
    with pytest.raises(TypeError):
        TwilioAuthenticatedReadCapability()


def test_authority_issues_trusted_opaque_capability() -> None:
    auth = authority()
    capability = auth.issue(request())

    assert type(capability) is TwilioAuthenticatedReadCapability
    assert auth.issued_count == 1
    assert auth.consumed_count == 0

    assert "opaque" in repr(capability).lower()
    assert str(capability) == "<opaque provider capability>"


def test_exact_twilio_provider_is_required_for_issue() -> None:
    auth = authority()

    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ) as caught:
        auth.issue(
            request(provider_source="future.provider")
        )

    assert (
        caught.value.reason
        is TwilioAuthorizationReason.PROVIDER_BINDING_REJECTED
    )


@pytest.mark.parametrize(
    "ttl",
    [0, 61, -1, True],
)
def test_ttl_is_bounded_and_exact_integer(ttl) -> None:
    auth = authority()

    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ):
        auth.issue(request(), ttl_seconds=ttl)


def test_maximum_ttl_is_exactly_60_seconds() -> None:
    assert MAX_CAPABILITY_TTL_SECONDS == 60

    auth = authority()
    capability = auth.issue(
        request(),
        ttl_seconds=60,
    )

    decision = auth.authorize_once(
        request(),
        capability=capability,
    )

    assert decision.allowed is True
    assert (
        decision.reason
        is TwilioAuthorizationReason.AUTHORIZED
    )


def test_capability_from_another_authority_is_untrusted() -> None:
    auth_a = authority()
    auth_b = authority()

    capability = auth_a.issue(request())

    decision = auth_b.authorize_once(
        request(),
        capability=capability,
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.CAPABILITY_UNTRUSTED
    )
