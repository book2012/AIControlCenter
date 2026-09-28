"""Durable C1 verification persistence tests.

All provider behavior here is synthetic.  The tests exercise the Mac-local
SQLite authority and never use a route, network, Ubuntu worker, or deployer.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import sqlite3
import threading

import pytest

from core.shopping import customer_identity as identity
from core.shopping import customer_persistence as persistence
from core.shopping.customer_auth import VerificationPurpose
from core.shopping.customer_session_service import (
    AuditPersistenceError, CustomerSessionService, ReceiptPolicyDenied,
)
from core.shopping.migration_contract import (
    CURRENT_PERSISTENCE_SCHEMA_VERSION, PERSISTENCE_SCHEMA_VERSION,
)
from core.shopping.phone_normalization import derive_phone_binding, normalize_phone
from core.shopping import phone_verification_service as verification_module
from core.shopping.phone_verification_service import (
    PhoneVerificationRejected, PhoneVerificationService,
)
from core.shopping.ports.phone_verification import (
    ChallengeStartResult, ChallengeStatus, ChallengeVerificationRequest,
    ChallengeVerificationResult, ProviderVerificationIdentifier, VerificationStatus,
)


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)
CUSTOMER = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
BROWSER = "AG-CHL-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
CONTACT = "AG-CON-" + "3" * 12 + "4" + "3" * 3 + "8" + "3" * 15
PHONE = "+821012345678"


@dataclass
class Clock:
    value: datetime

    def __call__(self) -> datetime:
        return self.value


class MockVerifier:
    def __init__(self, clock: Clock, provider_id: str = "provider-verification-1"):
        self.clock = clock
        self.provider_id = provider_id
        self.start_calls = 0
        self._start_lock = threading.Lock()
        self.start_entered = threading.Event()
        self.release_start = None
        self.start_exception = None
        self.verify_calls = 0
        self.verify_override = None

    def start_challenge(self, request):
        with self._start_lock:
            self.start_calls += 1
        self.start_entered.set()
        if self.release_start is not None:
            self.release_start.wait(timeout=5)
        if self.start_exception is not None:
            raise self.start_exception
        return ChallengeStartResult(
            provider_source=request.provider_source,
            provider_verification_id=ProviderVerificationIdentifier(value=self.provider_id),
            purpose=request.purpose, challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference, phone_binding=request.subject.phone_binding,
            status=ChallengeStatus.STARTED, started_at=self.clock.value,
            provider_expires_at=self.clock.value + timedelta(days=1),
        )

    def verify_challenge(self, request: ChallengeVerificationRequest):
        self.verify_calls += 1
        if self.verify_override is not None:
            return self.verify_override(request)
        return ChallengeVerificationResult(
            provider_source=request.provider_source,
            provider_verification_id=request.provider_verification_id,
            purpose=request.purpose, challenge_reference=request.challenge_reference,
            replay_reference=request.replay_reference, phone_binding=request.phone_binding,
            status=VerificationStatus.SUCCESS, verified_at=self.clock.value,
            provider_expires_at=self.clock.value + timedelta(days=1),
        )


def make_service(path, clock, verifier=None, **kwargs):
    verifier = verifier or MockVerifier(clock)
    service = PhoneVerificationService(
        verifier, utc_clock=clock, phone_binding_key=b"c1-test-only-key",
        database_path=path, **kwargs,
    )
    return service, verifier


def start(service, challenge="challenge-1", replay="replay-1", customer=CUSTOMER):
    return service.start_challenge(
        PHONE, customer_id=customer, browser_challenge=BROWSER,
        challenge_reference=challenge, replay_reference=replay,
    )


def verified(path):
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, verifier = make_service(path, clock)
    evidence = start(service)
    outcome = service.verify_challenge(service.verification_request(evidence, otp="123456"))
    return clock, service, verifier, evidence, outcome


def customer():
    return identity.Customer(
        id=CUSTOMER, state=identity.CustomerState.ACTIVE,
        created_at=NOW - timedelta(minutes=2), updated_at=NOW,
        contact_binding=identity.VerifiedContactBinding(
            customer_id=CUSTOMER, state=identity.VerificationState.VERIFIED,
            created_at=NOW - timedelta(minutes=2), updated_at=NOW,
            contact_ref=CONTACT, verified_at=NOW - timedelta(minutes=1),
        ),
    )


def test_fresh_v2_schema_has_required_tables_and_constraints(tmp_path):
    path = tmp_path / "v2.sqlite3"
    persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"shopping_verification_challenges", "shopping_verification_attempts",
                "shopping_trusted_receipts", "shopping_verification_receipts"} <= tables
        for table in ("shopping_verification_challenges", "shopping_verification_attempts",
                      "shopping_trusted_receipts"):
            assert db.execute(f"PRAGMA foreign_key_list({table})").fetchall() is not None
        challenge_sql = db.execute("SELECT sql FROM sqlite_master WHERE name='shopping_verification_challenges'").fetchone()[0]
        attempt_sql = db.execute("SELECT sql FROM sqlite_master WHERE name='shopping_verification_attempts'").fetchone()[0]
        receipt_sql = db.execute("SELECT sql FROM sqlite_master WHERE name='shopping_trusted_receipts'").fetchone()[0]
        assert "UNIQUE(replay_reference)" in challenge_sql or "replay_reference TEXT NOT NULL UNIQUE" in challenge_sql
        assert "UNIQUE(provider_source,provider_verification_id)" in challenge_sql
        assert "provider_start_status TEXT" in challenge_sql
        assert "provider_start_status IN ('STARTED','PENDING')" in challenge_sql
        assert "UNIQUE(provider_source,provider_verification_id)" in attempt_sql
        assert "receipt_id TEXT PRIMARY KEY" in receipt_sql


def test_v1_is_historical_and_not_silently_upgraded(tmp_path):
    path = tmp_path / "v1.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE shopping_customer_persistence_meta (name TEXT PRIMARY KEY, version TEXT NOT NULL)")
        db.execute("INSERT INTO shopping_customer_persistence_meta VALUES ('schema', ?)", (PERSISTENCE_SCHEMA_VERSION,))
        db.commit()
    with pytest.raises(persistence.PersistenceSchemaError):
        persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT version FROM shopping_customer_persistence_meta").fetchone()[0] == PERSISTENCE_SCHEMA_VERSION
        assert db.execute("SELECT name FROM sqlite_master WHERE name='shopping_verification_challenges'").fetchone() is None
    assert CURRENT_PERSISTENCE_SCHEMA_VERSION == persistence.SCHEMA_VERSION


def test_durable_rows_are_opaque_and_secret_free(tmp_path):
    path = tmp_path / "privacy.sqlite3"
    _, _, _, _, outcome = verified(path)
    with sqlite3.connect(path) as db:
        rendered = repr([tuple(row) for table in (
            "shopping_verification_challenges", "shopping_verification_attempts",
            "shopping_trusted_receipts", "shopping_auth_audit")
            for row in db.execute(f"SELECT * FROM {table}")])
    for secret in (PHONE, "123456", "provider-payload", "provider-secret", "api-key"):
        assert secret not in rendered
    assert "otp" not in rendered.lower()
    assert "digest" not in rendered.lower()
    assert "hmac" not in rendered.lower()
    assert str(outcome.receipt.receipt_id) in rendered


def test_replay_authority_is_not_process_local(tmp_path):
    path = tmp_path / "no-cache.sqlite3"
    _, service, _, _, _ = verified(path)
    assert not hasattr(service, "_last_request_identity")
    assert not hasattr(service, "_last_outcomes")


def test_challenge_and_exact_replay_survive_reconstruction(tmp_path):
    path = tmp_path / "reopen.sqlite3"
    clock, _, verifier, evidence, first = verified(path)
    reopened, verifier2 = make_service(path, clock, MockVerifier(clock))
    restored = start(reopened)
    assert restored.challenge_reference == evidence.challenge_reference
    assert restored.replay_reference == evidence.replay_reference
    assert restored.provider_verification_id == evidence.provider_verification_id
    assert restored.status is ChallengeStatus.STARTED
    second = reopened.verify_challenge(reopened.verification_request(restored, otp="123456"))
    assert second.receipt == first.receipt
    assert second == first
    assert second is not first
    assert verifier.verify_calls == 1 and verifier2.verify_calls == 0


def test_verified_lifecycle_preserves_start_evidence_and_alternate_otp_replays(tmp_path):
    path = tmp_path / "verified-replay.sqlite3"
    clock, service, verifier, evidence, first = verified(path)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT status,provider_start_status FROM shopping_verification_challenges"
        ).fetchone() == ("VERIFIED", "STARTED")

    reopened, verifier2 = make_service(path, clock)
    restored = start(reopened)
    assert restored == evidence
    replayed = reopened.verify_challenge(
        reopened.verification_request(restored, otp="654321")
    )
    assert replayed == first
    assert replayed.context == first.context
    assert verifier.verify_calls == 1
    assert verifier2.verify_calls == 0


def test_concurrent_exact_start_claim_has_one_provider_invocation(tmp_path):
    path = tmp_path / "concurrent-start.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    verifier = MockVerifier(clock)
    verifier.release_start = threading.Event()
    services = [make_service(path, clock, verifier)[0] for _ in range(2)]

    def invoke(service):
        try:
            return start(service)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(invoke, service) for service in services]
        assert verifier.start_entered.wait(timeout=2)
        verifier.release_start.set()
        results = [future.result(timeout=5) for future in futures]

    assert verifier.start_calls == 1
    assert all(
        isinstance(value, PhoneVerificationRejected)
        or value.provider_verification_id.value == "provider-verification-1"
        for value in results
    )
    assert any(not isinstance(value, Exception) for value in results)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status,version FROM shopping_verification_challenges").fetchone() == ("STARTED", 1)


def test_provider_exception_keeps_claim_unknown_and_forbids_reinvocation(tmp_path):
    path = tmp_path / "unknown-start.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    failing = MockVerifier(clock)
    failing.start_exception = RuntimeError("provider outcome unknown")
    service, _ = make_service(path, clock, failing)
    with pytest.raises(PhoneVerificationRejected):
        start(service)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status,version FROM shopping_verification_challenges").fetchone() == ("START_UNKNOWN", 1)

    retrying = MockVerifier(clock)
    reopened, _ = make_service(path, clock, retrying)
    with pytest.raises(PhoneVerificationRejected):
        start(reopened)
    assert retrying.start_calls == 0


def test_provider_call_is_outside_the_durable_claim_transaction(tmp_path):
    path = tmp_path / "provider-boundary.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)

    class TransactionProbe(MockVerifier):
        def start_challenge(self, request):
            probe = sqlite3.connect(path, timeout=0.1, isolation_level=None)
            try:
                probe.execute("PRAGMA busy_timeout=100")
                probe.execute("BEGIN IMMEDIATE")
                probe.execute("ROLLBACK")
            finally:
                probe.close()
            return super().start_challenge(request)

    verifier = TransactionProbe(clock)
    service, _ = make_service(path, clock, verifier)
    start(service)
    assert verifier.start_calls == 1


def test_replay_and_provider_collisions_fail_closed(tmp_path):
    path = tmp_path / "collisions.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, first_verifier = make_service(path, clock)
    first = start(service)
    assert first_verifier.start_calls == 1
    conflicting_verifier = MockVerifier(clock)
    conflicting, _ = make_service(path, clock, conflicting_verifier)
    with pytest.raises(PhoneVerificationRejected):
        start(conflicting, challenge="challenge-2", replay="replay-1")
    assert conflicting_verifier.start_calls == 0
    service.verify_challenge(service.verification_request(first, otp="123456"))
    replay = service.verify_challenge(service.verification_request(first, otp="654321"))
    assert replay.receipt == service.verify_challenge(
        service.verification_request(first, otp="123456")
    ).receipt
    collision_verifier = MockVerifier(clock, "provider-verification-1")
    second_service, _ = make_service(path, clock, collision_verifier)
    with pytest.raises(PhoneVerificationRejected):
        start(second_service, challenge="challenge-2", replay="replay-2")
    assert collision_verifier.start_calls == 1
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT COUNT(*) FROM shopping_verification_challenges "
            "WHERE provider_source=? AND provider_verification_id=?",
            ("synthetic.mock", "provider-verification-1"),
        ).fetchone()[0] == 1
        assert db.execute(
            "SELECT status FROM shopping_verification_challenges WHERE challenge_id=?",
            ("challenge-2",),
        ).fetchone()[0] == "START_UNKNOWN"


def test_alternate_otp_is_transport_only_and_not_durable(tmp_path):
    path = tmp_path / "otp-transport.sqlite3"
    clock, service, verifier, evidence, first = verified(path)
    alternate = service.verification_request(evidence, otp="654321")
    replayed = service.verify_challenge(alternate)
    assert replayed == first
    assert verifier.verify_calls == 1
    with sqlite3.connect(path) as db:
        rendered = repr([
            tuple(row) for table in (
                "shopping_verification_challenges", "shopping_verification_attempts",
                "shopping_trusted_receipts", "shopping_auth_audit",
            ) for row in db.execute(f"SELECT * FROM {table}")
        ])
    for value in ("123456", "654321", "otp", "digest", "hmac"):
        assert value not in rendered.lower()


def test_expiry_and_terminal_state_cannot_revive(tmp_path):
    path = tmp_path / "expiry.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, _ = make_service(path, clock, challenge_lifetime=timedelta(minutes=1))
    evidence = start(service)
    clock.value = NOW + timedelta(minutes=1)
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT status FROM shopping_verification_challenges").fetchone()[0] == "EXPIRED"


def test_tx1_audit_failure_rolls_back_everything(tmp_path):
    path = tmp_path / "audit.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, _ = make_service(path, clock, audit_failure_hook=lambda _: (_ for _ in ()).throw(RuntimeError()))
    evidence = start(service)
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        for table in ("shopping_verification_attempts", "shopping_trusted_receipts", "shopping_auth_audit"):
            assert db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
        assert db.execute("SELECT status,version FROM shopping_verification_challenges").fetchone() == ("STARTED", 1)


def test_tx1_result_validation_precedes_commit(tmp_path):
    path = tmp_path / "invalid-result.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, verifier = make_service(path, clock)
    evidence = start(service)
    verifier.verify_override = lambda request: {"provider": "payload"}
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_attempts").fetchone()[0] == 0


def test_tx1_model_failure_rolls_back_before_commit(tmp_path, monkeypatch):
    path = tmp_path / "model-failure.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, _ = make_service(path, clock)
    evidence = start(service)

    def fail_model(**_kwargs):
        raise RuntimeError("injected model failure")

    monkeypatch.setattr(verification_module, "TrustedPhoneVerification", fail_model)
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_attempts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM shopping_trusted_receipts").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM shopping_auth_audit").fetchone()[0] == 0
        assert db.execute("SELECT status,version FROM shopping_verification_challenges").fetchone() == ("STARTED", 1)


def test_tx1_returns_outcome_constructed_before_commit(tmp_path, monkeypatch):
    path = tmp_path / "precommit-result.sqlite3"
    persistence.initialize_schema(path)
    clock = Clock(NOW)
    service, _ = make_service(path, clock)
    evidence = start(service)
    original = service._replay_result
    states = []
    constructed = []

    def observe(connection, row, *, request, now):
        states.append(connection.in_transaction)
        result = original(connection, row, request=request, now=now)
        constructed.append(result)
        return result

    monkeypatch.setattr(service, "_replay_result", observe)
    outcome = service.verify_challenge(service.verification_request(evidence, otp="123456"))
    assert outcome.receipt.receipt_id
    assert states == [True]
    assert outcome is constructed[0]


def test_durable_conflicting_receipt_binding_fails_closed(tmp_path):
    path = tmp_path / "receipt-conflict.sqlite3"
    clock, service, verifier, evidence, outcome = verified(path)
    with sqlite3.connect(path) as db:
        db.execute(
            "UPDATE shopping_trusted_receipts SET provider_verification_id=? WHERE receipt_id=?",
            ("provider-verification-conflict", str(outcome.receipt.receipt_id)),
        )
        db.commit()
    with pytest.raises(PhoneVerificationRejected):
        service.verify_challenge(service.verification_request(evidence, otp="123456"))
    assert verifier.verify_calls == 1


def test_trusted_receipt_provenance_and_tx2_exactly_once(tmp_path):
    path = tmp_path / "tx2.sqlite3"
    persistence.initialize_schema(path)
    persistence.SQLiteCustomerSessionStore(path).save_customer(customer())
    clock, service, _, evidence, outcome = verified(path)
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT challenge_id,attempt_id,provider_source,provider_verification_id,lifecycle FROM shopping_trusted_receipts").fetchone()
        assert row[:4] == (str(evidence.challenge_reference),
                           db.execute("SELECT attempt_id FROM shopping_verification_attempts").fetchone()[0],
                           "synthetic.mock", "provider-verification-1")
        assert row[4] == "ISSUED"
    session = CustomerSessionService(path, secret_factory=lambda: "session-secret",
                                     session_id_factory=lambda: "AG-SES-" + "4" * 12 + "4" + "4" * 3 + "8" + "4" * 15)
    issued = session.consume_receipt_and_create_session(
        outcome.receipt, expected_challenge=BROWSER, trusted_context=outcome.context,
        now=clock.value, correlation_id="corr-tx2",
    )
    assert issued.receipt_id == outcome.receipt.receipt_id
    with pytest.raises(Exception):
        session.consume_receipt_and_create_session(
            outcome.receipt, expected_challenge=BROWSER, trusted_context=outcome.context,
            now=clock.value, correlation_id="corr-tx2-replay",
        )
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT lifecycle FROM shopping_trusted_receipts").fetchone()[0] == "CONSUMED"
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_receipts").fetchone()[0] == 1


def test_concurrent_tx2_consumption_has_one_winner(tmp_path):
    path = tmp_path / "tx2-concurrent.sqlite3"
    persistence.initialize_schema(path)
    persistence.SQLiteCustomerSessionStore(path).save_customer(customer())
    clock, _, _, _, outcome = verified(path)

    def consume(index):
        service = CustomerSessionService(
            path, secret_factory=lambda: f"secret-{index}",
            session_id_factory=lambda: "AG-SES-" + str(index) * 12 + "4" + str(index) * 3 + "8" + str(index) * 15,
        )
        try:
            return service.consume_receipt_and_create_session(
                outcome.receipt, expected_challenge=BROWSER, trusted_context=outcome.context,
                now=clock.value, correlation_id=f"corr-{index}",
            )
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(consume, (1, 2)))
    assert sum(not isinstance(value, Exception) for value in results) == 1
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM shopping_sessions").fetchone()[0] == 1
        assert db.execute("SELECT lifecycle FROM shopping_trusted_receipts").fetchone()[0] == "CONSUMED"


def test_concurrent_tx1_and_tx2_have_one_winner(tmp_path):
    path = tmp_path / "concurrent.sqlite3"
    persistence.initialize_schema(path)
    persistence.SQLiteCustomerSessionStore(path).save_customer(customer())
    clock = Clock(NOW)
    first, _ = make_service(path, clock)
    evidence = start(first)
    request = first.verification_request(evidence, otp="123456")

    def verify():
        try:
            return first.verify_challenge(request)
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: verify(), range(2)))
    assert all(not isinstance(value, Exception) for value in results)
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM shopping_trusted_receipts").fetchone()[0] == 1


def test_tx2_audit_failure_rolls_back_session_and_consumption(tmp_path):
    path = tmp_path / "tx2-audit.sqlite3"
    persistence.initialize_schema(path)
    persistence.SQLiteCustomerSessionStore(path).save_customer(customer())
    clock, _, _, _, outcome = verified(path)
    session = CustomerSessionService(path, audit_failure_hook=lambda _: (_ for _ in ()).throw(RuntimeError()))
    with pytest.raises(AuditPersistenceError):
        session.consume_receipt_and_create_session(outcome.receipt, expected_challenge=BROWSER,
                                                   trusted_context=outcome.context, now=clock.value,
                                                   correlation_id="corr-fail")
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM shopping_sessions").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM shopping_verification_receipts").fetchone()[0] == 0
        assert db.execute("SELECT lifecycle FROM shopping_trusted_receipts").fetchone()[0] == "ISSUED"


def test_storage_and_schema_fail_closed(tmp_path):
    path = tmp_path / "missing.sqlite3"
    clock = Clock(NOW)
    with pytest.raises(PhoneVerificationRejected):
        make_service(path, clock)[0].start_challenge(PHONE, customer_id=CUSTOMER,
                                                       browser_challenge=BROWSER)
    bad = tmp_path / "bad.sqlite3"
    with sqlite3.connect(bad) as db:
        db.execute("CREATE TABLE shopping_customer_persistence_meta (name TEXT PRIMARY KEY, version TEXT NOT NULL)")
        db.execute("INSERT INTO shopping_customer_persistence_meta VALUES ('schema','future')")
        db.commit()
    with pytest.raises(PhoneVerificationRejected):
        make_service(bad, clock)[0].start_challenge(PHONE, customer_id=CUSTOMER,
                                                      browser_challenge=BROWSER)


def test_existing_b3_receipt_ledger_semantics_are_not_repurposed():
    assert persistence.HISTORICAL_SCHEMA_VERSION == PERSISTENCE_SCHEMA_VERSION
    assert persistence.SCHEMA_VERSION == CURRENT_PERSISTENCE_SCHEMA_VERSION
    assert "shopping_verification_receipts" not in persistence.VERIFICATION_SCHEMA_TABLES


def test_c4_schema_metadata_is_v3_and_reconciliation_history_is_append_only(tmp_path):
    path = tmp_path / "c4-schema.sqlite3"
    persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT version FROM shopping_customer_persistence_meta WHERE name='schema'"
        ).fetchone()[0] == "shopping-customer-persistence/v3"
        assert {
            row[0] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND "
            "name LIKE 'shopping_verification_reconciliation_events_no_%'"
            ).fetchall()
        } == {
            "shopping_verification_reconciliation_events_no_delete",
            "shopping_verification_reconciliation_events_no_update",
        }


@pytest.mark.parametrize(
    "trigger_name",
    [
        "shopping_verification_reconciliation_events_no_update",
        "shopping_verification_reconciliation_events_no_delete",
    ],
)
def test_open_rejects_v3_schema_missing_required_append_only_trigger(tmp_path, trigger_name):
    path = tmp_path / f"missing-{trigger_name}.sqlite3"
    persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        db.execute(f"DROP TRIGGER {trigger_name}")
        db.commit()
    with pytest.raises(persistence.PersistenceSchemaError):
        persistence.open_connection(path)


def test_open_rejects_malformed_v3_append_only_trigger(tmp_path):
    path = tmp_path / "malformed-trigger.sqlite3"
    persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER shopping_verification_reconciliation_events_no_update")
        db.execute(
            "CREATE TRIGGER shopping_verification_reconciliation_events_no_update "
            "BEFORE DELETE ON shopping_verification_reconciliation_events BEGIN "
            "SELECT RAISE(ABORT, 'wrong shape'); END"
        )
        db.commit()
    with pytest.raises(persistence.PersistenceSchemaError):
        persistence.open_connection(path)


def test_initialize_schema_rejects_existing_unversioned_user_schema(tmp_path):
    path = tmp_path / "unversioned-user-schema.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE user_owned_data (id INTEGER PRIMARY KEY)")
        db.commit()
    with pytest.raises(persistence.PersistenceSchemaError):
        persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='shopping_customer_persistence_meta'"
        ).fetchone() is None


@pytest.mark.parametrize("historical_version", ["shopping-customer-persistence/v1", "shopping-customer-persistence/v2"])
def test_historical_v1_and_v2_open_fail_closed_without_silent_upgrade(tmp_path, historical_version):
    path = tmp_path / (historical_version.rsplit("/", 1)[-1] + ".sqlite3")
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE shopping_customer_persistence_meta "
            "(name TEXT PRIMARY KEY, version TEXT NOT NULL)"
        )
        db.execute(
            "INSERT INTO shopping_customer_persistence_meta VALUES ('schema', ?)",
            (historical_version,),
        )
        db.commit()
    with pytest.raises(persistence.PersistenceSchemaError):
        persistence.open_connection(path)
    with pytest.raises(persistence.PersistenceSchemaError):
        persistence.initialize_schema(path)
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT version FROM shopping_customer_persistence_meta WHERE name='schema'"
        ).fetchone()[0] == historical_version
        assert db.execute(
            "SELECT name FROM sqlite_master WHERE name='shopping_verification_unknown_outcomes'"
        ).fetchone() is None
