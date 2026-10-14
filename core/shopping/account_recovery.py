"""AIControlCenter account-recovery workflow core.

The service owns identity matching, challenge/reset lifecycle, throttling, and
redacted audit. WooCommerce, Twilio Verify, and Twilio Messaging are replaceable
ports. Schema provisioning is explicit; constructing the service is inert.
"""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import closing
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import sqlite3
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode


class RecoveryDenied(RuntimeError):
    """Sanitized policy failure."""


@dataclass(frozen=True)
class RecoveryAccount:
    account_ref: str
    login_id: str
    full_name: str
    phone: str

    def __repr__(self) -> str:
        return f"RecoveryAccount(account_ref={self.account_ref!r}, private_fields=<redacted>)"


class RecoveryAccountPort(Protocol):
    def find_by_name_phone(self, name: str, phone: str) -> RecoveryAccount | None: ...
    def find_by_login_name_phone(self, login_id: str, name: str, phone: str) -> RecoveryAccount | None: ...
    def find_by_ref_phone(self, account_ref: str, phone: str) -> RecoveryAccount | None: ...
    def change_password(self, account_ref: str, new_password: str) -> bool: ...


class RecoveryVerifyPort(Protocol):
    def start(self, phone: str, event_id: str) -> str: ...
    def verify(self, phone: str, verification_id: str, code: str) -> bool: ...


class RecoveryMessagePort(Protocol):
    def send(self, phone: str, body: str, event_id: str): ...


def _utc(value: datetime) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("UTC timestamp required")
    return value


def _phone(value: object) -> bool:
    return type(value) is str and len(value) == 13 and value.startswith("+8210") and value[5:].isdigit()


def _safe(value: object, length: int) -> bool:
    return type(value) is str and 1 <= len(value.strip()) <= length and value == value.strip()


