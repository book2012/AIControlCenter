from __future__ import annotations

from datetime import datetime, timedelta, timezone

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadRequest,
    TwilioAuthorizationReason,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)


class Clock:
    def __init__(self):
        self.value = datetime(
            2026, 9, 29, 12, 0,
            tzinfo=timezone.utc,
        )

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += timedelta(seconds=seconds)


SERVICE = TwilioServiceSid("VA" + "a" * 32)


def request(
    *,
    request_id="request-c3a-expiry",
):
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id=request_id,
            correlation_id="correlation-c3a-expiry",
        ),
        service_sid=SERVICE,
    )


def authority(clock):
    return TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=lambda: "c" * 32,
    )


def test_capability_is_valid_before_expiry() -> None:
    clock = Clock()
    auth = authority(clock)
    original = request()

    capability = auth.issue(
        original,
        ttl_seconds=10,
    )

    clock.advance(9)

    decision = auth.authorize_once(
        original,
        capability=capability,
    )

    assert decision.allowed is True


def test_capability_expires_at_boundary() -> None:
    clock = Clock()
    auth = authority(clock)
    original = request()

    capability = auth.issue(
        original,
        ttl_seconds=10,
    )

    clock.advance(10)

    decision = auth.authorize_once(
        original,
        capability=capability,
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.CAPABILITY_EXPIRED
    )


def test_successful_capability_is_one_shot() -> None:
    clock = Clock()
    auth = authority(clock)
    original = request()

    capability = auth.issue(original)

    first = auth.authorize_once(
        original,
        capability=capability,
    )

    second = auth.authorize_once(
        original,
        capability=capability,
    )

    assert first.allowed is True
    assert second.allowed is False
    assert (
        second.reason
        is TwilioAuthorizationReason.CAPABILITY_ALREADY_USED
    )

    assert auth.consumed_count == 1


def test_failed_binding_attempt_also_consumes() -> None:
    clock = Clock()
    auth = authority(clock)

    original = request()
    capability = auth.issue(original)

    mismatched = request(
        request_id="request-c3a-mismatch"
    )

    first = auth.authorize_once(
        mismatched,
        capability=capability,
    )

    second = auth.authorize_once(
        original,
        capability=capability,
    )

    assert first.allowed is False
    assert (
        first.reason
        is TwilioAuthorizationReason.IDENTITY_BINDING_REJECTED
    )

    assert second.allowed is False
    assert (
        second.reason
        is TwilioAuthorizationReason.CAPABILITY_ALREADY_USED
    )


def test_expired_attempt_cannot_be_retried() -> None:
    clock = Clock()
    auth = authority(clock)

    original = request()
    capability = auth.issue(
        original,
        ttl_seconds=1,
    )

    clock.advance(1)

    first = auth.authorize_once(
        original,
        capability=capability,
    )

    second = auth.authorize_once(
        original,
        capability=capability,
    )

    assert (
        first.reason
        is TwilioAuthorizationReason.CAPABILITY_EXPIRED
    )

    assert (
        second.reason
        is TwilioAuthorizationReason.CAPABILITY_ALREADY_USED
    )
