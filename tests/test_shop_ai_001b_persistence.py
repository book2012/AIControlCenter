"""Synthetic, isolated persistence tests for SHOP_AI_001B-2."""
from datetime import datetime, timedelta, timezone
import json
import socket
import sqlite3
import sys

import pytest

from core.shopping import customer_identity as identity
from core.shopping import customer_persistence as persistence
from core.shopping import customer_sessions as sessions
from core.shopping.inquiries import SQLiteInquiryRepository
from core.shopping.models import Product

START = datetime(2026, 9, 1, tzinfo=timezone.utc)
VERIFIED = START + timedelta(minutes=1)
CREATED = START + timedelta(minutes=5)
NOW = START + timedelta(minutes=10)
CUSTOMER_ID = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
OTHER_CUSTOMER_ID = "AG-CUS-" + "9" * 12 + "4" + "9" * 3 + "8" + "9" * 15
CONTACT_REF = "AG-CON-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
SESSION_ID = "AG-SES-" + "3" * 12 + "4" + "3" * 3 + "8" + "3" * 15
MOCK_HASH = "sha256:" + "a" * 64


@pytest.fixture(autouse=True)
def isolated_io(monkeypatch):
    attempts = []

    def deny(*args, **kwargs):
        attempts.append("external_access")
        raise AssertionError("external access is prohibited in persistence tests")

    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket, "getaddrinfo", deny)
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", deny)
    monkeypatch.delenv("AICC_INSTAGRAM_CONTACT_URL", raising=False)
    assert "core.api.app" not in sys.modules
    yield
    assert not attempts
    assert "core.api.app" not in sys.modules


@pytest.fixture
def customer():
    return identity.Customer(
        id=CUSTOMER_ID, state="ACTIVE", created_at=START, updated_at=CREATED,
        contact_binding=identity.VerifiedContactBinding(
            customer_id=CUSTOMER_ID, state="VERIFIED", created_at=START,
            updated_at=VERIFIED, contact_ref=CONTACT_REF, verified_at=VERIFIED,
        ),
    )


@pytest.fixture
def record():
    return sessions.PrivateSessionRecord(
        session=sessions.CustomerSession(
            id=SESSION_ID, customer_id=CUSTOMER_ID, created_at=CREATED,
            last_activity_at=CREATED, idle_expires_at=CREATED + sessions.IDLE_LIFETIME,
            absolute_expires_at=CREATED + sessions.ABSOLUTE_LIFETIME,
        ),
        session_secret_hash=MOCK_HASH, security_policy_version="1.0.0",
        credential_bound_at=CREATED, verified_contact_ref=CONTACT_REF,
        contact_verified_at=VERIFIED,
    )


@pytest.fixture
def store(tmp_path):
    path = tmp_path / "isolated-shopping.sqlite3"
    persistence.SQLiteCustomerSessionStore.initialize_schema(path)
    return persistence.SQLiteCustomerSessionStore(path)


@pytest.fixture
def inquiry(tmp_path):
    path = tmp_path / "isolated-inquiries.sqlite3"
    repo = SQLiteInquiryRepository(str(path))
    SQLiteInquiryRepository.initialize_persistence_schema(str(path))
    product = Product(id="mock-product", name="Synthetic", slug="synthetic", description="Mock",
                      price=1, currency="KRW", category="Mock", in_stock=True, source="mock")
    created = repo.create(product, None, "Initial inquiry")
    return repo, created.id, path


def test_schema_is_explicit_and_unknown_version_fails_closed(tmp_path):
    path = tmp_path / "uninitialized.sqlite3"
    store = persistence.SQLiteCustomerSessionStore(path)
    with pytest.raises(persistence.PersistenceSchemaError):
        store.get_customer(CUSTOMER_ID)
    persistence.initialize_schema(path)
    with sqlite3.connect(path) as connection:
        connection.execute("UPDATE shopping_customer_persistence_meta SET version='future' WHERE name='schema'")
    with pytest.raises(persistence.PersistenceSchemaError):
        store.get_customer(CUSTOMER_ID)


def test_customer_and_session_roundtrip_is_durable_and_secret_free(store, customer, record):
    store.save_customer(customer, contact_ref=CONTACT_REF)
    store.save_session(record)
    reopened = persistence.SQLiteCustomerSessionStore(store.database_path)
    assert reopened.get_customer(CUSTOMER_ID) == customer
    loaded = reopened.get_session(SESSION_ID)
    assert loaded is not None and loaded.session == record.session
    assert MOCK_HASH not in customer.model_dump_json()
    assert MOCK_HASH not in loaded.session.model_dump_json()
    with sqlite3.connect(store.database_path) as connection:
        raw = " ".join(str(row) for row in connection.execute("SELECT * FROM shopping_sessions"))
        assert MOCK_HASH in raw


