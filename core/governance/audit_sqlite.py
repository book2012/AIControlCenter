"""SQLite schema and integrity controls for governance audit snapshots."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Final


APPLICATION_ID: Final[int] = 1094927172
SCHEMA_VERSION: Final[int] = 1
BUSY_TIMEOUT_MS: Final[int] = 5000

_REQUIRED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "schema_metadata",
        "audit_snapshots",
    }
)

_REQUIRED_INDEXES: Final[frozenset[str]] = frozenset(
    {
        "idx_audit_snapshots_captured_at",
        "idx_audit_snapshots_source_commit",
    }
)

_REQUIRED_TRIGGERS: Final[frozenset[str]] = frozenset(
    {
        "deny_audit_snapshot_update",
        "deny_audit_snapshot_delete",
    }
)


class AuditDatabaseError(RuntimeError):
    """Raised when the audit database violates its contract."""


@dataclass(frozen=True)
class AuditDatabaseStatus:
    """Read-only database integrity status."""

    application_id: int
    user_version: int
    journal_mode: str
    foreign_keys_enabled: bool
    quick_check: str
    tables: tuple[str, ...]
    indexes: tuple[str, ...]
    triggers: tuple[str, ...]


def connect_database(
    path: str | Path,
    *,
    read_only: bool = False,
) -> sqlite3.Connection:
    """Open a configured SQLite connection."""

    database_path = Path(path).expanduser()

    if read_only:
        uri = database_path.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(
            uri,
            uri=True,
            timeout=BUSY_TIMEOUT_MS / 1000,
        )
    else:
        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        connection = sqlite3.connect(
            database_path,
            timeout=BUSY_TIMEOUT_MS / 1000,
        )

    connection.row_factory = sqlite3.Row

    connection.execute(
        f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}"
    )
    connection.execute("PRAGMA foreign_keys = ON")

    if not read_only:
        journal_mode = connection.execute(
            "PRAGMA journal_mode = WAL"
        ).fetchone()[0]

        if str(journal_mode).upper() != "WAL":
            connection.close()
            raise AuditDatabaseError(
                "SQLite WAL mode could not be enabled"
            )

        connection.execute("PRAGMA synchronous = NORMAL")

    return connection


def _create_schema_v1(
    connection: sqlite3.Connection,
    *,
    application_commit: str,
    applied_at: str,
) -> None:
    connection.executescript(
        """
        CREATE TABLE schema_metadata (
            schema_version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            application_commit TEXT NOT NULL
        );

        CREATE TABLE audit_snapshots (
            snapshot_id TEXT PRIMARY KEY
                CHECK(length(snapshot_id) = 64)
                CHECK(snapshot_id = lower(snapshot_id)),
            captured_at TEXT NOT NULL,
            source_commit TEXT NOT NULL
                CHECK(length(source_commit) = 40)
                CHECK(source_commit = lower(source_commit)),
            runtime_release TEXT NOT NULL
                CHECK(length(runtime_release) = 12)
                CHECK(runtime_release = lower(runtime_release)),
            governance_json TEXT NOT NULL
                CHECK(json_valid(governance_json)),
            summary_json TEXT NOT NULL
                CHECK(json_valid(summary_json)),
            created_at TEXT NOT NULL
        ) WITHOUT ROWID;

        CREATE INDEX idx_audit_snapshots_captured_at
            ON audit_snapshots(captured_at DESC);

        CREATE INDEX idx_audit_snapshots_source_commit
            ON audit_snapshots(source_commit ASC);

        CREATE TRIGGER deny_audit_snapshot_update
        BEFORE UPDATE ON audit_snapshots
        BEGIN
            SELECT RAISE(
                ABORT,
                'audit snapshots are immutable'
            );
        END;

        CREATE TRIGGER deny_audit_snapshot_delete
        BEFORE DELETE ON audit_snapshots
        BEGIN
            SELECT RAISE(
                ABORT,
                'audit snapshots cannot be deleted'
            );
        END;
        """
    )

    connection.execute(
        """
        INSERT INTO schema_metadata (
            schema_version,
            applied_at,
            application_commit
        )
        VALUES (?, ?, ?)
        """,
        (
            SCHEMA_VERSION,
            applied_at,
            application_commit,
        ),
    )


def migrate_database(
    connection: sqlite3.Connection,
    *,
    application_commit: str,
    applied_at: str,
) -> None:
    """Create or validate the supported schema."""

    current_application_id = connection.execute(
        "PRAGMA application_id"
    ).fetchone()[0]

    current_version = connection.execute(
        "PRAGMA user_version"
    ).fetchone()[0]

    if current_application_id not in (
        0,
        APPLICATION_ID,
    ):
        raise AuditDatabaseError(
            "database application_id belongs to another application"
        )

    if current_version > SCHEMA_VERSION:
        raise AuditDatabaseError(
            "database schema version is newer than supported"
        )

    if current_version == SCHEMA_VERSION:
        validate_database(connection)
        return

    if current_version != 0:
        raise AuditDatabaseError(
            f"unsupported audit schema version: {current_version}"
        )

    try:
        connection.execute("BEGIN IMMEDIATE")

        connection.execute(
            f"PRAGMA application_id = {APPLICATION_ID}"
        )

        _create_schema_v1(
            connection,
            application_commit=application_commit,
            applied_at=applied_at,
        )

        connection.execute(
            f"PRAGMA user_version = {SCHEMA_VERSION}"
        )

        connection.commit()
    except Exception:
        connection.rollback()
        raise

    validate_database(connection)


def _object_names(
    connection: sqlite3.Connection,
    object_type: str,
) -> frozenset[str]:
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = ?
          AND name NOT LIKE 'sqlite_%'
        """,
        (object_type,),
    ).fetchall()

    return frozenset(
        str(row["name"])
        for row in rows
    )


