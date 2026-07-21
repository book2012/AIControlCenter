"""Append-only SQLite execution event repository."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Sequence
from urllib.parse import quote
from uuid import UUID

from ...domain.events import (
    ExecutionEvent,
    Operation,
)
from ...domain.state import validate_event_sequence
from .codec import (
    event_from_row,
    event_payload_sha256,
    event_to_parameters,
)
from .schema import (
    EVENTS_FOR_RUN_SQL,
    INSERT_SQL,
    ITER_EVENTS_SQL,
    ITER_OPERATION_EVENTS_SQL,
    LAST_FAILURE_SQL,
    LAST_SUCCESS_SQL,
    REQUIRED_OBJECTS,
    SCHEMA_SQL,
    TABLE_NAME,
)


class RepositoryConfigurationError(RuntimeError):
    """Raised when SQLite policy cannot be established."""


class IdempotencyConflictError(RuntimeError):
    """Raised for a conflicting duplicate event ID."""


class SQLiteOperationsEventRepository:
    """Single-writer append-only event repository."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        busy_timeout_ms: int = 5000,
    ) -> None:
        self.database_path = Path(database_path)
        self.busy_timeout_ms = busy_timeout_ms

        if busy_timeout_ms < 1:
            raise RepositoryConfigurationError(
                "busy_timeout_ms must be positive"
            )


    def _open_writer(self) -> sqlite3.Connection:
        if not self.database_path.parent.is_dir():
            raise RepositoryConfigurationError(
                "database parent directory "
                "must already exist"
            )

        connection = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            f"PRAGMA busy_timeout = "
            f"{self.busy_timeout_ms}"
        )

        journal_mode = connection.execute(
            "PRAGMA journal_mode = WAL"
        ).fetchone()[0]

        if journal_mode.lower() != "wal":
            connection.close()
            raise RepositoryConfigurationError(
                "SQLite WAL mode is required"
            )

        connection.execute(
            "PRAGMA synchronous = NORMAL"
        )

        return connection


    def _open_reader(self) -> sqlite3.Connection:
        if not self.database_path.is_file():
            raise RepositoryConfigurationError(
                "database does not exist"
            )

        uri = (
            "file:"
            + quote(
                str(self.database_path),
                safe="/",
            )
            + "?mode=ro"
        )

        connection = sqlite3.connect(
            uri,
            uri=True,
            timeout=self.busy_timeout_ms / 1000,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        connection.execute(
            f"PRAGMA busy_timeout = "
            f"{self.busy_timeout_ms}"
        )

        return connection


    def initialize_schema(self) -> None:
        connection = self._open_writer()

        try:
            connection.executescript(SCHEMA_SQL)

            existing_objects = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type IN (
                        'table',
                        'index',
                        'trigger'
                    )
                    """
                ).fetchall()
            }

            missing = REQUIRED_OBJECTS - existing_objects

            if missing:
                raise RepositoryConfigurationError(
                    "required SQLite objects missing: "
                    + ", ".join(sorted(missing))
                )

        finally:
            connection.close()


    def append(
        self,
        event: ExecutionEvent,
    ) -> bool:
        connection = self._open_writer()

        try:
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                f"""
                SELECT payload_sha256
                FROM {TABLE_NAME}
                WHERE event_id = ?
                """,
                (str(event.event_id),),
            ).fetchone()

            candidate_hash = event_payload_sha256(
                event
            )

            if existing is not None:
                if (
                    existing["payload_sha256"]
                    == candidate_hash
                ):
                    connection.commit()
                    return False

                raise IdempotencyConflictError(
                    "event_id already exists with "
                    "different payload"
                )

            rows = connection.execute(
                EVENTS_FOR_RUN_SQL,
                (str(event.run_id),),
            ).fetchall()

            existing_events = tuple(
                event_from_row(row)
                for row in rows
            )

            validate_event_sequence(
                (*existing_events, event)
            )

            connection.execute(
                INSERT_SQL,
                event_to_parameters(event),
            )
            connection.commit()

            return True

        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise

        finally:
            connection.close()


    def events_for_run(
        self,
        run_id: UUID,
    ) -> Sequence[ExecutionEvent]:
        connection = self._open_reader()

        try:
            rows = connection.execute(
                EVENTS_FOR_RUN_SQL,
                (str(run_id),),
            ).fetchall()

            return tuple(
                event_from_row(row)
                for row in rows
            )

        finally:
            connection.close()


    def iter_events(
        self,
        operation: Operation | None = None,
    ) -> Iterable[ExecutionEvent]:
        connection = self._open_reader()

        try:
            if operation is None:
                rows = connection.execute(
                    ITER_EVENTS_SQL
                ).fetchall()
            else:
                rows = connection.execute(
                    ITER_OPERATION_EVENTS_SQL,
                    (operation.value,),
                ).fetchall()

            return tuple(
                event_from_row(row)
                for row in rows
            )

        finally:
            connection.close()


    def last_success(
        self,
        operation: Operation,
    ) -> ExecutionEvent | None:
        return self._single_event(
            LAST_SUCCESS_SQL,
            operation,
        )


    def last_failure(
        self,
        operation: Operation,
    ) -> ExecutionEvent | None:
        return self._single_event(
            LAST_FAILURE_SQL,
            operation,
        )


    def _single_event(
        self,
        query: str,
        operation: Operation,
    ) -> ExecutionEvent | None:
        connection = self._open_reader()

        try:
            row = connection.execute(
                query,
                (operation.value,),
            ).fetchone()

            if row is None:
                return None

            return event_from_row(row)

        finally:
            connection.close()


    def count(self) -> int:
        connection = self._open_reader()

        try:
            return connection.execute(
                f"SELECT COUNT(*) FROM {TABLE_NAME}"
            ).fetchone()[0]

        finally:
            connection.close()


    def schema_objects(self) -> frozenset[str]:
        connection = self._open_reader()

        try:
            rows = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type IN (
                    'table',
                    'index',
                    'trigger'
                )
                """
            ).fetchall()

            return frozenset(
                row[0] for row in rows
            )

        finally:
            connection.close()


    def journal_mode(self) -> str:
        connection = self._open_reader()

        try:
            return connection.execute(
                "PRAGMA journal_mode"
            ).fetchone()[0]

        finally:
            connection.close()
