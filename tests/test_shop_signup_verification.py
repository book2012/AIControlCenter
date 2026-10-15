from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from core.shopping.signup_verification import (
    CODE_ATTEMPT_LIMIT,
    CLIENT_START_LIMIT,
    PHONE_START_LIMIT,
    RESEND_COOLDOWN,
    SignupPhoneVerificationService,
    SQLiteSignupVerificationStore,
)


NOW = datetime(2026, 10, 16, 0, 0, tzinfo=timezone.utc)
PHONE = "+821012345678"
SESSION = "session-binding-000001"
CLIENT = "203.0.113.24"


class FakeVerificationProvider:
    """In-memory fake. Never performs network I/O or sends SMS."""

    def __init__(self, *, code="0427", fail_start=False, fail_verify=False):
        self.code = code
        self.fail_start = fail_start
        self.fail_verify = fail_verify
        self.starts = []
        self.verifications = []

    def start_sms(self, phone, challenge_ref):
        self.starts.append((phone, challenge_ref))
        if self.fail_start:
            raise TimeoutError("private test failure")
        return "fake-" + challenge_ref

    def verify_sms(self, phone, provider_ref, code):
        self.verifications.append((phone, provider_ref, code))
        if self.fail_verify:
            raise TimeoutError("private test failure")
        return phone == PHONE and provider_ref.startswith("fake-") and code == self.code


class Clock:
    def __init__(self):
        self.value = NOW

    def __call__(self):
        return self.value

    def advance(self, delta):
        self.value += delta


def make_service(tmp_path, *, provider=None, clock=None):
    store = SQLiteSignupVerificationStore(
        tmp_path / "signup-verification.sqlite3", binding_key=b"z" * 32,
    )
    provider = provider or FakeVerificationProvider()
    clock = clock or Clock()
    service = SignupPhoneVerificationService(
        store=store, provider=provider, clock=clock,
        ref_factory=iter(f"challenge-{n:03}" for n in range(2000)).__next__,
        ticket_factory=iter(f"ticket-{n:03}" for n in range(2000)).__next__,
    )
    return store, provider, clock, service


def test_construction_does_not_create_database_or_contact_provider(tmp_path):
    path = tmp_path / "not-created.sqlite3"
    store = SQLiteSignupVerificationStore(path, binding_key=b"k" * 32)
    provider = FakeVerificationProvider()
    SignupPhoneVerificationService(store=store, provider=provider)
    assert not path.exists()
    assert provider.starts == [] and provider.verifications == []


