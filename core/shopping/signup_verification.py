"""Provider-neutral, customer-signup phone verification core.

The provider is injected and construction is inert. This module is not mounted
in an API/runtime. It stores keyed digests and provider references only; OTPs
and raw contact/session/client values are never persisted.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from pathlib import Path
import re
import secrets
import sqlite3
from typing import Protocol


CHALLENGE_TTL = timedelta(minutes=5)
TICKET_TTL = timedelta(minutes=5)
RESEND_COOLDOWN = timedelta(seconds=60)
PHONE_START_LIMIT = 5
PHONE_START_WINDOW = timedelta(hours=24)
CLIENT_START_LIMIT = 10
CLIENT_START_WINDOW = timedelta(hours=1)
CODE_ATTEMPT_LIMIT = 5

_PHONE = re.compile(r"\+8210[0-9]{8}\Z", re.ASCII)
_CODE = re.compile(r"[0-9]{4}\Z", re.ASCII)
_REF = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)


class SignupVerificationError(RuntimeError):
    """Sanitized signup-verification failure."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"SignupVerificationError(code={self.code!r})"


class SignupVerificationPort(Protocol):
    def start_sms(self, phone: str, challenge_ref: str) -> str: ...
    def verify_sms(self, phone: str, provider_ref: str, code: str) -> bool: ...


@dataclass(frozen=True)
class PhoneChallengeReply:
    state: str
    challenge: str | None = field(default=None, repr=False)
    ticket: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"PhoneChallengeReply(state={self.state!r}, secrets=<redacted>)"


def _utc(value: datetime) -> datetime:
    if (type(value) is not datetime or value.tzinfo is None
            or value.utcoffset() != timedelta(0)):
        raise ValueError("UTC timestamp required")
    return value


def _valid_binding(value: object) -> bool:
    return (
        type(value) is str and 16 <= len(value) <= 256
        and value == value.strip() and all(32 < ord(char) < 127 for char in value)
    )


def _valid_client(value: object) -> bool:
    # The caller supplies a trusted client reference (often a normalized IP),
    # which can be shorter than a random session-binding token.
    return (
        type(value) is str and 3 <= len(value) <= 128
        and value == value.strip() and all(32 < ord(char) < 127 for char in value)
    )


