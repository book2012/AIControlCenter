"""Fake-testable email verification and two-contact signup claim boundary.

This module has no API/runtime binding, account creation, or production adapter.
Email tickets and phone tickets are combined in one SQLite transaction into a
durable registration claim; profile fields and passwords are never accepted.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import re
import secrets
import sqlite3
from typing import Protocol

from core.shopping.signup_verification import (
    CLIENT_START_LIMIT,
    CLIENT_START_WINDOW,
    CODE_ATTEMPT_LIMIT,
    RESEND_COOLDOWN,
    TICKET_TTL,
    SignupVerificationError,
    SQLiteSignupVerificationStore,
)


EMAIL_CHALLENGE_TTL = timedelta(minutes=5)
_REF = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)


def _utc(value: datetime) -> datetime:
    if (type(value) is not datetime or value.tzinfo is None
            or value.utcoffset() != timedelta(0)):
        raise ValueError("UTC timestamp required")
    return value


EMAIL_START_LIMIT = 5
EMAIL_START_WINDOW = timedelta(hours=24)
_EMAIL = re.compile(r"[^\s@]{1,64}@[^\s@.]{1,63}(?:\.[A-Za-z0-9-]{1,63})+\Z", re.ASCII)
_EMAIL_CODE = re.compile(r"[0-9]{6}\Z", re.ASCII)


class SignupEmailPort(Protocol):
    def start_email(self, email: str, challenge_ref: str) -> str: ...
    def verify_email(self, email: str, provider_ref: str, code: str) -> bool: ...


@dataclass(frozen=True)
class EmailChallengeReply:
    state: str
    challenge: str | None = field(default=None, repr=False)
    ticket: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"EmailChallengeReply(state={self.state!r}, secrets=<redacted>)"


@dataclass(frozen=True)
class SignupClaimReply:
    state: str
    claim_ref: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"SignupClaimReply(state={self.state!r}, secrets=<redacted>)"


class SignupEmailVerificationService:
    """Email proof service. Provider implementation is injected, never live here."""

    def __init__(
        self, *, store: SQLiteSignupVerificationStore, provider: SignupEmailPort,
        clock=lambda: datetime.now(timezone.utc),
        ref_factory=lambda: secrets.token_urlsafe(24),
        ticket_factory=lambda: secrets.token_urlsafe(32),
    ) -> None:
        if not callable(getattr(provider, "start_email", None)) or not callable(
            getattr(provider, "verify_email", None)
        ):
            raise ValueError("SIGNUP_EMAIL_PROVIDER_REQUIRED")
        self.store, self.provider, self.clock = store, provider, clock
        self.ref_factory, self.ticket_factory = ref_factory, ticket_factory

    def initialize(self) -> None:
        self.store.initialize()
        with closing(self.store._connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS signup_email_challenges (
                    challenge_hash TEXT PRIMARY KEY,
                    email_binding TEXT NOT NULL,
                    session_binding TEXT NOT NULL,
                    client_binding TEXT NOT NULL,
                    provider_ref TEXT,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    version INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS signup_email_challenges_email_created
                    ON signup_email_challenges(email_binding, created_at);
                CREATE INDEX IF NOT EXISTS signup_email_challenges_client_created
                    ON signup_email_challenges(client_binding, created_at);
                CREATE TABLE IF NOT EXISTS signup_email_tickets (
                    ticket_hash TEXT PRIMARY KEY,
                    email_binding TEXT NOT NULL,
                    session_binding TEXT NOT NULL,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS signup_privacy_consents (
                    session_binding TEXT PRIMARY KEY,
                    notice_version_hash TEXT NOT NULL,
                    accepted_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS signup_registration_claims (
                    claim_hash TEXT PRIMARY KEY,
                    idempotency_hash TEXT NOT NULL UNIQUE,
                    phone_ticket_hash TEXT NOT NULL UNIQUE,
                    email_ticket_hash TEXT NOT NULL UNIQUE,
                    session_binding TEXT NOT NULL,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    candidate_hash TEXT NOT NULL,
                    terms_version_hash TEXT NOT NULL,
                    privacy_notice_version_hash TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 0
                );
            """)

    def start_email(self, email: str, *, session_ref: str, client_ref: str) -> EmailChallengeReply:
        if (
            type(email) is not str or len(email) > 254 or not _EMAIL.fullmatch(email)
            or not self._binding(session_ref) or not self._binding(client_ref, minimum=3)
        ):
            return EmailChallengeReply("NOT_STARTED")
        email = email.strip().lower()
        now = _utc(self.clock())
        challenge = self.ref_factory()
        if type(challenge) is not str or not _REF.fullmatch(challenge):
            return EmailChallengeReply("NOT_STARTED")
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM signup_email_challenges WHERE created_at<=?",
                       ((now - EMAIL_START_WINDOW).isoformat(),))
            db.execute("DELETE FROM signup_email_tickets WHERE expires_at<=?", (now.isoformat(),))
            db.execute("DELETE FROM signup_client_attempts WHERE created_at<=?",
                       ((now - CLIENT_START_WINDOW).isoformat(),))
            eb = self.store.digest("email", email)
            sb = self.store.digest("session", session_ref)
            cb = self.store.digest("client", client_ref)
            counts = db.execute(
                "SELECT count(*),max(created_at) FROM signup_email_challenges "
                "WHERE email_binding=? AND created_at>?",
                (eb, (now - EMAIL_START_WINDOW).isoformat()),
            ).fetchone()
            client_count = db.execute(
                "SELECT count(*) FROM signup_client_attempts WHERE client_binding=? AND created_at>?",
                (cb, (now - CLIENT_START_WINDOW).isoformat()),
            ).fetchone()[0]
            recent = bool(counts[1] and datetime.fromisoformat(counts[1]) > now - RESEND_COOLDOWN)
            if counts[0] >= EMAIL_START_LIMIT or client_count >= CLIENT_START_LIMIT or recent:
                db.rollback()
                return EmailChallengeReply("RATE_LIMITED")
            db.execute("UPDATE signup_email_challenges SET lifecycle='SUPERSEDED',version=version+1 "
                       "WHERE email_binding=? AND lifecycle='PENDING'", (eb,))
            db.execute(
                "INSERT INTO signup_client_attempts(client_binding,channel,created_at) VALUES(?,?,?)",
                (cb, "email", now.isoformat()),
            )
            db.execute(
                "INSERT INTO signup_email_challenges VALUES(?,?,?,?,?,?,?,?,0,0)",
                (self.store.digest("email_challenge", challenge), eb, sb, cb, None,
                 "START_CLAIMED", now.isoformat(),
                 (now + EMAIL_CHALLENGE_TTL).isoformat()),
            )
            db.commit()
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()
        try:
            provider_ref = self.provider.start_email(email, challenge)
            if type(provider_ref) is not str or not _REF.fullmatch(provider_ref):
                raise ValueError("invalid provider ref")
        except Exception:
            self._start_result(challenge, None, "UNKNOWN_OUTCOME")
            return EmailChallengeReply("UNKNOWN_OUTCOME")
        self._start_result(challenge, provider_ref, "PENDING")
        return EmailChallengeReply("PENDING", challenge=challenge)

    def _start_result(self, challenge, provider_ref, state):
        with closing(self.store._connect()) as db:
            db.execute("UPDATE signup_email_challenges SET provider_ref=?,lifecycle=?,version=version+1 "
                       "WHERE challenge_hash=? AND lifecycle='START_CLAIMED'",
                       (provider_ref, state, self.store.digest("email_challenge", challenge)))

    def confirm_email(self, challenge_ref: str, email: str, code: str, *, session_ref: str) -> EmailChallengeReply:
        if (
            type(challenge_ref) is not str or not _REF.fullmatch(challenge_ref)
            or type(email) is not str or len(email) > 254 or not _EMAIL.fullmatch(email)
            or type(code) is not str or not _EMAIL_CODE.fullmatch(code)
            or not self._binding(session_ref)
        ):
            return EmailChallengeReply("NOT_VERIFIED")
        email = email.strip().lower()
        now = _utc(self.clock())
        key = self.store.digest("email_challenge", challenge_ref)
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM signup_email_challenges WHERE challenge_hash=?", (key,)).fetchone()
            if (row is None or row["lifecycle"] != "PENDING"
                    or row["email_binding"] != self.store.digest("email", email)
                    or row["session_binding"] != self.store.digest("session", session_ref)
                    or now.isoformat() >= row["expires_at"]
                    or not row["provider_ref"]):
                db.commit()
                return EmailChallengeReply("NOT_VERIFIED")
            if row["attempts"] >= CODE_ATTEMPT_LIMIT:
                db.execute("UPDATE signup_email_challenges SET lifecycle='FAILED' WHERE challenge_hash=?", (key,))
                db.commit()
                return EmailChallengeReply("NOT_VERIFIED")
            db.execute("UPDATE signup_email_challenges SET lifecycle='VERIFY_CLAIMED',attempts=attempts+1,"
                       "version=version+1 WHERE challenge_hash=? AND lifecycle='PENDING'", (key,))
            db.commit()
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()
        try:
            ok = self.provider.verify_email(email, row["provider_ref"], code)
            if type(ok) is not bool:
                raise ValueError("invalid provider response")
        except Exception:
            self._finish_email(key, "UNKNOWN_OUTCOME", None, email, session_ref)
            return EmailChallengeReply("UNKNOWN_OUTCOME")
        if not ok:
            self._finish_email(key, "FAILED" if row["attempts"] + 1 >= CODE_ATTEMPT_LIMIT else "PENDING",
                               None, email, session_ref)
            return EmailChallengeReply("NOT_VERIFIED")
        ticket = self.ticket_factory()
        if type(ticket) is not str or not _REF.fullmatch(ticket):
            self._finish_email(key, "UNKNOWN_OUTCOME", None, email, session_ref)
            return EmailChallengeReply("UNKNOWN_OUTCOME")
        if self._finish_email(key, "VERIFIED", ticket, email, session_ref):
            return EmailChallengeReply("EMAIL_VERIFIED", ticket=ticket)
        return EmailChallengeReply("NOT_VERIFIED")

    def _finish_email(self, key, outcome, ticket, email, session):
        now = _utc(self.clock())
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM signup_email_challenges WHERE challenge_hash=?", (key,)).fetchone()
            if (row is None or row["lifecycle"] != "VERIFY_CLAIMED"
                    or row["email_binding"] != self.store.digest("email", email)
                    or row["session_binding"] != self.store.digest("session", session)
                    or now.isoformat() >= row["expires_at"]):
                db.rollback()
                return False
            if outcome == "VERIFIED":
                db.execute("INSERT INTO signup_email_tickets VALUES(?,?,?,?,?,?,0)",
                           (self.store.digest("email_ticket", ticket), row["email_binding"],
                            row["session_binding"], "ISSUED", now.isoformat(), (now + TICKET_TTL).isoformat()))
                state = "VERIFIED"
            else:
                state = outcome
            db.execute("UPDATE signup_email_challenges SET lifecycle=?,version=version+1 WHERE challenge_hash=?",
                       (state, key))
            db.commit()
            return outcome == "VERIFIED"
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()

    @staticmethod
    def _binding(value, minimum=16):
        return (type(value) is str and minimum <= len(value) <= 256
                and value == value.strip() and all(32 < ord(c) < 127 for c in value))


