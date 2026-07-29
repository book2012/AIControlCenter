"""Explicit-path SQLite online backup and restore services."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.permit_replay_sqlite import (
    PermitReplayPathPolicy,
    PermitReplayReadOnlyInspector,
    PermitReplayStatus,
    PermitReplayStorageConfig,
)

from core.deployment.permit_replay_sqlite_recovery.models import (
    PermitReplayBackupConfig,
    PermitReplayBackupManifest,
    PermitReplayBackupReceipt,
    PermitReplayBackupRequest,
    PermitReplayRecoveryError,
    PermitReplayRestoreConfig,
    PermitReplayRestoreReceipt,
    PermitReplayRestoreRequest,
)

_FIELDS = (
    "ledger_sequence", "event_id", "permit_id", "permit_digest",
    "activation_id", "activation_request_digest", "event_type", "event_at",
    "actor_identity", "target_identity", "environment", "canonical_payload",
    "payload_digest", "previous_event_hash", "event_hash",
    "production_authorized",
)
_SECRET_MARKERS = (
    "nonce", "password", "secret", "token", "credential", "cookie",
    "private_key", "api_key", "authorization", "shell", "command", "argv",
    "script", "environment_variable",
)


def _identity(path: Path) -> str:
    return "sha256:" + hashlib.sha256(os.fsencode(path)).hexdigest()


def _bytes_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _validate_absolute(path: Path, *, repository_root: Path, root: Path | None = None,
                       must_exist: bool = False, directory: bool = False) -> None:
    if not path.is_absolute():
        raise PermitReplayRecoveryError("RELATIVE_PATH")
    if ".." in path.parts:
        raise PermitReplayRecoveryError("PATH_TRAVERSAL")
    normalized = path.name.lower().replace("-", "_")
    if any(marker in normalized for marker in _SECRET_MARKERS):
        raise PermitReplayRecoveryError("SECRET_BEARING_FILENAME")
    try:
        path.relative_to(repository_root.resolve())
    except ValueError:
        pass
    else:
        raise PermitReplayRecoveryError("REPOSITORY_PATH")
    protected = ("/System", "/Library", "/Applications", "/usr", "/bin", "/sbin",
                 "/etc", "/home", "/var", "/srv", "/mnt", "/media", "/Volumes")
    raw = str(path)
    if any(raw == item or raw.startswith(item + "/") for item in protected):
        raise PermitReplayRecoveryError("PROTECTED_PATH")
    if root is not None:
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise PermitReplayRecoveryError("OUTSIDE_SUPPLIED_ROOT") from exc
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        if current.is_symlink():
            raise PermitReplayRecoveryError("SYMLINK_PATH_COMPONENT")
        if not current.exists():
            break
    if must_exist and (
        (not path.is_dir() if directory else not path.is_file()) or path.is_symlink()
    ):
        raise PermitReplayRecoveryError("FILE_UNAVAILABLE")


def _open_read_only(path: Path) -> sqlite3.Connection:
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _snapshot(path: Path) -> tuple[list[dict[str, Any]], str, str]:
    with _open_read_only(path) as connection:
        rows = [dict(row) for row in connection.execute(
            f"SELECT {','.join(_FIELDS)} FROM permit_use_events "
            "ORDER BY ledger_sequence,event_id"
        )]
    logical = []
    for row in rows:
        item = dict(row)
        item["canonical_payload"] = json.loads(item["canonical_payload"])
        item["production_authorized"] = bool(item["production_authorized"])
        logical.append(item)
    states: dict[str, str] = {}
    for row in rows:
        states.setdefault(row["permit_id"], "UNUSED")
        states[row["permit_id"]] = row["event_type"]
    return rows, sha256_digest(logical), sha256_digest([
        {"permit_id": key, "state": value} for key, value in sorted(states.items())
    ])


def _inspect(path: Path, config: Any, inspected_at: str):
    policy = PermitReplayPathPolicy(config.repository_root, config.user_home)
    return PermitReplayReadOnlyInspector(
        config=PermitReplayStorageConfig(path), path_policy=policy
    ).inspect(inspected_at=inspected_at)


def _manifest_semantic(manifest: PermitReplayBackupManifest) -> dict[str, Any]:
    value = manifest.as_dict()
    value.pop("backup_id")
    value.pop("manifest_digest")
    return value


def _load_manifest(path: Path) -> PermitReplayBackupManifest:
    try:
        raw = path.read_bytes()
        data = json.loads(raw)
        if canonical_json_bytes(data) != raw:
            raise PermitReplayRecoveryError("NON_CANONICAL_MANIFEST")
        manifest = PermitReplayBackupManifest(**data)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, PermitReplayRecoveryError):
            raise
        raise PermitReplayRecoveryError("INVALID_MANIFEST") from exc
    semantic = _manifest_semantic(manifest)
    digest = sha256_digest(semantic)
    if digest != manifest.manifest_digest:
        raise PermitReplayRecoveryError("MANIFEST_DIGEST_MISMATCH")
    if "permit-replay-backup-" + digest[7:39] != manifest.backup_id:
        raise PermitReplayRecoveryError("BACKUP_ID_MISMATCH")
    if manifest.production_authorized or manifest.operational_backup:
        raise PermitReplayRecoveryError("PRODUCTION_OR_OPERATIONAL_PROHIBITED")
    return manifest


class PermitReplayBackupService:
    def __init__(self, *, config: PermitReplayBackupConfig,
                 failure_point: str | None = None) -> None:
        self._config = config
        self._failure_point = failure_point

    def backup(self, request: PermitReplayBackupRequest) -> PermitReplayBackupReceipt:
        config, source = self._config, self._config.source_path
        _validate_absolute(source, repository_root=config.repository_root, must_exist=True)
        _validate_absolute(config.backup_root, repository_root=config.repository_root,
                           must_exist=True, directory=True)
        _validate_absolute(request.backup_path, repository_root=config.repository_root,
                           root=config.backup_root)
        _validate_absolute(request.manifest_path, repository_root=config.repository_root,
                           root=config.backup_root)
        if request.production_authorized or request.operational_backup:
            raise PermitReplayRecoveryError("PRODUCTION_OR_OPERATIONAL_PROHIBITED")
        if request.backup_path == request.manifest_path or source in (
            request.backup_path, request.manifest_path
        ):
            raise PermitReplayRecoveryError("SOURCE_DESTINATION_OVERLAP")
        source_report = _inspect(source, config, request.created_at)
        if source_report.status is not PermitReplayStatus.HEALTHY:
            raise PermitReplayRecoveryError("SOURCE_NOT_HEALTHY")
        before = _bytes_digest(source)
        rows, logical_digest, state_digest = _snapshot(source)
        temp_db: Path | None = None
        temp_manifest: Path | None = None
        try:
            fd, name = tempfile.mkstemp(prefix=".permit-replay-", suffix=".tmp",
                                        dir=config.backup_root)
            os.close(fd)
            temp_db = Path(name)
            os.chmod(temp_db, 0o600)
            with _open_read_only(source) as source_connection:
                destination = sqlite3.connect(temp_db)
                try:
                    source_connection.backup(destination)
                finally:
                    destination.close()
            backup_report = _inspect(temp_db, config, request.created_at)
            if backup_report.status is not PermitReplayStatus.HEALTHY:
                raise PermitReplayRecoveryError("BACKUP_NOT_HEALTHY")
            backup_rows, backup_logical, backup_states = _snapshot(temp_db)
            if backup_rows != rows or backup_logical != logical_digest or backup_states != state_digest:
                raise PermitReplayRecoveryError("BACKUP_CONTENT_MISMATCH")
            byte_digest = _bytes_digest(temp_db)
            semantic = {
                "source_path_identity_digest": _identity(source),
                "backup_path_identity_digest": _identity(request.backup_path),
                "schema_version": source_report.schema_version,
                "event_count": source_report.event_count,
                "permit_count": source_report.permit_count,
                "reserved_count": source_report.reserved_count,
                "consumed_count": source_report.consumed_count,
                "failed_closed_count": source_report.failed_closed_count,
                "invalid_count": source_report.invalid_count,
                "first_sequence": rows[0]["ledger_sequence"] if rows else None,
                "last_sequence": rows[-1]["ledger_sequence"] if rows else None,
                "first_event_hash": rows[0]["event_hash"] if rows else None,
                "last_event_hash": rows[-1]["event_hash"] if rows else None,
                "database_byte_digest": byte_digest,
                "logical_event_ledger_digest": logical_digest,
                "derived_permit_state_digest": state_digest,
                "source_inspection_report_id": source_report.report_id,
                "source_inspection_report_digest": source_report.report_digest,
                "created_at": request.created_at,
                "production_authorized": False,
                "operational_backup": False,
            }
            manifest = PermitReplayBackupManifest.build(**semantic)
            if self._failure_point == "before_final_rename":
                raise PermitReplayRecoveryError("INJECTED_BACKUP_FAILURE")
            if request.backup_path.exists() or request.manifest_path.exists():
                if request.backup_path.is_file() and request.manifest_path.is_file():
                    existing = _load_manifest(request.manifest_path)
                    if (existing.manifest_digest == manifest.manifest_digest and
                            _bytes_digest(request.backup_path) == byte_digest):
                        return self._receipt(manifest, request, before == _bytes_digest(source))
                raise PermitReplayRecoveryError("CONFLICTING_EXISTING_BACKUP")
            os.replace(temp_db, request.backup_path)
            temp_db = None
            fd, name = tempfile.mkstemp(prefix=".permit-replay-manifest-", suffix=".tmp",
                                        dir=config.backup_root)
            os.close(fd)
            temp_manifest = Path(name)
            os.chmod(temp_manifest, 0o600)
            if self._failure_point == "manifest_write":
                raise PermitReplayRecoveryError("INJECTED_MANIFEST_FAILURE")
            temp_manifest.write_bytes(canonical_json_bytes(manifest.as_dict()))
            os.replace(temp_manifest, request.manifest_path)
            temp_manifest = None
            if before != _bytes_digest(source):
                raise PermitReplayRecoveryError("SOURCE_CHANGED_DURING_BACKUP")
            return self._receipt(manifest, request, True)
        except Exception:
            if request.backup_path.exists() and not request.manifest_path.exists():
                request.backup_path.unlink()
            raise
        finally:
            for temporary in (temp_db, temp_manifest):
                if temporary is not None and temporary.exists():
                    temporary.unlink()

    @staticmethod
    def _receipt(manifest: PermitReplayBackupManifest,
                 request: PermitReplayBackupRequest, unchanged: bool):
        semantic = {
            "backup_id": manifest.backup_id,
            "backup_path_identity_digest": manifest.backup_path_identity_digest,
            "manifest_path_identity_digest": _identity(request.manifest_path),
            "database_byte_digest": manifest.database_byte_digest,
            "logical_event_ledger_digest": manifest.logical_event_ledger_digest,
            "derived_permit_state_digest": manifest.derived_permit_state_digest,
            "manifest_digest": manifest.manifest_digest,
            "source_unchanged": unchanged,
            "production_authorized": False,
            "operational_backup": False,
        }
        return PermitReplayBackupReceipt(**semantic, receipt_digest=sha256_digest(semantic))


class PermitReplayRestoreService:
    def __init__(self, *, config: PermitReplayRestoreConfig,
                 failure_point: str | None = None) -> None:
        self._config = config
        self._failure_point = failure_point

    def restore(self, request: PermitReplayRestoreRequest) -> PermitReplayRestoreReceipt:
        config = self._config
        for path in (request.backup_path, request.manifest_path):
            _validate_absolute(path, repository_root=config.repository_root, must_exist=True)
        _validate_absolute(config.restore_root, repository_root=config.repository_root,
                           must_exist=True, directory=True)
        _validate_absolute(request.restore_path, repository_root=config.repository_root,
                           root=config.restore_root)
        if request.production_authorized:
            raise PermitReplayRecoveryError("PRODUCTION_PROHIBITED")
        if request.restore_path.exists():
            raise PermitReplayRecoveryError("RESTORE_TARGET_EXISTS")
        if request.restore_path in (request.backup_path, request.manifest_path):
            raise PermitReplayRecoveryError("SOURCE_DESTINATION_OVERLAP")
        manifest = _load_manifest(request.manifest_path)
        if manifest.backup_path_identity_digest != _identity(request.backup_path):
            raise PermitReplayRecoveryError("MANIFEST_PATH_MISMATCH")
        backup_before = _bytes_digest(request.backup_path)
        if backup_before != manifest.database_byte_digest:
            raise PermitReplayRecoveryError("DATABASE_DIGEST_MISMATCH")
        report = _inspect(request.backup_path, config, request.restored_at)
        if report.status is not PermitReplayStatus.HEALTHY:
            raise PermitReplayRecoveryError("BACKUP_NOT_HEALTHY")
        rows, logical, states = _snapshot(request.backup_path)
        if logical != manifest.logical_event_ledger_digest:
            raise PermitReplayRecoveryError("LOGICAL_LEDGER_DIGEST_MISMATCH")
        if states != manifest.derived_permit_state_digest:
            raise PermitReplayRecoveryError("PERMIT_STATE_DIGEST_MISMATCH")
        if report.schema_version != manifest.schema_version or report.event_count != manifest.event_count:
            raise PermitReplayRecoveryError("MANIFEST_DATABASE_MISMATCH")
        temp: Path | None = None
        try:
            fd, name = tempfile.mkstemp(prefix=".permit-replay-restore-", suffix=".tmp",
                                        dir=config.restore_root)
            os.close(fd)
            temp = Path(name)
            os.chmod(temp, 0o600)
            with _open_read_only(request.backup_path) as source:
                destination = sqlite3.connect(temp)
                try:
                    source.backup(destination)
                finally:
                    destination.close()
            restored_report = _inspect(temp, config, request.restored_at)
            restored_rows, restored_logical, restored_states = _snapshot(temp)
            if (restored_report.status is not PermitReplayStatus.HEALTHY or
                    restored_rows != rows or restored_logical != logical or
                    restored_states != states):
                raise PermitReplayRecoveryError("RESTORED_CONTENT_MISMATCH")
            if self._failure_point == "before_final_rename":
                raise PermitReplayRecoveryError("INJECTED_RESTORE_FAILURE")
            os.replace(temp, request.restore_path)
            temp = None
            if _bytes_digest(request.backup_path) != backup_before:
                raise PermitReplayRecoveryError("BACKUP_CHANGED_DURING_RESTORE")
            semantic = {
                "backup_id": manifest.backup_id,
                "restore_path_identity_digest": _identity(request.restore_path),
                "manifest_digest": manifest.manifest_digest,
                "database_byte_digest": manifest.database_byte_digest,
                "logical_event_ledger_digest": logical,
                "derived_permit_state_digest": states,
                "restored_at": request.restored_at,
                "selected_operationally": False,
                "production_authorized": False,
            }
            return PermitReplayRestoreReceipt(
                **semantic, receipt_digest=sha256_digest(semantic)
            )
        finally:
            if temp is not None and temp.exists():
                temp.unlink()