def inspect_database(
    connection: sqlite3.Connection,
) -> AuditDatabaseStatus:
    """Return immutable database integrity information."""

    application_id = int(
        connection.execute(
            "PRAGMA application_id"
        ).fetchone()[0]
    )

    user_version = int(
        connection.execute(
            "PRAGMA user_version"
        ).fetchone()[0]
    )

    journal_mode = str(
        connection.execute(
            "PRAGMA journal_mode"
        ).fetchone()[0]
    ).upper()

    foreign_keys_enabled = bool(
        connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]
    )

    quick_check_rows = connection.execute(
        "PRAGMA quick_check"
    ).fetchall()

    quick_check = ",".join(
        str(row[0])
        for row in quick_check_rows
    )

    tables = tuple(
        sorted(
            _object_names(
                connection,
                "table",
            )
        )
    )

    indexes = tuple(
        sorted(
            _object_names(
                connection,
                "index",
            )
        )
    )

    triggers = tuple(
        sorted(
            _object_names(
                connection,
                "trigger",
            )
        )
    )

    return AuditDatabaseStatus(
        application_id=application_id,
        user_version=user_version,
        journal_mode=journal_mode,
        foreign_keys_enabled=foreign_keys_enabled,
        quick_check=quick_check,
        tables=tables,
        indexes=indexes,
        triggers=triggers,
    )


def validate_database(
    connection: sqlite3.Connection,
) -> AuditDatabaseStatus:
    """Fail closed when schema or integrity checks are invalid."""

    status = inspect_database(connection)

    failures: list[str] = []

    if status.application_id != APPLICATION_ID:
        failures.append("application_id")

    if status.user_version != SCHEMA_VERSION:
        failures.append("user_version")

    if status.quick_check != "ok":
        failures.append("quick_check")

    if not status.foreign_keys_enabled:
        failures.append("foreign_keys")

    if not _REQUIRED_TABLES.issubset(status.tables):
        failures.append("tables")

    if not _REQUIRED_INDEXES.issubset(status.indexes):
        failures.append("indexes")

    if not _REQUIRED_TRIGGERS.issubset(status.triggers):
        failures.append("triggers")

    metadata = connection.execute(
        """
        SELECT schema_version
        FROM schema_metadata
        ORDER BY schema_version DESC
        LIMIT 1
        """
    ).fetchone()

    if (
        metadata is None
        or int(metadata["schema_version"]) != SCHEMA_VERSION
    ):
        failures.append("schema_metadata")

    if failures:
        raise AuditDatabaseError(
            "audit database validation failed: "
            + ",".join(failures)
        )

    return status
