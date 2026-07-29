from __future__ import annotations

import ast
import json
import os
import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.permit_replay_sqlite import (
    PermitReplayPathPolicy,
    PermitReplaySchemaExpectation,
)
from core.deployment.permit_replay_sqlite_recovery import (
    PermitReplayBackupConfig,
    PermitReplayBackupRequest,
    PermitReplayBackupService,
    PermitReplayPostRecoveryConcurrencyValidator,
    PermitReplayRecoveryError,
    PermitReplayRecoveryStatus,
    PermitReplayRecoveryValidator,
    PermitReplayRestoreConfig,
    PermitReplayRestoreRequest,
    PermitReplayRestoreService,
)
from core.deployment.permit_replay_sqlite_writer import (
    PermitReplayWriterConfig,
    PermitReservationRequest,
    PermitTerminalRequest,
    PermitTerminalState,
    SQLitePermitReplayRegistry,
)

NOW = "2026-07-30T12:00:00+09:00"
LATER = "2026-07-30T13:00:00+09:00"
EXPIRES = "2026-07-31T12:00:00+09:00"


def layout(tmp_path: Path):
    home = tmp_path / "Users" / "operator"
    app = home / "Library" / "Application Support" / "AIControlCenter"
    source_root, backup_root, restore_root = (
        app / "test-source", app / "test-backup", app / "test-restore"
    )
    for root in (source_root, backup_root, restore_root):
        root.mkdir(parents=True)
    source = source_root / "permit-replay.sqlite3"
    policy = PermitReplayPathPolicy(Path.cwd(), home)
    return home, policy, source, backup_root, restore_root


def create_db(path: Path) -> None:
    schema = PermitReplaySchemaExpectation()
    connection = sqlite3.connect(path)
    connection.executescript(schema.schema_sql_for_documentation())
    connection.execute("INSERT INTO permit_replay_meta VALUES (?)", (schema.schema_version,))
    connection.commit()
    assert connection.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    connection.close()


def reservation(number: int = 1) -> PermitReservationRequest:
    return PermitReservationRequest(
        permit_id=f"permit-{number}", permit_digest=f"sha256:permit-{number}",
        activation_id=f"activation-{number}",
        activation_request_digest=f"sha256:activation-{number}",
        package_digest="sha256:package", plan_digest="sha256:plan",
        readiness_report_id="readiness-1",
        readiness_report_digest="sha256:readiness",
        target_identity="mac-test-sandbox", environment="test",
        sandbox_root_identity_digest="sha256:sandbox",
        requester_identity="requester", operator_identity="operator",
        approver_identity="approver", reserved_at=NOW, expires_at=EXPIRES,
    )


def terminal(number: int, state: PermitTerminalState) -> PermitTerminalRequest:
    return PermitTerminalRequest(
        permit_id=f"permit-{number}", permit_digest=f"sha256:permit-{number}",
        activation_id=f"activation-{number}",
        activation_request_digest=f"sha256:activation-{number}",
        target_identity="mac-test-sandbox", environment="test",
        terminal_state=state, event_at=LATER, actor_identity="operator",
    )


def populated(tmp_path: Path):
    home, policy, source, backup_root, restore_root = layout(tmp_path)
    create_db(source)
    writer = SQLitePermitReplayRegistry(
        config=PermitReplayWriterConfig(source), path_policy=policy
    )
    writer.reserve(reservation(1))
    writer.transition_terminal(terminal(1, PermitTerminalState.CONSUMED))
    writer.reserve(reservation(2))
    writer.transition_terminal(terminal(2, PermitTerminalState.FAILED_CLOSED))
    writer.reserve(reservation(3))
    return home, policy, source, backup_root, restore_root


def backup_and_restore(tmp_path: Path, *, populated_state: bool = True):
    values = populated(tmp_path) if populated_state else layout(tmp_path)
    home, policy, source, backup_root, restore_root = values
    if not populated_state:
        create_db(source)
    backup = backup_root / "replay-backup.sqlite3"
    manifest = backup_root / "replay-backup.json"
    backup_service = PermitReplayBackupService(config=PermitReplayBackupConfig(
        source, backup_root, Path.cwd(), home
    ))
    backup_receipt = backup_service.backup(
        PermitReplayBackupRequest(backup, manifest, NOW)
    )
    restored = restore_root / "restored.sqlite3"
    restore_receipt = PermitReplayRestoreService(config=PermitReplayRestoreConfig(
        restore_root, Path.cwd(), home
    )).restore(PermitReplayRestoreRequest(backup, manifest, restored, LATER))
    return (*values, backup, manifest, restored, backup_receipt, restore_receipt)


def event_rows(path: Path):
    connection = sqlite3.connect(path)
    try:
        return connection.execute(
            "SELECT * FROM permit_use_events ORDER BY ledger_sequence,event_id"
        ).fetchall()
    finally:
        connection.close()


