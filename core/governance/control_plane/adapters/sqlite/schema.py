"""Initial, deliberately non-migrating SQLite schema."""

from __future__ import annotations

import sqlite3
import re

APPLICATION_ID = 0x41494343
USER_VERSION = 1

DDL = """
CREATE TABLE authorization_consumptions (
    lifecycle_id TEXT PRIMARY KEY NOT NULL,
    authorization_id TEXT NOT NULL UNIQUE,
    mutation_budget_id TEXT NOT NULL UNIQUE,
    claim_id TEXT NOT NULL UNIQUE,
    execution_request_id TEXT NOT NULL UNIQUE,
    authorization_request_id TEXT NOT NULL UNIQUE,
    authorization_decision_id TEXT NOT NULL UNIQUE,
    consumption_binding_digest TEXT NOT NULL,
    binding_json TEXT NOT NULL,
    barrier_state TEXT NOT NULL CHECK (barrier_state IN ('DURABLY_CLAIMED', 'COMMITTED')),
    committed_json TEXT,
    integrity_hash TEXT,
    CHECK (
        (barrier_state = 'DURABLY_CLAIMED' AND committed_json IS NULL AND integrity_hash IS NULL)
        OR
        (barrier_state = 'COMMITTED' AND committed_json IS NOT NULL AND integrity_hash IS NOT NULL)
    )
) STRICT;
"""


class SQLiteSchemaError(RuntimeError):
    """The evidence store schema cannot be trusted."""


def _normalized_sql(value: str | None) -> str | None:
    if value is None:
        return None
    return re.sub(r"\s+", " ", value.strip()).replace("( ", "(").replace(" )", ")")


def _schema_fingerprint(connection: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (row[0], row[1], row[2], _normalized_sql(row[3]))
        for row in connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_schema ORDER BY type, name"
        )
        if row[1] != "sqlite_sequence"
    )


def _supported_fingerprint() -> tuple[tuple[object, ...], ...]:
    with sqlite3.connect(":memory:") as expected:
        expected.executescript(DDL)
        return _schema_fingerprint(expected)


SUPPORTED_SCHEMA_FINGERPRINT = _supported_fingerprint()


def initialize_or_validate_schema(connection: sqlite3.Connection) -> None:
    try:
        application_id = connection.execute("PRAGMA application_id").fetchone()[0]
        user_version = connection.execute("PRAGMA user_version").fetchone()[0]
        objects = connection.execute(
            "SELECT name, type FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'"
        ).fetchall()
        if not objects:
            if application_id != 0 or user_version != 0:
                raise SQLiteSchemaError("empty foreign SQLite database cannot be adopted")
            connection.executescript(DDL)
            connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
            connection.execute(f"PRAGMA user_version = {USER_VERSION}")
            application_id, user_version = APPLICATION_ID, USER_VERSION
            objects = [("authorization_consumptions", "table")]
        if application_id != APPLICATION_ID or user_version != USER_VERSION:
            raise SQLiteSchemaError("unsupported SQLite application/schema version")
        if set(objects) != {("authorization_consumptions", "table")}:
            raise SQLiteSchemaError("SQLite schema contains unsupported objects")
        if _schema_fingerprint(connection) != SUPPORTED_SCHEMA_FINGERPRINT:
            raise SQLiteSchemaError("authorization consumption schema fingerprint is inconsistent")
        columns = tuple(connection.execute("PRAGMA table_info(authorization_consumptions)"))
        if not columns or columns[0][1:] != ("lifecycle_id", "TEXT", 1, None, 1):
            raise SQLiteSchemaError("lifecycle primary key is inconsistent")
        if any(row[3] != 1 for row in columns[:10]):
            raise SQLiteSchemaError("required NOT NULL semantics are inconsistent")
        table_list = tuple(connection.execute("PRAGMA table_list('authorization_consumptions')"))
        if len(table_list) != 1 or table_list[0][5] != 1:
            raise SQLiteSchemaError("authorization consumption table must be STRICT")
        unique_origins = sorted(
            row[3] for row in connection.execute("PRAGMA index_list('authorization_consumptions')")
            if row[2] == 1
        )
        if unique_origins != ["pk", "u", "u", "u", "u", "u", "u"]:
            raise SQLiteSchemaError("independent identity uniqueness is inconsistent")
        integrity = tuple(connection.execute("PRAGMA integrity_check"))
        if integrity != (("ok",),):
            raise SQLiteSchemaError("SQLite integrity check failed")
    except sqlite3.DatabaseError as exc:
        raise SQLiteSchemaError("SQLite schema is corrupt or unreadable") from exc


__all__ = ("APPLICATION_ID", "USER_VERSION", "SQLiteSchemaError", "initialize_or_validate_schema")
