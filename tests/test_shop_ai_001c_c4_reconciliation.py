"""C4 explicit reconciliation, CAS, replay, expiry, and trusted linkage."""
from datetime import timedelta
import sqlite3

import pytest

from core.shopping.ports.phone_verification_reconciliation import (
    StartReconciliationCommand, StartReconciliationStatus,
    VerificationReconciliationCapability, VerifyReconciliationCommand,
    VerifyReconciliationStatus,
)
from core.shopping.verification_reconciliation_service import (
    ReconciliationConflict, VerificationReconciliationError,
    VerificationReconciliationService,
)
from tests.test_shop_ai_001c_c4_quarantine import (
    BROWSER, NOW, Clock, Verifier, make_service, start, unknown_start, unknown_verify,
)
from core.shopping import customer_persistence as persistence
from core.shopping.phone_verification_service import PhoneVerificationRejected


def recon_service(path, clock):
    capability = VerificationReconciliationCapability.issue()
    return VerificationReconciliationService(
        database_path=path,
        capability=capability,
        utc_clock=clock,
    ), capability


def start_command(*, command_id="start-command", status=StartReconciliationStatus.FAILED,
                  challenge_version=1, quarantine_version=1, **values):
    payload = dict(
        command_id=command_id, challenge_reference="challenge-1",
        replay_reference="replay-1", expected_challenge_version=challenge_version,
        expected_quarantine_version=quarantine_version, provider_source="synthetic.mock",
        status=status, actor_ref="operator", correlation_id="correlation-1",
    )
    payload.update(values)
    return StartReconciliationCommand(**payload)


def verify_command(*, command_id="verify-command", status=VerifyReconciliationStatus.VERIFIED,
                   challenge_version=2, quarantine_version=1, provider_id="provider-verification-1",
                   replay="replay-1", **values):
    payload = dict(
        command_id=command_id, challenge_reference="challenge-1",
        replay_reference=replay, expected_challenge_version=challenge_version,
        expected_quarantine_version=quarantine_version, provider_source="synthetic.mock",
        provider_verification_id=provider_id, status=status,
        actor_ref="operator", correlation_id="correlation-2",
    )
    payload.update(values)
    return VerifyReconciliationCommand(**payload)


@pytest.mark.parametrize("status", list(StartReconciliationStatus))
def test_start_unknown_reconciles_to_each_explicit_lifecycle(tmp_path, status):
    path = tmp_path / f"start-{status.value}.sqlite3"
    clock = Clock(NOW)
    unknown_start(path, clock)
    values = {}
    if status in {StartReconciliationStatus.STARTED, StartReconciliationStatus.PENDING}:
        values.update(provider_verification_id="provider-reconciled", started_at=NOW)
    service, capability = recon_service(path, clock)
    result = service.reconcile_start(
        start_command(status=status, **values),
        capability=capability,
    )
    assert result.lifecycle.value == status.value
    with sqlite3.connect(path) as db:
        status_row = db.execute(
            "SELECT status,provider_verification_id,provider_start_status FROM "
            "shopping_verification_challenges"
        ).fetchone()
        if status in {StartReconciliationStatus.STARTED, StartReconciliationStatus.PENDING}:
            assert status_row == (status.value, "provider-reconciled", status.value)
        else:
            assert status_row == (status.value, None, None)


def test_accepted_start_requires_provider_identity_and_respects_local_expiry(tmp_path):
    path = tmp_path / "accepted-start-validation.sqlite3"
    clock = Clock(NOW)
    unknown_start(path, clock)
    service, capability = recon_service(path, clock)
    with pytest.raises(VerificationReconciliationError):
        service.reconcile_start(
            start_command(status=StartReconciliationStatus.STARTED), capability=capability,
        )

    short_path = tmp_path / "local-expiry.sqlite3"
    short_clock = Clock(NOW)
    persistence.initialize_schema(short_path)
    verifier = Verifier(short_clock)
    phone_service, _ = make_service(short_path, short_clock, verifier, challenge_lifetime=timedelta(minutes=1))
    with pytest.raises(PhoneVerificationRejected):
        # The provider exception opens the START quarantine without using a
        # provider timestamp as a local expiry extension.
        verifier.start_exception = RuntimeError("ambiguous")
        start(phone_service)
    short_clock.value = NOW + timedelta(minutes=1)
    with pytest.raises(VerificationReconciliationError):
        service, capability = recon_service(short_path, short_clock)
        service.reconcile_start(
            start_command(status=StartReconciliationStatus.STARTED,
                          provider_verification_id="provider-reconciled", started_at=NOW),
            capability=capability,
        )


