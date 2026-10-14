from datetime import datetime, timezone
import re
import sqlite3

from core.shopping.account_recovery import (
    AccountRecoveryService, RecoveryAccount, RecoveryReply, SQLiteRecoveryStore,
)


NOW = datetime(2026, 10, 14, 3, 0, tzinfo=timezone.utc)
PHONE = "+821012345678"
NAME = "홍길동"
LOGIN = "hong123"
ACCOUNT = RecoveryAccount("woo-customer:42", LOGIN, NAME, PHONE)


class Accounts:
    def __init__(self):
        self.account = ACCOUNT
        self.changed = []

    def find_by_name_phone(self, name, phone):
        return self.account if name == NAME and phone == PHONE else None

    def find_by_login_name_phone(self, login_id, name, phone):
        return self.account if (login_id, name, phone) == (LOGIN, NAME, PHONE) else None

    def find_by_ref_phone(self, account_ref, phone):
        return self.account if (account_ref, phone) == (ACCOUNT.account_ref, PHONE) else None

    def change_password(self, account_ref, new_password):
        self.changed.append((account_ref, new_password))
        return account_ref == ACCOUNT.account_ref


class Verify:
    def __init__(self, fail_start=False, fail_check=False):
        self.calls = []
        self.fail_start = fail_start
        self.fail_check = fail_check

    def start(self, phone, event_id):
        self.calls.append(("start", phone, event_id))
        if self.fail_start:
            raise TimeoutError("private error")
        return "VE-provider-proof-1"

    def verify(self, phone, verification_id, code):
        self.calls.append(("verify", phone, verification_id, code))
        if self.fail_check:
            raise TimeoutError("private error")
        return code == "123456"


class Sms:
    def __init__(self, state="QUEUED", fail=False):
        self.calls = []
        self.state = state
        self.fail = fail

    def send(self, phone, body, event_id):
        self.calls.append((phone, body, event_id))
        if self.fail:
            raise TimeoutError("private error")
        return type("Receipt", (), {"state": self.state, "message_sid": "SM-provider-proof-1"})()


def make_service(tmp_path, *, sms=None, verify=None):
    store = SQLiteRecoveryStore(tmp_path / "account-recovery.sqlite3", binding_key=b"k" * 32)
    service = AccountRecoveryService(
        store=store, accounts=Accounts(), verifier=verify or Verify(), messenger=sms,
        reset_origin="https://dev.bokstory.duckdns.org",
        clock=lambda: NOW,
        event_factory=iter(f"event-{i:04}" for i in range(1000)).__next__,
        secret_factory=lambda: "r" * 43,
    )
    return store, service


def test_service_construction_does_not_create_schema(tmp_path):
    path = tmp_path / "missing.sqlite3"
    SQLiteRecoveryStore(path, binding_key=b"k" * 32)
    assert not path.exists()


def test_id_is_disclosed_only_after_phone_code_and_exact_match(tmp_path):
    store, service = make_service(tmp_path)
    store.initialize()
    started = service.start_id_lookup(NAME, PHONE, "203.0.113.7")
    assert started.state == "ACKNOWLEDGED" and started.login_id is None
    assert started.challenge
    wrong_phone = service.confirm_id_lookup(started.challenge, "+821099999999", "123456", "203.0.113.7")
    assert wrong_phone.state == "NOT_FOUND" and wrong_phone.login_id is None
    confirmed = service.confirm_id_lookup(started.challenge, PHONE, "123456", "203.0.113.7")
    assert confirmed == RecoveryReply("FOUND", login_id=LOGIN)
    replay = service.confirm_id_lookup(started.challenge, PHONE, "123456", "203.0.113.7")
    assert replay.state == "NOT_FOUND"


def test_unknown_identity_has_same_public_ack_and_never_discloses_id(tmp_path):
    store, service = make_service(tmp_path)
    store.initialize()
    started = service.start_id_lookup("없는 이름", PHONE, "203.0.113.7")
    assert started.state == "ACKNOWLEDGED"
    assert not [call for call in service.verifier.calls if call[0] == "start"]
    confirmed = service.confirm_id_lookup(started.challenge, PHONE, "123456", "203.0.113.7")
    assert confirmed == RecoveryReply("NOT_FOUND")


