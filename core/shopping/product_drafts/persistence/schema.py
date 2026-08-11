"""Explicit, versioned SQLite schema for Shopping ProductDraft state."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import hashlib
import re
from typing import Final
from urllib.parse import quote
from .path_policy import DatabasePathPolicy, DEFAULT_DURABLE_PATH_POLICY

APPLICATION_ID: Final[int] = 0x53485044  # SHPD
SCHEMA_VERSION: Final[int] = 1
BUSY_TIMEOUT_MS: Final[int] = 2500


class ShoppingDatabaseError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ShoppingDatabaseStatus:
    application_id: int
    user_version: int
    journal_mode: str
    foreign_keys_enabled: bool
    quick_check: str
    objects: tuple[str, ...]


def connect_database(path: str | Path, *, read_only: bool = False,
                     busy_timeout_ms: int = BUSY_TIMEOUT_MS,
                     path_policy: DatabasePathPolicy = DEFAULT_DURABLE_PATH_POLICY) -> sqlite3.Connection:
    if not isinstance(busy_timeout_ms, int) or not 1 <= busy_timeout_ms <= 30000:
        raise ValueError("busy_timeout_ms must be in the bounded range [1, 30000]")
    database = Path(path) if read_only else path_policy.validate(path)
    if read_only:
        if not database.is_file():
            raise ShoppingDatabaseError("shopping database does not exist")
        uri = "file:" + quote(str(database.resolve()), safe="/") + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True, timeout=busy_timeout_ms / 1000,
                                     isolation_level=None)
    else:
        if not database.parent.is_dir():
            raise ShoppingDatabaseError("database parent directory must already exist")
        connection = sqlite3.connect(database, timeout=busy_timeout_ms / 1000,
                                     isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA busy_timeout = {busy_timeout_ms}")
    if read_only:
        connection.execute("PRAGMA query_only = ON")
    else:
        mode = str(connection.execute("PRAGMA journal_mode = WAL").fetchone()[0]).upper()
        if mode != "WAL":
            connection.close()
            raise ShoppingDatabaseError("SQLite WAL mode is required")
        connection.execute("PRAGMA synchronous = FULL")
    return connection


SCHEMA_SQL = """
CREATE TABLE schema_metadata (
 schema_version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL, component TEXT NOT NULL
);
CREATE TABLE product_draft_revisions (
 draft_id TEXT NOT NULL, revision_id TEXT NOT NULL, revision_number INTEGER NOT NULL CHECK(revision_number >= 1),
 previous_revision_id TEXT, revision_json TEXT NOT NULL CHECK(json_valid(revision_json)),
 revision_digest TEXT NOT NULL CHECK(revision_digest GLOB 'sha256:[0-9a-f]*' AND length(revision_digest)=71),
 lifecycle_state TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 PRIMARY KEY(draft_id, revision_id), UNIQUE(draft_id, revision_number),
 FOREIGN KEY(draft_id, previous_revision_id) REFERENCES product_draft_revisions(draft_id, revision_id),
 CHECK((revision_number=1 AND previous_revision_id IS NULL) OR (revision_number>1 AND previous_revision_id IS NOT NULL))
) WITHOUT ROWID;
CREATE INDEX product_draft_revisions_current ON product_draft_revisions(draft_id, revision_number DESC);
CREATE TRIGGER product_draft_revision_identity_immutable BEFORE UPDATE ON product_draft_revisions
WHEN OLD.draft_id != NEW.draft_id OR OLD.revision_id != NEW.revision_id OR OLD.revision_number != NEW.revision_number
 OR OLD.previous_revision_id IS NOT NEW.previous_revision_id OR OLD.created_at != NEW.created_at
BEGIN SELECT RAISE(ABORT, 'ProductDraft identity and chain are immutable'); END;
CREATE TABLE product_draft_generation_operations (
 operation_key TEXT PRIMARY KEY, command_digest TEXT NOT NULL
   CHECK(substr(command_digest,1,7)='sha256:' AND length(command_digest)=71 AND substr(command_digest,8) NOT GLOB '*[^0-9a-f]*'),
 state TEXT NOT NULL CHECK(state IN ('CLAIMED','COMPLETED','TERMINAL_FAILED')),
 claimed_at TEXT NOT NULL, terminal_at TEXT, draft_id TEXT NOT NULL, revision_id TEXT NOT NULL,
 failure_code TEXT,
 CHECK((state='CLAIMED' AND terminal_at IS NULL AND failure_code IS NULL)
    OR (state='COMPLETED' AND terminal_at IS NOT NULL AND failure_code IS NULL)
    OR (state='TERMINAL_FAILED' AND terminal_at IS NOT NULL AND failure_code IS NOT NULL))
) WITHOUT ROWID;
CREATE TRIGGER product_draft_generation_operation_transition BEFORE UPDATE ON product_draft_generation_operations
WHEN OLD.operation_key != NEW.operation_key OR OLD.command_digest != NEW.command_digest
 OR OLD.claimed_at != NEW.claimed_at OR OLD.draft_id != NEW.draft_id OR OLD.revision_id != NEW.revision_id
 OR OLD.state != 'CLAIMED'
 OR NEW.state NOT IN ('COMPLETED','TERMINAL_FAILED')