def test_phone_challenge_and_ticket_are_bound_expiring_and_single_use(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()

    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    assert started.state == "PENDING"
    assert started.challenge and len(provider.starts) == 1

    wrong_session = service.confirm_phone(
        started.challenge, PHONE, "0427", session_ref="other-session-000001",
    )
    assert wrong_session.state == "NOT_VERIFIED"
    assert provider.verifications == []

    wrong_phone = service.confirm_phone(
        started.challenge, "+821099999999", "0427", session_ref=SESSION,
    )
    assert wrong_phone.state == "NOT_VERIFIED"
    assert provider.verifications == []

    bad_code = service.confirm_phone(
        started.challenge, PHONE, "9999", session_ref=SESSION,
    )
    assert bad_code.state == "NOT_VERIFIED" and bad_code.ticket is None

    verified = service.confirm_phone(
        started.challenge, PHONE, "0427", session_ref=SESSION,
    )
    assert verified.state == "PHONE_VERIFIED"
    assert verified.ticket

    assert not service.consume_phone_ticket(
        verified.ticket, PHONE, session_ref="other-session-000001",
    )
    assert not service.consume_phone_ticket(
        verified.ticket, "+821099999999", session_ref=SESSION,
    )
    assert service.consume_phone_ticket(verified.ticket, PHONE, session_ref=SESSION)
    assert not service.consume_phone_ticket(verified.ticket, PHONE, session_ref=SESSION)


def test_challenge_expiry_blocks_provider_verification(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    clock.advance(timedelta(minutes=5))
    result = service.confirm_phone(started.challenge, PHONE, "0427", session_ref=SESSION)
    assert result.state == "NOT_VERIFIED"
    assert provider.verifications == []


def test_ticket_expiry_and_replay_are_rejected(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    verified = service.confirm_phone(started.challenge, PHONE, "0427", session_ref=SESSION)
    clock.advance(timedelta(minutes=5))
    assert not service.consume_phone_ticket(verified.ticket, PHONE, session_ref=SESSION)


def test_resend_cooldown_then_phone_daily_limit(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    first = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    assert first.state == "PENDING"
    assert service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT).state == "RATE_LIMITED"
    assert len(provider.starts) == 1

    for _ in range(PHONE_START_LIMIT - 1):
        clock.advance(RESEND_COOLDOWN)
        assert service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT).state == "PENDING"
    clock.advance(RESEND_COOLDOWN)
    assert service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT).state == "RATE_LIMITED"
    assert len(provider.starts) == PHONE_START_LIMIT


def test_client_hourly_limit_is_enforced_with_distinct_phones(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    for n in range(CLIENT_START_LIMIT):
        phone = f"+8210{n:08d}"
        result = service.start_phone(phone, session_ref=SESSION, client_ref=CLIENT)
        assert result.state == "PENDING"
        clock.advance(RESEND_COOLDOWN)
    limited = service.start_phone("+821099999999", session_ref=SESSION, client_ref=CLIENT)
    assert limited.state == "RATE_LIMITED"
    assert len(provider.starts) == CLIENT_START_LIMIT


def test_wrong_codes_are_limited_to_five_provider_checks(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    for _ in range(CODE_ATTEMPT_LIMIT):
        result = service.confirm_phone(
            started.challenge, PHONE, "9999", session_ref=SESSION,
        )
        assert result.state == "NOT_VERIFIED"
    assert len(provider.verifications) == CODE_ATTEMPT_LIMIT
    assert service.confirm_phone(
        started.challenge, PHONE, "0427", session_ref=SESSION,
    ).state == "NOT_VERIFIED"
    assert len(provider.verifications) == CODE_ATTEMPT_LIMIT


def test_unknown_provider_outcome_is_quarantined_without_retry(tmp_path):
    store, provider, clock, service = make_service(
        tmp_path, provider=FakeVerificationProvider(fail_verify=True),
    )
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    assert service.confirm_phone(
        started.challenge, PHONE, "0427", session_ref=SESSION,
    ).state == "UNKNOWN_OUTCOME"
    assert service.confirm_phone(
        started.challenge, PHONE, "0427", session_ref=SESSION,
    ).state == "NOT_VERIFIED"
    assert len(provider.verifications) == 1


def test_unknown_start_is_not_resent_automatically(tmp_path):
    store, provider, clock, service = make_service(
        tmp_path, provider=FakeVerificationProvider(fail_start=True),
    )
    store.initialize()
    assert service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT).state == "UNKNOWN_OUTCOME"
    assert service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT).state == "RATE_LIMITED"
    assert len(provider.starts) == 1


def test_persisted_store_contains_no_phone_session_ip_or_otp(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    verified = service.confirm_phone(started.challenge, PHONE, "0427", session_ref=SESSION)
    with sqlite3.connect(store.path) as connection:
        serialized = " ".join(
            str(value)
            for table in ("signup_phone_challenges", "signup_phone_tickets")
            for row in connection.execute(f"SELECT * FROM {table}")
            for value in row
        )
    for secret in (PHONE, SESSION, CLIENT, "0427", verified.ticket):
        assert secret not in serialized


def test_ticket_consumption_is_atomic_under_concurrency(tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    verified = service.confirm_phone(started.challenge, PHONE, "0427", session_ref=SESSION)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            lambda _: service.consume_phone_ticket(
                verified.ticket, PHONE, session_ref=SESSION,
            ),
            range(2),
        ))
    assert sorted(results) == [False, True]


@pytest.mark.parametrize("code", ["427", "12345", "12a4", "", None, 1234])
def test_only_four_ascii_digit_codes_reach_provider(code, tmp_path):
    store, provider, clock, service = make_service(tmp_path)
    store.initialize()
    started = service.start_phone(PHONE, session_ref=SESSION, client_ref=CLIENT)
    assert service.confirm_phone(
        started.challenge, PHONE, code, session_ref=SESSION,
    ).state == "NOT_VERIFIED"
    assert provider.verifications == []
