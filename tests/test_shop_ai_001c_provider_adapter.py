from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from core.shopping.adapters.phone_verification import (
    ProviderPhoneVerificationAdapter, ProviderPhoneVerificationError,
)
from core.shopping.customer_auth import VerificationPurpose
from core.shopping.phone_normalization import OpaquePhoneBinding
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStartRequest, ChallengeStartResult,
    ChallengeStatus, ChallengeSubject, ChallengeVerificationRequest,
    ChallengeVerificationResult, PhoneVerificationPort,
    ProviderSourceIdentifier, ProviderVerificationIdentifier, ReplayReference,
    VerificationStatus,
)
from core.shopping.ports.phone_verification_transport import (
    ProviderTransportError, ProviderTransportFailureCode,
    ProviderTransportStartResult, ProviderTransportStartStatus,
    ProviderTransportVerifyResult, ProviderTransportVerificationStatus,
)


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
SOURCE = ProviderSourceIdentifier(value="synthetic.mock")
CHALLENGE = ChallengeReference(value="challenge-1")
REPLAY = ReplayReference(value="replay-1")
VERIFICATION = ProviderVerificationIdentifier(value="provider-verification-1")
BINDING = OpaquePhoneBinding(value="phb_" + "a" * 64)


class FakeTransport:
    def __init__(self) -> None:
        self.start_request = None
        self.verify_request = None
        self.start_result = ProviderTransportStartResult(
            provider_verification_id=VERIFICATION,
            status=ProviderTransportStartStatus.STARTED,
            started_at=NOW,
            provider_expires_at=NOW + timedelta(hours=1),
        )
        self.verify_result = ProviderTransportVerifyResult(
            provider_verification_id=VERIFICATION,
            status=ProviderTransportVerificationStatus.SUCCESS,
            verified_at=NOW,
            provider_expires_at=NOW + timedelta(hours=1),
        )
        self.start_calls = 0
        self.verify_calls = 0
        self.start_error = None
        self.verify_error = None

    def start(self, request):
        self.start_calls += 1
        self.start_request = request
        if self.start_error is not None:
            raise self.start_error
        return self.start_result

    def verify(self, request):
        self.verify_calls += 1
        self.verify_request = request
        if self.verify_error is not None:
            raise self.verify_error
        return self.verify_result


def start_request() -> ChallengeStartRequest:
    return ChallengeStartRequest(
        provider_source=SOURCE,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        challenge_reference=CHALLENGE,
        replay_reference=REPLAY,
        subject=ChallengeSubject(phone_binding=BINDING),
    )


def verify_request() -> ChallengeVerificationRequest:
    return ChallengeVerificationRequest(
        provider_source=SOURCE,
        provider_verification_id=VERIFICATION,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        challenge_reference=CHALLENGE,
        replay_reference=REPLAY,
        phone_binding=BINDING,
        otp="123456",
    )


def test_adapter_satisfies_port_and_maps_typed_start() -> None:
    transport = FakeTransport()
    adapter = ProviderPhoneVerificationAdapter(transport, provider_source=SOURCE)

    assert isinstance(adapter, PhoneVerificationPort)
    result = adapter.start_challenge(start_request())

    assert type(result) is ChallengeStartResult
    assert result.status is ChallengeStatus.STARTED
    assert result.provider_verification_id == VERIFICATION
    assert result.challenge_reference == CHALLENGE
    assert result.replay_reference == REPLAY
    assert result.phone_binding == BINDING
    assert transport.start_request.phone_binding == BINDING


def test_adapter_maps_verify_success_and_echoes_only_trusted_request_bindings() -> None:
    transport = FakeTransport()
    result = ProviderPhoneVerificationAdapter(transport, SOURCE).verify_challenge(
        verify_request(),
    )

    assert type(result) is ChallengeVerificationResult
    assert result.status is VerificationStatus.SUCCESS
    assert result.provider_source == SOURCE
    assert result.purpose is VerificationPurpose.SESSION_ISSUANCE
    assert result.challenge_reference == CHALLENGE
    assert result.replay_reference == REPLAY
    assert result.phone_binding == BINDING
    assert transport.verify_request.provider_verification_id == VERIFICATION