BEGIN SELECT RAISE(ABORT, 'generation operation transition is immutable or invalid'); END;
CREATE TRIGGER product_draft_generation_operation_deny_delete BEFORE DELETE ON product_draft_generation_operations
BEGIN SELECT RAISE(ABORT, 'generation operation cannot be deleted'); END;
CREATE TABLE product_draft_generation_audit_events (
 event_id TEXT PRIMARY KEY, operation_key TEXT NOT NULL UNIQUE, event_type TEXT NOT NULL,
 draft_id TEXT NOT NULL, revision_id TEXT NOT NULL, actor_reference TEXT NOT NULL,
 correlation_reference TEXT NOT NULL, audit_reference TEXT NOT NULL, occurred_at TEXT NOT NULL,
 outcome TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, provider_request_id TEXT,
 response_digest TEXT NOT NULL, revision_digest TEXT NOT NULL,
 FOREIGN KEY(operation_key) REFERENCES product_draft_generation_operations(operation_key),
 FOREIGN KEY(draft_id, revision_id) REFERENCES product_draft_revisions(draft_id, revision_id)
) WITHOUT ROWID;
CREATE TRIGGER product_draft_generation_audit_immutable BEFORE UPDATE ON product_draft_generation_audit_events
BEGIN SELECT RAISE(ABORT, 'generation audit is immutable'); END;
CREATE TRIGGER product_draft_generation_audit_deny_delete BEFORE DELETE ON product_draft_generation_audit_events
BEGIN SELECT RAISE(ABORT, 'generation audit cannot be deleted'); END;
CREATE TABLE product_draft_transition_idempotency (
 draft_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, command_digest TEXT NOT NULL,
 result_json TEXT NOT NULL CHECK(json_valid(result_json)), PRIMARY KEY(draft_id,idempotency_key)
) WITHOUT ROWID;
"""


def _execute_schema(connection: sqlite3.Connection) -> None:
    statement = ""
    for line in SCHEMA_SQL.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            connection.execute(statement)
            statement = ""
    if statement.strip():
        raise ShoppingDatabaseError("incomplete Shopping schema statement")


def initialize_database(path: str | Path, *, applied_at: str | None = None,
                        busy_timeout_ms: int = BUSY_TIMEOUT_MS,
                        path_policy: DatabasePathPolicy = DEFAULT_DURABLE_PATH_POLICY) -> None:
    connection = connect_database(path, busy_timeout_ms=busy_timeout_ms, path_policy=path_policy)
    try:
        app_id = int(connection.execute("PRAGMA application_id").fetchone()[0])
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if app_id not in (0, APPLICATION_ID):
            raise ShoppingDatabaseError("database belongs to another application")
        if version > SCHEMA_VERSION:
            raise ShoppingDatabaseError("database schema is newer than supported")
        if version == SCHEMA_VERSION:
            validate_database(connection)
            return
        if version != 0:
            raise ShoppingDatabaseError(f"unsupported shopping schema version: {version}")
        existing = connection.execute("SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchone()
        if existing is not None:
            raise ShoppingDatabaseError("unversioned non-empty database cannot be migrated silently")
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            _execute_schema(connection)
            stamp = applied_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            connection.execute("INSERT INTO schema_metadata VALUES (?,?,?)", (1, stamp, "SHOP-AI-01B2"))
            connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        validate_database(connection)
    finally:
        connection.close()


def inspect_database(connection: sqlite3.Connection) -> ShoppingDatabaseStatus:
    objects = tuple(sorted(row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type IN ('table','index','trigger') AND name NOT LIKE 'sqlite_%'")))
    return ShoppingDatabaseStatus(
        int(connection.execute("PRAGMA application_id").fetchone()[0]),
        int(connection.execute("PRAGMA user_version").fetchone()[0]),
        str(connection.execute("PRAGMA journal_mode").fetchone()[0]).upper(),
        bool(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
        ",".join(str(row[0]) for row in connection.execute("PRAGMA quick_check")), objects)


def validate_database(connection: sqlite3.Connection) -> ShoppingDatabaseStatus:
    status = inspect_database(connection)
    failures = []
    if status.application_id != APPLICATION_ID: failures.append("application_id")
    if status.user_version != SCHEMA_VERSION: failures.append("user_version")
    if status.quick_check != "ok": failures.append("quick_check")
    if status.journal_mode != "WAL": failures.append("journal_mode")
    if not status.foreign_keys_enabled: failures.append("foreign_keys")
    if _actual_schema_digest(connection) != EXPECTED_SCHEMA_DIGEST: failures.append("schema_definitions")
    metadata = tuple(tuple(row) for row in connection.execute(
        "SELECT schema_version,component FROM schema_metadata ORDER BY schema_version"))
    if metadata != ((SCHEMA_VERSION, "SHOP-AI-01B2"),): failures.append("schema_metadata")
    if failures:
        raise ShoppingDatabaseError("shopping database validation failed: " + ",".join(failures))
    return status


def _normalize_schema_sql(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def _schema_definitions(connection: sqlite3.Connection) -> tuple[tuple[str, str, str], ...]:
    return tuple((row[0], row[1], _normalize_schema_sql(row[2])) for row in connection.execute(
        "SELECT type,name,sql FROM sqlite_master WHERE type IN ('table','index','trigger') "
        "AND name NOT LIKE 'sqlite_%' ORDER BY type,name") if row[2] is not None)


def _schema_digest(definitions: tuple[tuple[str, str, str], ...]) -> str:
    material = "\n".join("|".join(item) for item in definitions).encode()
    return "sha256:" + hashlib.sha256(material).hexdigest()


def _expected_schema_digest() -> str:
    connection = sqlite3.connect(":memory:")
    try:
        _execute_schema(connection)
        return _schema_digest(_schema_definitions(connection))
    finally:
        connection.close()


EXPECTED_SCHEMA_DIGEST: Final[str] = _expected_schema_digest()


def _actual_schema_digest(connection: sqlite3.Connection) -> str:
    return _schema_digest(_schema_definitions(connection))
