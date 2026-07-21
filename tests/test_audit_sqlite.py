import sqlite3
from pathlib import Path

import pytest

from core.governance.audit_sqlite import (
    APPLICATION_ID,
    SCHEMA_VERSION,
    AuditDatabaseError,
    connect_database,
    inspect_database,
    migrate_database,
    validate_database,
)


SOURCE_COMMIT = "38e01394222e0ff1e302c50ab7ecc1b3f48bca8a"
APPLIED_AT = "2026-07-21T13:00:00Z"


def create_database(path: Path) -> sqlite3.Connection:
    connection = connect_database(path)

    migrate_database(
        connection,
        application_commit=SOURCE_COMMIT,
        applied_at=APPLIED_AT,
    )

    return connection


def test_migration_creates_schema(tmp_path: Path) -> None:
    connection = create_database(
        tmp_path / "audit.sqlite3"
    )

    try:
        status = validate_database(connection)

        assert status.application_id == APPLICATION_ID
        assert status.user_version == SCHEMA_VERSION
        assert status.journal_mode == "WAL"
        assert status.foreign_keys_enabled is True
        assert status.quick_check == "ok"

        assert "schema_metadata" in status.tables
        assert "audit_snapshots" in status.tables

        assert (
            "idx_audit_snapshots_captured_at"
            in status.indexes
        )

        assert (
            "idx_audit_snapshots_source_commit"
            in status.indexes
        )

        assert (
            "deny_audit_snapshot_update"
            in status.triggers
        )

        assert (
            "deny_audit_snapshot_delete"
            in status.triggers
        )
    finally:
        connection.close()


def test_migration_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "audit.sqlite3"

    connection = create_database(path)

    try:
        migrate_database(
            connection,
            application_commit=SOURCE_COMMIT,
            applied_at=APPLIED_AT,
        )

        rows = connection.execute(
            "SELECT COUNT(*) FROM schema_metadata"
        ).fetchone()[0]

        assert rows == 1
    finally:
        connection.close()


def test_update_trigger_denies_mutation(
    tmp_path: Path,
) -> None:
    connection = create_database(
        tmp_path / "audit.sqlite3"
    )

    try:
        connection.execute(
            """
            INSERT INTO audit_snapshots (
                snapshot_id,
                captured_at,
                source_commit,
                runtime_release,
                governance_json,
                summary_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "a" * 64,
                "2026-07-21T13:00:00Z",
                "b" * 40,
                "c" * 12,
                "{}",
                "{}",
                "2026-07-21T13:00:00Z",
            ),
        )
        connection.commit()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="immutable",
        ):
            connection.execute(
                """
                UPDATE audit_snapshots
                SET captured_at = ?
                WHERE snapshot_id = ?
                """,
                (
                    "2026-07-21T14:00:00Z",
                    "a" * 64,
                ),
            )
    finally:
        connection.close()


def test_delete_trigger_denies_mutation(
    tmp_path: Path,
) -> None:
    connection = create_database(
        tmp_path / "audit.sqlite3"
    )

    try:
        connection.execute(
            """
            INSERT INTO audit_snapshots (
                snapshot_id,
                captured_at,
                source_commit,
                runtime_release,
                governance_json,
                summary_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "a" * 64,
                "2026-07-21T13:00:00Z",
                "b" * 40,
                "c" * 12,
                "{}",
                "{}",
                "2026-07-21T13:00:00Z",
            ),
        )
        connection.commit()

        with pytest.raises(
            sqlite3.IntegrityError,
            match="cannot be deleted",
        ):
            connection.execute(
                """
                DELETE FROM audit_snapshots
                WHERE snapshot_id = ?
                """,
                ("a" * 64,),
            )
    finally:
        connection.close()


def test_newer_schema_version_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite3"
    connection = connect_database(path)

    try:
        connection.execute(
            f"PRAGMA application_id = {APPLICATION_ID}"
        )
        connection.execute(
            f"PRAGMA user_version = {SCHEMA_VERSION + 1}"
        )

        with pytest.raises(
            AuditDatabaseError,
            match="newer than supported",
        ):
            migrate_database(
                connection,
                application_commit=SOURCE_COMMIT,
                applied_at=APPLIED_AT,
            )
    finally:
        connection.close()


def test_foreign_application_id_fails_closed(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite3"
    connection = connect_database(path)

    try:
        connection.execute(
            "PRAGMA application_id = 123456789"
        )

        with pytest.raises(
            AuditDatabaseError,
            match="another application",
        ):
            migrate_database(
                connection,
                application_commit=SOURCE_COMMIT,
                applied_at=APPLIED_AT,
            )
    finally:
        connection.close()


def test_missing_trigger_is_detected(
    tmp_path: Path,
) -> None:
    connection = create_database(
        tmp_path / "audit.sqlite3"
    )

    try:
        connection.execute(
            "DROP TRIGGER deny_audit_snapshot_delete"
        )

        with pytest.raises(
            AuditDatabaseError,
            match="triggers",
        ):
            validate_database(connection)
    finally:
        connection.close()


def test_read_only_connection_can_inspect(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.sqlite3"

    connection = create_database(path)
    connection.close()

    read_only = connect_database(
        path,
        read_only=True,
    )

    try:
        status = inspect_database(read_only)

        assert status.application_id == APPLICATION_ID
        assert status.user_version == SCHEMA_VERSION

        with pytest.raises(sqlite3.OperationalError):
            read_only.execute(
                """
                INSERT INTO schema_metadata (
                    schema_version,
                    applied_at,
                    application_commit
                )
                VALUES (?, ?, ?)
                """,
                (
                    2,
                    APPLIED_AT,
                    SOURCE_COMMIT,
                ),
            )
    finally:
        read_only.close()