@pytest.mark.parametrize(
    ("transport_status", "application_status"),
    [
        (ProviderTransportVerificationStatus.REJECTED, VerificationStatus.REJECTED),
        (ProviderTransportVerificationStatus.EXPIRED, VerificationStatus.EXPIRED),
        (ProviderTransportVerificationStatus.FAILED, VerificationStatus.FAILED),
    ],
)
def test_explicit_verify_outcomes_map_to_existing_bounded_statuses(
    transport_status, application_status,
) -> None:
    transport = FakeTransport()
    transport.verify_result = ProviderTransportVerifyResult(
        provider_verification_id=VERIFICATION,
        status=transport_status,
        verified_at=NOW,
    )
    result = ProviderPhoneVerificationAdapter(transport, SOURCE).verify_challenge(
        verify_request(),
    )
    assert result.status is application_status


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (TimeoutError("provider secret=do-not-leak"), ProviderTransportFailureCode.TIMEOUT),
        (
            ProviderTransportError(ProviderTransportFailureCode.PROVIDER_UNAVAILABLE),
            ProviderTransportFailureCode.PROVIDER_UNAVAILABLE,
        ),
    ],
)
def test_timeout_and_unavailable_failures_are_normalized_without_raw_text(error, code) -> None:
    transport = FakeTransport()
    transport.verify_error = error
    with pytest.raises(ProviderPhoneVerificationError) as captured:
        ProviderPhoneVerificationAdapter(transport, SOURCE).verify_challenge(
            verify_request(),
        )
    assert captured.value.code is code
    assert "do-not-leak" not in repr(captured.value)
    assert "provider secret" not in str(captured.value)


def test_malformed_result_and_unknown_outcome_fail_closed() -> None:
    transport = FakeTransport()
    transport.start_result = {"status": "STARTED"}
    with pytest.raises(ProviderPhoneVerificationError) as malformed:
        ProviderPhoneVerificationAdapter(transport, SOURCE).start_challenge(
            start_request(),
        )
    assert malformed.value.code is ProviderTransportFailureCode.MALFORMED_RESPONSE

    transport = FakeTransport()
    transport.verify_result = ProviderTransportVerifyResult(
        provider_verification_id=VERIFICATION,
        status=ProviderTransportVerificationStatus.UNKNOWN,
        verified_at=NOW,
    )
    with pytest.raises(ProviderPhoneVerificationError) as unknown:
        ProviderPhoneVerificationAdapter(transport, SOURCE).verify_challenge(
            verify_request(),
        )
    assert unknown.value.code is ProviderTransportFailureCode.UNKNOWN_OUTCOME


def test_identifier_and_timestamp_evidence_are_bounded() -> None:
    transport = FakeTransport()
    transport.start_result = ProviderTransportStartResult(
        provider_verification_id=ProviderVerificationIdentifier(value="provider-1"),
        status=ProviderTransportStartStatus.PENDING,
        started_at=NOW,
    )
    result = ProviderPhoneVerificationAdapter(transport, SOURCE).start_challenge(
        start_request(),
    )
    assert result.status is ChallengeStatus.PENDING
    with pytest.raises((ValidationError, ValueError)):
        ProviderVerificationIdentifier(value="provider id with spaces")
    with pytest.raises((ValidationError, ValueError)):
        ProviderTransportStartResult(
            provider_verification_id=VERIFICATION,
            status=ProviderTransportStartStatus.STARTED,
            started_at=datetime(2026, 9, 27, 12, 0),
        )


def test_provider_expiry_is_evidence_and_never_local_authority() -> None:
    transport = FakeTransport()
    transport.start_result = ProviderTransportStartResult(
        provider_verification_id=VERIFICATION,
        status=ProviderTransportStartStatus.STARTED,
        started_at=NOW,
        provider_expires_at=NOW + timedelta(days=365),
    )
    result = ProviderPhoneVerificationAdapter(transport, SOURCE).start_challenge(
        start_request(),
    )
    assert result.provider_expires_at == NOW + timedelta(days=365)
    assert result.started_at == NOW


def test_otp_is_never_rendered_or_dumped() -> None:
    request = verify_request()
    assert "123456" not in repr(request)

    transport = FakeTransport()
    ProviderPhoneVerificationAdapter(transport, SOURCE).verify_challenge(request)

    transport_request = transport.verify_request
    assert transport_request is not None
    assert "123456" not in repr(transport_request)
    assert "otp" not in transport_request.model_dump()
    assert "123456" not in transport_request.model_dump_json()
    assert transport_request.otp == "123456"


def test_adapter_source_has_no_forbidden_authority_or_transport_imports() -> None:
    path = Path(__file__).parents[1] / "core/shopping/adapters/phone_verification.py"
    tree = ast.parse(path.read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    rendered = "\n".join(imports).lower()
    for forbidden in (
        "sqlite3", "customer_persistence", "customer_session_service", "ubuntu",
        "requests", "httpx", "urllib", "socket", "subprocess", "twilio", "vonage",
        "messagebird", "boto",
    ):
        assert forbidden not in rendered
