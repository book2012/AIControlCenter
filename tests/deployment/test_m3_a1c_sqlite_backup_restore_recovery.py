from __future__ import annotations

import ast
import json
import os
import sqlite3
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.audit_contracts import (
    GENESIS_PREVIOUS_HASH,
    AuditAppendRequest,
    AuditEventType,
    create_audit_event,
)
from core.deployment.audit_sqlite import SQLiteAuditPathPolicy, SQLiteAuditStatus
from core.deployment.audit_sqlite_recovery import (
    SQLiteAuditBackupConfig,
    SQLiteAuditBackupRequest,
    SQLiteAuditBackupService,
    SQLiteAuditRecoveryError,
    SQLiteAuditRecoveryStatus,
    SQLiteAuditRecoveryValidator,
    SQLiteAuditRestoreConfig,
    SQLiteAuditRestoreRequest,
    SQLiteAuditRestoreService,
)
from core.deployment.audit_sqlite_writer import (
    SQLiteAuditSchemaDefinition,
    SQLiteAuditWriter,
    SQLiteAuditWriterConfig,
)
from core.deployment.policy import validate_dependency_boundaries

NOW = "2026-07-29T12:00:00+09:00"


def environment(tmp_path: Path, events: int = 0):
    home = tmp_path / "Users" / "operator"
    app = home / "Library" / "Application Support" / "AIControlCenter" / "audit"
    app.mkdir(parents=True)
    policy = SQLiteAuditPathPolicy(repository_root=Path.cwd(), user_home=home)
    source = app / "source.sqlite3"
    connection = sqlite3.connect(source)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(SQLiteAuditSchemaDefinition().ddl_for_test_bootstrap())
    connection.execute("INSERT INTO audit_ledger_meta VALUES (?)",
                       ("dpl/audit-sqlite/v1",))
    connection.commit()
    connection.close()
    previous = GENESIS_PREVIOUS_HASH
    writer = SQLiteAuditWriter(
        config=SQLiteAuditWriterConfig(source), path_policy=policy
    )
    for sequence in range(1, events + 1):
        event = create_audit_event(
            event_type=AuditEventType.INTEGRITY_VERIFIED,
            sequence=sequence, previous_event_hash=previous,
            recorded_at=NOW, actor_identity="operator", environment="test",
            policy_decision="ALLOW", payload={"ordinal": sequence},
        )
        writer.append(AuditAppendRequest(event, event.previous_event_hash))
        previous = event.event_hash
    backup_root = app / "backups"
    restore_root = app / "restores"
    backup_root.mkdir()
    restore_root.mkdir()
    return policy, source, backup_root, restore_root


def perform_backup(tmp_path: Path, events: int = 0):
    policy, source, backup_root, restore_root = environment(tmp_path, events)
    backup = backup_root / "audit-backup.sqlite3"
    manifest = backup_root / "audit-backup.manifest.json"
    service = SQLiteAuditBackupService(
        config=SQLiteAuditBackupConfig(source, backup_root), path_policy=policy
    )
    request = SQLiteAuditBackupRequest(backup, manifest, NOW)
    receipt = service.backup(request)
    return (policy, source, backup_root, restore_root, backup, manifest,
            service, request, receipt)


def test_contracts_are_explicit_immutable_and_default_deny(tmp_path):
    with pytest.raises(TypeError):
        SQLiteAuditBackupConfig()  # type: ignore[call-arg]
    with pytest.raises(ValueError):
        SQLiteAuditBackupConfig(Path("relative"), tmp_path)
    config = SQLiteAuditBackupConfig(tmp_path / "source", tmp_path)
    with pytest.raises(FrozenInstanceError):
        config.timeout_seconds = 3
    with pytest.raises(ValueError):
        SQLiteAuditBackupRequest(
            tmp_path / "b", tmp_path / "m", NOW, production_authorized=True
        )
    with pytest.raises(ValueError):
        SQLiteAuditRestoreRequest(
            tmp_path / "b", tmp_path / "m", tmp_path / "r", NOW,
            operational_restore=True,
        )


