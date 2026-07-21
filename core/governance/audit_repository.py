"""Append-only repositories for governance audit snapshots."""

from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.governance.audit_snapshot import (
    AuditSnapshot,
    AuditSnapshotError,
    GovernanceSummary,
    canonical_json,
    validate_rfc3339_utc,
)
from core.governance.audit_sqlite import (
    AuditDatabaseError,
    connect_database,
    migrate_database,
    validate_database,
)


DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 1000


class AuditRepositoryError(RuntimeError):
    """Raised when repository operations fail closed."""


@dataclass(frozen=True)
class AppendResult:
    """Result of an idempotent snapshot append."""

    snapshot: AuditSnapshot
    created: bool


class AuditRepository(ABC):
    """Read-mostly append-only audit repository contract."""

    @abstractmethod
    def append_snapshot(
        self,
        snapshot: AuditSnapshot,
        *,
        created_at: str,
    ) -> AppendResult:
        """Append a snapshot or return the existing identical row."""

    @abstractmethod
    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> AuditSnapshot | None:
        """Return one verified snapshot."""

    @abstractmethod
    def get_latest_snapshot(
        self,
    ) -> AuditSnapshot | None:
        """Return the newest verified snapshot."""

    @abstractmethod
    def list_snapshots(
        self,
        *,
        limit: int = DEFAULT_LIST_LIMIT,
        before_captured_at: str | None = None,
        before_snapshot_id: str | None = None,
    ) -> tuple[AuditSnapshot, ...]:
        """Return verified snapshots in reverse chronological order."""