def test_reconciliation_rejects_future_evidence_relative_to_injected_clock(tmp_path):
    path = tmp_path / "future-evidence.sqlite3"
    clock = Clock(NOW)
    unknown_start(path, clock)
    future = NOW + timedelta(seconds=1)
    with pytest.raises(VerificationReconciliationError):
        service, capability = recon_service(path, clock)
        service.reconcile_start(
            start_command(status=StartReconciliationStatus.STARTED,
                          provider_verification_id="provider-reconciled", started_at=future),
            capability=capability,
        )
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status FROM shopping_verification_challenges").fetchone()[0] == "START_UNKNOWN"


def test_verify_verified_links_one_attempt_and_receipt_and_replays_after_reconstruction(tmp_path):
    path = tmp_path / "verified-reconciliation.sqlite3"
    clock = Clock(NOW)
    _, _, evidence = unknown_verify(path, clock)
    clock.value = NOW + timedelta(seconds=30)
    command = verify_command(verified_at=clock.value)
    service, capability = recon_service(path, clock)
    first = service.reconcile_verify(command, capability=capability)
    assert first.lifecycle.value == "VERIFIED"
    assert first.attempt_id and first.receipt_id
    assert first.verification_outcome.receipt.receipt_id == first.receipt_id
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT challenge_id,attempt_id,receipt_id,outcome FROM "
            "shopping_verification_attempts"
        ).fetchone() == ("challenge-1", first.attempt_id, first.receipt_id, "SUCCESS")
        assert db.execute(
            "SELECT challenge_id,attempt_id,receipt_id FROM shopping_trusted_receipts"
        ).fetchone() == ("challenge-1", first.attempt_id, first.receipt_id)

    reopened, replay_capability = recon_service(path, clock)
    replayed = reopened.reconcile_verify(command, capability=replay_capability)
    assert replayed.replayed is True
    assert replayed.attempt_id == first.attempt_id
    assert replayed.receipt_id == first.receipt_id
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_attempts").fetchone()[0] == 1
        assert db.execute("SELECT COUNT(*) FROM shopping_trusted_receipts").fetchone()[0] == 1
    assert evidence.provider_verification_id.value == "provider-verification-1"


def test_verify_reconciliation_uses_challenge_and_quarantine_cas(tmp_path):
    path = tmp_path / "reconciliation-cas.sqlite3"
    clock = Clock(NOW)
    unknown_verify(path, clock)
    first_service, first_capability = recon_service(path, clock)
    first = verify_command(command_id="command-a", status=VerifyReconciliationStatus.FAILED)
    first_service.reconcile_verify(first, capability=first_capability)
    second = verify_command(command_id="command-b", status=VerifyReconciliationStatus.REJECTED)
    second_service, second_capability = recon_service(path, clock)
    with pytest.raises(ReconciliationConflict):
        second_service.reconcile_verify(second, capability=second_capability)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status,version FROM shopping_verification_challenges").fetchone() == (
            "FAILED", 3,
        )
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_reconciliation_events").fetchone()[0] == 2


def test_verify_unknown_reconciliation_remains_quarantined_without_attempt_or_receipt(tmp_path):
    path = tmp_path / "verify-still-unknown.sqlite3"
    clock = Clock(NOW)
    ordinary_service, _, evidence = unknown_verify(path, clock)
    service, capability = recon_service(path, clock)
    result = service.reconcile_verify(
        verify_command(status=VerifyReconciliationStatus.UNKNOWN),
        capability=capability,
    )
    assert result.lifecycle.value == "VERIFY_UNKNOWN"
    assert result.status == "UNKNOWN"
    assert result.attempt_id is None and result.receipt_id is None
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status,version FROM shopping_verification_challenges"
        ).fetchone() == ("VERIFY_UNKNOWN", 3)
        assert db.execute(
            "SELECT state,version,challenge_version FROM "
            "shopping_verification_unknown_outcomes"
        ).fetchone() == ("OPEN", 2, 3)
        assert db.execute(
            "SELECT provider_status,outcome FROM "
            "shopping_verification_reconciliation_events "
            "WHERE command_id='verify-command'"
        ).fetchone() == ("UNKNOWN", "QUARANTINED")
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_attempts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM shopping_trusted_receipts").fetchone()[0] == 0
    with pytest.raises(PhoneVerificationRejected):
        ordinary_service.verify_challenge(
            ordinary_service.verification_request(evidence, otp="123456")
        )


def test_future_verified_evidence_is_rejected_even_when_command_would_replay(tmp_path):
    path = tmp_path / "future-verify-replay.sqlite3"
    clock = Clock(NOW)
    unknown_verify(path, clock)
    future = NOW + timedelta(seconds=30)
    command = verify_command(verified_at=future)
    with pytest.raises(VerificationReconciliationError):
        service, capability = recon_service(path, clock)
        service.reconcile_verify(command, capability=capability)
    clock.value = future
    service, capability = recon_service(path, clock)
    result = service.reconcile_verify(command, capability=capability)
    assert result.lifecycle.value == "VERIFIED"