def test_verification_unknown_is_quarantined_without_automatic_retry(tmp_path):
    verify = Verify(fail_check=True)
    store, service = make_service(tmp_path, verify=verify)
    store.initialize()
    challenge = service.start_id_lookup(NAME, PHONE, "203.0.113.7").challenge
    assert service.confirm_id_lookup(challenge, PHONE, "123456", "203.0.113.7").state == "NOT_FOUND"
    assert service.confirm_id_lookup(challenge, PHONE, "123456", "203.0.113.7").state == "NOT_FOUND"
    assert len([c for c in verify.calls if c[0] == "verify"]) == 1
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT lifecycle FROM recovery_challenges").fetchone()[0] == "UNKNOWN_OUTCOME"


def test_password_reset_ack_is_generic_and_token_is_one_time(tmp_path):
    sms = Sms()
    store, service = make_service(tmp_path, sms=sms)
    store.initialize()
    unknown = service.request_password_reset("not-found", NAME, PHONE, "203.0.113.7")
    known = service.request_password_reset(LOGIN, NAME, PHONE, "203.0.113.7")
    assert unknown == known == RecoveryReply("ACKNOWLEDGED")
    assert len(sms.calls) == 1
    assert "https://dev.bokstory.duckdns.org/account-recovery/reset/?token=" in sms.calls[0][1]
    assert service.complete_password_reset("r" * 43, "new-password-123") == RecoveryReply("COMPLETED")
    assert service.complete_password_reset("r" * 43, "another-password-123") == RecoveryReply("NOT_COMPLETED")
    assert len(Accounts().changed) == 0
    with sqlite3.connect(store.path) as c:
        token_hash, lifecycle = c.execute("SELECT token_hash,lifecycle FROM recovery_tokens").fetchone()
        assert "r" * 43 not in token_hash
        assert lifecycle == "CONSUMED"


def test_reset_sms_unknown_does_not_return_token_or_allow_completion(tmp_path):
    sms = Sms(fail=True)
    store, service = make_service(tmp_path, sms=sms)
    store.initialize()
    assert service.request_password_reset(LOGIN, NAME, PHONE, "203.0.113.7").state == "ACKNOWLEDGED"
    assert service.complete_password_reset("r" * 43, "new-password-123") == RecoveryReply("NOT_COMPLETED")
    assert len(sms.calls) == 1
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT lifecycle FROM recovery_tokens").fetchone()[0] == "UNKNOWN_OUTCOME"


def test_ip_and_phone_throttles_are_enforced(tmp_path):
    store, service = make_service(tmp_path)
    store.initialize()
    replies = [service.start_id_lookup(NAME, PHONE, "203.0.113.7") for _ in range(4)]
    assert all(reply.state == "ACKNOWLEDGED" for reply in replies)
    with sqlite3.connect(store.path) as c:
        assert c.execute("SELECT count(*) FROM recovery_challenges").fetchone()[0] == 3
        assert c.execute("SELECT count(*) FROM recovery_limits").fetchone()[0] == 2


def test_audit_and_store_do_not_persist_plain_phone_code_password_or_token(tmp_path):
    sms = Sms()
    store, service = make_service(tmp_path, sms=sms)
    store.initialize()
    started = service.start_id_lookup(NAME, PHONE, "203.0.113.7")
    service.confirm_id_lookup(started.challenge, PHONE, "123456", "203.0.113.7")
    service.request_password_reset(LOGIN, NAME, PHONE, "203.0.113.7")
    service.complete_password_reset("r" * 43, "private-password-123")
    with sqlite3.connect(store.path) as c:
        serialized = " ".join(str(value) for table in (
            "recovery_challenges", "recovery_tokens", "recovery_limits", "recovery_audit"
        ) for row in c.execute(f"SELECT * FROM {table}") for value in row)
    for private in (PHONE, "123456", "private-password-123", "r" * 43):
        assert private not in serialized


def test_reset_origin_is_fixed_to_dev_host(tmp_path):
    store = SQLiteRecoveryStore(tmp_path / "a.sqlite3", binding_key=b"k" * 32)
    for origin in ("https://evil.example", "http://dev.bokstory.duckdns.org", "https://dev.bokstory.duckdns.org/path"):
        try:
            AccountRecoveryService(store=store, accounts=Accounts(), verifier=Verify(),
                messenger=None, reset_origin=origin, clock=lambda: NOW)
        except ValueError:
            pass
        else:
            raise AssertionError("unapproved recovery origin accepted")