def test_revocation_is_durable_and_cannot_be_reopened_as_eligible(store, customer, record):
    store.save_customer(customer)
    store.save_session(record)
    store.revoke_session(SESSION_ID, revoked_at=NOW)
    loaded = store.get_session(SESSION_ID)
    assert loaded is not None and loaded.session.revoked_at == NOW
    assert sessions.evaluate_session(loaded, customer, now=NOW) is sessions.SessionPolicyStatus.REVOKED
    with sqlite3.connect(store.database_path) as connection:
        connection.execute("UPDATE shopping_sessions SET session_json=? WHERE session_id=?",
                           (record.session.model_dump_json(), SESSION_ID))
    loaded_again = store.get_session(SESSION_ID)
    assert loaded_again is not None and loaded_again.session.revoked_at == NOW


@pytest.mark.parametrize("now", [CREATED + sessions.IDLE_LIFETIME, CREATED + sessions.ABSOLUTE_LIFETIME])
def test_idle_and_absolute_expiration_are_enforced(store, customer, record, now):
    store.save_customer(customer)
    store.save_session(record)
    connection = persistence.open_connection(store.database_path)
    try:
        assert persistence.persisted_session_status(connection, CUSTOMER_ID, SESSION_ID, now=now) is sessions.SessionPolicyStatus.EXPIRED
    finally:
        connection.close()


@pytest.mark.parametrize("customer_state", ["SUSPENDED", "CLOSED"])
def test_inactive_customer_rejects_persisted_session(store, customer, record, customer_state):
    changed = customer.model_copy(update={"state": identity.CustomerState(customer_state)})
    if customer_state == "CLOSED":
        changed = customer.model_copy(update={
            "state": identity.CustomerState.CLOSED,
            "contact_binding": customer.contact_binding.model_copy(
                update={"state": identity.VerificationState.REVOKED, "updated_at": CREATED, "revoked_at": CREATED}
            ),
        })
    store.save_customer(changed)
    store.save_session(record)
    connection = persistence.open_connection(store.database_path)
    try:
        assert persistence.persisted_session_status(connection, CUSTOMER_ID, SESSION_ID, now=NOW) is sessions.SessionPolicyStatus.CUSTOMER_INACTIVE
    finally:
        connection.close()


def test_customer_session_mismatch_rejects_persisted_session(store, customer, record):
    store.save_customer(customer)
    store.save_session(record.model_copy(update={"session": record.session.model_copy(update={"customer_id": OTHER_CUSTOMER_ID})}))
    connection = persistence.open_connection(store.database_path)
    try:
        assert persistence.persisted_session_status(connection, CUSTOMER_ID, SESSION_ID, now=NOW) is sessions.SessionPolicyStatus.BINDING_MISMATCH
    finally:
        connection.close()


def _prepare(repo, inquiry_id, store, customer, record):
    # The ownership, authority and inquiry mutation must share one SQLite DB.
    if str(store.database_path) != str(repo._db_path):
        persistence.initialize_schema(repo._db_path)
        store = persistence.SQLiteCustomerSessionStore(repo._db_path)
    store.save_customer(customer)
    store.save_session(record)
    repo.bind_customer_ownership(inquiry_id, CUSTOMER_ID, SESSION_ID)


def test_atomic_message_mutation_persists_version_and_audit(inquiry, store, customer, record):
    repo, inquiry_id, path = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    message = repo.append_message_authorized(
        inquiry_id, "Synthetic message", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
        expected_version=0, idempotency_key="idem-1", actor_ref="actor-1", correlation_id="corr-1", now=NOW,
    )
    assert message.body == "Synthetic message"
    payload = SQLiteInquiryRepository(str(path)).get(inquiry_id)
    assert payload is not None and payload.messages[-1].id == message.id
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM shopping_inquiry_ownership WHERE inquiry_id=?", (inquiry_id,)).fetchone()[0] == 1
        audit = connection.execute("SELECT actor_ref,resource_ref,action,outcome,correlation_id FROM shopping_inquiry_audit").fetchone()
        assert tuple(audit) == ("actor-1", inquiry_id, "INQUIRY_MESSAGE_APPEND", "APPLIED", "corr-1")


def test_ownership_mismatch_never_authorizes_mutation(inquiry, store, customer, record):
    repo, inquiry_id, _ = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    with pytest.raises(persistence.AuthorizationConflict):
        repo.append_message_authorized(
            inquiry_id, "Denied", "customer", customer_id=OTHER_CUSTOMER_ID, session_id=SESSION_ID,
            expected_version=0, idempotency_key="idem-denied", actor_ref="actor", correlation_id="corr", now=NOW,
        )


