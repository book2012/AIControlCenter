"""Fake-testable uniqueness and durable customer-registration operation boundary.

No production adapter or API composition is provided. Every write is preceded
by a durable dispatch claim; ambiguous writes are quarantined and never retried.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re
import secrets
import sqlite3
from typing import Protocol

from core.shopping.account_registration import (
    SignupCandidate, SignupInputError, validate_signup_candidate,
)
from core.shopping.signup_verification import SignupVerificationError, SQLiteSignupVerificationStore


_REF = re.compile(r"[A-Za-z0-9_-]{1,128}\Z", re.ASCII)


class SignupUniquenessPort(Protocol):
    def username_exists(self, login_id: str) -> bool: ...
    def email_exists(self, email: str) -> bool: ...
    def phone_exists(self, phone: str) -> bool: ...


class SignupCustomerWritePort(SignupUniquenessPort, Protocol):
    def create_customer(self, candidate: object, claim_ref: str) -> str: ...
    def customer_matches(self, provider_ref: str, candidate: object) -> bool: ...
    def find_by_claim(self, claim_ref: str) -> tuple[str, str | None]: ...


@dataclass(frozen=True)
class RegistrationOperationReply:
    state: str
    operation_ref: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return f"RegistrationOperationReply(state={self.state!r}, secrets=<redacted>)"


def _candidate_hash(store: SQLiteSignupVerificationStore, candidate: SignupCandidate) -> str:
    valid = validate_signup_candidate(candidate)
    return store.digest(
        "signup_candidate",
        json.dumps(
            [valid.login_id, valid.email.strip().lower(), valid.phone,
             valid.terms_version, valid.privacy_notice_version, valid.privacy_accepted],
            ensure_ascii=False, separators=(",", ":"),
        ),
    )


class SignupRegistrationOperationService:
    """Read-only identity preflight plus a durable one-attempt write ledger."""

    def __init__(self, *, store: SQLiteSignupVerificationStore, port: SignupCustomerWritePort,
                 clock=lambda: datetime.now(timezone.utc)):
        required = ("username_exists", "email_exists", "phone_exists", "create_customer",
                    "customer_matches", "find_by_claim")
        if any(not callable(getattr(port, name, None)) for name in required):
            raise ValueError("SIGNUP_CUSTOMER_PORT_REQUIRED")
        self.store, self.port, self.clock = store, port, clock

    def initialize(self) -> None:
        self.store.initialize()
        with closing(self.store._connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS signup_registration_operations (
                    operation_hash TEXT PRIMARY KEY,
                    claim_hash TEXT NOT NULL UNIQUE,
                    lifecycle TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    provider_ref TEXT,
                    version INTEGER NOT NULL DEFAULT 0
                );
            """)

    def execute(self, *, claim_ref: str, candidate: SignupCandidate) -> RegistrationOperationReply:
        if type(claim_ref) is not str or not _REF.fullmatch(claim_ref):
            return RegistrationOperationReply("NOT_COMPLETED")
        try:
            fingerprint = _candidate_hash(self.store, candidate)
        except SignupInputError:
            return RegistrationOperationReply("NOT_COMPLETED")
        now = self._now()
        claim_hash = self.store.digest("signup_claim", claim_ref)
        db = self.store._connect()
        try:
            claim = db.execute("SELECT * FROM signup_registration_claims WHERE claim_hash=?",
                               (claim_hash,)).fetchone()
            if claim is None or claim["candidate_hash"] != fingerprint:
                return RegistrationOperationReply("NOT_COMPLETED")
            existing = db.execute(
                "SELECT operation_hash,lifecycle FROM signup_registration_operations WHERE claim_hash=?",
                (claim_hash,),
            ).fetchone()
        finally:
            db.close()
        if existing:
            return RegistrationOperationReply(existing["lifecycle"])
        if claim["lifecycle"] != "CLAIMED":
            return RegistrationOperationReply("NOT_COMPLETED")

        # Perform every read so response timing does not reveal which identity collided.
        try:
            matches = (
                self.port.username_exists(candidate.login_id),
                self.port.email_exists(candidate.email.strip().lower()),
                self.port.phone_exists(candidate.phone),
            )
            if any(type(value) is not bool for value in matches):
                raise ValueError("invalid uniqueness response")
        except Exception:
            return RegistrationOperationReply("CHECK_UNAVAILABLE")
        if any(matches):
            self._set_claim_terminal(claim_hash, "DUPLICATE", now)
            return RegistrationOperationReply("NOT_COMPLETED")

        operation_ref = secrets.token_urlsafe(32)
        operation_hash = self.store.digest("signup_operation", operation_ref)
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            claim = db.execute("SELECT * FROM signup_registration_claims WHERE claim_hash=?",
                               (claim_hash,)).fetchone()
            existing = db.execute("SELECT lifecycle FROM signup_registration_operations WHERE claim_hash=?",
                                  (claim_hash,)).fetchone()
            if existing or claim is None or claim["lifecycle"] != "CLAIMED" or claim["candidate_hash"] != fingerprint:
                db.rollback()
                return RegistrationOperationReply(existing["lifecycle"] if existing else "NOT_COMPLETED")
            db.execute("INSERT INTO signup_registration_operations VALUES(?,?,?,?,?,?,0)",
                       (operation_hash, claim_hash, "DISPATCHING", now.isoformat(), now.isoformat(), None))
            db.execute("UPDATE signup_registration_claims SET lifecycle='CREATE_CLAIMED',version=version+1 "
                       "WHERE claim_hash=? AND lifecycle='CLAIMED'", (claim_hash,))
            db.commit()
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()

        try:
            provider_ref = self.port.create_customer(candidate, claim_ref)
            if type(provider_ref) is not str or not _REF.fullmatch(provider_ref):
                raise RuntimeError("unknown create result")
            self._transition(operation_hash, claim_hash, "CREATE_ACCEPTED", provider_ref)
            matched = self.port.customer_matches(provider_ref, candidate)
            if type(matched) is not bool or not matched:
                self._transition(operation_hash, claim_hash, "UNKNOWN_OUTCOME", provider_ref)
                return RegistrationOperationReply("UNKNOWN_OUTCOME", operation_ref)
            self._transition(operation_hash, claim_hash, "ACTIVE", provider_ref)
            return RegistrationOperationReply("ACTIVE", operation_ref)
        except Exception:
            self._transition(operation_hash, claim_hash, "UNKNOWN_OUTCOME", None)
            return RegistrationOperationReply("UNKNOWN_OUTCOME", operation_ref)

    def reconcile(self, *, operation_ref: str, claim_ref: str,
                  candidate: SignupCandidate) -> RegistrationOperationReply:
        if (type(operation_ref) is not str or not _REF.fullmatch(operation_ref)
                or type(claim_ref) is not str or not _REF.fullmatch(claim_ref)):
            return RegistrationOperationReply("NOT_RECONCILED")
        try:
            fingerprint = _candidate_hash(self.store, candidate)
        except SignupInputError:
            return RegistrationOperationReply("NOT_RECONCILED")
        oh = self.store.digest("signup_operation", operation_ref)
        ch = self.store.digest("signup_claim", claim_ref)
        db = self.store._connect()
        try:
            operation = db.execute("SELECT * FROM signup_registration_operations WHERE operation_hash=?",
                                   (oh,)).fetchone()
            claim = db.execute("SELECT * FROM signup_registration_claims WHERE claim_hash=?",
                               (ch,)).fetchone()
            if (operation is None or claim is None or operation["claim_hash"] != ch
                    or claim["candidate_hash"] != fingerprint
                    or operation["lifecycle"] not in {"DISPATCHING", "UNKNOWN_OUTCOME", "CREATE_ACCEPTED"}):
                return RegistrationOperationReply("NOT_RECONCILED")
        finally:
            db.close()
        try:
            status, provider_ref = self.port.find_by_claim(claim_ref)
            if status == "ABSENT" and provider_ref is None:
                self._transition(oh, ch, "FAILED", None)
                return RegistrationOperationReply("FAILED", operation_ref)
            if status != "FOUND" or type(provider_ref) is not str or not _REF.fullmatch(provider_ref):
                return RegistrationOperationReply("UNKNOWN_OUTCOME", operation_ref)
            if not self.port.customer_matches(provider_ref, candidate):
                return RegistrationOperationReply("UNKNOWN_OUTCOME", operation_ref)
            self._transition(oh, ch, "ACTIVE", provider_ref)
            return RegistrationOperationReply("ACTIVE", operation_ref)
        except Exception:
            return RegistrationOperationReply("UNKNOWN_OUTCOME", operation_ref)

    def _now(self):
        value = self.clock()
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise SignupVerificationError("SIGNUP_CLOCK_INVALID")
        if value.utcoffset().total_seconds() != 0:
            raise SignupVerificationError("SIGNUP_CLOCK_INVALID")
        return value

    def _set_claim_terminal(self, claim_hash, state, now):
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE signup_registration_claims SET lifecycle=?,version=version+1 "
                       "WHERE claim_hash=? AND lifecycle='CLAIMED'", (state, claim_hash))
            db.commit()
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()

    def _transition(self, operation_hash, claim_hash, state, provider_ref):
        now = self._now().isoformat()
        db = self.store._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE signup_registration_operations SET lifecycle=?,provider_ref=?,"
                       "updated_at=?,version=version+1 WHERE operation_hash=?",
                       (state, provider_ref, now, operation_hash))
            claim_state = {
                "CREATE_ACCEPTED": "CREATE_ACCEPTED", "ACTIVE": "ACTIVE",
                "UNKNOWN_OUTCOME": "UNKNOWN_OUTCOME", "FAILED": "RECONCILED",
            }[state]
            db.execute("UPDATE signup_registration_claims SET lifecycle=?,version=version+1 "
                       "WHERE claim_hash=?", (claim_state, claim_hash))
            db.commit()
        except sqlite3.Error:
            db.rollback()
            raise SignupVerificationError("SIGNUP_STORAGE_UNAVAILABLE") from None
        finally:
            db.close()


__all__ = [
    "SignupUniquenessPort", "SignupCustomerWritePort",
    "RegistrationOperationReply", "SignupRegistrationOperationService",
]
