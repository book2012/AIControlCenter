"""Bounded trusted customer-session service for the future auth boundary.

The service is repository-only and has no HTTP, cookie, SMS, or production
issuer integration.  Receipt consumption, session creation, and required auth
audit are one SQLite transaction.  Every public result is a fixed status or a
secret-bearing internal issuance object; raw database and verifier failures are
never projected.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import hmac
import secrets
import sqlite3
from typing import Callable
import uuid

from pydantic import SecretStr

from core.shopping.customer_auth import (
    ReceiptValidationResult, TrustedVerificationContext,
    TrustedVerificationReceipt, validate_trusted_receipt,
)
from core.shopping.customer_identity import (
    Customer, CustomerState, VerificationState, customer_is_session_eligible,
    require_utc,
)
from core.shopping.customer_persistence import (
    BUSY_TIMEOUT_MS, PersistenceError, StorageUnavailable, _utc, customer_from_connection,
    open_connection, session_from_connection,
)
from core.shopping.customer_sessions import (
    CustomerSession, PrivateSessionRecord, SessionPolicyStatus,
    evaluate_session, safe_session_projection,
)


AUTH_SCHEMA_TABLES = (
    "shopping_verification_receipts", "shopping_auth_audit",
    "shopping_verification_challenges", "shopping_verification_attempts",
    "shopping_trusted_receipts",
)
SECRET_DOMAIN = "aicontrolcenter/shopping/session/v1:"


class SessionServiceError(RuntimeError):
    """Base class for sanitized service failures."""


class ReceiptPolicyDenied(SessionServiceError):
    pass


class ReceiptAlreadyConsumed(SessionServiceError):
    pass


class CustomerNotEligible(SessionServiceError):
    pass


class AuditPersistenceError(SessionServiceError):
    pass


class SessionValidationCode(str, Enum):
    VALID = "VALID"
    MISSING = "MISSING"
    INVALID_SECRET = "INVALID_SECRET"
    INELIGIBLE = "INELIGIBLE"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True)
class IssuedSession:
    """Internal issuance result; the secret is never included in repr/dumps."""

    session_id: str
    session_secret: SecretStr
    projection: object
    receipt_id: str

    def __repr__(self) -> str:  # pragma: no cover - defensive output boundary
        return f"IssuedSession(session_id={self.session_id!r}, receipt_id={self.receipt_id!r})"


@dataclass(frozen=True)
class SessionValidation:
    code: str
    projection: object | None = None


@dataclass(frozen=True)
class RevocationResult:
    code: str


def _bounded(value: object, *, max_length: int = 160) -> bool:
    return type(value) is str and 1 <= len(value) <= max_length


def _session_id() -> str:
    return "AG-SES-" + uuid.uuid4().hex


def _secret() -> str:
    return secrets.token_urlsafe(32)


def _hash_secret(secret: str) -> str:
    return "sha256:" + hashlib.sha256((SECRET_DOMAIN + secret).encode("utf-8")).hexdigest()


def _required_auth_tables(connection: sqlite3.Connection) -> None:
    names = {
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    if any(table not in names for table in AUTH_SCHEMA_TABLES):
        raise StorageUnavailable("authentication persistence is unavailable")


def _audit(
    connection: sqlite3.Connection,
    *,
    event_id: str,
    actor_ref: str,
    resource_ref: str,
    action: str,
    outcome: str,
    correlation_id: str,
    occurred_at: datetime,
    failure_hook: Callable[[str], None] | None,
) -> None:
    if failure_hook is not None:
        try:
            failure_hook(action)
        except Exception:
            raise AuditPersistenceError("authentication audit persistence failed") from None
    try:
        connection.execute(
            "INSERT INTO shopping_auth_audit(event_id,actor_ref,resource_ref,action,outcome,correlation_id,occurred_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (event_id, actor_ref, resource_ref, action, outcome, correlation_id, _utc(occurred_at)),
        )
    except sqlite3.Error:
        raise AuditPersistenceError("authentication audit persistence failed") from None


def _validate_durable_trusted_receipt(
    connection: sqlite3.Connection,
    receipt: TrustedVerificationReceipt,
    *,
    now: datetime,
) -> sqlite3.Row | None:
    """Validate immutable server-owned challenge/attempt provenance."""
    try:
        row = connection.execute(
            "SELECT r.*, c.status AS challenge_status, c.customer_id AS challenge_customer, "
            "c.receipt_id AS challenge_receipt, c.provider_source AS challenge_source, "
            "c.provider_verification_id AS challenge_provider_id, c.phone_binding AS challenge_binding, "
            "c.provider_start_status AS challenge_start_status, "
            "a.outcome AS attempt_outcome, a.receipt_id AS attempt_receipt, "
            "a.challenge_id AS attempt_challenge, a.provider_source AS attempt_source, "
            "a.provider_verification_id AS attempt_provider_id, a.phone_binding AS attempt_binding "
            "FROM shopping_trusted_receipts r "
            "JOIN shopping_verification_challenges c ON c.challenge_id=r.challenge_id "
            "JOIN shopping_verification_attempts a ON a.attempt_id=r.attempt_id "
            "WHERE r.receipt_id=?",
            (receipt.receipt_id,),
        ).fetchone()
        if row is None:
            # B3-A synthetic callers predate the v2 issued-receipt ledger. A
            # receipt with a matching trusted context remains compatible only
            # when this database has no evidence that it was a C1 receipt.
            # Once TX1 evidence exists, a missing provenance row fails closed.
            marker = connection.execute(
                "SELECT 1 FROM shopping_auth_audit WHERE action='PHONE_VERIFICATION' "
                "AND outcome='APPLIED' AND actor_ref=? LIMIT 1",
                (receipt.customer_id,),
            ).fetchone()
            if marker is not None:
                raise ReceiptPolicyDenied("receipt policy denied")
            return None
        if (
            row["lifecycle"] != "ISSUED"
            or row["challenge_status"] != "VERIFIED"
            or row["challenge_start_status"] not in {"STARTED", "PENDING"}
            or row["attempt_outcome"] != "SUCCESS"
            or row["attempt_challenge"] != row["challenge_id"]
            or row["challenge_customer"] != receipt.customer_id
            or row["provider_source"] != row["challenge_source"]
            or row["provider_source"] != row["attempt_source"]
            or row["provider_verification_id"] != row["challenge_provider_id"]
            or row["provider_verification_id"] != row["attempt_provider_id"]
            or row["phone_binding"] != row["challenge_binding"]
            or row["phone_binding"] != row["attempt_binding"]
            or row["challenge_receipt"] != receipt.receipt_id
            or row["attempt_receipt"] != receipt.receipt_id
            or row["customer_id"] != receipt.customer_id
            or row["issuer_ref"] != receipt.issuer_ref
            or row["browser_challenge"] != receipt.browser_challenge
            or row["purpose"] != receipt.purpose.value
        ):
            raise ReceiptPolicyDenied("receipt policy denied")
        persisted_issued = datetime.fromisoformat(row["issued_at"].replace("Z", "+00:00"))
        persisted_expires = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        if persisted_issued != receipt.issued_at or persisted_expires != receipt.expires_at:
            raise ReceiptPolicyDenied("receipt policy denied")
        if now >= persisted_expires:
            raise ReceiptPolicyDenied("receipt policy denied")
        return row
    except ReceiptPolicyDenied:
        raise
    except (KeyError, TypeError, ValueError, sqlite3.Error):
        raise ReceiptPolicyDenied("receipt policy denied") from None


class CustomerSessionService:
    """Trusted service seam; no constructor side effects or schema migration."""

    def __init__(
        self,
        database_path: str,
        *,
        busy_timeout_ms: int = BUSY_TIMEOUT_MS,
        secret_factory: Callable[[], str] | None = None,
        session_id_factory: Callable[[], str] | None = None,
        event_id_factory: Callable[[], str] | None = None,
        audit_failure_hook: Callable[[str], None] | None = None,
    ) -> None:
        self.database_path = database_path
        self.busy_timeout_ms = busy_timeout_ms
        self._secret_factory = secret_factory or _secret
        self._session_id_factory = session_id_factory or _session_id
        self._event_id_factory = event_id_factory or (lambda: "AG-AUD-" + uuid.uuid4().hex)
        self._audit_failure_hook = audit_failure_hook

    def consume_receipt_and_create_session(
        self,
        receipt: TrustedVerificationReceipt,
        *,
        expected_challenge: str,
        trusted_context: TrustedVerificationContext,
        now: datetime,
        correlation_id: str,
    ) -> IssuedSession:
        """Atomically consume trusted receipt, issue session, and write audit."""
        try:
            require_utc(now)
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise ReceiptPolicyDenied("receipt policy denied") from None
        if not _bounded(correlation_id):
            raise ReceiptPolicyDenied("receipt policy denied")
        policy = validate_trusted_receipt(
            receipt, now=now, expected_challenge=expected_challenge,
            context=trusted_context,
        )
        if policy is not ReceiptValidationResult.ACCEPTED:
            raise ReceiptPolicyDenied("receipt policy denied")

        connection: sqlite3.Connection | None = None
        try:
            connection = open_connection(self.database_path, timeout_ms=self.busy_timeout_ms)
            connection.execute("BEGIN IMMEDIATE")
            _required_auth_tables(connection)
            durable_provenance = _validate_durable_trusted_receipt(connection, receipt, now=now)
            consumed = connection.execute(
                "SELECT 1 FROM shopping_verification_receipts WHERE receipt_id=?",
                (receipt.receipt_id,),
            ).fetchone()
            if consumed is not None:
                raise ReceiptAlreadyConsumed("receipt already consumed")
            customer = customer_from_connection(connection, receipt.customer_id)
            if customer is None or not customer_is_session_eligible(customer, now=now):
                raise CustomerNotEligible("customer is not eligible")
            binding = customer.contact_binding
            if binding is None or binding.state is not VerificationState.VERIFIED:
                raise CustomerNotEligible("customer is not eligible")
            session_id = self._session_id_factory()
            secret = self._secret_factory()
            if (not _bounded(session_id, max_length=64)
                    or not _bounded(secret, max_length=256)):
                raise SessionServiceError("session issuance failed")
            session = CustomerSession(
                id=session_id, customer_id=customer.id, created_at=now,
                last_activity_at=now, idle_expires_at=now + timedelta(minutes=30),
                absolute_expires_at=now + timedelta(hours=24),
            )
            record = PrivateSessionRecord(
                session=session, session_secret_hash=_hash_secret(secret),
                security_policy_version="1.0.0", credential_bound_at=now,
                verified_contact_ref=binding.contact_ref,
                contact_verified_at=binding.verified_at,
            )
            connection.execute(
                "INSERT INTO shopping_sessions(session_id,customer_id,session_json,secret_hash,policy_version,credential_bound_at,verified_contact_ref,contact_verified_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (session.id, session.customer_id, session.model_dump_json(),
                 record.session_secret_hash.get_secret_value(), record.security_policy_version,
                 _utc(record.credential_bound_at), record.verified_contact_ref,
                 _utc(record.contact_verified_at)),
            )
            connection.execute(
                "INSERT INTO shopping_verification_receipts(receipt_id,customer_id,issuer_ref,browser_challenge,purpose,session_id,consumed_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (receipt.receipt_id, receipt.customer_id, receipt.issuer_ref,
                 receipt.browser_challenge, receipt.purpose.value, session.id, _utc(now)),
            )
            if durable_provenance is not None:
                trusted_row = connection.execute(
                    "SELECT version FROM shopping_trusted_receipts WHERE receipt_id=? AND lifecycle='ISSUED'",
                    (receipt.receipt_id,),
                ).fetchone()
                if trusted_row is None:
                    raise ReceiptPolicyDenied("receipt policy denied")
                changed = connection.execute(
                    "UPDATE shopping_trusted_receipts SET lifecycle='CONSUMED',consumed_at=?,version=version+1 "
                    "WHERE receipt_id=? AND lifecycle='ISSUED' AND version=?",
                    (_utc(now), receipt.receipt_id, trusted_row["version"]),
                ).rowcount
                if changed != 1:
                    raise ReceiptAlreadyConsumed("receipt already consumed")
            _audit(
                connection, event_id=self._event_id_factory(), actor_ref=customer.id,
                resource_ref=session.id, action="SESSION_ISSUE", outcome="APPLIED",
                correlation_id=correlation_id, occurred_at=now,
                failure_hook=self._audit_failure_hook,
            )
            projection = safe_session_projection(record, customer, now=now)
            if projection is None:
                raise SessionServiceError("session issuance failed")
            PrivateSessionRecord.model_validate(record)
            issued = IssuedSession(session.id, SecretStr(secret), projection, receipt.receipt_id)
            connection.commit()
            return issued
        except (ReceiptAlreadyConsumed, CustomerNotEligible, AuditPersistenceError, ReceiptPolicyDenied,
                SessionServiceError):
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise
        except sqlite3.IntegrityError as exc:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            if "shopping_verification_receipts" in str(exc):
                raise ReceiptAlreadyConsumed("receipt already consumed") from None
            raise StorageUnavailable("authentication persistence is unavailable") from None
        except (PersistenceError, sqlite3.Error, OSError):
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise StorageUnavailable("authentication persistence is unavailable") from None
        except Exception:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise SessionServiceError("session issuance failed") from None
        finally:
            if connection is not None:
                connection.close()

    def validate_session(
        self, session_id: str, session_secret: str, customer_id: str, *, now: datetime,
    ) -> SessionValidation:
        try:
            require_utc(now)
        except (TypeError, ValueError, AttributeError, OverflowError):
            return SessionValidation(SessionValidationCode.INVALID_INPUT)
        if not (_bounded(session_id, max_length=64) and _bounded(session_secret, max_length=256)
                and _bounded(customer_id, max_length=64)):
            return SessionValidation(SessionValidationCode.INVALID_INPUT)
        connection: sqlite3.Connection | None = None
        try:
            connection = open_connection(self.database_path, timeout_ms=self.busy_timeout_ms)
            _required_auth_tables(connection)
            record = session_from_connection(connection, session_id)
            customer = customer_from_connection(connection, customer_id)
            if record is None or customer is None:
                return SessionValidation(SessionValidationCode.MISSING)
            if record.session.customer_id != customer_id:
                return SessionValidation(SessionValidationCode.INELIGIBLE)
            expected = record.session_secret_hash.get_secret_value()
            if not hmac.compare_digest(expected, _hash_secret(session_secret)):
                return SessionValidation(SessionValidationCode.INVALID_SECRET)
            if evaluate_session(record, customer, now=now) is not SessionPolicyStatus.ELIGIBLE:
                return SessionValidation(SessionValidationCode.INELIGIBLE)
            projection = safe_session_projection(record, customer, now=now)
            return SessionValidation(SessionValidationCode.VALID, projection)
        except (PersistenceError, sqlite3.Error, OSError):
            return SessionValidation(SessionValidationCode.STORAGE_UNAVAILABLE)
        finally:
            if connection is not None:
                connection.close()

    def revoke_session(
        self, session_id: str, *, now: datetime, actor_ref: str, correlation_id: str,
    ) -> RevocationResult:
        try:
            require_utc(now)
        except (TypeError, ValueError, AttributeError, OverflowError):
            raise SessionServiceError("revocation denied") from None
        if not (_bounded(session_id, max_length=64) and _bounded(actor_ref) and _bounded(correlation_id)):
            raise SessionServiceError("revocation denied")
        connection: sqlite3.Connection | None = None
        try:
            connection = open_connection(self.database_path, timeout_ms=self.busy_timeout_ms)
            connection.execute("BEGIN IMMEDIATE")
            _required_auth_tables(connection)
            record = session_from_connection(connection, session_id)
            if record is None:
                raise KeyError(session_id)
            if record.session.customer_id != actor_ref:
                raise SessionServiceError("revocation denied")
            if record.session.revoked_at is not None:
                connection.commit()
                return RevocationResult("ALREADY_REVOKED")
            updated = record.session.model_copy(update={"revoked_at": now})
            PrivateSessionRecord.model_validate(record.model_copy(update={"session": updated}))
            connection.execute("UPDATE shopping_sessions SET session_json=? WHERE session_id=?",
                               (updated.model_dump_json(), session_id))
            connection.execute(
                "INSERT OR REPLACE INTO shopping_session_revocations(session_id,revoked_at) VALUES(?,?)",
                (session_id, _utc(now)),
            )
            _audit(connection, event_id=self._event_id_factory(), actor_ref=actor_ref,
                   resource_ref=session_id, action="SESSION_REVOKE", outcome="APPLIED",
                   correlation_id=correlation_id, occurred_at=now,
                   failure_hook=self._audit_failure_hook)
            connection.commit()
            return RevocationResult("REVOKED")
        except KeyError:
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise SessionServiceError("session not found") from None
        except (AuditPersistenceError, SessionServiceError):
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise
        except (PersistenceError, sqlite3.Error, OSError):
            if connection is not None and connection.in_transaction:
                connection.rollback()
            raise StorageUnavailable("authentication persistence is unavailable") from None
        finally:
            if connection is not None:
                connection.close()
