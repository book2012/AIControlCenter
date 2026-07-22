from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.governance.operations.runtime_capabilities import (
    GovernanceAuditSnapshotExecutor,
    SQLiteOnlineBackupVerifier,
)


REPOSITORY = Path(__file__).resolve().parents[1]
RUNNER_CONFIG = (
    REPOSITORY
    / "config/governance_operations_runner.json"
)


def _database(path: Path) -> Path:
    connection = sqlite3.connect(path)

    try:
        connection.execute(
            "CREATE TABLE audit_events "
            "(event_id TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO audit_events(event_id, value) "
            "VALUES (?, ?)",
            (
                ("event-1", "first"),
                ("event-2", "second"),
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return path


def test_snapshot_executor_creates_read_only_json_evidence(
    tmp_path: Path,
) -> None:
    database = _database(
        tmp_path / "source.sqlite3"
    )
    output = tmp_path / "operations"

    result = GovernanceAuditSnapshotExecutor(
        database_path=database,
        output_directory=output,
    ).execute()
    evidence = result.to_evidence()

    snapshot_path = Path(
        evidence["snapshot_path"]
    )

    assert snapshot_path.is_file()
    assert evidence["read_only"] is True
    assert evidence["model_write"] is False
    assert evidence["quick_check"] == ["ok"]
    assert evidence["table_row_counts"] == {
        "audit_events": 2,
    }
    assert len(evidence["snapshot_sha256"]) == 64

    snapshot = json.loads(
        snapshot_path.read_text(
            encoding="utf-8"
        )
    )

    assert snapshot["read_only"] is True
    assert snapshot["table_row_counts"] == {
        "audit_events": 2,
    }


def test_online_backup_verifier_creates_valid_copy(
    tmp_path: Path,
) -> None:
    database = _database(
        tmp_path / "source.sqlite3"
    )
    output = tmp_path / "operations"

    result = SQLiteOnlineBackupVerifier(
        database_path=database,
        output_directory=output,
    ).verify()
    evidence = result.to_evidence()

    backup_path = Path(
        evidence["backup_path"]
    )

    assert backup_path.is_file()
    assert evidence["automatic_restore"] is False
    assert evidence["model_write"] is False
    assert evidence["quick_check"] == ["ok"]
    assert evidence["row_counts_match"] is True
    assert evidence["source_row_counts"] == {
        "audit_events": 2,
    }
    assert evidence["backup_row_counts"] == {
        "audit_events": 2,
    }
    assert len(evidence["backup_sha256"]) == 64

    connection = sqlite3.connect(
        "file:" + str(backup_path) + "?mode=ro",
        uri=True,
    )

    try:
        assert connection.execute(
            "SELECT COUNT(*) FROM audit_events"
        ).fetchone()[0] == 2
    finally:
        connection.close()


def test_runner_composition_uses_semantic_capabilities() -> None:
    document = json.loads(
        RUNNER_CONFIG.read_text(
            encoding="utf-8"
        )
    )
    composition = document["composition"]

    assert composition[
        "snapshot_executor"
    ]["module"] == (
        "core.governance.operations.runtime_capabilities"
    )
    assert composition[
        "snapshot_executor"
    ]["class"] == (
        "GovernanceAuditSnapshotExecutor"
    )

    assert composition[
        "backup_verifier"
    ]["module"] == (
        "core.governance.operations.runtime_capabilities"
    )
    assert composition[
        "backup_verifier"
    ]["class"] == (
        "SQLiteOnlineBackupVerifier"
    )