def test_missing_source_denied_and_outputs_absent(tmp_path):
    policy, source, backup_root, _ = environment(tmp_path)
    source.unlink()
    backup = backup_root / "backup.sqlite3"
    manifest = backup_root / "manifest.json"
    with pytest.raises(SQLiteAuditRecoveryError) as raised:
        SQLiteAuditBackupService(
            config=SQLiteAuditBackupConfig(source, backup_root), path_policy=policy
        ).backup(SQLiteAuditBackupRequest(backup, manifest, NOW))
    assert raised.value.status is SQLiteAuditRecoveryStatus.DENIED
    assert not backup.exists() and not manifest.exists()


@pytest.mark.parametrize("events", [0, 3])
def test_online_backup_manifest_permissions_source_unchanged_and_idempotency(
    tmp_path, events
):
    values = perform_backup(tmp_path, events)
    source, backup, manifest, service, request, receipt = (
        values[1], values[4], values[5], values[6], values[7], values[8]
    )
    before = source.read_bytes()
    retry = service.backup(request)
    data = json.loads(manifest.read_text())
    assert receipt.status is SQLiteAuditRecoveryStatus.BACKUP_COMPLETE
    assert retry.idempotent_retry and retry.backup_id == receipt.backup_id
    assert data["event_count"] == events
    assert data["database_byte_digest"].startswith("sha256:")
    assert data["logical_ledger_digest"].startswith("sha256:")
    assert source.read_bytes() == before and receipt.source_unchanged
    assert os.stat(backup).st_mode & 0o077 == 0
    assert os.stat(manifest).st_mode & 0o077 == 0


def test_restore_and_deterministic_recovery_validation(tmp_path):
    values = perform_backup(tmp_path, 3)
    policy, source, _, restore_root, backup, manifest = values[:6]
    target = restore_root / "restored.sqlite3"
    restore = SQLiteAuditRestoreService(
        config=SQLiteAuditRestoreConfig(restore_root), path_policy=policy
    )
    receipt = restore.restore(
        SQLiteAuditRestoreRequest(backup, manifest, target, NOW)
    )
    assert receipt.status is SQLiteAuditRecoveryStatus.RESTORE_COMPLETE
    assert receipt.event_count == 3 and receipt.backup_unchanged
    validator = SQLiteAuditRecoveryValidator(policy)
    first = validator.validate(
        source_path=source, backup_path=backup, restore_path=target,
        manifest_path=manifest, validated_at=NOW
    )
    second = validator.validate(
        source_path=source, backup_path=backup, restore_path=target,
        manifest_path=manifest, validated_at=NOW
    )
    assert first == second
    assert first.status is SQLiteAuditRecoveryStatus.RECOVERY_VALID
    assert first.event_count_matches and first.event_identity_matches
    assert first.previous_hashes_match and first.event_hashes_match
    assert first.restored_inspection_healthy
    assert first.production_authorization_violations == 0
    assert first.secret_bearing_violations == 0


def test_existing_conflicting_backup_and_restore_targets_are_denied(tmp_path):
    values = perform_backup(tmp_path, 1)
    policy, _, backup_root, restore_root, backup, manifest = values[:6]
    backup.write_bytes(b"conflict")
    with pytest.raises(SQLiteAuditRecoveryError):
        values[6].backup(values[7])
    target = restore_root / "restored.sqlite3"
    target.write_text("existing")
    with pytest.raises(SQLiteAuditRecoveryError) as raised:
        SQLiteAuditRestoreService(
            config=SQLiteAuditRestoreConfig(restore_root), path_policy=policy
        ).restore(SQLiteAuditRestoreRequest(backup, manifest, target, NOW))
    assert raised.value.code == "RESTORE_TARGET_EXISTS"