class SQLiteRecoveryStore:
    """Explicit, isolated recovery ledger; stores only keyed identity/token digests."""

    def __init__(self, path: str | Path, *, binding_key: bytes) -> None:
        self.path = Path(path)
        if self.path.is_symlink() or type(binding_key) is not bytes or len(binding_key) < 32:
            raise ValueError("RECOVERY_STORAGE_POLICY")
        self._key = binding_key

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS recovery_meta (
                    name TEXT PRIMARY KEY, version TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS recovery_challenges (
                    challenge_hash TEXT PRIMARY KEY,
                    account_ref TEXT,
                    phone_binding TEXT NOT NULL,
                    provider_ref TEXT,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS recovery_tokens (
                    token_hash TEXT PRIMARY KEY,
                    account_ref TEXT NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    provider_ref TEXT,
                    version INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS recovery_limits (
                    bucket_hash TEXT PRIMARY KEY,
                    window_start TEXT NOT NULL,
                    attempts INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS recovery_audit (
                    event_id TEXT PRIMARY KEY,
                    account_ref TEXT,
                    action TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    correlation_id TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );
            """)
            c.execute(
                "INSERT OR IGNORE INTO recovery_meta(name,version) VALUES('schema','account-recovery/v1')"
            )
            row = c.execute("SELECT version FROM recovery_meta WHERE name='schema'").fetchone()
            if row is None or row[0] != "account-recovery/v1":
                raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE")
        try:
            self.path.chmod(0o600)
        except OSError:
            raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE") from None

    def _connect(self) -> sqlite3.Connection:
        if self.path.is_symlink():
            raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE")
        c = sqlite3.connect(str(self.path), timeout=0.75, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA busy_timeout=750")
        return c

    def digest(self, domain: str, value: str) -> str:
        return hmac.new(self._key, (domain + ":" + value).encode("utf-8"), hashlib.sha256).hexdigest()

    def claim_limits(self, *, phone: str, client: str, now: datetime) -> bool:
        now = _utc(now)
        window = now - timedelta(hours=1)
        keys = (
            (self.digest("phone", phone), 3),
            (self.digest("client", client), 10),
        )
        c = self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            for key, maximum in keys:
                row = c.execute("SELECT window_start,attempts FROM recovery_limits WHERE bucket_hash=?", (key,)).fetchone()
                if row is not None and datetime.fromisoformat(row["window_start"]) > window and row["attempts"] >= maximum:
                    c.rollback()
                    return False
            for key, _ in keys:
                row = c.execute("SELECT window_start,attempts FROM recovery_limits WHERE bucket_hash=?", (key,)).fetchone()
                if row is None or datetime.fromisoformat(row["window_start"]) <= window:
                    c.execute("INSERT OR REPLACE INTO recovery_limits VALUES(?,?,1)", (key, now.isoformat()))
                else:
                    c.execute("UPDATE recovery_limits SET attempts=attempts+1 WHERE bucket_hash=?", (key,))
            c.commit()
            return True
        except sqlite3.Error:
            c.rollback()
            raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE") from None
        finally:
            c.close()

    def create_challenge(self, challenge_hash: str, account_ref: str | None, phone_binding: str,
                         now: datetime) -> None:
        c = self._connect()
        try:
            c.execute(
                "INSERT INTO recovery_challenges VALUES(?,?,?,?,?,?,?,0)",
                (challenge_hash, account_ref, phone_binding, None, "START_CLAIMED",
                 now.isoformat(), (now + timedelta(minutes=5)).isoformat()),
            )
        except sqlite3.Error:
            raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE") from None
        finally:
            c.close()

    def challenge_started(self, challenge_hash: str, provider_ref: str | None, lifecycle: str) -> None:
        if lifecycle not in {"PENDING", "FAILED", "UNKNOWN_OUTCOME"}:
            raise RecoveryDenied("RECOVERY_STATE_INVALID")
        with closing(self._connect()) as c:
            c.execute(
                "UPDATE recovery_challenges SET provider_ref=?,lifecycle=?,version=version+1 "
                "WHERE challenge_hash=? AND lifecycle='START_CLAIMED'",
                (provider_ref, lifecycle, challenge_hash),
            )

    def claim_challenge(self, challenge_hash: str, phone_binding: str, now: datetime):
        c = self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute(
                "SELECT * FROM recovery_challenges WHERE challenge_hash=? AND phone_binding=?",
                (challenge_hash, phone_binding),
            ).fetchone()
            if (row is None or row["lifecycle"] != "PENDING"
                    or now.isoformat() >= row["expires_at"]):
                c.rollback()
                return None
            changed = c.execute(
                "UPDATE recovery_challenges SET lifecycle='VERIFY_CLAIMED',version=version+1 "
                "WHERE challenge_hash=? AND lifecycle='PENDING' AND version=?",
                (challenge_hash, row["version"]),
            ).rowcount
            c.commit()
            return dict(row) if changed == 1 else None
        except sqlite3.Error:
            c.rollback()
            raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE") from None
        finally:
            c.close()

    def challenge_state(self, challenge_hash: str, lifecycle: str) -> None:
        with closing(self._connect()) as c:
            c.execute(
                "UPDATE recovery_challenges SET lifecycle=?,version=version+1 "
                "WHERE challenge_hash=? AND lifecycle='VERIFY_CLAIMED'",
                (lifecycle, challenge_hash),
            )

    def create_reset(self, token_hash: str, account_ref: str, event_id: str, now: datetime) -> None:
        with closing(self._connect()) as c:
            c.execute(
                "INSERT INTO recovery_tokens VALUES(?,?,?,?,?,?,NULL,0)",
                (token_hash, account_ref, event_id, "SENDING",
                 now.isoformat(), (now + timedelta(minutes=15)).isoformat()),
            )

    def reset_sent(self, token_hash: str, provider_ref: str | None, lifecycle: str) -> None:
        with closing(self._connect()) as c:
            c.execute(
                "UPDATE recovery_tokens SET provider_ref=?,lifecycle=?,version=version+1 "
                "WHERE token_hash=? AND lifecycle='SENDING'",
                (provider_ref, lifecycle, token_hash),
            )

    def claim_token(self, token_hash: str, now: datetime):
        c = self._connect()
        try:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM recovery_tokens WHERE token_hash=?", (token_hash,)).fetchone()
            if row is None or row["lifecycle"] != "ACCEPTED" or now.isoformat() >= row["expires_at"]:
                c.rollback()
                return None
            changed = c.execute(
                "UPDATE recovery_tokens SET lifecycle='UPDATE_CLAIMED',version=version+1 "
                "WHERE token_hash=? AND lifecycle='ACCEPTED' AND version=?",
                (token_hash, row["version"]),
            ).rowcount
            c.commit()
            return dict(row) if changed == 1 else None
        except sqlite3.Error:
            c.rollback()
            raise RecoveryDenied("RECOVERY_STORAGE_UNAVAILABLE") from None
        finally:
            c.close()

    def token_state(self, token_hash: str, state: str) -> None:
        with closing(self._connect()) as c:
            c.execute(
                "UPDATE recovery_tokens SET lifecycle=?,version=version+1 "
                "WHERE token_hash=? AND lifecycle='UPDATE_CLAIMED'",
                (state, token_hash),
            )

    def audit(self, event_id: str, account_ref: str | None, action: str, outcome: str,
              correlation_id: str, now: datetime) -> None:
        with closing(self._connect()) as c:
            c.execute(
                "INSERT INTO recovery_audit VALUES(?,?,?,?,?,?)",
                (event_id, account_ref, action, outcome, correlation_id, now.isoformat()),
            )


@dataclass(frozen=True)
class RecoveryReply:
    state: str
    challenge: str | None = None
    login_id: str | None = None


class AccountRecoveryService:
    """Fail-closed recovery workflows; provider and account side effects are single-attempt."""

    def __init__(self, *, store: SQLiteRecoveryStore, accounts: RecoveryAccountPort,
                 verifier: RecoveryVerifyPort, messenger: RecoveryMessagePort | None,
                 reset_origin: str, clock, event_factory=None, secret_factory=None) -> None:
        from urllib.parse import urlsplit
        parsed = urlsplit(reset_origin)
        if (parsed.scheme != "https" or parsed.hostname != "dev.bokstory.duckdns.org"
                or parsed.path not in {"", "/"} or parsed.query or parsed.fragment
                or parsed.username or parsed.password or parsed.port not in {None, 443}):
            raise ValueError("RECOVERY_ORIGIN_REQUIRED")
        self.store = store
        self.accounts = accounts
        self.verifier = verifier
        self.messenger = messenger
        self.reset_origin = reset_origin.rstrip("/")
        self.clock = clock
        self.event_factory = event_factory or (lambda: secrets.token_urlsafe(18))
        self.secret_factory = secret_factory or (lambda: secrets.token_urlsafe(32))

    def start_id_lookup(self, name: str, phone: str, client: str) -> RecoveryReply:
        now = _utc(self.clock())
        if not _safe(name, 100) or not _phone(phone) or not _safe(client, 128):
            return RecoveryReply("ACKNOWLEDGED")
        # Keep the public response shape identical for throttled, unknown, and
        # matched identities. Unknown identities never trigger an OTP send.
        handle = secrets.token_urlsafe(32)
        if not self.store.claim_limits(phone=phone, client=client, now=now):
            return RecoveryReply("ACKNOWLEDGED", challenge=handle)
        try:
            account = self.accounts.find_by_name_phone(name, phone)
        except Exception:
            account = None
        challenge_hash = self.store.digest("challenge", handle)
        phone_binding = self.store.digest("phone", phone)
        event_id = self.event_factory()
        try:
            self.store.create_challenge(challenge_hash, account.account_ref if account else None,
                                        phone_binding, now)
        except Exception:
            return RecoveryReply("ACKNOWLEDGED", challenge=handle)
        if account is None:
            self.store.challenge_started(challenge_hash, None, "FAILED")
            self.store.audit(self.event_factory(), None, "ID_CHALLENGE", "ACKNOWLEDGED", event_id, now)
            return RecoveryReply("ACKNOWLEDGED", challenge=handle)
        try:
            provider_ref = self.verifier.start(phone, event_id)
        except Exception:
            self.store.challenge_started(challenge_hash, None, "UNKNOWN_OUTCOME")
            self.store.audit(self.event_factory(), account.account_ref if account else None,
                             "ID_CHALLENGE", "UNKNOWN_OUTCOME", event_id, now)
            return RecoveryReply("ACKNOWLEDGED")
        self.store.challenge_started(challenge_hash, provider_ref, "PENDING")
        self.store.audit(self.event_factory(), account.account_ref if account else None,
                         "ID_CHALLENGE", "ACCEPTED", event_id, now)
        return RecoveryReply("ACKNOWLEDGED", challenge=handle)

    def confirm_id_lookup(self, challenge: str, phone: str, code: str, client: str) -> RecoveryReply:
        now = _utc(self.clock())
        if (not _safe(challenge, 128) or not _phone(phone) or not _safe(client, 128)
                or type(code) is not str or not 4 <= len(code) <= 10 or not code.isdigit()):
            return RecoveryReply("NOT_FOUND")
        challenge_hash = self.store.digest("challenge", challenge)
        row = self.store.claim_challenge(challenge_hash, self.store.digest("phone", phone), now)
        if row is None:
            return RecoveryReply("NOT_FOUND")
        event_id = self.event_factory()
        try:
            verified = self.verifier.verify(phone, row["provider_ref"], code)
        except Exception:
            self.store.challenge_state(challenge_hash, "UNKNOWN_OUTCOME")
            self.store.audit(self.event_factory(), row["account_ref"], "ID_CONFIRM", "UNKNOWN_OUTCOME", event_id, now)
            return RecoveryReply("NOT_FOUND")
        self.store.challenge_state(challenge_hash, "VERIFIED" if verified else "FAILED")
        account = None
        if verified and row["account_ref"]:
            # Re-resolve after the phone proof; never trust a stale account claim.
            try:
                account = self.accounts.find_by_ref_phone(row["account_ref"], phone)
            except Exception:
                account = None
        outcome = "VERIFIED" if account else "NOT_FOUND"
        self.store.audit(self.event_factory(), row["account_ref"] if account else None,
                         "ID_CONFIRM", outcome, event_id, now)
        return RecoveryReply("FOUND", login_id=account.login_id) if account else RecoveryReply("NOT_FOUND")

    def request_password_reset(self, login_id: str, name: str, phone: str, client: str) -> RecoveryReply:
        now = _utc(self.clock())
        generic = RecoveryReply("ACKNOWLEDGED")
        if (not _safe(login_id, 100) or not _safe(name, 100) or not _phone(phone)
                or not _safe(client, 128) or not self.store.claim_limits(phone=phone, client=client, now=now)):
            return generic
        try:
            account = self.accounts.find_by_login_name_phone(login_id, name, phone)
        except Exception:
            account = None
        event_id = self.event_factory()
        if account is None or self.messenger is None:
            self.store.audit(self.event_factory(), account.account_ref if account else None,
                             "PASSWORD_RESET_REQUEST", "ACKNOWLEDGED", event_id, now)
            return generic
        token = self.secret_factory()
        token_hash = self.store.digest("reset", token)
        try:
            self.store.create_reset(token_hash, account.account_ref, event_id, now)
        except Exception:
            return generic
        link = self.reset_origin + "/account-recovery/reset/?" + urlencode({"token": token})
        body = "agachichi 비밀번호 재설정 링크입니다. 15분 이내에 변경해 주세요: " + link
        try:
            receipt = self.messenger.send(phone, body, event_id)
            state = getattr(receipt, "state", "")
            sid = getattr(receipt, "message_sid", None)
            accepted = state in {"QUEUED", "ACCEPTED", "SENDING", "SENT"}
            self.store.reset_sent(token_hash, sid if type(sid) is str else None,
                                  "ACCEPTED" if accepted else "UNKNOWN_OUTCOME")
        except Exception:
            self.store.reset_sent(token_hash, None, "UNKNOWN_OUTCOME")
        self.store.audit(self.event_factory(), account.account_ref, "PASSWORD_RESET_REQUEST",
                         "ACKNOWLEDGED", event_id, now)
        return generic

    def complete_password_reset(self, token: str, new_password: str) -> RecoveryReply:
        now = _utc(self.clock())
        if (not _safe(token, 128) or type(new_password) is not str
                or not 8 <= len(new_password) <= 128 or "\x00" in new_password):
            return RecoveryReply("NOT_COMPLETED")
        token_hash = self.store.digest("reset", token)
        row = self.store.claim_token(token_hash, now)
        if row is None:
            return RecoveryReply("NOT_COMPLETED")
        event_id = self.event_factory()
        try:
            changed = self.accounts.change_password(row["account_ref"], new_password)
        except Exception:
            self.store.token_state(token_hash, "UNKNOWN_UPDATE")
            self.store.audit(self.event_factory(), row["account_ref"], "PASSWORD_RESET", "UNKNOWN_OUTCOME", event_id, now)
            return RecoveryReply("NOT_COMPLETED")
        self.store.token_state(token_hash, "CONSUMED" if changed else "FAILED")
        self.store.audit(self.event_factory(), row["account_ref"], "PASSWORD_RESET",
                         "COMPLETED" if changed else "FAILED", event_id, now)
        return RecoveryReply("COMPLETED" if changed else "NOT_COMPLETED")
