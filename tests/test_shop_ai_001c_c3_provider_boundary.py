from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from core.shopping.adapters.phone_verification import ProviderPhoneVerificationAdapter
from core.shopping.customer_auth import VerificationPurpose
from core.shopping.phone_normalization import OpaquePhoneBinding
from core.shopping.phone_verification_service import (
    PhoneVerificationRejected, PhoneVerificationService,
)
from core.shopping.customer_persistence import SQLiteVerificationRepository
from core.shopping.ports.destination_resolution import DestinationHandle
from core.shopping.ports.phone_verification import (
    ChallengeReference, ChallengeStartRequest, ChallengeStartResult,
    ChallengeStatus, ChallengeSubject, ProviderSourceIdentifier,
    ProviderVerificationIdentifier, ReplayReference,
)
from core.shopping.ports.phone_verification_transport import (
    ProviderTransportStartResult, ProviderTransportStartStatus,
)


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
SOURCE = ProviderSourceIdentifier(value="synthetic.mock")
BINDING = OpaquePhoneBinding("phb_" + "c" * 64)


class RecordingTransport:
    def __init__(self) -> None:
        self.request = None

    def start(self, request):
        self.request = request
        return ProviderTransportStartResult(
            provider_verification_id=ProviderVerificationIdentifier(
                value="provider-verification-1",
            ),
            status=ProviderTransportStartStatus.STARTED,
            started_at=NOW,
        )

    def verify(self, request):
        raise AssertionError("VERIFY is not part of this START boundary test")


class IssueOnlyResolver:
    def __init__(self) -> None:
        self.handle = DestinationHandle._issue()
        self.calls = []

    def issue_destination(self, destination, scope):
        self.calls.append((destination, scope))
        return self.handle


class FailingIssueResolver:
    def issue_destination(self, destination, scope):
        raise RuntimeError("local destination failure")


class RecordingVerifier:
    def __init__(self) -> None:
        self.request = None

    def start_challenge(self, request):
        self.request = request
        return ChallengeStartResult(
            provider_source=request.provider_source,
            provider_verification_id=ProviderVerificationIdentifier(
                value="provider-verification-1",
            ),
            purpose=request.purpose,
            challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference,
            phone_binding=request.subject.phone_binding,
            status=ChallengeStatus.STARTED,
            started_at=NOW,
            provider_expires_at=NOW + timedelta(minutes=4),
        )

    def verify_challenge(self, request):
        raise AssertionError("VERIFY is not part of this issue boundary test")


def test_generic_adapter_forwards_only_opaque_handle_on_start() -> None:
    transport = RecordingTransport()
    handle = DestinationHandle._issue()
    request = ChallengeStartRequest(
        provider_source=SOURCE,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
        challenge_reference=ChallengeReference(value="challenge-1"),
        replay_reference=ReplayReference(value="replay-1"),
        subject=ChallengeSubject(phone_binding=BINDING),
        destination_handle=handle,
    )
    result = ProviderPhoneVerificationAdapter(transport, SOURCE).start_challenge(request)
    assert transport.request.destination_handle is handle
    assert transport.request.phone_binding == BINDING
    assert not hasattr(result, "destination_handle")
    assert "DestinationHandle" not in result.model_dump_json()
    assert "destination_handle" not in transport.request.model_dump_json()
    assert not hasattr(ChallengeSubject, "destination_handle")
    assert "destination_handle" not in request.model_dump()
    assert "destination_handle" not in request.model_dump_json()


def test_service_issues_but_never_needs_a_destination_resolve_method(tmp_path) -> None:
    path = tmp_path / "verification.sqlite3"
    SQLiteVerificationRepository.initialize_schema(path)
    resolver = IssueOnlyResolver()
    verifier = RecordingVerifier()
    service = PhoneVerificationService(
        verifier, utc_clock=lambda: NOW, phone_binding_key=b"test-only-key",
        database_path=path, destination_resolution=resolver,
    )
    service.start_challenge(
        "+821012345678",
        customer_id="AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15,
        browser_challenge="AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15,
        challenge_reference="challenge-1", replay_reference="replay-1",
    )
    assert len(resolver.calls) == 1
    assert verifier.request.destination_handle is resolver.handle
    with sqlite3.connect(path) as connection:
        durable = "\n".join(str(row) for row in connection.iterdump())
    assert "+821012345678" not in durable


def test_local_destination_issue_failure_does_not_claim_provider_invocation(tmp_path) -> None:
    path = tmp_path / "verification.sqlite3"
    SQLiteVerificationRepository.initialize_schema(path)

    class MustNotStart(RecordingVerifier):
        def start_challenge(self, request):
            raise AssertionError("provider must not be invoked")

    verifier = MustNotStart()
    service = PhoneVerificationService(
        verifier, utc_clock=lambda: NOW, phone_binding_key=b"test-only-key",
        database_path=path, destination_resolution=FailingIssueResolver(),
    )
    customer = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
    with pytest.raises(PhoneVerificationRejected):
        service.start_challenge(
            "+821012345678", customer_id=customer,
            browser_challenge="AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15,
            challenge_reference="challenge-local-failure", replay_reference="replay-local-failure",
        )
    with sqlite3.connect(path) as connection:
        status = connection.execute(
            "SELECT status FROM shopping_verification_challenges WHERE challenge_id=?",
            ("challenge-local-failure",),
        ).fetchone()[0]
    assert status == "FAILED"
