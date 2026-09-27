from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
import copy
import pickle

import pytest

from core.shopping.customer_auth import VerificationPurpose
from core.shopping.phone_normalization import CanonicalPhone, OpaquePhoneBinding
from core.shopping.ports.destination_resolution import (
    DestinationHandle, DestinationResolutionError, DestinationScope,
)
from ops.macos.shopping.provider_destination_resolver import ProviderDestinationResolver


PHONE = CanonicalPhone("+821012345678")
BINDING = OpaquePhoneBinding("phb_" + "a" * 64)


def scope(**updates) -> DestinationScope:
    values = dict(
        provider_source="synthetic.mock",
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        challenge_reference="challenge-1",
        replay_reference="replay-1",
        customer_id="customer-1",
        phone_binding=BINDING,
        browser_challenge="browser-1",
    )
    values.update(updates)
    return DestinationScope(**values)


def test_phone_and_handle_diagnostics_are_redacted_and_not_publicly_serializable() -> None:
    handle = DestinationHandle._issue()
    assert repr(PHONE) == "CanonicalPhone(<redacted>)"
    assert str(PHONE) not in repr(PHONE)
    assert str(handle) == "<opaque destination handle>"
    assert "a" * 32 not in repr(handle)
    with pytest.raises((TypeError, ValueError)):
        json.dumps(handle)
    with pytest.raises((TypeError, AttributeError)):
        vars(handle)
    with pytest.raises(TypeError):
        DestinationHandle(b"public-token")
    with pytest.raises(TypeError):
        copy.copy(handle)
    with pytest.raises(TypeError):
        pickle.dumps(handle)


def test_scope_requires_a_real_purpose_and_equality_includes_purpose() -> None:
    members = tuple(VerificationPurpose)
    assert VerificationPurpose.SESSION_ISSUANCE in members
    with pytest.raises(TypeError):
        scope(purpose="SESSION_ISSUANCE")
    if len(members) > 1:
        other = next(member for member in members if member is not VerificationPurpose.SESSION_ISSUANCE)
        assert scope() != scope(purpose=other)
    else:
        assert scope() == scope(purpose=VerificationPurpose.SESSION_ISSUANCE)


@pytest.mark.parametrize(
    "dimension",
    [
        "provider_source", "challenge_reference", "replay_reference",
        "customer_id", "phone_binding", "browser_challenge",
    ],
)
def test_wrong_scope_dimensions_fail_closed_without_leaking_the_phone(dimension: str) -> None:
    resolver = ProviderDestinationResolver()
    original = scope()
    handle = resolver.issue_destination(PHONE, original)
    replacement = {
        "provider_source": "other.provider",
        "challenge_reference": "challenge-2",
        "replay_reference": "replay-2",
        "customer_id": "customer-2",
        "phone_binding": OpaquePhoneBinding("phb_" + "b" * 64),
        "browser_challenge": "browser-2",
    }[dimension]
    with pytest.raises(DestinationResolutionError) as error:
        resolver.resolve_destination(handle, scope(**{dimension: replacement}))
    assert str(PHONE) not in str(error.value)
    assert resolver.resolve_destination(handle, original) == PHONE


def test_resolution_consumes_before_returning_and_is_instance_scoped() -> None:
    first = ProviderDestinationResolver()
    second = ProviderDestinationResolver()
    original = scope()
    handle = first.issue_destination(PHONE, original)
    with pytest.raises(DestinationResolutionError):
        second.resolve_destination(handle, original)
    assert first.resolve_destination(handle, original) == PHONE
    with pytest.raises(DestinationResolutionError):
        first.resolve_destination(handle, original)


def test_destination_expiry_is_bounded_injected_and_removed() -> None:
    current = [datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)]
    resolver = ProviderDestinationResolver(
        utc_clock=lambda: current[0], ttl=timedelta(minutes=5), max_pending=2,
    )
    original = scope()
    handle = resolver.issue_destination(PHONE, original)
    current[0] += timedelta(minutes=5)
    with pytest.raises(DestinationResolutionError):
        resolver.resolve_destination(handle, original)
    assert resolver.pending_count == 0
    with pytest.raises(DestinationResolutionError):
        resolver.resolve_destination(handle, original)


def test_destination_capacity_fails_closed_without_eviction() -> None:
    resolver = ProviderDestinationResolver(max_pending=1)
    original = scope()
    first = resolver.issue_destination(PHONE, original)
    with pytest.raises(DestinationResolutionError):
        resolver.issue_destination(PHONE, scope(challenge_reference="challenge-2"))
    assert resolver.resolve_destination(first, original) == PHONE
