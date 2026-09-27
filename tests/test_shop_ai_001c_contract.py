from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from core.shopping.customer_auth import VerificationPurpose
from core.shopping.phone_normalization import (
    OpaquePhoneBinding, PhoneNormalizationError, derive_phone_binding, normalize_phone,
)
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStartRequest, ChallengeStartResult, ChallengeStatus,
    ChallengeSubject, ChallengeVerificationRequest, ChallengeVerificationResult,
    PhoneVerificationPort, ProviderSourceIdentifier, ProviderVerificationIdentifier,
    ReplayReference, VerificationStatus,
)
from core.secrets.ports import SecretReference


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)


def test_normalization_is_strict_and_requires_explicit_country_context() -> None:
    assert str(normalize_phone("+82 10-1234-5678")) == "+821012345678"
    assert str(normalize_phone(
        "010-1234-5678", country_calling_code="+82", national_trunk_prefix="0",
    )) == "+821012345678"
    for value, context in (
        ("010-1234-5678", None),
        ("010-1234-5678", "+1"),
        ("0010-1234-5678", "+82"),
        ("1012345678", "+82"),
        ("+821012345678", "+82"),
        ("+999", None),
        ("phone", None),
    ):
        with pytest.raises((PhoneNormalizationError, ValueError)):
            normalize_phone(value, country_calling_code=context)


def test_binding_is_deterministic_keyed_and_phone_opaque() -> None:
    phone = normalize_phone("+821012345678")
    first = derive_phone_binding(phone, b"test-only-key-a")
    same = derive_phone_binding(phone, b"test-only-key-a")
    other = derive_phone_binding(phone, b"test-only-key-b")
    assert isinstance(first, OpaquePhoneBinding)
    assert first == same
    assert first != other
    assert str(phone) not in repr(first)
    assert str(phone) not in str(first)


def test_contracts_are_immutable_closed_and_provider_neutral() -> None:
    source = ProviderSourceIdentifier(value="synthetic.mock")
    assert ProviderSourceIdentifier(value="another.adapter") != source
    with pytest.raises((ValidationError, TypeError, ValueError)):
        ProviderSourceIdentifier(value="synthetic.mock", extra="forbidden")
    with pytest.raises((ValidationError, TypeError, ValueError)):
        source.value = "changed"  # type: ignore[misc]

    subject = ChallengeSubject(phone_binding=derive_phone_binding(
        normalize_phone("+821012345678"), b"key",
    ))
    start = ChallengeStartRequest(
        provider_source=source,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        challenge_reference=ChallengeReference(value="challenge-1"),
        replay_reference=ReplayReference(value="replay-1"),
        subject=subject,
    )
    assert start.model_config.get("extra") == "forbid"
    assert start.model_config.get("frozen") is True
    assert issubclass(PhoneVerificationPort, object)
    assert not hasattr(ProviderSourceIdentifier, "__members__")
    assert ChallengeStartResult is not ChallengeVerificationResult
    assert ChallengeStatus.STARTED.value == "STARTED"
    assert VerificationStatus.SUCCESS.value == "SUCCESS"


def test_c2_secret_reference_is_metadata_only() -> None:
    reference = SecretReference(backend="macos.keychain", key_name="shopping.provider")
    assert reference.to_dict() == {
        "backend": "macos.keychain",
        "key_name": "shopping.provider",
    }
