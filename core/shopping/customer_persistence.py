"""Explicit, isolated persistence for trusted customer/session records.

This module is a storage foundation only. It does not authenticate a caller,
issue a session, verify a contact, or authorize an inquiry. Schema creation is
explicit so constructing a repository never migrates an existing database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Callable

from core.shopping.customer_identity import Customer
from core.shopping.customer_sessions import (
    CustomerSession, PrivateSessionRecord, SessionPolicyStatus, evaluate_session,
)


# v1 remains the historical B3 schema described by migration_contract.py.
# A database must be explicitly provisioned as v2 before durable verification
# authority may be used; opening v1 never performs an implicit migration.
SCHEMA_VERSION = "shopping-customer-persistence/v2"
HISTORICAL_SCHEMA_VERSION = "shopping-customer-persistence/v1"
CURRENT_SCHEMA_VERSION = SCHEMA_VERSION
BUSY_TIMEOUT_MS = 750
FailureHook = Callable[[str], None]


class PersistenceError(RuntimeError):
    """Base class for sanitized persistence failures."""


class PersistenceSchemaError(PersistenceError):
    pass


class StorageUnavailable(PersistenceError):
    pass


class OwnershipConflict(PersistenceError):
    pass


class InquiryVersionConflict(PersistenceError):
    pass


class IdempotencyConflict(PersistenceError):
    pass


class AuthorizationConflict(PersistenceError):
    pass


def _utc(value: datetime) -> str:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _open(path: str | Path, *, timeout_ms: int = BUSY_TIMEOUT_MS) -> sqlite3.Connection:
    connection = sqlite3.connect(str(path), timeout=timeout_ms / 1000, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(f"PRAGMA busy_timeout={int(timeout_ms)}")
    _validate_schema(connection)
    return connection


def open_connection(path: str | Path, *, timeout_ms: int = BUSY_TIMEOUT_MS) -> sqlite3.Connection:
    """Open an already provisioned persistence database; never creates schema."""
    return _open(path, timeout_ms=timeout_ms)


def _validate_schema(connection: sqlite3.Connection) -> None:
    try:
        row = connection.execute(
            "SELECT version FROM shopping_customer_persistence_meta WHERE name='schema'"
        ).fetchone()
    except sqlite3.OperationalError:
        raise PersistenceSchemaError("persistence schema is not initialized") from None
    if row is None or row[0] != SCHEMA_VERSION:
        raise PersistenceSchemaError("unsupported persistence schema version")
    try:
        challenge_columns = {
            item[1] for item in connection.execute(
                "PRAGMA table_info(shopping_verification_challenges)"
            ).fetchall()
        }
    except sqlite3.OperationalError:
        raise PersistenceSchemaError("unsupported persistence schema shape") from None
    if "provider_start_status" not in challenge_columns:
        raise PersistenceSchemaError("unsupported persistence schema shape")


def initialize_schema(database_path: str | Path, *, timeout_ms: int = BUSY_TIMEOUT_MS) -> None:
    """Explicitly initialize a test-owned or separately provisioned database."""
    connection = sqlite3.connect(str(database_path), timeout=timeout_ms / 1000,
                                 isolation_level=None)
    try:
        connection.execute(f"PRAGMA busy_timeout={int(timeout_ms)}")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_customer_persistence_meta "
            "(name TEXT PRIMARY KEY, version TEXT NOT NULL)"
        )
        existing = connection.execute(
            "SELECT version FROM shopping_customer_persistence_meta WHERE name='schema'"
        ).fetchone()
        if existing is not None and existing[0] != SCHEMA_VERSION:
            raise PersistenceSchemaError("unsupported persistence schema version")
        connection.execute(
            "INSERT OR IGNORE INTO shopping_customer_persistence_meta(name,version) VALUES('schema',?)",
            (SCHEMA_VERSION,),
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_customers "
            "(customer_id TEXT PRIMARY KEY, payload TEXT NOT NULL, contact_ref TEXT, updated_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_sessions "
            "(session_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, session_json TEXT NOT NULL, "
            "secret_hash TEXT NOT NULL, policy_version TEXT NOT NULL, credential_bound_at TEXT NOT NULL, "
            "verified_contact_ref TEXT NOT NULL, contact_verified_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_session_revocations "
            "(session_id TEXT PRIMARY KEY, revoked_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_inquiry_ownership "
            "(inquiry_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, session_id TEXT NOT NULL, version INTEGER NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_inquiry_idempotency "
            "(inquiry_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, request_digest TEXT NOT NULL, "
            "message_id TEXT NOT NULL, result_version INTEGER NOT NULL, PRIMARY KEY(inquiry_id,idempotency_key))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_inquiry_audit "
            "(event_id TEXT PRIMARY KEY, actor_ref TEXT NOT NULL, resource_ref TEXT NOT NULL, action TEXT NOT NULL, "
            "outcome TEXT NOT NULL, correlation_id TEXT NOT NULL, occurred_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_verification_receipts "
            "(receipt_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, issuer_ref TEXT NOT NULL, "
            "browser_challenge TEXT NOT NULL, purpose TEXT NOT NULL, session_id TEXT NOT NULL, "
            "consumed_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_auth_audit "
            "(event_id TEXT PRIMARY KEY, actor_ref TEXT NOT NULL, resource_ref TEXT NOT NULL, "
            "action TEXT NOT NULL, outcome TEXT NOT NULL, correlation_id TEXT NOT NULL, occurred_at TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_verification_challenges "
            "(challenge_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, phone_binding TEXT NOT NULL, "
            "provider_source TEXT NOT NULL, provider_challenge_reference TEXT, "
            "provider_verification_id TEXT, replay_reference TEXT NOT NULL UNIQUE, "
            "purpose TEXT NOT NULL, browser_challenge TEXT NOT NULL, status TEXT NOT NULL, "
            "created_at TEXT NOT NULL, expires_at TEXT NOT NULL, provider_started_at TEXT, "
            "provider_expires_at TEXT, provider_start_status TEXT, "
            "receipt_id TEXT, start_claim_token TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 0, "
            "CHECK(status IN ('START_CLAIMED','START_UNKNOWN','STARTED','PENDING','VERIFIED','FAILED','EXPIRED')), "
            "CHECK(provider_start_status IN ('STARTED','PENDING') OR provider_start_status IS NULL), "
            "CHECK(version >= 0), UNIQUE(provider_source,provider_verification_id), UNIQUE(receipt_id))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_verification_attempts "
            "(attempt_id TEXT PRIMARY KEY, challenge_id TEXT NOT NULL, replay_reference TEXT NOT NULL UNIQUE, "
            "provider_source TEXT NOT NULL, provider_verification_id TEXT NOT NULL, phone_binding TEXT NOT NULL, "
            "outcome TEXT NOT NULL, attempted_at TEXT NOT NULL, provider_verified_at TEXT, "
            "provider_expires_at TEXT, receipt_id TEXT, "
            "CHECK(outcome IN ('SUCCESS','FAILED','EXPIRED','REJECTED')), "
            "FOREIGN KEY(challenge_id) REFERENCES shopping_verification_challenges(challenge_id), "
            "UNIQUE(provider_source,provider_verification_id), UNIQUE(receipt_id))"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS shopping_trusted_receipts "
            "(receipt_id TEXT PRIMARY KEY, challenge_id TEXT NOT NULL UNIQUE, attempt_id TEXT NOT NULL UNIQUE, "
            "customer_id TEXT NOT NULL, issuer_ref TEXT NOT NULL, browser_challenge TEXT NOT NULL, "
            "purpose TEXT NOT NULL, provider_source TEXT NOT NULL, provider_verification_id TEXT NOT NULL, "
            "phone_binding TEXT NOT NULL, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, "
            "lifecycle TEXT NOT NULL, consumed_at TEXT, version INTEGER NOT NULL DEFAULT 0, "
            "CHECK(lifecycle IN ('ISSUED','CONSUMED','REVOKED')), CHECK(version >= 0), "
            "FOREIGN KEY(challenge_id) REFERENCES shopping_verification_challenges(challenge_id), "
            "FOREIGN KEY(attempt_id) REFERENCES shopping_verification_attempts(attempt_id))"
        )
        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        connection.close()


def _customer_from_row(row: sqlite3.Row) -> Customer:
    return Customer.model_validate_json(row["payload"])


def _session_from_row(row: sqlite3.Row) -> PrivateSessionRecord:
    return PrivateSessionRecord(
        session=CustomerSession.model_validate_json(row["session_json"]),
        session_secret_hash=row["secret_hash"],
        security_policy_version=row["policy_version"],
        credential_bound_at=datetime.fromisoformat(row["credential_bound_at"].replace("Z", "+00:00")),
        verified_contact_ref=row["verified_contact_ref"],
        contact_verified_at=datetime.fromisoformat(row["contact_verified_at"].replace("Z", "+00:00")),
    )


def customer_from_connection(connection: sqlite3.Connection, customer_id: str) -> Customer | None:
    row = connection.execute(
        "SELECT payload FROM shopping_customers WHERE customer_id=?", (customer_id,)
    ).fetchone()
    return None if row is None else Customer.model_validate_json(row["payload"])


def session_from_connection(connection: sqlite3.Connection, session_id: str) -> PrivateSessionRecord | None:
    row = connection.execute(
        "SELECT * FROM shopping_sessions WHERE session_id=?", (session_id,)
    ).fetchone()
    if row is None:
        return None
    record = _session_from_row(row)
    revoked = connection.execute(
        "SELECT revoked_at FROM shopping_session_revocations WHERE session_id=?", (session_id,)
    ).fetchone()
    if revoked is not None:
        revoked_at = datetime.fromisoformat(revoked["revoked_at"].replace("Z", "+00:00"))
        if record.session.revoked_at is None or revoked_at < record.session.revoked_at:
            record = PrivateSessionRecord.model_validate(record.model_copy(update={
                "session": record.session.model_copy(update={"revoked_at": revoked_at}),
            }))
    return record


def persisted_session_status(connection: sqlite3.Connection, customer_id: str,
                             session_id: str, *, now: datetime) -> SessionPolicyStatus:
    customer = customer_from_connection(connection, customer_id)
    record = session_from_connection(connection, session_id)
    if customer is None or record is None:
        return SessionPolicyStatus.INVALID_RECORD
    return evaluate_session(record, customer, now=now)


class SQLiteCustomerSessionStore:
    """Durable customer/session metadata with explicit schema provisioning."""

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS):
        self.database_path = Path(database_path)
        self.busy_timeout_ms = busy_timeout_ms

    @staticmethod
    def initialize_schema(database_path: str | Path, *, timeout_ms: int = BUSY_TIMEOUT_MS) -> None:
        initialize_schema(database_path, timeout_ms=timeout_ms)

    def _writer(self) -> sqlite3.Connection:
        return _open(self.database_path, timeout_ms=self.busy_timeout_ms)

    def save_customer(self, customer: Customer, *, contact_ref: str | None = None) -> None:
        if type(customer) is not Customer:
            raise TypeError("customer record required")
        if contact_ref is not None and customer.contact_binding is not None and contact_ref != customer.contact_binding.contact_ref:
            raise ValueError("contact reference does not match customer binding")
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO shopping_customers(customer_id,payload,contact_ref,updated_at) VALUES(?,?,?,?) "
                "ON CONFLICT(customer_id) DO UPDATE SET payload=excluded.payload,contact_ref=excluded.contact_ref,updated_at=excluded.updated_at",
                (customer.id, customer.model_dump_json(), contact_ref,
                 _utc(customer.updated_at)),
            )
            connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def save_session(self, record: PrivateSessionRecord) -> None:
        if type(record) is not PrivateSessionRecord:
            raise TypeError("private session record required")
        session = record.session
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO shopping_sessions(session_id,customer_id,session_json,secret_hash,policy_version,credential_bound_at,verified_contact_ref,contact_verified_at) "
                "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET customer_id=excluded.customer_id,session_json=excluded.session_json,secret_hash=excluded.secret_hash,policy_version=excluded.policy_version,credential_bound_at=excluded.credential_bound_at,verified_contact_ref=excluded.verified_contact_ref,contact_verified_at=excluded.contact_verified_at",
                (session.id, session.customer_id, session.model_dump_json(),
                 record.session_secret_hash.get_secret_value(), record.security_policy_version,
                 _utc(record.credential_bound_at), record.verified_contact_ref,
                 _utc(record.contact_verified_at)),
            )
            connection.execute("DELETE FROM shopping_session_revocations WHERE session_id=?", (session.id,))
            if session.revoked_at is not None:
                connection.execute("INSERT OR REPLACE INTO shopping_session_revocations VALUES(?,?)",
                                   (session.id, _utc(session.revoked_at)))
            connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def revoke_session(self, session_id: str, *, revoked_at: datetime) -> None:
        connection = self._writer()
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT * FROM shopping_sessions WHERE session_id=?", (session_id,)).fetchone()
            if row is None:
                raise KeyError(session_id)
            record = _session_from_row(row)
            session = record.session.model_copy(update={"revoked_at": revoked_at})
            updated = PrivateSessionRecord.model_validate(record.model_copy(update={"session": session}))
            connection.execute(
                "UPDATE shopping_sessions SET session_json=? WHERE session_id=?",
                (updated.session.model_dump_json(), session_id),
            )
            connection.execute("INSERT OR REPLACE INTO shopping_session_revocations VALUES(?,?)",
                               (session_id, _utc(revoked_at)))
            connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    def get_customer(self, customer_id: str) -> Customer | None:
        connection = self._writer()
        try:
            return customer_from_connection(connection, customer_id)
        finally:
            connection.close()

    def get_session(self, session_id: str) -> PrivateSessionRecord | None:
        connection = self._writer()
        try:
            return session_from_connection(connection, session_id)
        finally:
            connection.close()


VERIFICATION_SCHEMA_TABLES = (
    "shopping_verification_challenges",
    "shopping_verification_attempts",
    "shopping_trusted_receipts",
)


class SQLiteVerificationRepository:
    """Explicit SQLite boundary for durable verification authority.

    The repository deliberately exposes connections instead of hiding the
    transaction.  TX1 and TX2 must include their own validation, projection,
    and audit work in one ``BEGIN IMMEDIATE`` transaction.
    """

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = BUSY_TIMEOUT_MS):
        self.database_path = Path(database_path)
        self.busy_timeout_ms = busy_timeout_ms

    @staticmethod
    def initialize_schema(database_path: str | Path, *, timeout_ms: int = BUSY_TIMEOUT_MS) -> None:
        initialize_schema(database_path, timeout_ms=timeout_ms)

    def open(self) -> sqlite3.Connection:
        return open_connection(self.database_path, timeout_ms=self.busy_timeout_ms)


# Naming aliases make the approved persistence boundary discoverable without
# introducing a second framework or a second implementation.
DurableVerificationRepository = SQLiteVerificationRepository
VerificationRepository = SQLiteVerificationRepository
PhoneVerificationRepository = SQLiteVerificationRepository