class TwoContactSignupClaimService:
    """Atomically consumes verified phone+email tickets into a durable claim.

    Claim only authorizes a later registration operation. It stores no profile,
    password, email, phone, or request body, and never creates a WooCommerce user.
    """

    def __init__(self, *, store: SQLiteSignupVerificationStore, clock=lambda: datetime.now(timezone.utc)):
        self.store, self.clock = store, clock

    def record_privacy_consent(self, *, session_ref: str, notice_version: str,
                               accepted: bool) -> str:
        if (not SignupEmailVerificationService._binding(session_ref)
                or type(notice_version) is not str or not 1 <= len(notice_version) <= 64
                or notice_version != notice_version.strip() or type(accepted) is not bool):
            return "NOT_ACCEPTED"
        session_binding = self.store.digest("session", session_ref)
        if not accepted:
            db = self.store._connect()
            try:
                db.execute("DELETE FROM signup_privacy_consents WHERE session_binding=?",
                           (session_binding,))
                db.commit()
            except sqlite3.Error:
                db.rollback()
                raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
            finally:
                db.close()
            return "NOT_ACCEPTED"
        now = _utc(self.clock())
        db = self.store._connect()
        try:
            db.execute(
                "INSERT INTO signup_privacy_consents VALUES(?,?,?) "
                "ON CONFLICT(session_binding) DO UPDATE SET "
                "notice_version_hash=excluded.notice_version_hash,accepted_at=excluded.accepted_at",
                (session_binding, self.store.digest("signup_privacy_notice", notice_version),
                 now.isoformat()),
            )
            db.commit()
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()
        return "ACCEPTED"

    def has_privacy_consent(self, *, session_ref: str, notice_version: str) -> bool:
        if (not SignupEmailVerificationService._binding(session_ref)
                or type(notice_version) is not str or not 1 <= len(notice_version) <= 64):
            return False
        with closing(self.store._connect()) as db:
            row = db.execute(
                "SELECT 1 FROM signup_privacy_consents WHERE session_binding=? AND notice_version_hash=?",
                (self.store.digest("session", session_ref),
                 self.store.digest("signup_privacy_notice", notice_version)),
            ).fetchone()
        return row is not None

    def claim(self, *, phone_ticket: str, email_ticket: str, session_ref: str,
              idempotency_key: str, candidate) -> SignupClaimReply:
        from core.shopping.account_registration import (
            SignupCandidate, SignupInputError, validate_signup_candidate,
        )
        try:
            if type(candidate) is not SignupCandidate:
                return SignupClaimReply("NOT_AUTHORIZED")
            validated = validate_signup_candidate(candidate)
        except SignupInputError:
            return SignupClaimReply("NOT_AUTHORIZED")
        if any(type(v) is not str or not _REF.fullmatch(v)
               for v in (phone_ticket, email_ticket, idempotency_key)):
            return SignupClaimReply("NOT_AUTHORIZED")
        if not SignupEmailVerificationService._binding(session_ref):
            return SignupClaimReply("NOT_AUTHORIZED")
        now = _utc(self.clock())
        ph = self.store.digest("ticket", phone_ticket)
        eh = self.store.digest("email_ticket", email_ticket)
        sb = self.store.digest("session", session_ref)
        ih = self.store.digest("signup_idempotency", idempotency_key)
        claim_ref = secrets.token_urlsafe(32)
        ch = self.store.digest("signup_claim", claim_ref)
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT claim_hash FROM signup_registration_claims "
                                  "WHERE idempotency_hash=?", (ih,)).fetchone()
            if existing:
                db.commit()
                return SignupClaimReply("ALREADY_CLAIMED")
            consent = db.execute(
                "SELECT 1 FROM signup_privacy_consents WHERE session_binding=? AND notice_version_hash=?",
                (sb, self.store.digest("signup_privacy_notice", validated.privacy_notice_version)),
            ).fetchone()
            phone = db.execute("SELECT * FROM signup_phone_tickets WHERE ticket_hash=?", (ph,)).fetchone()
            email = db.execute("SELECT * FROM signup_email_tickets WHERE ticket_hash=?", (eh,)).fetchone()
            if (consent is None or not validated.privacy_accepted
                    or not self._ticket_ok(phone, sb, now) or not self._ticket_ok(email, sb, now)
                    or phone["phone_binding"] != self.store.digest("phone", validated.phone)
                    or email["email_binding"] != self.store.digest("email", validated.email.strip().lower())):
                db.rollback()
                return SignupClaimReply("NOT_AUTHORIZED")
            # Bind the durable claim to non-secret registration intent and the
            # accepted terms version. Never persist or hash the password.
            candidate_hash = self.store.digest(
                "signup_candidate",
                json.dumps(
                    [validated.login_id, validated.email.strip().lower(),
                     validated.phone, validated.terms_version,
                     validated.privacy_notice_version, validated.privacy_accepted],
                    ensure_ascii=False, separators=(",", ":"),
                ),
            )
            terms_hash = self.store.digest("signup_terms", validated.terms_version)
            notice_hash = self.store.digest("signup_privacy_notice", validated.privacy_notice_version)
            db.execute("UPDATE signup_phone_tickets SET lifecycle='CONSUMED',version=version+1 "
                       "WHERE ticket_hash=? AND lifecycle='ISSUED'", (ph,))
            db.execute("UPDATE signup_email_tickets SET lifecycle='CONSUMED',version=version+1 "
                       "WHERE ticket_hash=? AND lifecycle='ISSUED'", (eh,))
            db.execute("INSERT INTO signup_registration_claims VALUES(?,?,?,?,?,?,?,?,?,?,0)",
                       (ch, ih, ph, eh, sb, "CLAIMED", now.isoformat(),
                        candidate_hash, terms_hash, notice_hash))
            db.commit()
            return SignupClaimReply("CLAIMED", claim_ref=claim_ref)
        except sqlite3.IntegrityError:
            db.rollback()
            return SignupClaimReply("NOT_AUTHORIZED")
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()

    @staticmethod
    def _ticket_ok(row, session_binding, now):
        return bool(row is not None and row["lifecycle"] == "ISSUED"
                    and row["session_binding"] == session_binding
                    and now.isoformat() < row["expires_at"])


__all__ = [
    "EMAIL_CHALLENGE_TTL", "SignupEmailPort", "EmailChallengeReply",
    "SignupEmailVerificationService", "SignupClaimReply",
    "TwoContactSignupClaimService",
]