class SQLiteAuditRepository(AuditRepository):
    """SQLite-backed append-only audit repository."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        application_commit: str,
        migrated_at: str,
    ) -> None:
        self._database_path = Path(database_path).expanduser()
        self._application_commit = application_commit
        self._migrated_at = validate_rfc3339_utc(migrated_at)

    def initialize(self) -> None:
        connection = connect_database(
            self._database_path,
        )

        try:
            migrate_database(
                connection,
                application_commit=self._application_commit,
                applied_at=self._migrated_at,
            )
        finally:
            connection.close()

    @staticmethod
    def _validate_snapshot_id(
        snapshot_id: str,
    ) -> str:
        if (
            not isinstance(snapshot_id, str)
            or len(snapshot_id) != 64
            or snapshot_id.lower() != snapshot_id
        ):
            raise AuditRepositoryError(
                "snapshot_id must be 64 lowercase hexadecimal characters"
            )

        try:
            int(snapshot_id, 16)
        except ValueError as error:
            raise AuditRepositoryError(
                "snapshot_id must be 64 lowercase hexadecimal characters"
            ) from error

        return snapshot_id

    @staticmethod
    def _validate_limit(limit: int) -> int:
        if isinstance(limit, bool):
            raise AuditRepositoryError(
                "limit must be an integer"
            )

        if not isinstance(limit, int):
            raise AuditRepositoryError(
                "limit must be an integer"
            )

        if limit < 1 or limit > MAX_LIST_LIMIT:
            raise AuditRepositoryError(
                f"limit must be between 1 and {MAX_LIST_LIMIT}"
            )

        return limit

    @staticmethod
    def _row_to_snapshot(
        row: sqlite3.Row,
    ) -> AuditSnapshot:
        try:
            governance = json.loads(
                row["governance_json"]
            )
            summary_payload = json.loads(
                row["summary_json"]
            )

            payload: Mapping[str, Any] = {
                "schema_version": "1.0",
                "snapshot_id": row["snapshot_id"],
                "captured_at": row["captured_at"],
                "source_commit": row["source_commit"],
                "runtime_release": row["runtime_release"],
                "governance": governance,
                "summary": summary_payload,
            }

            return AuditSnapshot.from_dict(payload)
        except (
            AuditSnapshotError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ) as error:
            raise AuditRepositoryError(
                "stored audit snapshot failed canonical validation"
            ) from error

    @staticmethod
    def _snapshot_row_values(
        snapshot: AuditSnapshot,
        *,
        created_at: str,
    ) -> tuple[str, str, str, str, str, str, str]:
        return (
            snapshot.snapshot_id,
            snapshot.captured_at,
            snapshot.source_commit,
            snapshot.runtime_release,
            snapshot.governance_json,
            canonical_json(snapshot.summary.to_dict()),
            created_at,
        )

    @staticmethod
    def _snapshots_equal(
        first: AuditSnapshot,
        second: AuditSnapshot,
    ) -> bool:
        return first.to_dict() == second.to_dict()

    def append_snapshot(
        self,
        snapshot: AuditSnapshot,
        *,
        created_at: str,
    ) -> AppendResult:
        if not isinstance(snapshot, AuditSnapshot):
            raise AuditRepositoryError(
                "snapshot must be an AuditSnapshot"
            )

        created_at = validate_rfc3339_utc(created_at)

        connection = connect_database(
            self._database_path,
        )

        try:
            validate_database(connection)
            connection.execute("BEGIN IMMEDIATE")

            existing_row = connection.execute(
                """
                SELECT
                    snapshot_id,
                    captured_at,
                    source_commit,
                    runtime_release,
                    governance_json,
                    summary_json,
                    created_at
                FROM audit_snapshots
                WHERE snapshot_id = ?
                """,
                (snapshot.snapshot_id,),
            ).fetchone()

            if existing_row is not None:
                existing = self._row_to_snapshot(
                    existing_row
                )

                if not self._snapshots_equal(
                    existing,
                    snapshot,
                ):
                    raise AuditRepositoryError(
                        "snapshot_id collision with different content"
                    )

                connection.commit()

                return AppendResult(
                    snapshot=existing,
                    created=False,
                )

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
                self._snapshot_row_values(
                    snapshot,
                    created_at=created_at,
                ),
            )

            connection.commit()

            return AppendResult(
                snapshot=snapshot,
                created=True,
            )
        except (
            AuditDatabaseError,
            sqlite3.DatabaseError,
            AuditSnapshotError,
        ) as error:
            connection.rollback()
            raise AuditRepositoryError(
                "audit snapshot append failed"
            ) from error
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> AuditSnapshot | None:
        snapshot_id = self._validate_snapshot_id(
            snapshot_id
        )

        connection = connect_database(
            self._database_path,
            read_only=True,
        )

        try:
            validate_database(connection)

            row = connection.execute(
                """
                SELECT
                    snapshot_id,
                    captured_at,
                    source_commit,
                    runtime_release,
                    governance_json,
                    summary_json,
                    created_at
                FROM audit_snapshots
                WHERE snapshot_id = ?
                """,
                (snapshot_id,),
            ).fetchone()

            if row is None:
                return None

            return self._row_to_snapshot(row)
        except (
            AuditDatabaseError,
            sqlite3.DatabaseError,
        ) as error:
            raise AuditRepositoryError(
                "audit snapshot lookup failed"
            ) from error
        finally:
            connection.close()

    def get_latest_snapshot(
        self,
    ) -> AuditSnapshot | None:
        connection = connect_database(
            self._database_path,
            read_only=True,
        )

        try:
            validate_database(connection)

            row = connection.execute(
                """
                SELECT
                    snapshot_id,
                    captured_at,
                    source_commit,
                    runtime_release,
                    governance_json,
                    summary_json,
                    created_at
                FROM audit_snapshots
                ORDER BY
                    captured_at DESC,
                    snapshot_id DESC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return None

            return self._row_to_snapshot(row)
        except (
            AuditDatabaseError,
            sqlite3.DatabaseError,
        ) as error:
            raise AuditRepositoryError(
                "latest audit snapshot lookup failed"
            ) from error
        finally:
            connection.close()

    def list_snapshots(
        self,
        *,
        limit: int = DEFAULT_LIST_LIMIT,
        before_captured_at: str | None = None,
        before_snapshot_id: str | None = None,
    ) -> tuple[AuditSnapshot, ...]:
        limit = self._validate_limit(limit)

        cursor_requested = (
            before_captured_at is not None
            or before_snapshot_id is not None
        )

        if cursor_requested:
            if (
                before_captured_at is None
                or before_snapshot_id is None
            ):
                raise AuditRepositoryError(
                    "both cursor fields are required"
                )

            before_captured_at = validate_rfc3339_utc(
                before_captured_at
            )
            before_snapshot_id = self._validate_snapshot_id(
                before_snapshot_id
            )

        connection = connect_database(
            self._database_path,
            read_only=True,
        )

        try:
            validate_database(connection)

            if cursor_requested:
                rows: Sequence[sqlite3.Row] = connection.execute(
                    """
                    SELECT
                        snapshot_id,
                        captured_at,
                        source_commit,
                        runtime_release,
                        governance_json,
                        summary_json,
                        created_at
                    FROM audit_snapshots
                    WHERE
                        captured_at < ?
                        OR (
                            captured_at = ?
                            AND snapshot_id < ?
                        )
                    ORDER BY
                        captured_at DESC,
                        snapshot_id DESC
                    LIMIT ?
                    """,
                    (
                        before_captured_at,
                        before_captured_at,
                        before_snapshot_id,
                        limit,
                    ),
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT
                        snapshot_id,
                        captured_at,
                        source_commit,
                        runtime_release,
                        governance_json,
                        summary_json,
                        created_at
                    FROM audit_snapshots
                    ORDER BY
                        captured_at DESC,
                        snapshot_id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

            return tuple(
                self._row_to_snapshot(row)
                for row in rows
            )
        except (
            AuditDatabaseError,
            sqlite3.DatabaseError,
        ) as error:
            raise AuditRepositoryError(
                "audit snapshot list failed"
            ) from error
        finally:
            connection.close()
