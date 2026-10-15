import sqlite3

import pytest
from fastapi.testclient import TestClient

from core.shopping.signup_dev_app import DEV_ORIGIN, create_signup_dev_app
from core.shopping.signup_email_and_claim import SignupEmailVerificationService, TwoContactSignupClaimService
from core.shopping.signup_registration_operation import SignupRegistrationOperationService
from core.shopping.signup_verification import SignupPhoneVerificationService, SQLiteSignupVerificationStore
from tests.test_shop_signup_email_and_claim import Clock, NOW


class DevFakePhone:
    environment = "DEV"
    is_test_double = True

    def __init__(self):
        self.rows = {}
        self.starts = []

    def start_sms(self, phone, challenge):
        ref = "devphone-" + challenge
        self.rows[ref] = (phone, "0427")
        self.starts.append((phone, challenge))
        return ref

    def verify_sms(self, phone, provider_ref, code):
        return self.rows.get(provider_ref) == (phone, code)


class DevFakeEmail:
    environment = "DEV"
    is_test_double = True

    def __init__(self):
        self.rows = {}

    def start_email(self, email, challenge):
        ref = "devemail-" + challenge
        self.rows[ref] = (email, "735194")
        return ref

    def verify_email(self, email, provider_ref, code):
        return self.rows.get(provider_ref) == (email, code)


class DevFakeCustomers:
    environment = "DEV"
    is_test_double = True

    def __init__(self):
        self.identities = set()
        self.created = {}

    def username_exists(self, login_id):
        return any(x[0] == login_id for x in self.identities)

    def email_exists(self, email):
        return any(x[1] == email for x in self.identities)

    def phone_exists(self, phone):
        return any(x[2] == phone for x in self.identities)

    def create_customer(self, candidate, claim_ref):
        ref = "synthetic-customer-0001"
        self.created[claim_ref] = (ref, candidate.email, candidate.phone, candidate.login_id, "customer")
        self.identities.add((candidate.login_id, candidate.email, candidate.phone))
        return ref

    def customer_matches(self, provider_ref, candidate):
        return any(row == (provider_ref, candidate.email, candidate.phone,
                           candidate.login_id, "customer") for row in self.created.values())

    def find_by_claim(self, claim_ref):
        row = self.created.get(claim_ref)
        return ("FOUND", row[0]) if row else ("ABSENT", None)


def make_app(tmp_path, *, environment="DEV", enabled=True, outside_root=False,
             provider_marker=True):
    root = tmp_path / "signup-dev-data"
    root.mkdir(parents=True)
    dbpath = (tmp_path / "outside.sqlite3") if outside_root else root / "signup.sqlite3"
    store = SQLiteSignupVerificationStore(dbpath, binding_key=b"d" * 32)
    phone_provider, email_provider, customer_port = DevFakePhone(), DevFakeEmail(), DevFakeCustomers()
    if not provider_marker:
        phone_provider.is_test_double = False
    clock = Clock()
    phone = SignupPhoneVerificationService(store=store, provider=phone_provider, clock=clock)
    email = SignupEmailVerificationService(store=store, provider=email_provider, clock=clock)
    claims = TwoContactSignupClaimService(store=store, clock=clock)
    operation = SignupRegistrationOperationService(store=store, port=customer_port, clock=clock)
    app = create_signup_dev_app(
        environment=environment, enable_dev_signup=enabled, dev_data_root=root,
        store=store, phone_service=phone, email_service=email,
        claim_service=claims, operation_service=operation,
    )
    return app, store, phone_provider, email_provider, customer_port


def test_dev_only_opt_in_path_and_test_double_guards_are_fail_closed(tmp_path):
    root = tmp_path / "signup-dev-data"
    root.mkdir()
    store = SQLiteSignupVerificationStore(root / "not-created.sqlite3", binding_key=b"d" * 32)
    phone_provider, email_provider, port = DevFakePhone(), DevFakeEmail(), DevFakeCustomers()
    clock = Clock()
    phone = SignupPhoneVerificationService(store=store, provider=phone_provider, clock=clock)
    email = SignupEmailVerificationService(store=store, provider=email_provider, clock=clock)
    claims = TwoContactSignupClaimService(store=store, clock=clock)
    operation = SignupRegistrationOperationService(store=store, port=port, clock=clock)
    params = dict(enable_dev_signup=True, dev_data_root=root, store=store, phone_service=phone,
                  email_service=email, claim_service=claims, operation_service=operation)
    with pytest.raises(ValueError, match="DEV_SIGNUP_EXPLICIT_OPT_IN_REQUIRED"):
        create_signup_dev_app(environment="PROD", **params)
    with pytest.raises(ValueError, match="DEV_SIGNUP_EXPLICIT_OPT_IN_REQUIRED"):
        create_signup_dev_app(environment="DEV", enable_dev_signup=False, dev_data_root=root,
                              store=store, phone_service=phone, email_service=email,
                              claim_service=claims, operation_service=operation)
    with pytest.raises(ValueError, match="DEV_SIGNUP_DATABASE_OUTSIDE_ROOT"):
        make_app(tmp_path / "outside", outside_root=True)
    with pytest.raises(ValueError, match="DEV_SIGNUP_TEST_PROVIDERS_REQUIRED"):
        make_app(tmp_path / "unmarked", provider_marker=False)
    assert not store.path.exists()


