"""Exact, non-migrating schema for protected-evidence acquisition consumption."""

import re
import sqlite3

APPLICATION_ID = 0x50454143  # PEAC
USER_VERSION = 1
DDL = """
CREATE TABLE protected_evidence_acquisition_authorization_consumptions (
    authorization_id TEXT PRIMARY KEY NOT NULL,
    acquisition_request_id TEXT NOT NULL UNIQUE,
    fixed_source_slot_identity TEXT NOT NULL,
    concrete_source_location_identity TEXT NOT NULL,
    leaf_basename TEXT NOT NULL,
    concrete_leaf_path TEXT NOT NULL,
    maximum_acquisition_attempts INTEGER NOT NULL CHECK (maximum_acquisition_attempts = 1),
    binding_digest TEXT NOT NULL,
    barrier_state TEXT NOT NULL CHECK (barrier_state IN ('DURABLY_CLAIMED', 'COMMITTED')),
    committed_json TEXT,
    committed_digest TEXT,
    CHECK (
        (barrier_state = 'DURABLY_CLAIMED' AND committed_json IS NULL AND committed_digest IS NULL)
        OR
        (barrier_state = 'COMMITTED' AND committed_json IS NOT NULL AND committed_digest IS NOT NULL)
    )
) STRICT;
"""


class ProtectedEvidenceAcquisitionSQLiteSchemaError(RuntimeError):
    pass


def _normalized(value: str | None) -> str | None:
    return None if value is None else re.sub(r"\s+", " ", value.strip()).replace("( ", "(").replace(" )", ")")


def schema_fingerprint(connection: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (row[0], row[1], row[2], _normalized(row[3]))
        for row in connection.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name")
        if row[1] != "sqlite_sequence"
    )


with sqlite3.connect(":memory:") as _expected:
    _expected.executescript(DDL)
    SUPPORTED_SCHEMA_FINGERPRINT = schema_fingerprint(_expected)


def initialize_or_validate_schema(connection: sqlite3.Connection) -> None:
    try:
        app_id = connection.execute("PRAGMA application_id").fetchone()[0]
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        objects = connection.execute("SELECT name,type FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%'").fetchall()
        if not objects:
            if (app_id, version) != (0, 0):
                raise ProtectedEvidenceAcquisitionSQLiteSchemaError("foreign empty database cannot be adopted")
            connection.executescript(DDL)
            connection.execute(f"PRAGMA application_id={APPLICATION_ID}")
            connection.execute(f"PRAGMA user_version={USER_VERSION}")
            app_id, version = APPLICATION_ID, USER_VERSION
        if (app_id, version) != (APPLICATION_ID, USER_VERSION):
            raise ProtectedEvidenceAcquisitionSQLiteSchemaError("foreign database identity")
        expected_object = [("protected_evidence_acquisition_authorization_consumptions", "table")]
        if objects and objects != expected_object:
            raise ProtectedEvidenceAcquisitionSQLiteSchemaError("unknown schema objects")
        if schema_fingerprint(connection) != SUPPORTED_SCHEMA_FINGERPRINT:
            raise ProtectedEvidenceAcquisitionSQLiteSchemaError("schema fingerprint mismatch")
        if tuple(connection.execute("PRAGMA integrity_check")) != (("ok",),):
            raise ProtectedEvidenceAcquisitionSQLiteSchemaError("database integrity failure")
    except sqlite3.DatabaseError as exc:
        raise ProtectedEvidenceAcquisitionSQLiteSchemaError("schema is unreadable") from exc


__all__ = ("APPLICATION_ID", "USER_VERSION", "DDL", "SUPPORTED_SCHEMA_FINGERPRINT", "ProtectedEvidenceAcquisitionSQLiteSchemaError", "initialize_or_validate_schema")