def test_immutable_contracts_explicit_paths_and_missing_source(tmp_path):
    home, _, source, backup_root, _ = layout(tmp_path)
    config = PermitReplayBackupConfig(source, backup_root, Path.cwd(), home)
    with pytest.raises(FrozenInstanceError):
        config.source_path = Path("/changed")
    service = PermitReplayBackupService(config=config)
    with pytest.raises(PermitReplayRecoveryError) as raised:
        service.backup(PermitReplayBackupRequest(
            backup_root / "backup.sqlite3", backup_root / "manifest.json", NOW
        ))
    assert raised.value.code == "FILE_UNAVAILABLE"
    assert list(backup_root.iterdir()) == []


@pytest.mark.parametrize("populated_state", [False, True])
def test_online_backup_restore_exact_equality_permissions_and_digests(
    tmp_path, populated_state
):
    (home, policy, source, _, _, backup, manifest, restored,
     backup_receipt, restore_receipt) = backup_and_restore(
        tmp_path, populated_state=populated_state
    )
    assert event_rows(source) == event_rows(backup) == event_rows(restored)
    assert backup_receipt.source_unchanged
    assert backup_receipt.logical_event_ledger_digest == (
        restore_receipt.logical_event_ledger_digest
    )
    assert backup_receipt.derived_permit_state_digest == (
        restore_receipt.derived_permit_state_digest
    )
    assert not (backup.stat().st_mode & 0o077)
    assert not (manifest.stat().st_mode & 0o077)
    assert not (restored.stat().st_mode & 0o077)
    report = PermitReplayRecoveryValidator(path_policy=policy).validate(
        source, restored, validated_at=LATER
    )
    assert report.status is PermitReplayRecoveryStatus.VALID
    assert report.exact_event_equality and report.exact_permit_state_equality
    assert report.recovered_healthy and report.replay_violations == 0
    assert str(source) not in repr(backup_receipt)
    assert str(restored) not in repr(restore_receipt)


