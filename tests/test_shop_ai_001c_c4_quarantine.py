"""C4 durable quarantine projections and provider failure classification."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from core.shopping import customer_persistence as persistence
from core.shopping.adapters.phone_verification import ProviderPhoneVerificationError
from core.shopping.customer_auth import VerificationPurpose
from core.shopping.phone_verification_service import PhoneVerificationRejected, PhoneVerificationService
from core.shopping.ports.phone_verification import (
    ChallengeStartResult, ChallengeStatus, ChallengeVerificationRequest,
    ChallengeVerificationResult, ProviderVerificationIdentifier, VerificationStatus,
)
from core.shopping.ports.phone_verification_transport import ProviderTransportFailureCode


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
CUSTOMER = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
BROWSER = "AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
PHONE = "+821012345678"


@dataclass
class Clock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class Verifier:
    def __init__(self, clock: Clock, provider_id: str = "provider-verification-1"):
        self.clock = clock
        self.provider_id = provider_id
        self.start_exception = None
        self.verify_exception = None
        self.verify_override = None
        self.start_calls = 0
        self.verify_calls = 0

    def start_challenge(self, request):
        self.start_calls += 1
        if self.start_exception is not None:
            raise self.start_exception
        return ChallengeStartResult(
            provider_source=request.provider_source,
            provider_verification_id=ProviderVerificationIdentifier(value=self.provider_id),
            purpose=request.purpose, challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference, phone_binding=request.subject.phone_binding,
            status=ChallengeStatus.STARTED, started_at=self.clock.value,
            provider_expires_at=self.clock.value + timedelta(hours=1),
        )

    def verify_challenge(self, request: ChallengeVerificationRequest):
        self.verify_calls += 1
        if self.verify_exception is not None:
            raise self.verify_exception
        if self.verify_override is not None:
            return self.verify_override(request)
        return ChallengeVerificationResult(
            provider_source=request.provider_source,
            provider_verification_id=request.provider_verification_id,
            purpose=request.purpose, challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference, phone_binding=request.phone_binding,
            status=VerificationStatus.SUCCESS, verified_at=self.clock.value,
            provider_expires_at=self.clock.value + timedelta(hours=1),
        )


def make_service(path, clock, verifier=None, **kwargs):
    verifier = verifier or Verifier(clock)
    return PhoneVerificationService(
        verifier, utc_clock=clock, phone_binding_key=b"c4-test-only-key",
        database_path=path, **kwargs,
    ), verifier


def start(service, challenge="challenge-1", replay="replay-1"):
    return service.start_challenge(
        PHONE, customer_id=CUSTOMER, browser_challenge=BROWSER,
        challenge_reference=challenge, replay_reference=replay,
        purpose=VerificationPurpose.SESSION_ISSUANCE,
    )


def unknown_start(path, clock, *, challenge="challenge-1", replay="replay-1"):
    persistence.initialize_schema(path)
    verifier = Verifier(clock)
    verifier.start_exception = RuntimeError("ambiguous provider execution")
    service, _ = make_service(path, clock, verifier)
    with pytest.raises(PhoneVerificationRejected):
        start(service, challenge=challenge, replay=replay)
    return service, verifier


def unknown_verify(path, clock):
    persistence.initialize_schema(path)
    verifier = Verifier(clock)
    service, _ = make_service(path, clock, verifier)
    evidence = start(service)
    verifier.verify_exception = RuntimeError("ambiguous provider execution")
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    return service, verifier, evidence


def test_start_unknown_is_durable_with_open_quarantine_and_event(tmp_path):
    path = tmp_path / "start-quarantine.sqlite3"
    clock = Clock(NOW)
    unknown_start(path, clock)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status,version FROM shopping_verification_challenges"
        ).fetchone() == ("START_UNKNOWN", 1)
        assert db.execute(
            "SELECT operation,state,reason_code,version,challenge_version "
            "FROM shopping_verification_unknown_outcomes"
        ).fetchone() == ("START", "OPEN", "UNKNOWN_OUTCOME", 1, 1)
        assert db.execute(
            "SELECT from_lifecycle,to_lifecycle,outcome FROM "
            "shopping_verification_reconciliation_events"
        ).fetchone() == ("START_CLAIMED", "START_UNKNOWN", "QUARANTINED")


def test_verify_unknown_is_durable_and_ordinary_service_cannot_reconcile(tmp_path):
    path = tmp_path / "verify-quarantine.sqlite3"
    clock = Clock(NOW)
    service, verifier, evidence = unknown_verify(path, clock)
    assert verifier.verify_calls == 1
    assert not hasattr(service, "reconcile")
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status,version FROM shopping_verification_challenges"
        ).fetchone() == ("VERIFY_UNKNOWN", 2)
        assert db.execute(
            "SELECT operation,state,provider_verification_id FROM "
            "shopping_verification_unknown_outcomes"
        ).fetchone() == ("VERIFY", "OPEN", "provider-verification-1")
        assert db.execute(
            "SELECT COUNT(*) FROM shopping_verification_attempts"
        ).fetchone()[0] == 0
    assert evidence.provider_verification_id.value == "provider-verification-1"


def test_quarantine_audit_failure_rolls_back_projection_and_history(tmp_path):
    path = tmp_path / "quarantine-audit-rollback.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = Verifier(clock)
    verifier.start_exception = RuntimeError("ambiguous provider execution")
    service, _ = make_service(
        path, clock, verifier,
        audit_failure_hook=lambda _: (_ for _ in ()).throw(RuntimeError("audit unavailable")),
    )
    with pytest.raises(PhoneVerificationRejected):
        start(service)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status,version FROM shopping_verification_challenges").fetchone() == (
            "START_CLAIMED", 0,
        )
        for table in (
            "shopping_verification_unknown_outcomes",
            "shopping_verification_reconciliation_events",
            "shopping_auth_audit",
        ):
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_structured_provider_rejection_is_terminal_not_unknown(tmp_path):
    path = tmp_path / "explicit-rejection.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = Verifier(clock)
    service, _ = make_service(path, clock, verifier)
    evidence = start(service)
    verifier.verify_exception = ProviderPhoneVerificationError(
        ProviderTransportFailureCode.REJECTED,
    )
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status FROM shopping_verification_challenges").fetchone()[0] == "REJECTED"
        assert db.execute("SELECT outcome FROM shopping_verification_attempts").fetchone()[0] == "REJECTED"
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_unknown_outcomes").fetchone()[0] == 0


def test_structured_start_provider_rejection_is_terminal_without_fake_identity(tmp_path):
    path = tmp_path / "start-explicit-rejection.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = Verifier(clock)
    verifier.start_exception = ProviderPhoneVerificationError(
        ProviderTransportFailureCode.REJECTED,
    )
    service, _ = make_service(path, clock, verifier)
    with pytest.raises(PhoneVerificationRejected):
        start(service)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status,provider_start_status,provider_verification_id,version "
            "FROM shopping_verification_challenges"
        ).fetchone() == ("REJECTED", None, None, 1)
        assert db.execute(
            "SELECT COUNT(*) FROM shopping_verification_unknown_outcomes"
        ).fetchone()[0] == 0
        assert db.execute(
            "SELECT action,outcome FROM shopping_auth_audit"
        ).fetchone() == ("PHONE_VERIFICATION", "REJECTED")
    with pytest.raises(PhoneVerificationRejected):
        start(service)
    assert verifier.start_calls == 1


def test_start_evidence_is_rejected_when_local_expiry_passes_after_provider_returns(tmp_path):
    class ExpiringStartVerifier(Verifier):
        def start_challenge(self, request):
            result = super().start_challenge(request)
            self.clock.value = NOW + timedelta(minutes=2)
            return result

    path = tmp_path / "start-expiry-race.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = ExpiringStartVerifier(clock)
    service, _ = make_service(path, clock, verifier, challenge_lifetime=timedelta(minutes=1))
    with pytest.raises(PhoneVerificationRejected):
        start(service)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status FROM shopping_verification_challenges"
        ).fetchone()[0] == "START_UNKNOWN"


def test_verify_evidence_is_rejected_when_local_expiry_passes_after_provider_returns(tmp_path):
    class ExpiringVerifyVerifier(Verifier):
        def verify_challenge(self, request):
            result = super().verify_challenge(request)
            self.clock.value = NOW + timedelta(minutes=6)
            return result

    path = tmp_path / "verify-expiry-race.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = ExpiringVerifyVerifier(clock)
    service, _ = make_service(path, clock, verifier)
    evidence = start(service)
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status FROM shopping_verification_challenges"
        ).fetchone()[0] == "VERIFY_UNKNOWN"
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_attempts").fetchone()[0] == 0


def test_start_provider_rejection_after_local_expiry_projects_expired(tmp_path):
    class LateRejectedStartVerifier(Verifier):
        def start_challenge(self, request):
            self.clock.value = NOW + timedelta(minutes=2)
            raise ProviderPhoneVerificationError(ProviderTransportFailureCode.REJECTED)

    path = tmp_path / "start-rejection-expiry-race.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = LateRejectedStartVerifier(clock)
    service, _ = make_service(path, clock, verifier, challenge_lifetime=timedelta(minutes=1))
    with pytest.raises(PhoneVerificationRejected):
        start(service)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status FROM shopping_verification_challenges"
        ).fetchone()[0] == "EXPIRED"
        assert db.execute(
            "SELECT COUNT(*) FROM shopping_verification_unknown_outcomes"
        ).fetchone()[0] == 0


def test_verify_provider_rejection_after_local_expiry_projects_expired(tmp_path):
    class LateRejectedVerifyVerifier(Verifier):
        def verify_challenge(self, request):
            self.clock.value = NOW + timedelta(minutes=6)
            raise ProviderPhoneVerificationError(ProviderTransportFailureCode.REJECTED)

    path = tmp_path / "verify-rejection-expiry-race.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = LateRejectedVerifyVerifier(clock)
    service, _ = make_service(path, clock, verifier)
    evidence = start(service)
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status FROM shopping_verification_challenges"
        ).fetchone()[0] == "EXPIRED"
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_attempts").fetchone()[0] == 0
