from datetime import datetime, timedelta, timezone

import pytest

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
)
from core.shopping.governance.twilio_authenticated_read_authority import (
    AUTHORITY_RECORD_RETENTION_SECONDS,
    MAX_CAPABILITY_TTL_SECONDS,
    TwilioAuthenticatedReadAuthority,
    TwilioAuthenticatedReadAuthorizationError,
    TwilioAuthenticatedReadRequest,
    TwilioAuthorizationReason,
)
from core.shopping.ports.provider_activation import (
    ProviderOperation,
    ProviderRequestIdentity,
)


class MutableClock:
    def __init__(self) -> None:
        self.value = datetime(
            2026,
            9,
            30,
            0,
            0,
            tzinfo=timezone.utc,
        )

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value = self.value + timedelta(
            seconds=seconds
        )


def _request(tag: str = "001") -> TwilioAuthenticatedReadRequest:
    return TwilioAuthenticatedReadRequest(
        provider_source=TWILIO_PROVIDER_SOURCE,
        operation=ProviderOperation.READ_HEALTH,
        identity=ProviderRequestIdentity(
            request_id=f"h1-request-{tag}",
            correlation_id=f"h1-correlation-{tag}",
        ),
        service_sid=TwilioServiceSid(
            value="VA" + ("A" * 32)
        ),
    )


def test_retention_window_equals_existing_max_ttl():
    assert (
        AUTHORITY_RECORD_RETENTION_SECONDS
        == MAX_CAPABILITY_TTL_SECONDS
    )


def test_duplicate_issuance_id_fails_closed():
    clock = MutableClock()
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=lambda: "a" * 32,
    )

    authority.issue(
        _request("001")
    )

    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ):
        authority.issue(
            _request("002")
        )

    assert authority.issued_count == 1
    assert authority.consumed_count == 0


def test_expired_but_retained_id_still_collides():
    clock = MutableClock()
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=lambda: "b" * 32,
    )

    authority.issue(
        _request("003"),
        ttl_seconds=1,
    )

    clock.advance(2)

    with pytest.raises(
        TwilioAuthenticatedReadAuthorizationError
    ):
        authority.issue(
            _request("004")
        )

    assert authority.issued_count == 1


def test_retired_record_allows_bounded_id_reuse():
    clock = MutableClock()
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=lambda: "c" * 32,
    )

    authority.issue(
        _request("005"),
        ttl_seconds=1,
    )

    clock.advance(
        1 + AUTHORITY_RECORD_RETENTION_SECONDS
    )

    replacement = authority.issue(
        _request("006"),
        ttl_seconds=1,
    )

    assert replacement is not None
    assert authority.issued_count == 1
    assert authority.consumed_count == 0


def test_expired_reason_is_preserved_inside_retention():
    clock = MutableClock()
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
    )

    request = _request("007")
    capability = authority.issue(
        request,
        ttl_seconds=1,
    )

    clock.advance(2)

    decision = authority.authorize_once(
        request,
        capability=capability,
    )

    assert decision.allowed is False
    assert (
        decision.reason
        is TwilioAuthorizationReason.CAPABILITY_EXPIRED
    )
    assert authority.consumed_count == 1


def test_already_used_reason_is_preserved_inside_retention():
    clock = MutableClock()
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
    )

    request = _request("008")
    capability = authority.issue(
        request
    )

    first = authority.authorize_once(
        request,
        capability=capability,
    )
    second = authority.authorize_once(
        request,
        capability=capability,
    )

    assert first.allowed is True
    assert second.allowed is False
    assert (
        second.reason
        is TwilioAuthorizationReason.CAPABILITY_ALREADY_USED
    )


def test_retired_used_capability_becomes_untrusted():
    clock = MutableClock()
    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
    )

    request = _request("009")
    capability = authority.issue(
        request,
        ttl_seconds=1,
    )

    first = authority.authorize_once(
        request,
        capability=capability,
    )

    assert first.allowed is True

    clock.advance(
        1 + AUTHORITY_RECORD_RETENTION_SECONDS
    )

    retired = authority.authorize_once(
        request,
        capability=capability,
    )

    assert retired.allowed is False
    assert (
        retired.reason
        is TwilioAuthorizationReason.CAPABILITY_UNTRUSTED
    )
    assert authority.issued_count == 0
    assert authority.consumed_count == 0


def test_issue_prunes_retired_used_state():
    clock = MutableClock()
    ids = iter(
        [
            "d" * 32,
            "e" * 32,
        ]
    )

    authority = TwilioAuthenticatedReadAuthority(
        clock=clock,
        id_factory=lambda: next(ids),
    )

    request = _request("010")
    capability = authority.issue(
        request,
        ttl_seconds=1,
    )

    decision = authority.authorize_once(
        request,
        capability=capability,
    )

    assert decision.allowed is True
    assert authority.issued_count == 1
    assert authority.consumed_count == 1

    clock.advance(
        1 + AUTHORITY_RECORD_RETENTION_SECONDS
    )

    authority.issue(
        _request("011"),
        ttl_seconds=1,
    )

    assert authority.issued_count == 1
    assert authority.consumed_count == 0
    assert authority.network_enabled is False
    assert authority.credential_resolution_enabled is False
