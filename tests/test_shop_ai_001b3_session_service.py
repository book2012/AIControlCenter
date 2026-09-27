"""Mock-only tests for the bounded trusted customer-session service."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import itertools
import socket
import sqlite3
import sys

import pytest

from core.shopping import customer_identity as identity
from core.shopping import customer_persistence as persistence
from core.shopping.customer_auth import (
    RECEIPT_MAX_LIFETIME, ReceiptLifecycle, TrustedReceiptBinding,
    TrustedVerificationContext, TrustedVerificationReceipt, VerificationPurpose,
)
from core.shopping.customer_session_service import (
    AuditPersistenceError, CustomerNotEligible, CustomerSessionService,
    ReceiptAlreadyConsumed, ReceiptPolicyDenied, SessionServiceError,
    SessionValidationCode,
)


START = datetime(2026, 9, 1, tzinfo=timezone.utc)
VERIFIED = START + timedelta(seconds=30)
NOW = START + timedelta(minutes=2)
CUSTOMER_ID = "AG-CUS-" + "1" * 12 + "4" + "1" * 3 + "8" + "1" * 15
OTHER_CUSTOMER_ID = "AG-CUS-" + "9" * 12 + "4" + "9" * 3 + "8" + "9" * 15
CONTACT_REF = "AG-CON-" + "2" * 12 + "4" + "2" * 3 + "8" + "2" * 15
RECEIPT_ID = "AG-VRF-" + "3" * 12 + "4" + "3" * 3 + "8" + "3" * 15
CHALLENGE = "AG-CHL-" + "4" * 12 + "4" + "4" * 3 + "8" + "4" * 15
ISSUER = "AG-ISS-" + "5" * 12 + "4" + "5" * 3 + "8" + "5" * 15
SESSION_ID = "AG-SES-" + "6" * 12 + "4" + "6" * 3 + "8" + "6" * 15
SECRET = "synthetic-session-secret"
EVENT_COUNTER = itertools.count(1)


@pytest.fixture(autouse=True)
def isolated_io(monkeypatch):
    attempts = []

    def deny(*args, **kwargs):
        attempts.append(True)
        raise AssertionError("external access is prohibited in service tests")

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
        id=CUSTOMER_ID, state=identity.CustomerState.ACTIVE,
        created_at=START, updated_at=START + timedelta(minutes=1),
        contact_binding=identity.VerifiedContactBinding(
            customer_id=CUSTOMER_ID, state=identity.VerificationState.VERIFIED,
            created_at=START, updated_at=VERIFIED,
            contact_ref=CONTACT_REF, verified_at=VERIFIED,
        ),
    )


def make_receipt(**updates):
    payload = dict(
        receipt_id=RECEIPT_ID, purpose=VerificationPurpose.SESSION_ISSUANCE,
        browser_challenge=CHALLENGE, issuer_ref=ISSUER, customer_id=CUSTOMER_ID,
        issued_at=START, expires_at=START + RECEIPT_MAX_LIFETIME,
        lifecycle=ReceiptLifecycle.ISSUED,
    )
    payload.update(updates)
    return TrustedVerificationReceipt(**payload)


def make_context(receipt_value=None, customer_id=CUSTOMER_ID):
    current = receipt_value or make_receipt(customer_id=customer_id)
    return TrustedVerificationContext(accepted_bindings=frozenset({
        TrustedReceiptBinding(current.receipt_id, current.issuer_ref, current.customer_id),
    }))


def service(path, *, secret=SECRET, session_id=SESSION_ID, audit_failure_hook=None):
    return CustomerSessionService(
        str(path), secret_factory=lambda: secret,
        session_id_factory=lambda: session_id,
        event_id_factory=lambda: "AG-AUD-" + f"{next(EVENT_COUNTER):032d}",
        audit_failure_hook=audit_failure_hook,
    )


@pytest.fixture
def database(tmp_path, customer):
    path = tmp_path / "trusted-session.sqlite3"
    persistence.initialize_schema(path)
    persistence.SQLiteCustomerSessionStore(path).save_customer(customer)
    return path


def issue(database, *, receipt_value=None, context=None, **kwargs):
    current = receipt_value or make_receipt()
    return service(database, **kwargs).consume_receipt_and_create_session(
        current, expected_challenge=current.browser_challenge,
        trusted_context=context or make_context(current), now=NOW,
        correlation_id="corr-issue",
    )


def test_valid_receipt_issues_secret_and_projection(database):
    result = issue(database)
    assert result.session_id == SESSION_ID
    assert result.session_secret.get_secret_value() == SECRET
    assert result.projection.customer_id == CUSTOMER_ID
    assert SECRET not in repr(result)
    with sqlite3.connect(database) as connection:
        row = connection.execute("SELECT secret_hash,session_json FROM shopping_sessions").fetchone()
        assert SECRET not in " ".join(row)
        assert row[0].startswith("sha256:")


@pytest.mark.parametrize("mutator", [
    lambda r: r.model_copy(update={"browser_challenge": CHALLENGE.replace("4", "6")}),
    lambda r: r.model_copy(update={"expires_at": START}),
    lambda r: r.model_copy(update={"lifecycle": ReceiptLifecycle.CONSUMED}),
])
def test_invalid_receipt_policy_is_rejected(database, mutator):
    current = mutator(make_receipt())
    with pytest.raises(ReceiptPolicyDenied):
        issue(database, receipt_value=current, context=make_context(current))


def test_untrusted_receipt_and_customer_binding_are_rejected(database):
    with pytest.raises(ReceiptPolicyDenied):
        issue(database, context=TrustedVerificationContext())
    forged = make_receipt(customer_id=OTHER_CUSTOMER_ID)
    with pytest.raises(CustomerNotEligible):
        issue(database, receipt_value=forged, context=make_context(forged))


def test_receipt_replay_is_single_winner_and_durable(database):
    first = issue(database)
    with pytest.raises(ReceiptAlreadyConsumed):
        issue(database)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM shopping_verification_receipts").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM shopping_sessions").fetchone()[0] == 1
    reopened = service(database)
    with pytest.raises(ReceiptAlreadyConsumed):
        reopened.consume_receipt_and_create_session(
            make_receipt(), expected_challenge=CHALLENGE,
            trusted_context=make_context(), now=NOW, correlation_id="corr-reopen",
        )
    assert first.receipt_id == RECEIPT_ID


def test_competing_consumers_produce_at_most_one_session(database):
    def attempt(index):
        try:
            result = CustomerSessionService(
                str(database), secret_factory=lambda: f"secret-{index}",
                session_id_factory=lambda: "AG-SES-" + str(index) * 12 + "4" + str(index) * 3 + "8" + str(index) * 15,
            ).consume_receipt_and_create_session(
                make_receipt(), expected_challenge=CHALLENGE,
                trusted_context=make_context(), now=NOW, correlation_id=f"corr-{index}",
            )
            return "ok", result
        except Exception as exc:
            return "error", exc

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))
    assert sum(kind == "ok" for kind, _ in results) == 1
    assert sum(kind == "error" for kind, _ in results) == 1
    assert all(isinstance(value, ReceiptAlreadyConsumed) or isinstance(value, SessionServiceError)
               for kind, value in results if kind == "error")


def test_customer_states_and_contact_binding_fail_closed(tmp_path, customer):
    for state in (identity.CustomerState.SUSPENDED, identity.CustomerState.CLOSED):
        current = customer.model_copy(update={"state": state})
        if state is identity.CustomerState.CLOSED:
            current = current.model_copy(update={
                "contact_binding": customer.contact_binding.model_copy(
                    update={"state": identity.VerificationState.REVOKED,
                            "revoked_at": VERIFIED, "updated_at": VERIFIED}),
            })
        path = tmp_path / f"{state.value}.sqlite3"
        persistence.initialize_schema(path)
        persistence.SQLiteCustomerSessionStore(path).save_customer(current)
        with pytest.raises(CustomerNotEligible):
            issue(path)


def test_audit_failure_rolls_back_session_and_receipt(database):
    def fail(_action):
        raise RuntimeError("synthetic audit failure")

    with pytest.raises(AuditPersistenceError):
        issue(database, audit_failure_hook=fail)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM shopping_sessions").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM shopping_verification_receipts").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM shopping_auth_audit").fetchone()[0] == 0


def test_missing_or_uninitialized_storage_denies(tmp_path):
    path = tmp_path / "uninitialized.sqlite3"
    current = CustomerSessionService(str(path)).validate_session(SESSION_ID, SECRET, CUSTOMER_ID, now=NOW)
    assert current.code == SessionValidationCode.STORAGE_UNAVAILABLE


def test_valid_session_and_secret_mismatch(database):
    result = issue(database)
    checked = service(database).validate_session(SESSION_ID, SECRET, CUSTOMER_ID, now=NOW)
    assert checked.code == SessionValidationCode.VALID
    assert checked.projection is not None
    assert service(database).validate_session(SESSION_ID, "wrong", CUSTOMER_ID, now=NOW).code == SessionValidationCode.INVALID_SECRET
    assert service(database).validate_session(SESSION_ID, SECRET, OTHER_CUSTOMER_ID, now=NOW).code == SessionValidationCode.MISSING
    assert result.session_secret.get_secret_value() == SECRET


@pytest.mark.parametrize("now", [NOW + timedelta(minutes=30), START + timedelta(hours=24)])
def test_idle_and_absolute_expiry(database, now):
    issue(database)
    assert service(database).validate_session(SESSION_ID, SECRET, CUSTOMER_ID, now=now).code == SessionValidationCode.INELIGIBLE


def test_durable_revocation_and_idempotence(database):
    issue(database)
    revoked = service(database).revoke_session(SESSION_ID, now=NOW, actor_ref=CUSTOMER_ID, correlation_id="corr-revoke")
    assert revoked.code == "REVOKED"
    assert service(database).validate_session(SESSION_ID, SECRET, CUSTOMER_ID, now=NOW).code == SessionValidationCode.INELIGIBLE
    reopened = service(database)
    assert reopened.revoke_session(SESSION_ID, now=NOW, actor_ref=CUSTOMER_ID, correlation_id="corr-revoke-2").code == "ALREADY_REVOKED"


def test_revocation_audit_failure_rolls_back(database):
    issue(database)
    def fail(_action):
        raise RuntimeError("synthetic audit failure")
    with pytest.raises(AuditPersistenceError):
        service(database, audit_failure_hook=fail).revoke_session(
            SESSION_ID, now=NOW, actor_ref=CUSTOMER_ID, correlation_id="corr-fail",
        )
    assert service(database).validate_session(SESSION_ID, SECRET, CUSTOMER_ID, now=NOW).code == SessionValidationCode.VALID


def test_auth_audit_is_bounded_and_secret_free(database):
    issue(database)
    with sqlite3.connect(database) as connection:
        rows = list(connection.execute("SELECT * FROM shopping_auth_audit"))
    assert rows and all(SECRET not in str(row) for row in rows)
    assert all(len(str(value)) <= 160 for row in rows for value in row)
    assert json.dumps(rows)


def test_no_legacy_token_fallback_or_public_secret_projection(database):
    result = issue(database)
    assert not hasattr(result.projection, "session_secret_hash")
    assert not hasattr(result.projection, "public_access_token")
    assert service(database).validate_session(SESSION_ID, "legacy-token", CUSTOMER_ID, now=NOW).code == SessionValidationCode.INVALID_SECRET


def test_b3a_and_existing_contract_compatibility():
    from core.shopping.customer_auth import ReceiptValidationResult
    from core.shopping.customer_sessions import IDLE_LIFETIME, ABSOLUTE_LIFETIME
    assert ReceiptValidationResult.ACCEPTED.value == "ACCEPTED"
    assert IDLE_LIFETIME == timedelta(minutes=30)
    assert ABSOLUTE_LIFETIME == timedelta(hours=24)
