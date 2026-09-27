"""Deterministic, network-blocked SHOP_AI_001B-1 contract tests only."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import socket
import sqlite3
import sys

from pydantic import ValidationError
import pytest


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
    connect = sqlite3.connect

    def deny_external(*args, **kwargs):
        attempts.append("external_access")
        raise AssertionError("External access is prohibited in identity/session tests")

    def memory_connect(database, *args, **kwargs):
        # Inquiry route imports compute an expected schema digest in memory.
        if database != ":memory:" or kwargs.get("uri"):
            return deny_external()
        return connect(database, *args, **kwargs)

    for name in ("connect", "connect_ex", "sendto"):
        monkeypatch.setattr(socket.socket, name, deny_external)
    monkeypatch.setattr(socket, "create_connection", deny_external)
    monkeypatch.setattr(socket, "getaddrinfo", deny_external)
    monkeypatch.setattr(sqlite3, "connect", memory_connect)
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", deny_external)
    monkeypatch.delenv("AICC_INSTAGRAM_CONTACT_URL", raising=False)
    from core.config.loader import ConfigLoader
    monkeypatch.setattr(ConfigLoader, "load", deny_external)
    assert "core.api.app" not in sys.modules
    yield
    assert not attempts
    assert "core.api.app" not in sys.modules


@pytest.fixture
def identity(isolated_io):
    from core.shopping import customer_identity
    return customer_identity


@pytest.fixture
def sessions(isolated_io):
    from core.shopping import customer_sessions
    return customer_sessions


@pytest.fixture
def customer(identity):
    return identity.Customer(
        id=CUSTOMER_ID, state="ACTIVE", created_at=START, updated_at=CREATED,
        contact_binding=identity.VerifiedContactBinding(
            customer_id=CUSTOMER_ID, state="VERIFIED", created_at=START,
            updated_at=VERIFIED, contact_ref=CONTACT_REF, verified_at=VERIFIED),
    )


@pytest.fixture
def record(sessions):
    return sessions.PrivateSessionRecord(
        session=sessions.CustomerSession(
            id=SESSION_ID, customer_id=CUSTOMER_ID, created_at=CREATED,
            last_activity_at=CREATED, idle_expires_at=CREATED + sessions.IDLE_LIFETIME,
            absolute_expires_at=CREATED + sessions.ABSOLUTE_LIFETIME),
        session_secret_hash=MOCK_HASH, security_policy_version="1.0.0",
        credential_bound_at=CREATED, verified_contact_ref=CONTACT_REF,
        contact_verified_at=VERIFIED,
    )


def changed(model, **updates):
    # Revalidate rather than relying on Pydantic's unchecked copy(update=...).
    return type(model).model_validate(model.model_copy(update=updates))


def consent(identity, purpose, state="GRANTED", **updates):
    return identity.PurposeSpecificConsent(**{
        "customer_id": CUSTOMER_ID, "purpose": purpose, "state": state,
        "decided_at": VERIFIED, "policy_version": "sms-v1", **updates,
    })


def test_valid_customer_roundtrip_and_explicit_nullable_fields(identity, customer):
    assert identity.Customer.model_validate_json(customer.model_dump_json()) == customer
    assert customer.schema_version == "1.0.0"
    assert customer.contact_binding.revoked_at is None
    unverified = identity.Customer(id=CUSTOMER_ID, state="ACTIVE", created_at=START,
                                   updated_at=START)
    assert unverified.model_dump()["contact_binding"] is None
    assert not identity.customer_is_session_eligible(unverified, now=NOW)
    assert identity.customer_is_session_eligible(customer, now=NOW)
    with pytest.raises(ValidationError):
        customer.state = identity.CustomerState.CLOSED


@pytest.mark.parametrize("value", ["", " ", "customer", "0" * 11, "+mock-contact",
                                    CUSTOMER_ID + "x", CUSTOMER_ID + "\n",
                                    CUSTOMER_ID.lower(), "AG-CUS-" + "a" * 32, 17, None])
def test_invalid_customer_identifiers(customer, value):
    with pytest.raises(ValidationError):
        changed(customer, id=value)


@pytest.mark.parametrize("field", ["phone_number", "raw_session_secret", "otp",
                                    "authenticated", "inquiry_authorized"])
def test_customer_unknown_fields_rejected(identity, customer, field):
    with pytest.raises(ValidationError):
        identity.Customer.model_validate({**customer.model_dump(), field: "mock-only"})


@pytest.mark.parametrize("state", ["UNKNOWN", "verified", "", True, None])
def test_invalid_verification_states(customer, state):
    with pytest.raises(ValidationError):
        changed(customer.contact_binding, state=state)


@pytest.mark.parametrize("updates", [
    {"contact_ref": None}, {"contact_ref": "mock-invalid-contact"}, {"verified_at": None},
    {"verified_at": START - timedelta(seconds=1)}, {"verified_at": NOW},
    {"updated_at": START - timedelta(seconds=1)}, {"revoked_at": VERIFIED},
    {"state": "UNVERIFIED"}, {"state": "REVOKED"},
    {"state": "REVOKED", "revoked_at": START},
])
def test_inconsistent_verified_bindings_rejected(customer, updates):
    with pytest.raises(ValidationError):
        changed(customer.contact_binding, **updates)


def test_binding_must_belong_to_customer_and_fit_its_lifetime(customer):
    for binding in (changed(customer.contact_binding, customer_id=OTHER_CUSTOMER_ID),
                    changed(customer.contact_binding, created_at=START - timedelta(seconds=1))):
        with pytest.raises(ValidationError):
            changed(customer, contact_binding=binding)


@pytest.mark.parametrize("state", ["UNVERIFIED", "REVERIFICATION_REQUIRED", "REVOKED"])
def test_nonverified_contact_never_eligible(identity, customer, state):
    updates = {"state": state}
    if state == "UNVERIFIED":
        updates.update(contact_ref=None, verified_at=None)
    if state == "REVOKED":
        updates["revoked_at"] = VERIFIED
    current = changed(customer, contact_binding=changed(customer.contact_binding, **updates))
    assert not identity.customer_is_session_eligible(current, now=NOW)


def test_suspended_and_closed_customer_rules(identity, customer):
    assert not identity.customer_is_session_eligible(changed(customer, state="SUSPENDED"), now=NOW)
    with pytest.raises(ValidationError):
        changed(customer, state="CLOSED")
    revoked = changed(customer.contact_binding, state="REVOKED", revoked_at=VERIFIED)
    closed = changed(customer, state="CLOSED", contact_binding=revoked)
    assert not identity.customer_is_session_eligible(closed, now=NOW)


@pytest.mark.parametrize("purpose", ["SMS_VERIFICATION", "SMS_NOTIFICATION", "SMS_MARKETING"])
def test_consent_is_specific_to_one_purpose(identity, customer, purpose):
    purpose = identity.ConsentPurpose(purpose)
    current = changed(customer, consents=(consent(identity, purpose),))
    for requested in identity.ConsentPurpose:
        assert identity.has_current_consent(current, requested, policy_version="sms-v1", now=NOW) is (
            requested is purpose)
    assert not identity.has_current_consent(current, purpose, policy_version="sms-v2", now=NOW)


@pytest.mark.parametrize("state", [None, "NOT_GRANTED", "WITHDRAWN"])
def test_missing_or_withdrawn_consent_is_denied(identity, customer, state):
    entries = () if state is None else (consent(identity, "SMS_MARKETING", state),)
    current = changed(customer, consents=entries)
    assert not identity.has_current_consent(current, identity.ConsentPurpose.SMS_MARKETING,
                                            policy_version="sms-v1", now=NOW)


def test_verification_never_implies_notification_or_marketing(identity, customer):
    current = changed(customer, consents=(consent(identity, "SMS_VERIFICATION"),))
    for purpose in (identity.ConsentPurpose.SMS_NOTIFICATION, identity.ConsentPurpose.SMS_MARKETING):
        for candidate in (customer, current):
            assert not identity.has_current_consent(candidate, purpose, policy_version="sms-v1", now=NOW)


@pytest.mark.parametrize("field", ["decided_at", "policy_version", "purpose", "state"])
def test_consent_requires_explicit_decision_fields(identity, field):
    payload = consent(identity, "SMS_VERIFICATION").model_dump()
    del payload[field]
    with pytest.raises(ValidationError):
        identity.PurposeSpecificConsent.model_validate(payload)


def test_ambiguous_cross_customer_and_invalid_consent_rejected(identity, customer):
    entry = consent(identity, "SMS_NOTIFICATION")
    for entries in ((entry, entry), (changed(entry, customer_id=OTHER_CUSTOMER_ID),),
                    (changed(entry, decided_at=NOW),)):
        with pytest.raises(ValidationError):
            changed(customer, consents=entries)
    for updates in ({"policy_version": ""}, {"policy_version": "x" * 65},
                    {"purpose": "ALL_SMS"}, {"state": "UNKNOWN"}, {"extra": True}):
        with pytest.raises(ValidationError):
            identity.PurposeSpecificConsent.model_validate({**entry.model_dump(), **updates})


def test_inactive_future_and_malformed_customers_cannot_grant_consent(identity, customer):
    current = changed(customer, consents=(consent(identity, "SMS_MARKETING"),))
    for value in (changed(current, state="SUSPENDED"),
                  changed(current, state="CLOSED", contact_binding=None),
                  changed(current, updated_at=NOW + timedelta(seconds=1)),
                  current.model_copy(update={"id": "bad"}), current.model_dump(), None):
        assert not identity.has_current_consent(value, identity.ConsentPurpose.SMS_MARKETING,
                                                policy_version="sms-v1", now=NOW)
        assert not identity.customer_is_session_eligible(value, now=NOW)


def test_valid_active_session_is_inert_eligibility_only(sessions, customer, record):
    assert sessions.evaluate_session(record, customer, now=NOW) is sessions.SessionPolicyStatus.ELIGIBLE
    assert sessions.CustomerSession.model_validate_json(record.session.model_dump_json()) == record.session
    assert sessions.IDLE_LIFETIME == timedelta(minutes=30)
    assert sessions.ABSOLUTE_LIFETIME == timedelta(hours=24)
    for value in (customer, record, record.session, sessions.safe_session_projection(record, customer, now=NOW)):
        assert not hasattr(value, "authenticated") and not hasattr(value, "inquiry_authorized")


def test_customer_session_and_contact_mismatches_fail_closed(sessions, customer, record):
    mismatched = changed(record, session=changed(record.session, customer_id=OTHER_CUSTOMER_ID))
    assert sessions.evaluate_session(mismatched, customer, now=NOW) is sessions.SessionPolicyStatus.BINDING_MISMATCH
    for current in (
        changed(customer, contact_binding=changed(customer.contact_binding,
            contact_ref=CONTACT_REF.replace("2", "5"))),
        changed(customer, contact_binding=changed(customer.contact_binding,
            verified_at=VERIFIED + timedelta(seconds=1), updated_at=VERIFIED + timedelta(seconds=1))),
    ):
        assert sessions.evaluate_session(record, current, now=NOW) is sessions.SessionPolicyStatus.BINDING_MISMATCH
        assert sessions.safe_session_projection(record, current, now=NOW) is None


@pytest.mark.parametrize("delta,expected", [(-1, "ELIGIBLE"), (0, "EXPIRED"), (1, "EXPIRED")])
def test_idle_expiration_boundary(sessions, customer, record, delta, expected):
    now = record.session.idle_expires_at + timedelta(microseconds=delta)
    assert sessions.evaluate_session(record, customer, now=now).value == expected


@pytest.mark.parametrize("delta,expected", [(-1, "ELIGIBLE"), (0, "EXPIRED"), (1, "EXPIRED")])
def test_absolute_expiration_boundary_with_fresh_activity(sessions, customer, record, delta, expected):
    activity = record.session.absolute_expires_at - timedelta(minutes=1)
    current = changed(record, session=changed(record.session, last_activity_at=activity,
                                              idle_expires_at=activity + sessions.IDLE_LIFETIME))
    now = current.session.absolute_expires_at + timedelta(microseconds=delta)
    assert sessions.evaluate_session(current, customer, now=now).value == expected


def test_revoked_session_rejected_at_revocation(sessions, customer, record):
    current = changed(record, session=changed(record.session, revoked_at=NOW))
    assert sessions.evaluate_session(current, customer, now=NOW) is sessions.SessionPolicyStatus.REVOKED
    assert sessions.safe_session_projection(current, customer, now=NOW) is None
    with pytest.raises(ValueError):
        sessions.with_session_activity(current, customer, now=NOW)


@pytest.mark.parametrize("state", ["SUSPENDED", "CLOSED"])
def test_inactive_customer_has_no_eligible_session(sessions, customer, record, state):
    current = changed(customer, state=state, contact_binding=None if state == "CLOSED" else customer.contact_binding)
    assert sessions.evaluate_session(record, current, now=NOW) is sessions.SessionPolicyStatus.CUSTOMER_INACTIVE
    assert sessions.safe_session_projection(record, current, now=NOW) is None


@pytest.mark.parametrize("state", [None, "UNVERIFIED", "REVERIFICATION_REQUIRED", "REVOKED"])
def test_unverified_or_revoked_contact_rejects_session(sessions, customer, record, state):
    binding = None
    if state:
        updates = {"state": state}
        if state == "UNVERIFIED":
            updates.update(contact_ref=None, verified_at=None)
        if state == "REVOKED":
            updates["revoked_at"] = VERIFIED
        binding = changed(customer.contact_binding, **updates)
    current = changed(customer, contact_binding=binding)
    assert sessions.evaluate_session(record, current, now=NOW) is sessions.SessionPolicyStatus.CONTACT_UNVERIFIED


@pytest.mark.parametrize("stamp", [START.replace(tzinfo=None),
    START.astimezone(timezone(timedelta(hours=9))), "2026-09-01", "0", 0, True, None])
def test_non_utc_and_implicit_timestamps_rejected(identity, sessions, customer, record, stamp):
    with pytest.raises(ValidationError):
        changed(customer, created_at=stamp)
    with pytest.raises(ValidationError):
        changed(record.session, created_at=stamp)
    assert sessions.evaluate_session(record, customer, now=stamp) is sessions.SessionPolicyStatus.INVALID_TIME


@pytest.mark.parametrize("updates", [
    {"last_activity_at": START}, {"last_activity_at": CREATED + timedelta(hours=24)},
    {"idle_expires_at": CREATED}, {"absolute_expires_at": CREATED},
    {"absolute_expires_at": CREATED + timedelta(hours=25)}, {"revoked_at": START},
])
def test_invalid_session_timestamp_relationships(sessions, customer, record, updates):
    with pytest.raises(ValidationError):
        changed(record.session, **updates)
    malformed = record.model_copy(update={"session": record.session.model_copy(update=updates)})
    assert sessions.evaluate_session(malformed, customer, now=NOW) is sessions.SessionPolicyStatus.INVALID_RECORD
    assert sessions.safe_session_projection(malformed, customer, now=NOW) is None


def test_future_records_clock_rollback_and_pre_customer_session_fail_closed(sessions, customer, record):
    assert sessions.evaluate_session(record, customer, now=START) is not sessions.SessionPolicyStatus.ELIGIBLE
    future = changed(record, session=changed(record.session, revoked_at=NOW + timedelta(seconds=1)))
    assert sessions.evaluate_session(future, customer, now=NOW) is sessions.SessionPolicyStatus.INVALID_TIME
    later_customer = changed(customer, created_at=NOW, updated_at=NOW, contact_binding=None)
    assert sessions.evaluate_session(record, later_customer, now=NOW) is sessions.SessionPolicyStatus.INVALID_TIME


@pytest.mark.parametrize("field", ["session_secret_hash", "security_policy_version",
                                    "credential_bound_at", "verified_contact_ref", "contact_verified_at"])
def test_missing_security_metadata_fails_closed(sessions, customer, record, field):
    data = dict(record)
    del data[field]
    with pytest.raises(ValidationError):
        sessions.PrivateSessionRecord.model_validate(data)
    malformed = sessions.PrivateSessionRecord.model_construct(**data)
    assert sessions.evaluate_session(malformed, customer, now=NOW) is sessions.SessionPolicyStatus.INVALID_RECORD
    assert sessions.safe_session_projection(malformed, customer, now=NOW) is None


@pytest.mark.parametrize("updates", [
    {"session_secret_hash": ""}, {"session_secret_hash": "mock-raw-secret"},
    {"session_secret_hash": "sha256:" + "g" * 64}, {"session_secret_hash": None},
    {"security_policy_version": "2.0.0"}, {"credential_bound_at": START},
    {"contact_verified_at": NOW}, {"verified_contact_ref": "bad"},
])
def test_invalid_security_metadata_fails_closed(sessions, customer, record, updates):
    with pytest.raises(ValidationError):
        changed(record, **updates)
    malformed = record.model_copy(update=updates)
    assert sessions.evaluate_session(malformed, customer, now=NOW) is sessions.SessionPolicyStatus.INVALID_RECORD


def test_activity_cannot_extend_absolute_lifetime_or_revive_expired_session(sessions, customer, record):
    current = record
    # Exercise the actual pure update across the full absolute lifetime.
    for offset in range(20, 1440, 20):
        current = sessions.with_session_activity(current, customer, now=CREATED + timedelta(minutes=offset))
        assert current.session.absolute_expires_at == record.session.absolute_expires_at
        assert current.session.created_at == record.session.created_at
        assert current.session.idle_expires_at == current.session.last_activity_at + sessions.IDLE_LIFETIME
    assert record.session.last_activity_at == CREATED
    assert sessions.evaluate_session(current, customer, now=record.session.absolute_expires_at) is sessions.SessionPolicyStatus.EXPIRED
    for source, stamp in ((current, record.session.absolute_expires_at),
                          (record, record.session.idle_expires_at), (current, NOW)):
        with pytest.raises(ValueError):
            sessions.with_session_activity(source, customer, now=stamp)


def test_public_serialization_and_repr_exclude_all_private_metadata(sessions, customer, record):
    projection = sessions.safe_session_projection(record, customer, now=NOW)
    assert isinstance(projection, sessions.SafeSessionProjection)
    public_fields = {"schema_version", "id", "customer_id", "created_at", "last_activity_at",
                     "idle_expires_at", "absolute_expires_at", "revoked_at"}
    private_fields = {"session_secret_hash", "security_policy_version", "credential_bound_at",
                      "verified_contact_ref", "contact_verified_at"}
    assert set(projection.model_dump()) == set(record.session.model_dump()) == public_fields
    assert set(record.model_dump()) == {"schema_version", "session"}
    for value in (projection, record.session, record):
        dumps = (value.model_dump_json(), json.dumps(value.model_dump(mode="json")),
                 value.model_dump_json(serialize_as_any=True), repr(value))
        for text in dumps:
            assert MOCK_HASH not in text and CONTACT_REF not in text
            assert all(field not in text for field in private_fields)
            assert all(field not in text for field in ("raw_session_secret", "phone_number", "otp", "credentials"))
    assert not (set(record.model_json_schema(mode="serialization")["properties"]) & private_fields)
    assert sessions.safe_session_projection(record, customer, now=record.session.idle_expires_at) is None


@pytest.mark.parametrize("field", ["raw_session_secret", "session_secret_hash", "phone_number",
                                    "credentials", "otp", "security_policy_version", "authenticated"])
def test_public_models_reject_private_fields(sessions, record, field):
    for model in (sessions.CustomerSession, sessions.SafeSessionProjection):
        with pytest.raises(ValidationError):
            model.model_validate({**record.session.model_dump(), field: "mock-only"})


def test_contract_versions_identifiers_and_closed_private_schema(sessions, customer, record):
    for model in (customer, customer.contact_binding, record.session, record):
        with pytest.raises(ValidationError):
            changed(model, schema_version="2.0.0")
    for identifier in ("", CUSTOMER_ID, SESSION_ID + "x", 123):
        with pytest.raises(ValidationError):
            changed(record.session, id=identifier)
    with pytest.raises(ValidationError):
        sessions.PrivateSessionRecord.model_validate({**dict(record), "otp": "mock-only"})


def test_malformed_and_public_claims_never_produce_eligible_projection(sessions, customer, record):
    for value in (None, {}, dict(record), record.session,
                  sessions.safe_session_projection(record, customer, now=NOW),
                  record.model_copy(update={"session": None}),
                  sessions.PrivateSessionRecord.model_construct()):
        assert sessions.evaluate_session(value, customer, now=NOW) is sessions.SessionPolicyStatus.INVALID_RECORD
        assert sessions.safe_session_projection(value, customer, now=NOW) is None
    malformed = customer.model_copy(update={"contact_binding": customer.contact_binding.model_copy(
        update={"verified_at": None})})
    assert sessions.evaluate_session(record, malformed, now=NOW) is sessions.SessionPolicyStatus.INVALID_RECORD
    assert sessions.evaluate_session(record, customer.model_dump(), now=NOW) is sessions.SessionPolicyStatus.INVALID_RECORD


def test_inquiry_behavior_unchanged_and_contracts_do_not_authorize_inquiries(
        sessions, customer, record, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from core.api.dependencies.inquiries import get_inquiry_repository
    from core.api.routes.shopping import router
    from core.shopping import inquiries
    from core.shopping.models import Product

    monkeypatch.setattr(inquiries.secrets, "token_urlsafe", lambda count: "mock-existing-inquiry-token")
    repository = inquiries.InMemoryInquiryRepository()
    product = Product(id="mock-product", name="Synthetic", slug="synthetic", description="Mock",
                      price=Decimal("1.00"), currency="KRW", category="Mock", in_stock=True, source="mock")
    created = repository.create(product, None, "Synthetic inquiry")
    assert created.public_access_token == "mock-existing-inquiry-token"
    assert repository.get(created.id).public_access_token is None
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_inquiry_repository] = lambda: repository
    projection = sessions.safe_session_projection(record, customer, now=NOW)
    with TestClient(app) as client:
        path = f"/shopping/inquiries/{created.id}"
        for headers in ({}, {"X-Customer-ID": CUSTOMER_ID, "X-Session-ID": SESSION_ID},
                        {"Authorization": f"Bearer {SESSION_ID}"}):
            assert client.get(path, headers=headers).status_code == 401
        for token in (CUSTOMER_ID, SESSION_ID, MOCK_HASH, projection.model_dump_json(), customer.model_dump_json()):
            response = client.get(path, headers={"X-Inquiry-Access-Token": token})
            assert response.status_code == (401 if len(token) > 256 else 403)
        response = client.get(path, headers={"X-Inquiry-Access-Token": created.public_access_token})
        assert response.status_code == 200
        assert response.json() == {**created.model_dump(), "public_access_token": None}
    assert repository.get(created.id).messages == []
