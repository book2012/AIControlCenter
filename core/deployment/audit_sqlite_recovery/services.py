"""Fail-closed online backup, restore, and recovery validation services."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import quote

from core.deployment.audit_sqlite import (
    SQLiteAuditPathPolicy,
    SQLiteAuditReadOnlyInspector,
    SQLiteAuditStatus,
    SQLiteAuditStorageConfig,
)
from core.deployment.contracts import canonical_json_bytes, sha256_digest

from .models import (
    SQLiteAuditBackupConfig,
    SQLiteAuditBackupManifest,
    SQLiteAuditBackupReceipt,
    SQLiteAuditBackupRequest,
    SQLiteAuditRecoveryError,
    SQLiteAuditRecoveryFinding,
    SQLiteAuditRecoveryStatus,
    SQLiteAuditRecoveryValidationReport,
    SQLiteAuditRestoreConfig,
    SQLiteAuditRestoreReceipt,
    SQLiteAuditRestoreRequest,
)

_EVENT_QUERY = (
    "SELECT ledger_sequence,event_id,schema_version,event_type,recorded_at,"
    "actor_identity,canonical_payload,payload_digest,previous_event_hash,"
    "event_hash,production_authorized FROM audit_events ORDER BY ledger_sequence,event_id"
)


def _bytes_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _rows(path: Path, timeout: float) -> tuple[tuple[object, ...], ...]:
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True, timeout=timeout, isolation_level=None)
    try:
        connection.execute("PRAGMA query_only=ON")
        return tuple(tuple(row) for row in connection.execute(_EVENT_QUERY))
    finally:
        connection.close()


def _logical_digest(rows: tuple[tuple[object, ...], ...]) -> str:
    return sha256_digest([list(row) for row in rows])


def _manifest(path: Path) -> SQLiteAuditBackupManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError
        digest = raw.pop("manifest_digest")
        if digest != sha256_digest(raw):
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.TAMPERED, "MANIFEST_DIGEST_MISMATCH"
            )
        return SQLiteAuditBackupManifest(**raw, manifest_digest=digest)
    except SQLiteAuditRecoveryError:
        raise
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        raise SQLiteAuditRecoveryError(
            SQLiteAuditRecoveryStatus.DENIED, "MANIFEST_INVALID"
        ) from error


class _Base:
    def __init__(self, path_policy: SQLiteAuditPathPolicy) -> None:
        if path_policy is None:
            raise ValueError("explicit path policy required")
        self._policy = path_policy

    def _validate(self, path: Path, *, root: Path | None = None) -> None:
        violations = self._policy.validate(path)
        if violations:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.BLOCKED, violations[0]
            )
        if root is not None:
            if not root.is_dir() or root.is_symlink():
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.BLOCKED, "ROOT_UNAVAILABLE"
                )
            try:
                path.relative_to(root)
            except ValueError as error:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.BLOCKED, "PATH_OUTSIDE_SUPPLIED_ROOT"
                ) from error
            if path.parent != root:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.BLOCKED, "TARGET_PARENT_NOT_ROOT"
                )

    def _inspect(self, path: Path, at: str):
        return SQLiteAuditReadOnlyInspector(
            config=SQLiteAuditStorageConfig(path), path_policy=self._policy
        ).inspect(inspected_at=at)


class SQLiteAuditBackupService(_Base):
    def __init__(self, *, config: SQLiteAuditBackupConfig,
                 path_policy: SQLiteAuditPathPolicy) -> None:
        super().__init__(path_policy)
        self._config = config

    def _receipt(self, manifest: SQLiteAuditBackupManifest, *,
                 unchanged: bool, idempotent: bool) -> SQLiteAuditBackupReceipt:
        return SQLiteAuditBackupReceipt.build(
            backup_id=manifest.backup_id,
            backup_path_identity_digest=manifest.backup_path_identity_digest,
            manifest_digest=manifest.manifest_digest,
            database_byte_digest=manifest.database_byte_digest,
            logical_ledger_digest=manifest.logical_ledger_digest,
            event_count=manifest.event_count, source_unchanged=unchanged,
            idempotent_retry=idempotent,
            status=SQLiteAuditRecoveryStatus.BACKUP_COMPLETE,
            production_authorized=False, operational_backup=False,
        )

    def backup(self, request: SQLiteAuditBackupRequest) -> SQLiteAuditBackupReceipt:
        source = self._config.source_path
        backup, manifest_path = request.backup_path, request.manifest_path
        self._validate(source)
        self._validate(backup, root=self._config.backup_root)
        self._validate(manifest_path, root=self._config.backup_root)
        if len({source, backup, manifest_path}) != 3:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.DENIED, "PATH_OVERLAP"
            )
        if source.is_symlink() or not source.is_file():
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.DENIED, "SOURCE_UNAVAILABLE"
            )
        source_before = _bytes_digest(source)
        report = self._inspect(source, request.created_at)
        if report.status is not SQLiteAuditStatus.HEALTHY:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.DENIED, "SOURCE_NOT_HEALTHY"
            )
        source_rows = _rows(source, self._config.timeout_seconds)
        logical = _logical_digest(source_rows)
        identity = {
            "source_path_identity_digest": self._policy.identity_digest(source),
            "backup_path_identity_digest": self._policy.identity_digest(backup),
            "source_database_byte_digest": source_before,
            "logical_ledger_digest": logical,
            "created_at": request.created_at,
            "production_authorized": False,
            "operational_backup": False,
        }
        backup_id = "sqlite-backup-" + sha256_digest(identity)[7:39]
        if backup.exists() or manifest_path.exists():
            if not (backup.is_file() and manifest_path.is_file()):
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.DENIED, "BACKUP_TARGET_CONFLICT"
                )
            existing = _manifest(manifest_path)
            if (
                existing.backup_id == backup_id
                and existing.database_byte_digest == _bytes_digest(backup)
                and existing.logical_ledger_digest
                == _logical_digest(_rows(backup, self._config.timeout_seconds))
                and existing.backup_path_identity_digest
                == self._policy.identity_digest(backup)
            ):
                return self._receipt(existing, unchanged=_bytes_digest(source) == source_before,
                                     idempotent=True)
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.DENIED, "BACKUP_TARGET_CONFLICT"
            )
        temporary: Path | None = None
        temporary_manifest: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                prefix=".m3-a1c-backup-", suffix=".sqlite3",
                dir=self._config.backup_root
            )
            os.close(descriptor)
            temporary = Path(name)
            os.chmod(temporary, 0o600)
            source_connection = sqlite3.connect(
                "file:" + quote(str(source), safe="/") + "?mode=ro",
                uri=True, timeout=self._config.timeout_seconds
            )
            destination_connection = sqlite3.connect(temporary)
            try:
                source_connection.backup(destination_connection)
            finally:
                destination_connection.close()
                source_connection.close()
            temporary_report = self._inspect(temporary, request.created_at)
            if temporary_report.status is not SQLiteAuditStatus.HEALTHY:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "BACKUP_INSPECTION_FAILED"
                )
            backup_rows = _rows(temporary, self._config.timeout_seconds)
            if backup_rows != source_rows:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "BACKUP_LOGICAL_MISMATCH"
                )
            manifest = SQLiteAuditBackupManifest.build(
                backup_id=backup_id,
                source_path_identity_digest=self._policy.identity_digest(source),
                backup_path_identity_digest=self._policy.identity_digest(backup),
                schema_version=report.schema_version or "",
                event_count=len(source_rows),
                first_ledger_sequence=int(source_rows[0][0]) if source_rows else None,
                last_ledger_sequence=int(source_rows[-1][0]) if source_rows else None,
                first_event_hash=str(source_rows[0][9]) if source_rows else None,
                last_event_hash=str(source_rows[-1][9]) if source_rows else None,
                database_byte_digest=_bytes_digest(temporary),
                logical_ledger_digest=logical,
                source_inspection_report_id=report.report_id,
                source_inspection_report_digest=report.report_digest,
                created_at=request.created_at, production_authorized=False,
                operational_backup=False,
            )
            descriptor, name = tempfile.mkstemp(
                prefix=".m3-a1c-manifest-", suffix=".json",
                dir=self._config.backup_root
            )
            temporary_manifest = Path(name)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(canonical_json_bytes(manifest.as_dict()))
            os.chmod(temporary_manifest, 0o600)
            if _manifest(temporary_manifest) != manifest:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "MANIFEST_BINDING_FAILED"
                )
            os.replace(temporary, backup)
            temporary = None
            os.replace(temporary_manifest, manifest_path)
            temporary_manifest = None
            unchanged = _bytes_digest(source) == source_before
            if not unchanged:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "SOURCE_CHANGED"
                )
            return self._receipt(manifest, unchanged=True, idempotent=False)
        except Exception:
            if backup.exists() and not manifest_path.exists():
                backup.unlink()
            raise
        finally:
            for candidate in (temporary, temporary_manifest):
                if candidate is not None and candidate.parent == self._config.backup_root:
                    candidate.unlink(missing_ok=True)


class SQLiteAuditRestoreService(_Base):
    def __init__(self, *, config: SQLiteAuditRestoreConfig,
                 path_policy: SQLiteAuditPathPolicy) -> None:
        super().__init__(path_policy)
        self._config = config

    def restore(self, request: SQLiteAuditRestoreRequest) -> SQLiteAuditRestoreReceipt:
        backup, manifest_path, target = (
            request.backup_path, request.manifest_path, request.restore_path
        )
        self._validate(backup)
        self._validate(manifest_path)
        self._validate(target, root=self._config.restore_root)
        if len({backup, manifest_path, target}) != 3:
            raise SQLiteAuditRecoveryError(SQLiteAuditRecoveryStatus.DENIED, "PATH_OVERLAP")
        if target.exists():
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.DENIED, "RESTORE_TARGET_EXISTS"
            )
        if not backup.is_file() or backup.is_symlink() or not manifest_path.is_file():
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.DENIED, "BACKUP_OR_MANIFEST_UNAVAILABLE"
            )
        manifest = _manifest(manifest_path)
        backup_before = _bytes_digest(backup)
        backup_rows = _rows(backup, self._config.timeout_seconds)
        if backup_before != manifest.database_byte_digest:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.TAMPERED, "DATABASE_BYTE_DIGEST_MISMATCH"
            )
        if _logical_digest(backup_rows) != manifest.logical_ledger_digest:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.TAMPERED, "LOGICAL_LEDGER_DIGEST_MISMATCH"
            )
        report = self._inspect(backup, request.restored_at)
        if report.status is not SQLiteAuditStatus.HEALTHY:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.TAMPERED, "BACKUP_INSPECTION_FAILED"
            )
        if report.schema_version != manifest.schema_version:
            raise SQLiteAuditRecoveryError(
                SQLiteAuditRecoveryStatus.TAMPERED, "SCHEMA_MISMATCH"
            )
        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                prefix=".m3-a1c-restore-", suffix=".sqlite3",
                dir=self._config.restore_root
            )
            os.close(descriptor)
            temporary = Path(name)
            os.chmod(temporary, 0o600)
            source = sqlite3.connect(
                "file:" + quote(str(backup), safe="/") + "?mode=ro",
                uri=True, timeout=self._config.timeout_seconds
            )
            destination = sqlite3.connect(temporary)
            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()
            restored_rows = _rows(temporary, self._config.timeout_seconds)
            restored_report = self._inspect(temporary, request.restored_at)
            if restored_report.status is not SQLiteAuditStatus.HEALTHY:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "RESTORED_INSPECTION_FAILED"
                )
            if restored_rows != backup_rows:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "RESTORED_LEDGER_MISMATCH"
                )
            restored_byte_digest = _bytes_digest(temporary)
            if restored_byte_digest != manifest.database_byte_digest:
                raise SQLiteAuditRecoveryError(
                    SQLiteAuditRecoveryStatus.FAILED, "RESTORED_BYTE_DIGEST_MISMATCH"
                )
            os.replace(temporary, target)
            temporary = None
            return SQLiteAuditRestoreReceipt.build(
                backup_id=manifest.backup_id,
                restore_path_identity_digest=self._policy.identity_digest(target),
                manifest_digest=manifest.manifest_digest,
                database_byte_digest=restored_byte_digest,
                logical_ledger_digest=_logical_digest(restored_rows),
                event_count=len(restored_rows),
                backup_unchanged=_bytes_digest(backup) == backup_before,
                restored_at=request.restored_at,
                status=SQLiteAuditRecoveryStatus.RESTORE_COMPLETE,
                production_authorized=False, operational_restore=False,
            )
        finally:
            if temporary is not None and temporary.parent == self._config.restore_root:
                temporary.unlink(missing_ok=True)


class SQLiteAuditRecoveryValidator(_Base):
    def validate(self, *, source_path: Path, backup_path: Path, restore_path: Path,
                 manifest_path: Path, validated_at: str
                 ) -> SQLiteAuditRecoveryValidationReport:
        for path in (source_path, backup_path, restore_path, manifest_path):
            self._validate(Path(path))
        if len({source_path, backup_path, restore_path, manifest_path}) != 4:
            raise SQLiteAuditRecoveryError(SQLiteAuditRecoveryStatus.DENIED, "PATH_OVERLAP")
        manifest = _manifest(manifest_path)
        source_rows = _rows(source_path, 2.0)
        backup_rows = _rows(backup_path, 2.0)
        restored_rows = _rows(restore_path, 2.0)
        source_report = self._inspect(source_path, validated_at)
        backup_report = self._inspect(backup_path, validated_at)
        restored_report = self._inspect(restore_path, validated_at)
        checks = {
            "schema_matches": (
                source_report.schema_version == backup_report.schema_version
                == restored_report.schema_version == manifest.schema_version
            ),
            "event_count_matches": (
                len(source_rows) == len(backup_rows) == len(restored_rows)
                == manifest.event_count
            ),
            "event_identity_matches": (
                tuple((r[0], r[1]) for r in source_rows)
                == tuple((r[0], r[1]) for r in backup_rows)
                == tuple((r[0], r[1]) for r in restored_rows)
            ),
            "payload_digests_match": (
                tuple(r[7] for r in source_rows) == tuple(r[7] for r in backup_rows)
                == tuple(r[7] for r in restored_rows)
            ),
            "previous_hashes_match": (
                tuple(r[8] for r in source_rows) == tuple(r[8] for r in backup_rows)
                == tuple(r[8] for r in restored_rows)
            ),
            "event_hashes_match": (
                tuple(r[9] for r in source_rows) == tuple(r[9] for r in backup_rows)
                == tuple(r[9] for r in restored_rows)
            ),
        }
        logical = tuple(_logical_digest(rows) for rows in
                        (source_rows, backup_rows, restored_rows))
        source_unchanged = (
            logical[0] == manifest.logical_ledger_digest
            and self._policy.identity_digest(source_path)
            == manifest.source_path_identity_digest
        )
        backup_unchanged = (
            logical[1] == manifest.logical_ledger_digest
            and _bytes_digest(backup_path) == manifest.database_byte_digest
            and self._policy.identity_digest(backup_path)
            == manifest.backup_path_identity_digest
        )
        findings = list(
            SQLiteAuditRecoveryFinding(key.upper(), "ERROR", "recovery comparison failed")
            for key, valid in checks.items() if not valid
        )
        if len(set(logical)) != 1:
            findings.append(SQLiteAuditRecoveryFinding(
                "LOGICAL_LEDGER_DIGEST_MISMATCH", "ERROR",
                "source, backup and restored logical digests differ",
            ))
        if not source_unchanged:
            findings.append(SQLiteAuditRecoveryFinding(
                "SOURCE_STATE_MISMATCH", "ERROR",
                "source state does not match the backup manifest",
            ))
        if not backup_unchanged:
            findings.append(SQLiteAuditRecoveryFinding(
                "BACKUP_STATE_MISMATCH", "ERROR",
                "backup state does not match the backup manifest",
            ))
        healthy = all(
            report.status is SQLiteAuditStatus.HEALTHY
            for report in (source_report, backup_report, restored_report)
        )
        if not healthy:
            findings.append(SQLiteAuditRecoveryFinding(
                "INSPECTION_NOT_HEALTHY", "ERROR",
                "one or more recovery databases failed read-only inspection",
            ))
        valid = not findings
        return SQLiteAuditRecoveryValidationReport.build(
            status=(SQLiteAuditRecoveryStatus.RECOVERY_VALID if valid
                    else SQLiteAuditRecoveryStatus.TAMPERED),
            backup_id=manifest.backup_id,
            source_path_identity_digest=self._policy.identity_digest(source_path),
            backup_path_identity_digest=self._policy.identity_digest(backup_path),
            restore_path_identity_digest=self._policy.identity_digest(restore_path),
            source_logical_ledger_digest=logical[0],
            backup_logical_ledger_digest=logical[1],
            restored_logical_ledger_digest=logical[2],
            **checks, source_unchanged=source_unchanged,
            backup_unchanged=backup_unchanged,
            restored_inspection_healthy=(
                restored_report.status is SQLiteAuditStatus.HEALTHY
            ),
            production_authorization_violations=sum(
                r.production_authorization_violations
                for r in (source_report, backup_report, restored_report)
            ),
            secret_bearing_violations=sum(
                int(r.privacy_result != "VALID")
                for r in (source_report, backup_report, restored_report)
            ),
            findings=findings, validated_at=validated_at,
            operational_activation=False, production_authorized=False,
        )