@pytest.mark.parametrize(
    "kind", ["manifest", "backup", "truncated"]
)
def test_corruption_and_manifest_modification_fail_closed(tmp_path, kind):
    values = perform_backup(tmp_path, 2)
    policy, _, _, restore_root, backup, manifest = values[:6]
    if kind == "manifest":
        data = json.loads(manifest.read_text())
        data["event_count"] = 99
        manifest.write_text(json.dumps(data))
    elif kind == "backup":
        raw = bytearray(backup.read_bytes())
        raw[-1] ^= 1
        backup.write_bytes(raw)
    else:
        backup.write_bytes(backup.read_bytes()[:128])
    target = restore_root / "restored.sqlite3"
    with pytest.raises((SQLiteAuditRecoveryError, sqlite3.DatabaseError)):
        SQLiteAuditRestoreService(
            config=SQLiteAuditRestoreConfig(restore_root), path_policy=policy
        ).restore(SQLiteAuditRestoreRequest(backup, manifest, target, NOW))
    assert not target.exists()


def test_overlap_symlink_traversal_repository_protected_and_volume_paths(tmp_path):
    policy, source, backup_root, _ = environment(tmp_path)
    link = backup_root / "link.sqlite3"
    link.symlink_to(source)
    assert policy.validate(link)
    for path in (
        Path("relative.sqlite3"), Path.cwd() / "db.sqlite3",
        Path("/System/db.sqlite3"), Path("/Volumes/network/db.sqlite3"),
        Path("/home/ubuntu/db.sqlite3"),
        Path(str(backup_root) + "/../backup.sqlite3"),
    ):
        assert policy.validate(path)
    service = SQLiteAuditBackupService(
        config=SQLiteAuditBackupConfig(source, backup_root), path_policy=policy
    )
    with pytest.raises(SQLiteAuditRecoveryError):
        service.backup(SQLiteAuditBackupRequest(source, backup_root / "m.json", NOW))


def test_unhealthy_secret_source_is_denied_and_schema_blocks_production(tmp_path):
    policy, source, backup_root, _ = environment(tmp_path)
    connection = sqlite3.connect(source)
    connection.execute("DROP TRIGGER trg_audit_events_no_update")
    connection.execute(
        "INSERT INTO audit_events VALUES (1,'bad','dpl/audit/v1','INTEGRITY_VERIFIED',"
        "?,?,?,?,?,?,0)",
        (NOW, "operator", '{"environment":"test","policy_decision":"ALLOW",'
         '"payload":{"access_token":"x"}}', "sha256:bad",
         GENESIS_PREVIOUS_HASH, "sha256:bad"),
    )
    connection.commit()
    connection.close()
    with pytest.raises(SQLiteAuditRecoveryError) as raised:
        SQLiteAuditBackupService(
            config=SQLiteAuditBackupConfig(source, backup_root), path_policy=policy
        ).backup(SQLiteAuditBackupRequest(
            backup_root / "b.sqlite3", backup_root / "m.json", NOW
        ))
    assert raised.value.code == "SOURCE_NOT_HEALTHY"
    connection = sqlite3.connect(source)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO audit_events VALUES (2,'production','dpl/audit/v1',"
            "'INTEGRITY_VERIFIED',?,?,?,?,?,?,1)",
            (NOW, "operator", "{}", "sha256:bad", "sha256:bad", "sha256:bad"),
        )
    connection.close()


def test_dependencies_online_api_and_no_runtime_side_effect_facilities():
    root = Path("core/deployment/audit_sqlite_recovery")
    text = "\n".join(path.read_text() for path in root.glob("*.py"))
    tree = ast.parse(text)
    imports = {
        node.names[0].name if isinstance(node, ast.Import) else node.module
        for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
    }
    assert ".backup(" in text
    assert not any(str(value).startswith((
        "subprocess", "socket", "requests", "paramiko", "core.api", "core.worker"
    )) for value in imports)
    assert "VACUUM" not in text and "mode=rwc" not in text
    assert validate_dependency_boundaries(
        repository_root=Path.cwd()
    )["overall_result"] == "PASS"
