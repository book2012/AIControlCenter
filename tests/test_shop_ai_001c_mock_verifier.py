from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import pytest

from core.shopping.customer_auth import (
    ReceiptValidationResult, VerificationPurpose, validate_trusted_receipt,
)
from core.shopping.phone_normalization import derive_phone_binding, normalize_phone
from core.shopping.phone_verification_service import (
    PhoneVerificationRejected, PhoneVerificationService,
)
from core.shopping.ports.phone_verification import (
    ChallengeStartResult, ChallengeStatus, ChallengeVerificationResult,
    ChallengeVerificationRequest, ProviderVerificationIdentifier, VerificationStatus,
)


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
CUSTOMER = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
BROWSER = "AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
PHONE = "+821012345678"


@dataclass
class FixedClock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class MockVerifier:
    def __init__(self, clock: FixedClock) -> None:
        self.clock = clock
        self.start_request = None
        self.verify_request = None
        self.verify_calls = 0
        self.start_result_override = None
        self.verify_result_override = None

    def start_challenge(self, request):
        self.start_request = request
        if self.start_result_override is not None:
            return self.start_result_override(request)
        return ChallengeStartResult(
            provider_source=request.provider_source,
            provider_verification_id=ProviderVerificationIdentifier(value="provider-verification-1"),
            purpose=request.purpose,
            challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference,
            phone_binding=request.subject.phone_binding,
            status=ChallengeStatus.STARTED,
            started_at=self.clock.value,
            provider_expires_at=self.clock.value + timedelta(days=2),
        )

    def verify_challenge(self, request: ChallengeVerificationRequest):
        self.verify_calls += 1
        self.verify_request = request
        if self.verify_result_override is not None:
            return self.verify_result_override(request)
        return ChallengeVerificationResult(
            provider_source=request.provider_source,
            provider_verification_id=request.provider_verification_id,
            purpose=request.purpose,
            challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference,
            phone_binding=request.phone_binding,
            status=VerificationStatus.SUCCESS,
            verified_at=self.clock.value,
            provider_expires_at=self.clock.value + timedelta(days=2),
        )


def make_service(clock: FixedClock, mock: MockVerifier | None = None):
    verifier = mock or MockVerifier(clock)
    return PhoneVerificationService(
        verifier,
        utc_clock=clock,
        phone_binding_key=b"test-only-injected-binding-key",
        provider_source="synthetic.mock",
    ), verifier


def start(service: PhoneVerificationService):
    return service.start_challenge(
        PHONE, customer_id=CUSTOMER, browser_challenge=BROWSER,
        challenge_reference="challenge-1", replay_reference="replay-1",
    )


def test_successful_synthetic_flow_creates_only_existing_trusted_seam() -> None:
    clock = FixedClock(NOW)
    service, mock = make_service(clock)
    evidence = start(service)
    request = service.verification_request(evidence, otp="123456")
    assert "123456" not in repr(request)
    assert str(PHONE) not in repr(mock.start_request)

    accepted = service.verify_challenge(request)
    assert accepted.receipt.customer_id == CUSTOMER
    assert accepted.receipt.browser_challenge == BROWSER
    assert accepted.context.accepted_bindings
    assert PHONE not in repr(accepted.receipt)
    assert PHONE not in repr(accepted.context)
    assert validate_trusted_receipt(
        accepted.receipt, now=NOW, expected_challenge=BROWSER, context=accepted.context,
    ) is ReceiptValidationResult.ACCEPTED
    assert accepted.receipt.expires_at <= NOW + timedelta(minutes=5)

    replayed = service.verify_challenge(request)
    assert replayed == accepted
    assert replayed is not accepted
    assert mock.verify_calls == 1


@pytest.mark.parametrize("field", [
    "phone_binding", "challenge_reference", "provider_source",
    "provider_verification_id", "purpose",
])
def test_wrong_verification_binding_fails_closed(field: str) -> None:
    clock = FixedClock(NOW)
    service, mock = make_service(clock)
    evidence = start(service)
    request = service.verification_request(evidence, otp="123456")
    if field == "phone_binding":
        update = {field: derive_phone_binding(normalize_phone("+14155550123"), b"other-key")}
    elif field == "challenge_reference":
        update = {field: "wrong-challenge"}
    elif field == "provider_source":
        update = {field: "other.adapter"}
    elif field == "provider_verification_id":
        update = {field: "other-verification"}
    else:
        update = {field: "not-a-purpose"}
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(request.model_copy(update=update))


@pytest.mark.parametrize("status", [VerificationStatus.FAILED, VerificationStatus.EXPIRED])
def test_unsuccessful_provider_status_is_rejected(status: VerificationStatus) -> None:
    clock = FixedClock(NOW)
    service, mock = make_service(clock)
    evidence = start(service)

    def failed(request):
        return ChallengeVerificationResult(
            provider_source=request.provider_source,
            provider_verification_id=request.provider_verification_id,
            purpose=request.purpose,
            challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference,
            phone_binding=request.phone_binding,
            status=status,
            verified_at=NOW,
        )

    mock.verify_result_override = failed
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))


@pytest.mark.parametrize("timestamp", [
    NOW - timedelta(minutes=6), NOW + timedelta(seconds=1),
])
def test_expired_and_future_provider_timestamps_are_rejected(timestamp: datetime) -> None:
    clock = FixedClock(NOW)
    service, mock = make_service(clock)
    evidence = start(service)

    def invalid_time(request):
        return ChallengeVerificationResult(
            provider_source=request.provider_source,
            provider_verification_id=request.provider_verification_id,
            purpose=request.purpose,
            challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference,
            phone_binding=request.phone_binding,
            status=VerificationStatus.SUCCESS,
            verified_at=timestamp,
        )

    mock.verify_result_override = invalid_time
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))


def test_provider_expiry_cannot_extend_local_expiry_and_alternate_otp_replays() -> None:
    clock = FixedClock(NOW)
    service, mock = make_service(clock)
    evidence = start(service)
    request = service.verification_request(evidence, otp="123456")
    accepted = service.verify_challenge(request)
    assert accepted.receipt.expires_at <= NOW + timedelta(minutes=5)
    replayed = service.verify_challenge(request.model_copy(update={"otp": "654321"}))
    assert replayed == accepted
    assert mock.verify_calls == 1


def test_malformed_provider_return_and_duplicate_provider_identifier_fail() -> None:
    clock = FixedClock(NOW)
    service, mock = make_service(clock)
    mock.start_result_override = lambda request: {"status": "STARTED"}
    with pytest.raises(PhoneVerificationRejected):
        start(service)

    clock2 = FixedClock(NOW)
    service2, mock2 = make_service(clock2)
    first = start(service2)
    assert first.provider_verification_id.value == "provider-verification-1"
    with pytest.raises(PhoneVerificationRejected):
        service2.start_challenge(
            PHONE, customer_id=CUSTOMER, browser_challenge=BROWSER,
            challenge_reference="challenge-2", replay_reference="replay-2",
        )