class SQLiteSignupVerificationStore:
    """Explicit signup-only ledger storing keyed bindings and one-time states."""

    def __init__(self, path: str | Path, *, binding_key: bytes) -> None:
        self.path = Path(path)
        if (self.path.is_symlink() or type(binding_key) is not bytes
                or len(binding_key) < 32):
            raise ValueError("SIGNUP_STORAGE_POLICY")
        self._key = binding_key

    def initialize(self) -> None:
        if self.path.is_symlink():
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS signup_phone_challenges (
                    challenge_hash TEXT PRIMARY KEY,
                    phone_binding TEXT NOT NULL,
                    session_binding TEXT NOT NULL,
                    client_binding TEXT NOT NULL,
                    provider_ref TEXT,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    version INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS signup_phone_challenges_phone_created
                    ON signup_phone_challenges(phone_binding, created_at);
                CREATE INDEX IF NOT EXISTS signup_phone_challenges_client_created
                    ON signup_phone_challenges(client_binding, created_at);
                CREATE TABLE IF NOT EXISTS signup_phone_tickets (
                    ticket_hash TEXT PRIMARY KEY,
                    phone_binding TEXT NOT NULL,
                    session_binding TEXT NOT NULL,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0
                );
            """)
        try:
            self.path.chmod(0o600)
        except OSError:
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None

    def _connect(self) -> sqlite3.Connection:
        if self.path.is_symlink():
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE")
        connection = sqlite3.connect(str(self.path), timeout=0.75, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=750")
        return connection

    def digest(self, domain: str, value: str) -> str:
        return hmac.new(
            self._key, (domain + ":" + value).encode("utf-8"), hashlib.sha256,
        ).hexdigest()

    def claim_start(
        self, *, challenge_ref: str, phone: str, session: str, client: str,
        now: datetime,
    ) -> bool:
        now = _utc(now)
        challenge_hash = self.digest("challenge", challenge_ref)
        phone_binding = self.digest("phone", phone)
        session_binding = self.digest("session", session)
        client_binding = self.digest("client", client)
        phone_since = (now - PHONE_START_WINDOW).isoformat()
        client_since = (now - CLIENT_START_WINDOW).isoformat()
        cooldown_since = (now - RESEND_COOLDOWN).isoformat()
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            # Keep rate-limit evidence for at most its longest active window.
            connection.execute(
                "DELETE FROM signup_phone_challenges WHERE created_at<=?",
                (phone_since,),
            )
            connection.execute(
                "DELETE FROM signup_phone_tickets WHERE expires_at<=?",
                (now.isoformat(),),
            )
            phone_count = connection.execute(
                "SELECT count(*) FROM signup_phone_challenges "
                "WHERE phone_binding=? AND created_at>?",
                (phone_binding, phone_since),
            ).fetchone()[0]
            client_count = connection.execute(
                "SELECT count(*) FROM signup_phone_challenges "
                "WHERE client_binding=? AND created_at>?",
                (client_binding, client_since),
            ).fetchone()[0]
            recent = connection.execute(
                "SELECT 1 FROM signup_phone_challenges "
                "WHERE phone_binding=? AND created_at>? LIMIT 1",
                (phone_binding, cooldown_since),
            ).fetchone()
            if phone_count >= PHONE_START_LIMIT or client_count >= CLIENT_START_LIMIT or recent:
                connection.rollback()
                return False
            connection.execute(
                "UPDATE signup_phone_challenges SET lifecycle='SUPERSEDED',version=version+1 "
                "WHERE phone_binding=? AND lifecycle='PENDING'",
                (phone_binding,),
            )
            connection.execute(
                "INSERT INTO signup_phone_challenges "
                "(challenge_hash,phone_binding,session_binding,client_binding,lifecycle,"
                "created_at,expires_at,attempts,version) VALUES(?,?,?,?,?,?,?,?,0)",
                (challenge_hash, phone_binding, session_binding, client_binding,
                 "START_CLAIMED", now.isoformat(),
                 (now + CHALLENGE_TTL).isoformat(), 0),
            )
            connection.commit()
            return True
        except sqlite3.Error:
            connection.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            connection.close()

    def start_result(
        self, challenge_ref: str, provider_ref: str | None, lifecycle: str,
    ) -> None:
        if lifecycle not in {"PENDING", "UNKNOWN_OUTCOME"}:
            raise SignupVerificationError("SIGNUP_STATE_INVALID")
        with closing(self._connect()) as connection:
            connection.execute(
                "UPDATE signup_phone_challenges SET provider_ref=?,lifecycle=?,version=version+1 "
                "WHERE challenge_hash=? AND lifecycle='START_CLAIMED'",
                (provider_ref, lifecycle, self.digest("challenge", challenge_ref)),
            )

    def claim_verify(
        self, *, challenge_ref: str, phone: str, session: str, now: datetime,
    ) -> dict | None:
        now = _utc(now)
        key = self.digest("challenge", challenge_ref)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM signup_phone_challenges WHERE challenge_hash=?",
                (key,),
            ).fetchone()
            if (
                row is None or row["lifecycle"] != "PENDING"
                or row["phone_binding"] != self.digest("phone", phone)
                or row["session_binding"] != self.digest("session", session)
                or now.isoformat() >= row["expires_at"]
            ):
                if row is not None and now.isoformat() >= row["expires_at"]:
                    connection.execute(
                        "UPDATE signup_phone_challenges SET lifecycle='EXPIRED',version=version+1 "
                        "WHERE challenge_hash=? AND lifecycle='PENDING'",
                        (key,),
                    )
                connection.commit()
                return None
            attempts = int(row["attempts"])
            if attempts >= CODE_ATTEMPT_LIMIT:
                connection.execute(
                    "UPDATE signup_phone_challenges SET lifecycle='FAILED',version=version+1 "
                    "WHERE challenge_hash=? AND lifecycle='PENDING'",
                    (key,),
                )
                connection.commit()
                return None
            changed = connection.execute(
                "UPDATE signup_phone_challenges SET lifecycle='VERIFY_CLAIMED',"
                "attempts=attempts+1,version=version+1 "
                "WHERE challenge_hash=? AND lifecycle='PENDING' AND version=?",
                (key, row["version"]),
            ).rowcount
            connection.commit()
            return dict(row) if changed == 1 else None
        except sqlite3.Error:
            connection.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            connection.close()

    def finish_verify(
        self, *, challenge_ref: str, outcome: str, ticket: str | None,
        phone: str, session: str, now: datetime,
    ) -> bool:
        now = _utc(now)
        key = self.digest("challenge", challenge_ref)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM signup_phone_challenges WHERE challenge_hash=?",
                (key,),
            ).fetchone()
            if row is None or row["lifecycle"] != "VERIFY_CLAIMED":
                connection.rollback()
                return False
            if (
                row["phone_binding"] != self.digest("phone", phone)
                or row["session_binding"] != self.digest("session", session)
                or now.isoformat() >= row["expires_at"]
            ):
                connection.execute(
                    "UPDATE signup_phone_challenges SET lifecycle='EXPIRED',version=version+1 "
                    "WHERE challenge_hash=? AND lifecycle='VERIFY_CLAIMED'",
                    (key,),
                )
                connection.commit()
                return False
            if outcome == "VERIFIED" and type(ticket) is str:
                connection.execute(
                    "INSERT INTO signup_phone_tickets "
                    "(ticket_hash,phone_binding,session_binding,lifecycle,created_at,expires_at,version) "
                    "VALUES(?,?,?,?,?,?,0)",
                    (self.digest("ticket", ticket), row["phone_binding"],
                     row["session_binding"], "ISSUED", now.isoformat(),
                     (now + TICKET_TTL).isoformat()),
                )
                connection.execute(
                    "UPDATE signup_phone_challenges SET lifecycle='VERIFIED',version=version+1 "
                    "WHERE challenge_hash=? AND lifecycle='VERIFY_CLAIMED'",
                    (key,),
                )
                connection.commit()
                return True
            lifecycle = (
                "UNKNOWN_OUTCOME" if outcome == "UNKNOWN_OUTCOME"
                else "FAILED" if int(row["attempts"]) >= CODE_ATTEMPT_LIMIT
                else "PENDING"
            )
            connection.execute(
                "UPDATE signup_phone_challenges SET lifecycle=?,version=version+1 "
                "WHERE challenge_hash=? AND lifecycle='VERIFY_CLAIMED'",
                (lifecycle, key),
            )
            connection.commit()
            return False
        except sqlite3.Error:
            connection.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            connection.close()

    def consume_ticket(
        self, *, ticket: str, phone: str, session: str, now: datetime,
    ) -> bool:
        now = _utc(now)
        ticket_hash = self.digest("ticket", ticket)
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM signup_phone_tickets WHERE ticket_hash=?",
                (ticket_hash,),
            ).fetchone()
            if (
                row is None or row["lifecycle"] != "ISSUED"
                or row["phone_binding"] != self.digest("phone", phone)
                or row["session_binding"] != self.digest("session", session)
                or now.isoformat() >= row["expires_at"]
            ):
                connection.rollback()
                return False
            changed = connection.execute(
                "UPDATE signup_phone_tickets SET lifecycle='CONSUMED',version=version+1 "
                "WHERE ticket_hash=? AND lifecycle='ISSUED' AND version=?",
                (ticket_hash, row["version"]),
            ).rowcount
            connection.commit()
            return changed == 1
        except sqlite3.Error:
            connection.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            connection.close()


class SignupPhoneVerificationService:
    """Phone OTP challenge and one-use phone-proof ticket; no account creation."""

    def __init__(
        self, *, store: SQLiteSignupVerificationStore,
        provider: SignupVerificationPort,
        clock=lambda: datetime.now(timezone.utc),
        ref_factory=lambda: secrets.token_urlsafe(24),
        ticket_factory=lambda: secrets.token_urlsafe(32),
    ) -> None:
        if not callable(getattr(provider, "start_sms", None)) or not callable(
            getattr(provider, "verify_sms", None)
        ):
            raise ValueError("SIGNUP_PROVIDER_REQUIRED")
        self.store = store
        self.provider = provider
        self.clock = clock
        self.ref_factory = ref_factory
        self.ticket_factory = ticket_factory

    def start_phone(
        self, phone: str, *, session_ref: str, client_ref: str,
    ) -> PhoneChallengeReply:
        if type(phone) is not str or not _PHONE.fullmatch(phone):
            return PhoneChallengeReply("NOT_STARTED")
        if not _valid_binding(session_ref) or not _valid_client(client_ref):
            return PhoneChallengeReply("NOT_STARTED")
        now = _utc(self.clock())
        challenge = self.ref_factory()
        if type(challenge) is not str or not _REF.fullmatch(challenge):
            return PhoneChallengeReply("NOT_STARTED")
        if not self.store.claim_start(
            challenge_ref=challenge, phone=phone, session=session_ref,
            client=client_ref, now=now,
        ):
            return PhoneChallengeReply("RATE_LIMITED")
        try:
            provider_ref = self.provider.start_sms(phone, challenge)
            if type(provider_ref) is not str or not _REF.fullmatch(provider_ref):
                raise ValueError("provider reference invalid")
        except Exception:
            self.store.start_result(challenge, None, "UNKNOWN_OUTCOME")
            return PhoneChallengeReply("UNKNOWN_OUTCOME")
        self.store.start_result(challenge, provider_ref, "PENDING")
        return PhoneChallengeReply("PENDING", challenge=challenge)

    def confirm_phone(
        self, challenge_ref: str, phone: str, code: str, *,
        session_ref: str,
    ) -> PhoneChallengeReply:
        if (
            type(challenge_ref) is not str or not _REF.fullmatch(challenge_ref)
            or type(phone) is not str or not _PHONE.fullmatch(phone)
            or type(code) is not str or not _CODE.fullmatch(code)
            or not _valid_binding(session_ref)
        ):
            return PhoneChallengeReply("NOT_VERIFIED")
        now = _utc(self.clock())
        claimed = self.store.claim_verify(
            challenge_ref=challenge_ref, phone=phone,
            session=session_ref, now=now,
        )
        if claimed is None or not claimed.get("provider_ref"):
            return PhoneChallengeReply("NOT_VERIFIED")
        try:
            verified = self.provider.verify_sms(phone, claimed["provider_ref"], code)
            if type(verified) is not bool:
                raise ValueError("provider result invalid")
        except Exception:
            self.store.finish_verify(
                challenge_ref=challenge_ref, outcome="UNKNOWN_OUTCOME", ticket=None,
                phone=phone, session=session_ref, now=_utc(self.clock()),
            )
            return PhoneChallengeReply("UNKNOWN_OUTCOME")
        if not verified:
            self.store.finish_verify(
                challenge_ref=challenge_ref, outcome="REJECTED", ticket=None,
                phone=phone, session=session_ref, now=_utc(self.clock()),
            )
            return PhoneChallengeReply("NOT_VERIFIED")
        ticket = self.ticket_factory()
        if type(ticket) is not str or not _REF.fullmatch(ticket):
            self.store.finish_verify(
                challenge_ref=challenge_ref, outcome="UNKNOWN_OUTCOME", ticket=None,
                phone=phone, session=session_ref, now=_utc(self.clock()),
            )
            return PhoneChallengeReply("UNKNOWN_OUTCOME")
        issued = self.store.finish_verify(
            challenge_ref=challenge_ref, outcome="VERIFIED", ticket=ticket,
            phone=phone, session=session_ref, now=_utc(self.clock()),
        )
        return PhoneChallengeReply("PHONE_VERIFIED", ticket=ticket) if issued else PhoneChallengeReply("NOT_VERIFIED")

    def consume_phone_ticket(
        self, ticket: str, phone: str, *, session_ref: str,
    ) -> bool:
        if (
            type(ticket) is not str or not _REF.fullmatch(ticket)
            or type(phone) is not str or not _PHONE.fullmatch(phone)
            or not _valid_binding(session_ref)
        ):
            return False
        return self.store.consume_ticket(
            ticket=ticket, phone=phone, session=session_ref,
            now=_utc(self.clock()),
        )


__all__ = [
    "CHALLENGE_TTL", "TICKET_TTL", "RESEND_COOLDOWN",
    "PHONE_START_LIMIT", "PHONE_START_WINDOW", "CLIENT_START_LIMIT",
    "CLIENT_START_WINDOW", "CODE_ATTEMPT_LIMIT",
    "PhoneChallengeReply", "SignupVerificationError",
    "SignupVerificationPort", "SQLiteSignupVerificationStore",
    "SignupPhoneVerificationService",
]
