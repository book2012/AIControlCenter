"""Verified SQLite online backup adapter."""

from __future__ import annotations

import hashlib
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .schema import REQUIRED_OBJECTS, TABLE_NAME


class BackupVerificationError(RuntimeError):
    """Raised when online backup verification fails."""


@dataclass(frozen=True, slots=True)
class BackupVerificationResult:
    source_path: Path
    destination_path: Path
    sha256: str
    quick_check: tuple[str, ...]
    source_row_count: int
    backup_row_count: int
    required_objects: tuple[str, ...]


class SQLiteOnlineBackupVerifier:
    """Create and verify one SQLite online backup."""

    def __init__(
        self,
        source_path: str | Path,
        *,
        busy_timeout_ms: int = 5000,
        pages_per_step: int = 256,
    ) -> None:
        self.source_path = Path(source_path)
        self.busy_timeout_ms = busy_timeout_ms
        self.pages_per_step = pages_per_step

        if busy_timeout_ms < 1:
            raise BackupVerificationError(
                "busy_timeout_ms must be positive"
            )

        if pages_per_step < 1:
            raise BackupVerificationError(
                "pages_per_step must be positive"
            )


    def _open_source(self) -> sqlite3.Connection:
        if not self.source_path.is_file():
            raise BackupVerificationError(
                "source database does not exist"
            )

        uri = (
            "file:"
            + quote(
                str(self.source_path),
                safe="/",
            )
            + "?mode=ro"
        )

        connection = sqlite3.connect(
            uri,
            uri=True,
            timeout=self.busy_timeout_ms / 1000,
        )
        connection.execute("PRAGMA query_only = ON")
        connection.execute(
            f"PRAGMA busy_timeout = "
            f"{self.busy_timeout_ms}"
        )

        return connection


    def verify_to(
        self,
        destination_path: str | Path,
    ) -> BackupVerificationResult:
        destination = Path(destination_path)
        partial = destination.with_name(
            destination.name + ".partial"
        )

        try:
            if (
                self.source_path.resolve()
                == destination.resolve()
            ):
                raise BackupVerificationError(
                    "backup destination must differ "
                    "from source"
                )

            if not destination.parent.is_dir():
                raise BackupVerificationError(
                    "backup destination directory "
                    "must already exist"
                )

            if destination.exists():
                raise BackupVerificationError(
                    "backup destination already exists"
                )

            if partial.exists():
                raise BackupVerificationError(
                    "partial backup already exists"
                )

            source = self._open_source()

            try:
                source_row_count = source.execute(
                    f"SELECT COUNT(*) "
                    f"FROM {TABLE_NAME}"
                ).fetchone()[0]

                target = sqlite3.connect(partial)

                try:
                    source.backup(
                        target,
                        pages=self.pages_per_step,
                        sleep=0.01,
                    )
                    target.commit()
                finally:
                    target.close()

            finally:
                source.close()

            uri = (
                "file:"
                + quote(str(partial), safe="/")
                + "?mode=ro"
            )

            verification = sqlite3.connect(
                uri,
                uri=True,
            )

            try:
                verification.execute(
                    "PRAGMA query_only = ON"
                )

                quick_check = tuple(
                    row[0]
                    for row in verification.execute(
                        "PRAGMA quick_check"
                    ).fetchall()
                )

                backup_row_count = (
                    verification.execute(
                        f"SELECT COUNT(*) "
                        f"FROM {TABLE_NAME}"
                    ).fetchone()[0]
                )

                objects = {
                    row[0]
                    for row in verification.execute(
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

            finally:
                verification.close()

            missing = REQUIRED_OBJECTS - objects

            if quick_check != ("ok",):
                raise BackupVerificationError(
                    "SQLite quick_check failed"
                )

            if missing:
                raise BackupVerificationError(
                    "backup schema objects missing: "
                    + ", ".join(sorted(missing))
                )

            if source_row_count != backup_row_count:
                raise BackupVerificationError(
                    "source and backup row counts "
                    "do not match"
                )

            os.replace(partial, destination)

            digest = hashlib.sha256(
                destination.read_bytes()
            ).hexdigest()

            return BackupVerificationResult(
                source_path=self.source_path,
                destination_path=destination,
                sha256=digest,
                quick_check=quick_check,
                source_row_count=source_row_count,
                backup_row_count=backup_row_count,
                required_objects=tuple(
                    sorted(REQUIRED_OBJECTS)
                ),
            )

        except Exception:
            if partial.exists():
                partial.unlink()
            raise
