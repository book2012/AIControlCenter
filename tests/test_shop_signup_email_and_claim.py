from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import sqlite3

import pytest

from core.shopping.account_registration import SignupCandidate
from core.shopping.signup_email_and_claim import (
    EMAIL_CHALLENGE_TTL,
    SignupEmailVerificationService,
    TwoContactSignupClaimService,
)
from core.shopping.signup_verification import SignupPhoneVerificationService, SQLiteSignupVerificationStore
from tests.test_shop_signup_verification import Clock, FakeVerificationProvider, NOW, PHONE, SESSION, CLIENT


EMAIL = "customer@example.test"


class FakeEmailProvider:
    """No-network test provider."""

    def __init__(self, *, fail_start=False, fail_verify=False):
        self.fail_start, self.fail_verify = fail_start, fail_verify
        self.starts, self.verifications = [], []

    def start_email(self, email, challenge_ref):
        self.starts.append((email, challenge_ref))
        if self.fail_start:
            raise TimeoutError("private")
        return "email-" + challenge_ref

    def verify_email(self, email, provider_ref, code):
        self.verifications.append((email, provider_ref, code))
        if self.fail_verify:
            raise TimeoutError("private")
        return email == EMAIL and provider_ref.startswith("email-") and code == "735194"


def setup(tmp_path, *, phone_provider=None, email_provider=None, clock=None):
    clock = clock or Clock()
    store = SQLiteSignupVerificationStore(tmp_path / "signup.sqlite3", binding_key=b"q" * 32)
    phone_provider = phone_provider or FakeVerificationProvider()
    email_provider = email_provider or FakeEmailProvider()
    # Email initialize installs both email and combined-claim tables.
    email_refs = iter(f"emailchallenge-{i:03}" for i in range(100))
    email_tickets = iter(f"emailticket-{i:03}" for i in range(100))
    email = SignupEmailVerificationService(
        store=store, provider=email_provider, clock=clock,
        ref_factory=lambda: next(email_refs), ticket_factory=lambda: next(email_tickets),
    )
    email.initialize()
    phone_refs = iter(f"phonechallenge-{i:03}" for i in range(100))
    phone_tickets = iter(f"phoneticket-{i:03}" for i in range(100))
    phone = SignupPhoneVerificationService(
        store=store, provider=phone_provider, clock=clock,
        ref_factory=lambda: next(phone_refs), ticket_factory=lambda: next(phone_tickets),
    )
    claims = TwoContactSignupClaimService(store=store, clock=clock)
    return store, clock, phone_provider, email_provider, phone, email, claims


def verified_contact_pair(phone, email, *, email_address=EMAIL):
    p = phone.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    assert p.state == "PENDING"
    e = email.start_email(email_address, session_ref=SESSION, client_ref=CLIENT)
    assert e.state == "PENDING"
    pt = phone.confirm_phone(p.challenge, PHONE, "0427", session_ref=SESSION)
    et = email.confirm_email(e.challenge, email_address, "735194", session_ref=SESSION)
    assert pt.state == "PHONE_VERIFIED"
    assert et.state == "EMAIL_VERIFIED"
    return pt.ticket, et.ticket


def candidate(**overrides):
    data = dict(
        login_id="customer_1", email=EMAIL, password="S3cure-pass-123",
        password_confirmation="S3cure-pass-123", full_name="Kim Customer",
        phone=PHONE, terms_accepted=True, privacy_accepted=True,
        terms_version="terms-2026-10",
    )
    data.update(overrides)
    return SignupCandidate(**data)