def test_synthetic_api_end_to_end_is_session_bound_no_store_and_durable_only(tmp_path):
    app, store, phone_provider, email_provider, customers = make_app(tmp_path)
    headers = {"Origin": DEV_ORIGIN}
    with TestClient(app, base_url=DEV_ORIGIN) as client:
        session = client.get("/v1/shop/signup/session", headers=headers)
        assert session.json() == {"state": "READY"}
        cookie = session.cookies.get("aicc_signup_dev_session")
        assert cookie and len(cookie) >= 32
        assert session.headers["cache-control"].startswith("no-store")
        assert "httponly" in session.headers["set-cookie"].lower()
        assert "secure" in session.headers["set-cookie"].lower()

        phone_start = client.post("/v1/shop/signup/phone-challenge", headers=headers,
                                  json={"phone": "+821012345678"})
        assert phone_start.json()["state"] == "PENDING"
        phone_verify = client.post("/v1/shop/signup/phone-confirm", headers=headers,
                                   json={"challenge": phone_start.json()["challenge"],
                                         "phone": "+821012345678", "code": "0427"})
        assert phone_verify.json()["state"] == "PHONE_VERIFIED"

        email_start = client.post("/v1/shop/signup/email-challenge", headers=headers,
                                  json={"email": "customer@example.test"})
        assert email_start.json()["state"] == "PENDING"
        email_verify = client.post("/v1/shop/signup/email-confirm", headers=headers,
                                   json={"challenge": email_start.json()["challenge"],
                                         "email": "customer@example.test", "code": "735194"})
        assert email_verify.json()["state"] == "EMAIL_VERIFIED"

        completed = client.post("/v1/shop/signup/complete", headers=headers, json={
            "login_id": "customer_1",
            "email": "customer@example.test",
            "password": "S3cure-pass-123",
            "password_confirmation": "S3cure-pass-123",
            "phone": "+821012345678",
            "terms_accepted": True,
            "terms_version": "terms-dev-001",
            "privacy_notice_version": "privacy-dev-001",
            "phone_ticket": phone_verify.json()["ticket"],
            "email_ticket": email_verify.json()["ticket"],
            "idempotency_key": "signup-dev-operation-0001",
        })
        assert completed.json() == {"state": "ACTIVE"}
        assert len(customers.created) == 1
        assert phone_provider.starts and email_provider.rows

    with sqlite3.connect(store.path) as db:
        tables = ("signup_phone_challenges", "signup_phone_tickets",
                  "signup_email_challenges", "signup_email_tickets",
                  "signup_registration_claims", "signup_registration_operations")
        persisted = " ".join(str(v) for table in tables
                             for row in db.execute(f"SELECT * FROM {table}") for v in row)
    for sensitive in ("+821012345678", "customer@example.test", "0427", "735194",
                      "S3cure-pass-123", "customer_1"):
        assert sensitive not in persisted


def test_wrong_origin_host_or_remote_peer_is_blocked(tmp_path):
    app, *_ = make_app(tmp_path)
    with TestClient(app, base_url=DEV_ORIGIN) as client:
        wrong_origin = client.get("/v1/shop/signup/session", headers={"Origin": "https://agachichi.duckdns.org"})
        assert wrong_origin.status_code == 403
        assert wrong_origin.json() == {"state": "NOT_COMPLETED"}
    with TestClient(app, base_url="https://agachichi.duckdns.org") as client:
        response = client.get("/v1/shop/signup/session", headers={"Origin": DEV_ORIGIN})
        assert response.status_code == 403
    with TestClient(app, base_url=DEV_ORIGIN, client=("127.0.0.1", 55123)) as client:
        response = client.get("/v1/shop/signup/session", headers={"Origin": DEV_ORIGIN})
        assert response.status_code == 403


def test_terms_acceptance_rejects_coerced_boolean_values(tmp_path):
    app, *_ = make_app(tmp_path)
    payload = {
        "login_id": "customer_1",
        "email": "customer@example.test",
        "password": "S3cure-pass-123",
        "password_confirmation": "S3cure-pass-123",
        "phone": "+821012345678",
        "terms_accepted": 1,
        "terms_version": "terms-dev-001",
        "privacy_notice_version": "privacy-dev-001",
        "phone_ticket": "phone-ticket",
        "email_ticket": "email-ticket",
        "idempotency_key": "signup-dev-strict-boolean-0001",
    }
    with TestClient(app, base_url=DEV_ORIGIN) as client:
        response = client.post("/v1/shop/signup/complete",
                               headers={"Origin": DEV_ORIGIN}, json=payload)
    assert response.status_code == 422
    assert response.json()["state"] == "NOT_COMPLETED"