def test_version_conflict_and_competing_update_are_fail_closed(inquiry, store, customer, record):
    repo, inquiry_id, _ = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    repo.append_message_authorized(
        inquiry_id, "First", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
        expected_version=0, idempotency_key="idem-first", actor_ref="actor", correlation_id="corr-1", now=NOW,
    )
    with pytest.raises(persistence.InquiryVersionConflict):
        repo.append_message_authorized(
            inquiry_id, "Competing", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
            expected_version=0, idempotency_key="idem-second", actor_ref="actor", correlation_id="corr-2", now=NOW,
        )


def test_identical_replay_is_secret_free_and_conflicting_reuse_fails(inquiry, store, customer, record):
    repo, inquiry_id, _ = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    first = repo.append_message_authorized(
        inquiry_id, "Replay", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
        expected_version=0, idempotency_key="idem-replay", actor_ref="actor", correlation_id="corr", now=NOW,
    )
    replay = repo.append_message_authorized(
        inquiry_id, "Replay", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
        expected_version=0, idempotency_key="idem-replay", actor_ref="actor", correlation_id="corr", now=NOW,
    )
    assert replay == first
    with pytest.raises(persistence.IdempotencyConflict):
        repo.append_message_authorized(
            inquiry_id, "Different", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
            expected_version=0, idempotency_key="idem-replay", actor_ref="actor", correlation_id="corr", now=NOW,
        )


def test_audit_contains_no_message_or_security_material(inquiry, store, customer, record):
    repo, inquiry_id, path = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    repo.append_message_authorized(
        inquiry_id, "secret-message-body", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
        expected_version=0, idempotency_key="idem-audit", actor_ref="actor", correlation_id="corr", now=NOW,
    )
    with sqlite3.connect(path) as connection:
        audit = json.dumps([tuple(row) for row in connection.execute("SELECT * FROM shopping_inquiry_audit")])
        idem = json.dumps([tuple(row) for row in connection.execute("SELECT * FROM shopping_inquiry_idempotency")])
        assert "secret-message-body" not in audit and MOCK_HASH not in audit and "token" not in audit.lower()
        assert MOCK_HASH not in idem


def test_audit_failure_rolls_back_message_version_and_idempotency(inquiry, store, customer, record):
    repo, inquiry_id, path = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON shopping_inquiry_audit BEGIN SELECT RAISE(ABORT,'audit failure'); END")
    with pytest.raises(persistence.StorageUnavailable):
        repo.append_message_authorized(
            inquiry_id, "must rollback", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
            expected_version=0, idempotency_key="idem-rollback", actor_ref="actor", correlation_id="corr", now=NOW,
        )
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT version FROM shopping_inquiry_ownership WHERE inquiry_id=?", (inquiry_id,)).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM shopping_inquiry_idempotency").fetchone()[0] == 0
    assert SQLiteInquiryRepository(str(path)).get(inquiry_id).messages == []


def test_lock_contention_is_bounded_and_fail_closed(inquiry, store, customer, record):
    repo, inquiry_id, path = inquiry
    _prepare(repo, inquiry_id, store, customer, record)
    connection = persistence.open_connection(path)
    connection.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(persistence.StorageUnavailable):
            repo.append_message_authorized(
                inquiry_id, "locked", "customer", customer_id=CUSTOMER_ID, session_id=SESSION_ID,
                expected_version=0, idempotency_key="idem-lock", actor_ref="actor", correlation_id="corr", now=NOW,
            )
    finally:
        connection.rollback()
        connection.close()


def test_legacy_token_storage_and_projection_remain_redacted(inquiry, monkeypatch):
    repo, inquiry_id, path = inquiry
    from core.shopping import inquiries
    monkeypatch.setattr(inquiries.secrets, "token_urlsafe", lambda count: "legacy-secret-token")
    product = Product(id="second-product", name="Second", slug="second", description="Mock",
                      price=1, currency="KRW", category="Mock", in_stock=True, source="mock")
    created = repo.create(product, None, "Legacy")
    assert created.public_access_token == "legacy-secret-token"
    result = repo.get(inquiry_id)
    assert result is not None and result.public_access_token is None
    with sqlite3.connect(path) as connection:
        payload = connection.execute("SELECT payload FROM inquiries WHERE id=?", (inquiry_id,)).fetchone()[0]
        assert "public_access_token" not in payload
        stored = connection.execute("SELECT payload,token_hash FROM inquiries WHERE id=?", (created.id,)).fetchone()
        assert "legacy-secret-token" not in stored[0]
        assert stored[1] == __import__("hashlib").sha256(b"legacy-secret-token").hexdigest()


def test_no_persistence_records_grant_legacy_inquiry_access(inquiry, customer, record, store):
    repo, inquiry_id, _ = inquiry
    store.save_customer(customer)
    store.save_session(record)
    assert repo.authorize(inquiry_id, CUSTOMER_ID) is False
    assert repo.authorize(inquiry_id, SESSION_ID) is False