def test_email_challenge_and_ticket_are_bound_expiring_and_single_use(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    started = email.start_email(EMAIL.upper(), session_ref=SESSION, client_ref=CLIENT)
    assert started.state == "PENDING"
    assert email.confirm_email(started.challenge, EMAIL, "735194", session_ref="other-session-00001").state == "NOT_VERIFIED"
    assert ep.verifications == []
    assert email.confirm_email(started.challenge, EMAIL, "000000", session_ref=SESSION).state == "NOT_VERIFIED"
    verified = email.confirm_email(started.challenge, EMAIL, "735194", session_ref=SESSION)
    assert verified.state == "EMAIL_VERIFIED"
    assert email.confirm_email(started.challenge, EMAIL, "735194", session_ref=SESSION).state == "NOT_VERIFIED"
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT lifecycle FROM signup_email_tickets").fetchone()[0] == "ISSUED"


def test_email_expiry_attempt_limit_and_unknown_outcome_no_retry(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    started = email.start_email(EMAIL, session_ref=SESSION, client_ref=CLIENT)
    clock.advance(EMAIL_CHALLENGE_TTL)
    assert email.confirm_email(started.challenge, EMAIL, "735194", session_ref=SESSION).state == "NOT_VERIFIED"
    assert ep.verifications == []

    store2, clock2, pp2, ep2, phone2, email2, claims2 = setup(
        tmp_path / "sub", email_provider=FakeEmailProvider(fail_verify=True),
    )
    started2 = email2.start_email(EMAIL, session_ref=SESSION, client_ref=CLIENT)
    assert email2.confirm_email(started2.challenge, EMAIL, "735194", session_ref=SESSION).state == "UNKNOWN_OUTCOME"
    assert email2.confirm_email(started2.challenge, EMAIL, "735194", session_ref=SESSION).state == "NOT_VERIFIED"
    assert len(ep2.verifications) == 1


def test_email_start_unknown_outcome_is_not_resent_and_email_rate_limited(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(
        tmp_path, email_provider=FakeEmailProvider(fail_start=True),
    )
    assert email.start_email(EMAIL, session_ref=SESSION, client_ref=CLIENT).state == "UNKNOWN_OUTCOME"
    assert email.start_email(EMAIL, session_ref=SESSION, client_ref=CLIENT).state == "RATE_LIMITED"
    assert len(ep.starts) == 1


def test_two_contact_claim_requires_valid_input_and_matching_bound_tickets(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    pt, et = verified_contact_pair(phone, email)
    missing_consent = candidate(privacy_accepted=False)
    assert claims.claim(phone_ticket=pt, email_ticket=et, session_ref=SESSION,
                        idempotency_key="signup-request-0001", candidate=missing_consent).state == "NOT_AUTHORIZED"
    wrong_identity = candidate(email="other@example.test")
    assert claims.claim(phone_ticket=pt, email_ticket=et, session_ref=SESSION,
                        idempotency_key="signup-request-0001", candidate=wrong_identity).state == "NOT_AUTHORIZED"
    wrong_session = claims.claim(phone_ticket=pt, email_ticket=et, session_ref="other-session-00001",
                                 idempotency_key="signup-request-0001", candidate=candidate())
    assert wrong_session.state == "NOT_AUTHORIZED"
    claimed = claims.claim(phone_ticket=pt, email_ticket=et, session_ref=SESSION,
                           idempotency_key="signup-request-0001", candidate=candidate())
    assert claimed.state == "CLAIMED" and claimed.claim_ref


def test_claim_is_atomic_one_use_and_idempotent_without_saving_profile_or_password(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    pt, et = verified_contact_pair(phone, email)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            lambda _: claims.claim(phone_ticket=pt, email_ticket=et, session_ref=SESSION,
                                   idempotency_key="signup-request-unique", candidate=candidate()).state,
            range(2),
        ))
    assert sorted(results) == ["ALREADY_CLAIMED", "CLAIMED"]
    with sqlite3.connect(store.path) as db:
        data = " ".join(str(v) for table in (
            "signup_phone_tickets", "signup_email_tickets", "signup_registration_claims"
        ) for row in db.execute(f"SELECT * FROM {table}") for v in row)
    for secret in (EMAIL, PHONE, "S3cure-pass-123", "Kim Customer", "customer_1"):
        assert secret not in data
    assert "terms-2026-10" not in data


def test_email_ticket_expiry_blocks_combined_claim(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    pt, et = verified_contact_pair(phone, email)
    clock.advance(timedelta(minutes=5))
    assert claims.claim(phone_ticket=pt, email_ticket=et, session_ref=SESSION,
                        idempotency_key="signup-request-expiry", candidate=candidate()).state == "NOT_AUTHORIZED"



def test_phone_and_email_starts_share_client_hourly_budget(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    for n in range(5):
        result = phone.start_phone(f"+8210{n:08d}", session_ref=SESSION, client_ref=CLIENT)
        assert result.state == "PENDING"
        clock.advance(timedelta(seconds=60))
    for n in range(5):
        result = email.start_email(f"user{n}@example.test", session_ref=SESSION, client_ref=CLIENT)
        assert result.state == "PENDING"
        clock.advance(timedelta(seconds=60))
    assert email.start_email("last@example.test", session_ref=SESSION, client_ref=CLIENT).state == "RATE_LIMITED"
    assert len(pp.starts) == len(ep.starts) == 5


def test_email_wrong_codes_stop_after_five_provider_checks(tmp_path):
    store, clock, pp, ep, phone, email, claims = setup(tmp_path)
    started = email.start_email(EMAIL, session_ref=SESSION, client_ref=CLIENT)
    for _ in range(5):
        assert email.confirm_email(started.challenge, EMAIL, "000000", session_ref=SESSION).state == "NOT_VERIFIED"
    assert len(ep.verifications) == 5
    assert email.confirm_email(started.challenge, EMAIL, "735194", session_ref=SESSION).state == "NOT_VERIFIED"
    assert len(ep.verifications) == 5