def test_manifest_is_canonical_deterministic_and_binds_lifecycle_counts(tmp_path):
    (*_, backup, manifest, restored, backup_receipt, restore_receipt) = (
        backup_and_restore(tmp_path)
    )
    data = json.loads(manifest.read_bytes())
    assert manifest.read_bytes() == json.dumps(
        data, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode()
    assert data["event_count"] == 5 and data["permit_count"] == 3
    assert data["consumed_count"] == data["failed_closed_count"] == data["reserved_count"] == 1
    assert data["invalid_count"] == 0
    assert data["first_sequence"] == 1 and data["last_sequence"] == 5
    assert data["production_authorized"] is data["operational_backup"] is False
    assert backup_receipt.backup_id == restore_receipt.backup_id
    assert backup.exists() and restored.exists()


def test_idempotent_existing_backup_and_conflict_denial(tmp_path):
    home, _, source, backup_root, _ = populated(tmp_path)
    request = PermitReplayBackupRequest(
        backup_root / "backup.sqlite3", backup_root / "manifest.json", NOW
    )
    service = PermitReplayBackupService(config=PermitReplayBackupConfig(
        source, backup_root, Path.cwd(), home
    ))
    first = service.backup(request)
    second = service.backup(request)
    assert first == second
    request.manifest_path.write_text("{}")
    with pytest.raises(PermitReplayRecoveryError):
        service.backup(request)


@pytest.mark.parametrize("mutation,code", [
    (lambda backup, manifest: backup.write_bytes(backup.read_bytes()[:-20]),
     "DATABASE_DIGEST_MISMATCH"),
    (lambda backup, manifest: manifest.write_text(
        manifest.read_text().replace('"event_count":5', '"event_count":6')
    ), "MANIFEST_DIGEST_MISMATCH"),
])
def test_corrupt_backup_and_modified_manifest_are_denied(tmp_path, mutation, code):
    home, _, source, backup_root, restore_root = populated(tmp_path)
    backup = backup_root / "backup.sqlite3"
    manifest = backup_root / "manifest.json"
    PermitReplayBackupService(config=PermitReplayBackupConfig(
        source, backup_root, Path.cwd(), home
    )).backup(PermitReplayBackupRequest(backup, manifest, NOW))
    mutation(backup, manifest)
    target = restore_root / "restored.sqlite3"
    with pytest.raises(PermitReplayRecoveryError) as raised:
        PermitReplayRestoreService(config=PermitReplayRestoreConfig(
            restore_root, Path.cwd(), home
        )).restore(PermitReplayRestoreRequest(backup, manifest, target, LATER))
    assert raised.value.code == code
    assert not target.exists()


def test_path_overlap_existing_symlink_repository_and_secret_names_denied(tmp_path):
    home, _, source, backup_root, restore_root = populated(tmp_path)
    service = PermitReplayBackupService(config=PermitReplayBackupConfig(
        source, backup_root, Path.cwd(), home
    ))
    bad = (
        PermitReplayBackupRequest(Path("relative"), backup_root / "manifest.json", NOW),
        PermitReplayBackupRequest(source, backup_root / "manifest.json", NOW),
        PermitReplayBackupRequest(
            Path.cwd() / "backup.sqlite3", backup_root / "manifest.json", NOW
        ),
        PermitReplayBackupRequest(
            backup_root / "raw-nonce.sqlite3", backup_root / "manifest.json", NOW
        ),
    )
    for request in bad:
        with pytest.raises(PermitReplayRecoveryError):
            service.backup(request)
    link = backup_root / "link"
    link.symlink_to(restore_root, target_is_directory=True)
    with pytest.raises(PermitReplayRecoveryError):
        service.backup(PermitReplayBackupRequest(
            link / "backup.sqlite3", backup_root / "manifest.json", NOW
        ))


def test_backup_and_restore_failure_cleanup_and_originals_unchanged(tmp_path):
    home, _, source, backup_root, restore_root = populated(tmp_path)
    source_before = source.read_bytes()
    for point in ("before_final_rename", "manifest_write"):
        backup = backup_root / f"{point}.sqlite3"
        manifest = backup_root / f"{point}.json"
        with pytest.raises(PermitReplayRecoveryError):
            PermitReplayBackupService(
                config=PermitReplayBackupConfig(
                    source, backup_root, Path.cwd(), home
                ), failure_point=point,
            ).backup(PermitReplayBackupRequest(backup, manifest, NOW))
        assert not backup.exists() and not manifest.exists()
    assert source.read_bytes() == source_before
    backup = backup_root / "good.sqlite3"
    manifest = backup_root / "good.json"
    PermitReplayBackupService(config=PermitReplayBackupConfig(
        source, backup_root, Path.cwd(), home
    )).backup(PermitReplayBackupRequest(backup, manifest, NOW))
    backup_before = backup.read_bytes()
    target = restore_root / "failed.sqlite3"
    with pytest.raises(PermitReplayRecoveryError):
        PermitReplayRestoreService(
            config=PermitReplayRestoreConfig(
                restore_root, Path.cwd(), home
            ), failure_point="before_final_rename",
        ).restore(PermitReplayRestoreRequest(backup, manifest, target, LATER))
    assert not target.exists() and backup.read_bytes() == backup_before


def test_post_recovery_replay_and_concurrency_validation(tmp_path):
    (*values, restored, _, _) = backup_and_restore(tmp_path)
    home, policy, source, backup_root, restore_root, backup, manifest = values
    writer = SQLitePermitReplayRegistry(
        config=PermitReplayWriterConfig(restored), path_policy=policy
    )
    before = len(event_rows(restored))
    consumed_retry = writer.reserve(reservation(1))
    assert consumed_retry[1] is not None and consumed_retry[1].idempotent_retry
    assert writer.transition_terminal(
        terminal(2, PermitTerminalState.CONSUMED)
    )[1] is None
    assert writer.reserve(reservation(3))[1] is not None
    assert len(event_rows(restored)) == before
    report = PermitReplayPostRecoveryConcurrencyValidator(
        database_path=restored, path_policy=policy
    ).validate(
        reservation=reservation(4),
        consumed=terminal(4, PermitTerminalState.CONSUMED),
        failed_closed=terminal(4, PermitTerminalState.FAILED_CLOSED),
        validated_at=LATER,
    )
    assert report.status is PermitReplayRecoveryStatus.VALID
    assert report.reservation_commits == report.reservation_idempotent == 1
    assert report.terminal_commits == report.terminal_denials == 1
    assert report.duplicate_sequences == report.duplicate_event_ids == 0
    assert report.final_healthy and report.replay_violations == 0


def test_transaction_interruptions_rollback(tmp_path, monkeypatch):
    home, policy, source, *_ = populated(tmp_path)
    writer = SQLitePermitReplayRegistry(
        config=PermitReplayWriterConfig(source), path_policy=policy
    )
    original = writer._insert

    def interrupted(connection, *args, **kwargs):
        original(connection, *args, **kwargs)
        raise sqlite3.OperationalError("controlled interruption")

    monkeypatch.setattr(writer, "_insert", interrupted)
    before = event_rows(source)
    assert writer.reserve(reservation(8))[1] is None
    assert event_rows(source) == before
    assert writer.transition_terminal(
        terminal(3, PermitTerminalState.CONSUMED)
    )[1] is None
    assert event_rows(source) == before


def test_no_forbidden_dependencies_creation_or_default_operational_composition():
    root = Path("core/deployment/permit_replay_sqlite_recovery")
    source = "\n".join(path.read_text() for path in root.glob("*.py"))
    tree = ast.parse(source)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert "source_connection.backup(destination)" in source
    assert not any(str(item).startswith((
        "subprocess", "socket", "requests", "paramiko", "core.api", "core.worker",
        "core.deployment.audit_sqlite_writer",
    )) for item in imports)
    assert "VACUUM INTO" not in source.upper()
    assert "mode=rwc" not in source
    assert not list(Path.cwd().glob("*.sqlite3"))
