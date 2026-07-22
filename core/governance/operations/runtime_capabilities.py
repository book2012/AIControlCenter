from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4


DEFAULT_DATABASE_PATH = (
    Path.home()
    / "Library/Application Support/AIControlCenter/data/"
    "model-governance-audit.sqlite3"
)
DEFAULT_OUTPUT_DIRECTORY = (
    Path.home()
    / "Library/Application Support/AIControlCenter/"
    "backups/governance-audit/operations"
)


class GovernanceCapabilityError(RuntimeError):
    """Raised when a governed read-only capability cannot complete."""


@dataclass(frozen=True, slots=True)
class OperationEvidenceResult:
    evidence: Mapping[str, Any]

    def to_evidence(self) -> dict[str, Any]:
        return dict(self.evidence)


def _read_only_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise GovernanceCapabilityError(
            "governance audit database does not exist"
        )

    return sqlite3.connect(
        "file:" + str(path) + "?mode=ro",
        uri=True,
    )


def _quoted_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _table_row_counts(
    connection: sqlite3.Connection,
) -> dict[str, int]:
    names = [
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
    ]

    return {
        name: int(
            connection.execute(
                "SELECT COUNT(*) FROM "
                + _quoted_identifier(name)
            ).fetchone()[0]
        )
        for name in names
    }


def _quick_check(
    connection: sqlite3.Connection,
) -> list[str]:
    return [
        str(row[0])
        for row in connection.execute(
            "PRAGMA quick_check"
        ).fetchall()
    ]


def _timestamp() -> str:
    return datetime.now(
        timezone.utc
    ).strftime("%Y%m%dT%H%M%S%fZ")


def _sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def _prepare_output_directory(path: Path) -> None:
    path.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )


def _write_json_atomically(
    path: Path,
    document: Mapping[str, Any],
) -> None:
    temporary = path.with_name(
        path.name
        + ".tmp-"
        + uuid4().hex
    )

    try:
        temporary.write_text(
            json.dumps(
                document,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if temporary.exists():
            temporary.unlink()


class GovernanceAuditSnapshotExecutor:
    """Create an immutable JSON snapshot without mutating the audit DB."""

    def __init__(
        self,
        *unused_arguments: Any,
        database_path: str | Path | None = None,
        output_directory: str | Path | None = None,
        **unused_keywords: Any,
    ) -> None:
        del unused_arguments
        del unused_keywords

        self.database_path = Path(
            database_path
            or DEFAULT_DATABASE_PATH
        ).expanduser()
        self.output_directory = Path(
            output_directory
            or DEFAULT_OUTPUT_DIRECTORY
        ).expanduser()

    def execute(self) -> OperationEvidenceResult:
        _prepare_output_directory(
            self.output_directory
        )

        connection = _read_only_connection(
            self.database_path
        )

        try:
            quick_check = _quick_check(
                connection
            )
            table_row_counts = (
                _table_row_counts(
                    connection
                )
            )
        finally:
            connection.close()

        if quick_check != ["ok"]:
            raise GovernanceCapabilityError(
                "governance audit database quick_check failed"
            )

        snapshot_path = (
            self.output_directory
            / (
                "governance-audit-snapshot-"
                + _timestamp()
                + "-"
                + uuid4().hex[:12]
                + ".json"
            )
        )

        snapshot = {
            "automatic_remediation": False,
            "database_path": str(
                self.database_path
            ),
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "model_write": False,
            "quick_check": quick_check,
            "read_only": True,
            "schema_version": "1.0.0",
            "table_row_counts": (
                table_row_counts
            ),
        }

        _write_json_atomically(
            snapshot_path,
            snapshot,
        )

        return OperationEvidenceResult(
            {
                "automatic_remediation": False,
                "model_write": False,
                "quick_check": quick_check,
                "read_only": True,
                "snapshot_path": str(
                    snapshot_path
                ),
                "snapshot_sha256": _sha256(
                    snapshot_path
                ),
                "table_row_counts": (
                    table_row_counts
                ),
            }
        )


class SQLiteOnlineBackupVerifier:
    """Create and verify a SQLite online backup without restoring it."""

    def __init__(
        self,
        *unused_arguments: Any,
        database_path: str | Path | None = None,
        output_directory: str | Path | None = None,
        **unused_keywords: Any,
    ) -> None:
        del unused_arguments
        del unused_keywords

        self.database_path = Path(
            database_path
            or DEFAULT_DATABASE_PATH
        ).expanduser()
        self.output_directory = Path(
            output_directory
            or DEFAULT_OUTPUT_DIRECTORY
        ).expanduser()

    def verify(self) -> OperationEvidenceResult:
        _prepare_output_directory(
            self.output_directory
        )

        backup_path = (
            self.output_directory
            / (
                "governance-audit-operation-"
                + _timestamp()
                + "-"
                + uuid4().hex[:12]
                + ".sqlite3"
            )
        )

        source = _read_only_connection(
            self.database_path
        )
        destination = sqlite3.connect(
            backup_path
        )

        try:
            source_row_counts = (
                _table_row_counts(source)
            )
            source.backup(destination)
            destination.commit()

            quick_check = _quick_check(
                destination
            )
            backup_row_counts = (
                _table_row_counts(
                    destination
                )
            )
        finally:
            destination.close()
            source.close()

        os.chmod(backup_path, 0o600)

        row_counts_match = (
            source_row_counts
            == backup_row_counts
        )

        if quick_check != ["ok"]:
            raise GovernanceCapabilityError(
                "SQLite backup quick_check failed"
            )

        if not row_counts_match:
            raise GovernanceCapabilityError(
                "SQLite backup row counts do not match"
            )

        return OperationEvidenceResult(
            {
                "automatic_restore": False,
                "backup_path": str(
                    backup_path
                ),
                "backup_row_counts": (
                    backup_row_counts
                ),
                "backup_sha256": _sha256(
                    backup_path
                ),
                "model_write": False,
                "quick_check": quick_check,
                "row_counts_match": True,
                "source_row_counts": (
                    source_row_counts
                ),
            }
        )
