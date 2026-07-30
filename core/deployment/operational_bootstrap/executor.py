"""Controlled Mac bootstrap executor restricted to injected pytest paths."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
from dataclasses import asdict
from pathlib import Path
from typing import Any

from core.deployment.audit_sqlite import (
    SQLiteAuditReadOnlyInspector, SQLiteAuditSchemaExpectation,
    SQLiteAuditStatus, SQLiteAuditStorageConfig,
)
from core.deployment.contracts import sha256_digest
from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapPermitUseGuard, OperationalBootstrapPermitValidator,
)
from core.deployment.permit_replay_sqlite import (
    PermitReplayReadOnlyInspector, PermitReplaySchemaExpectation,
    PermitReplayStatus, PermitReplayStorageConfig,
)

from .models import (
    ORDERED_STEPS, OperationalBootstrapError, OperationalBootstrapEvidenceBundle,
    OperationalBootstrapExecutionPlan, OperationalBootstrapExecutorConfig,
    OperationalBootstrapReceipt, OperationalBootstrapRequest,
    OperationalBootstrapSchemaPlan, OperationalBootstrapStatus,
    OperationalBootstrapStepReceipt, OperationalBootstrapTargetPaths, path_identity,
)


class _TestRootPathPolicy:
    def __init__(self, root: Path, repository_root: Path) -> None:
        self.root, self.repository_root = root, repository_root

    def identity_digest(self, path: Path) -> str:
        return path_identity(path)

    def validate(self, path: Path) -> tuple[str, ...]:
        try:
            path.relative_to(self.root)
        except ValueError:
            return ("OUTSIDE_TEST_ROOT",)
        try:
            path.relative_to(self.repository_root)
            return ("REPOSITORY_PATH",)
        except ValueError:
            return ()


class MacSQLiteBootstrapAdapter:
    """Standard-library-only SQLite schema and backup adapter."""

    AUDIT_DDL = """
    CREATE TABLE audit_ledger_meta(schema_version TEXT NOT NULL);
    CREATE TABLE audit_events(
      ledger_sequence INTEGER NOT NULL,event_id TEXT NOT NULL,
      schema_version TEXT NOT NULL,event_type TEXT NOT NULL,recorded_at TEXT NOT NULL,
      actor_identity TEXT NOT NULL,canonical_payload TEXT NOT NULL,
      payload_digest TEXT NOT NULL,previous_event_hash TEXT NOT NULL,
      event_hash TEXT NOT NULL,production_authorized INTEGER NOT NULL
      CHECK(production_authorized=0));
    CREATE UNIQUE INDEX ux_audit_events_event_id ON audit_events(event_id);
    CREATE UNIQUE INDEX ux_audit_events_ledger_sequence ON audit_events(ledger_sequence);
    CREATE TRIGGER trg_audit_events_no_update BEFORE UPDATE ON audit_events
      BEGIN SELECT RAISE(ABORT,'immutable'); END;
    CREATE TRIGGER trg_audit_events_no_delete BEFORE DELETE ON audit_events
      BEGIN SELECT RAISE(ABORT,'immutable'); END;
    """
    REPLAY_DDL = """
    CREATE TABLE permit_replay_meta(schema_version TEXT NOT NULL);
    CREATE TABLE permit_use_events(
      ledger_sequence INTEGER NOT NULL,event_id TEXT NOT NULL,permit_id TEXT NOT NULL,
      permit_digest TEXT NOT NULL,activation_id TEXT NOT NULL,
      activation_request_digest TEXT NOT NULL,event_type TEXT NOT NULL
      CHECK(event_type IN ('RESERVED','CONSUMED','FAILED_CLOSED')),
      event_at TEXT NOT NULL,actor_identity TEXT NOT NULL,target_identity TEXT NOT NULL,
      environment TEXT NOT NULL CHECK(environment <> 'production'),
      canonical_payload TEXT NOT NULL,payload_digest TEXT NOT NULL,
      previous_event_hash TEXT NOT NULL,event_hash TEXT NOT NULL,
      production_authorized INTEGER NOT NULL CHECK(production_authorized=0));
    CREATE UNIQUE INDEX ux_permit_use_events_event_id ON permit_use_events(event_id);
    CREATE UNIQUE INDEX ux_permit_use_events_ledger_sequence ON permit_use_events(ledger_sequence);
    CREATE UNIQUE INDEX ux_permit_use_events_one_reservation ON permit_use_events(permit_id)
      WHERE event_type='RESERVED';
    CREATE UNIQUE INDEX ux_permit_use_events_one_terminal ON permit_use_events(permit_id)
      WHERE event_type IN ('CONSUMED','FAILED_CLOSED');
    CREATE TRIGGER trg_permit_use_events_no_update BEFORE UPDATE ON permit_use_events
      BEGIN SELECT RAISE(ABORT,'immutable'); END;
    CREATE TRIGGER trg_permit_use_events_no_delete BEFORE DELETE ON permit_use_events
      BEGIN SELECT RAISE(ABORT,'immutable'); END;
    """

    @staticmethod
    def create(path: Path, ddl: str, meta_table: str, version: str,
               timeout_ms: int) -> None:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(path, timeout=timeout_ms / 1000)
            connection.execute(f"PRAGMA busy_timeout={timeout_ms}")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=FULL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.executescript(ddl)
            connection.execute(f"INSERT INTO {meta_table} VALUES (?)", (version,))
            connection.commit()
        except Exception:
            if connection is not None:
                connection.rollback()
            raise
        finally:
            if connection is not None:
                connection.close()
        os.chmod(path, 0o600)

    @staticmethod
    def backup(source: Path, destination: Path, manifest: Path) -> tuple[str, str]:
        source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        destination_connection = sqlite3.connect(destination)
        try:
            source_connection.backup(destination_connection)
        finally:
            destination_connection.close()
            source_connection.close()
        os.chmod(destination, 0o600)
        digest = "sha256:" + hashlib.sha256(destination.read_bytes()).hexdigest()
        content = {"database_byte_digest": digest, "production_authorized": False}
        manifest.write_text(json.dumps(content, sort_keys=True, separators=(",", ":")))
        os.chmod(manifest, 0o600)
        return digest, sha256_digest(content)


class ControlledMacBootstrapExecutor:
    def __init__(self, *, config: OperationalBootstrapExecutorConfig,
                 permit_registry: object) -> None:
        self.config = config
        self.registry = permit_registry
        self.paths = OperationalBootstrapTargetPaths.under(config.test_root)
        self.plan = OperationalBootstrapExecutionPlan.build()
        self.schema = OperationalBootstrapSchemaPlan()

    def _validate_root(self) -> None:
        root = self.config.test_root
        expected = os.environ.get("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT")
        if not expected or root != Path(expected) or not root.is_absolute() or ".." in root.parts:
            raise OperationalBootstrapError("TEST_ROOT_BINDING_INVALID")
        raw = str(root)
        if not raw.startswith("/private/tmp/"):
            raise OperationalBootstrapError("TEST_ROOT_NOT_PRIVATE_TMP")
        protected = ("/System", "/Library", "/Applications", "/usr", "/bin", "/sbin",
                     "/etc", "/home", "/var", "/srv", "/mnt", "/media", "/Volumes")
        if any(raw == value or raw.startswith(value + "/") for value in protected):
            raise OperationalBootstrapError("PROTECTED_TARGET_REJECTED")
        try:
            root.relative_to(self.config.repository_root.resolve())
            raise OperationalBootstrapError("REPOSITORY_TARGET_REJECTED")
        except ValueError:
            pass
        current = Path(root.anchor)
        for part in root.parts[1:]:
            current /= part
            if current.is_symlink():
                raise OperationalBootstrapError("SYMLINK_TARGET_REJECTED")
            if not current.exists():
                break

    def execute(self, *, request: OperationalBootstrapRequest, permit: object,
                authorization_request: object, authorization_decision: object
                ) -> OperationalBootstrapEvidenceBundle:
        created: list[Path] = []
        step_receipts: list[Any] = []
        claim = None
        try:
            self._step(ORDERED_STEPS[0], step_receipts)
            self._validate_root()
            self._step(ORDERED_STEPS[1], step_receipts)
            if request.branch != "feature/deployment-package":
                raise OperationalBootstrapError("BRANCH_REJECTED")
            target = authorization_request.target_binding
            expected_targets = {
                "audit_database_identity_digest": path_identity(self.paths.audit_database),
                "audit_backup_root_identity_digest": path_identity(self.paths.audit_backup_root),
                "replay_database_identity_digest": path_identity(self.paths.replay_database),
                "replay_backup_root_identity_digest": path_identity(self.paths.replay_backup_root),
                "monitoring_root_identity_digest": path_identity(self.paths.monitoring_directory),
            }
            if any(getattr(target, key) != value
                   for key, value in expected_targets.items()):
                raise OperationalBootstrapError("TARGET_BINDING_INVALID")
            if (authorization_request.schema_binding.audit_schema_expectation_digest
                    != sha256_digest(asdict(SQLiteAuditSchemaExpectation()))
                    or authorization_request.schema_binding.replay_schema_expectation_digest
                    != sha256_digest(asdict(PermitReplaySchemaExpectation()))
                    or authorization_request.plan_binding.bootstrap_plan_digest
                    != self.plan.plan_digest):
                raise OperationalBootstrapError("SCHEMA_OR_PLAN_BINDING_INVALID")
            report = OperationalBootstrapPermitValidator().validate(
                permit=permit, request=authorization_request,
                decision=authorization_decision, validated_at=request.started_at,
                branch=request.branch, commit=request.commit)
            if not report.valid:
                raise OperationalBootstrapError("SYNTHETIC_PERMIT_INVALID")
            self._step(ORDERED_STEPS[2], step_receipts)
            claim = OperationalBootstrapPermitUseGuard(self.registry).claim(
                permit=permit, request=authorization_request,
                decision=authorization_decision, claimant_identity=request.claimant_identity,
                claimed_at=request.started_at, branch=request.branch, commit=request.commit)
            self._step(ORDERED_STEPS[3], step_receipts)
            if self.paths.application_state.exists() or self.paths.restore_validation_root.exists():
                raise OperationalBootstrapError("TARGET_ALREADY_EXISTS")
            self._step(ORDERED_STEPS[4], step_receipts)
            for path in (self.paths.application_state, self.paths.audit_directory,
                         self.paths.audit_backup_root, self.paths.security_directory,
                         self.paths.replay_backup_root, self.paths.monitoring_directory):
                path.mkdir()
                os.chmod(path, 0o700)
                created.append(path)
            self._step(ORDERED_STEPS[5], step_receipts)
            if any(stat.S_IMODE(path.stat().st_mode) != 0o700 for path in created):
                raise OperationalBootstrapError("DIRECTORY_PERMISSION_INVALID")
            self._step(ORDERED_STEPS[6], step_receipts)
            MacSQLiteBootstrapAdapter.create(
                self.paths.audit_database, MacSQLiteBootstrapAdapter.AUDIT_DDL,
                "audit_ledger_meta", self.schema.audit_schema_version,
                self.config.busy_timeout_ms)
            created.append(self.paths.audit_database)
            self._step(ORDERED_STEPS[7], step_receipts)
            self._step(ORDERED_STEPS[8], step_receipts)
            policy = _TestRootPathPolicy(self.config.test_root, self.config.repository_root)
            audit_report = SQLiteAuditReadOnlyInspector(
                config=SQLiteAuditStorageConfig(self.paths.audit_database),
                path_policy=policy, schema=SQLiteAuditSchemaExpectation()).inspect(
                    inspected_at=request.started_at)
            if audit_report.status is not SQLiteAuditStatus.HEALTHY or audit_report.event_count:
                raise OperationalBootstrapError("AUDIT_INSPECTION_FAILED")
            self._step(ORDERED_STEPS[9], step_receipts)
            MacSQLiteBootstrapAdapter.create(
                self.paths.replay_database, MacSQLiteBootstrapAdapter.REPLAY_DDL,
                "permit_replay_meta", self.schema.replay_schema_version,
                self.config.busy_timeout_ms)
            created.append(self.paths.replay_database)
            self._step(ORDERED_STEPS[10], step_receipts)
            self._step(ORDERED_STEPS[11], step_receipts)
            replay_report = PermitReplayReadOnlyInspector(
                config=PermitReplayStorageConfig(self.paths.replay_database),
                path_policy=policy, schema=PermitReplaySchemaExpectation()).inspect(
                    inspected_at=request.started_at)
            if replay_report.status is not PermitReplayStatus.HEALTHY or replay_report.event_count:
                raise OperationalBootstrapError("REPLAY_INSPECTION_FAILED")
            self._step(ORDERED_STEPS[12], step_receipts)
            audit_backup = self.paths.audit_backup_root / "baseline-audit.sqlite3"
            audit_manifest = self.paths.audit_backup_root / "baseline-audit.manifest.json"
            audit_backup_digest, audit_manifest_digest = MacSQLiteBootstrapAdapter.backup(
                self.paths.audit_database, audit_backup, audit_manifest)
            created.extend((audit_backup, audit_manifest))
            self._step(ORDERED_STEPS[13], step_receipts)
            restore_root = self.paths.restore_validation_root
            restore_root.mkdir()
            os.chmod(restore_root, 0o700)
            created.append(restore_root)
            audit_restore = restore_root / "audit.sqlite3"
            shutil.copyfile(audit_backup, audit_restore)
            os.chmod(audit_restore, 0o600)
            created.append(audit_restore)
            restored_audit = SQLiteAuditReadOnlyInspector(
                config=SQLiteAuditStorageConfig(audit_restore), path_policy=policy).inspect(
                    inspected_at=request.completed_at)
            if restored_audit.status is not SQLiteAuditStatus.HEALTHY:
                raise OperationalBootstrapError("AUDIT_RESTORE_INVALID")
            self._step(ORDERED_STEPS[14], step_receipts)
            replay_backup = self.paths.replay_backup_root / "baseline-replay.sqlite3"
            replay_manifest = self.paths.replay_backup_root / "baseline-replay.manifest.json"
            replay_backup_digest, replay_manifest_digest = MacSQLiteBootstrapAdapter.backup(
                self.paths.replay_database, replay_backup, replay_manifest)
            created.extend((replay_backup, replay_manifest))
            self._step(ORDERED_STEPS[15], step_receipts)
            replay_restore = restore_root / "replay.sqlite3"
            shutil.copyfile(replay_backup, replay_restore)
            os.chmod(replay_restore, 0o600)
            created.append(replay_restore)
            restored_replay = PermitReplayReadOnlyInspector(
                config=PermitReplayStorageConfig(replay_restore), path_policy=policy).inspect(
                    inspected_at=request.completed_at)
            if restored_replay.status is not PermitReplayStatus.HEALTHY:
                raise OperationalBootstrapError("REPLAY_RESTORE_INVALID")
            self._step(ORDERED_STEPS[16], step_receipts)
            monitoring_content = {
                "stage": "PRE_ACTIVATION", "audit_integrity": "HEALTHY",
                "replay_integrity": "HEALTHY", "backup_restore": "VALID",
                "writers_active": False, "monitoring_active": False,
                "external_dispatch_active": False, "production_authorized": False,
            }
            monitoring_digest = sha256_digest(monitoring_content)
            monitoring_id = "m3-a4b2a-monitoring-" + monitoring_digest[7:39]
            self._step(ORDERED_STEPS[17], step_receipts)
            self._step(ORDERED_STEPS[18], step_receipts)
            receipt_content = {
                "request_id": request.request_id, "permit_id": permit.permit_id,
                "execution_mode": self.config.mode.value, "branch": request.branch,
                "commit": request.commit, "status": "COMPLETE",
                "completed_steps": list(ORDERED_STEPS), "created_directory_count": 6,
                "created_database_count": 2, "created_backup_count": 2,
                "validated_restore_count": 2, "transaction_committed": True,
                "complete": True, "test_only": True, "operational_bootstrap": False,
                "writers_activated": False, "monitoring_activated": False,
                "external_dispatch_activated": False, "production_authorized": False,
            }
            receipt_digest = sha256_digest(receipt_content)
            receipt_id = "m3-a4b2a-receipt-" + receipt_digest[7:39]
            receipt = OperationalBootstrapReceipt(
                receipt_id, request.request_id, permit.permit_id, self.config.mode,
                request.branch, request.commit, OperationalBootstrapStatus.COMPLETE,
                ORDERED_STEPS, 6, 2, 2, 2, True, True, receipt_digest)
            self._step(ORDERED_STEPS[19], step_receipts)
            claim_digest = sha256_digest(asdict(claim))
            permissions = tuple(
                (path_identity(path), oct(stat.S_IMODE(path.stat().st_mode)))
                for path in (self.paths.application_state, self.paths.audit_directory,
                             self.paths.audit_backup_root, self.paths.security_directory,
                             self.paths.replay_backup_root, self.paths.monitoring_directory))
            inventory_paths = (
                self.paths.audit_database, self.paths.replay_database, audit_backup,
                audit_manifest, replay_backup, replay_manifest)
            inventory = tuple((path_identity(path), "sha256:" + hashlib.sha256(
                path.read_bytes()).hexdigest()) for path in inventory_paths)
            evidence_content = {
                "receipt_id": receipt_id, "receipt_digest": receipt_digest,
                "permit_id": permit.permit_id, "permit_digest": permit.permit_digest,
                "claim_id": claim.claim_id, "claim_digest": claim_digest,
                "branch": request.branch, "commit": request.commit,
                "mode": self.config.mode.value, "target": path_identity(self.config.test_root),
                "steps": [item.as_dict() for item in step_receipts],
                "audit_inspection": audit_report.report_digest,
                "replay_inspection": replay_report.report_digest,
                "monitoring": monitoring_digest, "inventory": inventory,
                "started_at": request.started_at, "completed_at": request.completed_at,
            }
            evidence_digest = sha256_digest(evidence_content)
            bundle = OperationalBootstrapEvidenceBundle(
                "m3-a4b2a-evidence-" + evidence_digest[7:39], receipt, receipt_id,
                receipt_digest, permit.permit_id, permit.permit_digest, claim.claim_id,
                claim_digest, request.branch, request.commit, self.config.mode,
                path_identity(self.config.test_root), tuple(step_receipts), permissions,
                path_identity(self.paths.audit_database), self.schema.plan_digest,
                audit_report.report_digest, path_identity(self.paths.replay_database),
                self.schema.plan_digest, replay_report.report_digest,
                audit_backup_digest, restored_audit.report_digest, replay_backup_digest,
                restored_replay.report_digest, monitoring_id, monitoring_digest,
                inventory, request.started_at, request.completed_at, evidence_digest)
            if self.config.cleanup_restore_targets:
                shutil.rmtree(restore_root)
            return bundle
        except Exception:
            # Both roots were proven absent immediately before mutation, so recursive
            # removal is confined to artifacts owned by this execution (including
            # SQLite-managed WAL/SHM sidecars).
            for owned_root in (self.paths.restore_validation_root,
                               self.paths.application_state):
                if owned_root.exists():
                    shutil.rmtree(owned_root)
            for path in reversed(created):
                try:
                    if path.is_file() or path.is_symlink():
                        path.unlink()
                    elif path.is_dir():
                        path.rmdir()
                except OSError:
                    pass
            raise

    def _step(self, code: str, receipts: list[Any]) -> None:
        if self.config.failure_step == code:
            raise OperationalBootstrapError("INJECTED_FAILURE_" + code)
        receipts.append(OperationalBootstrapStepReceipt(
            ORDERED_STEPS.index(code) + 1, code, True,
            sha256_digest({"sequence": ORDERED_STEPS.index(code) + 1, "code": code})))


class OperationalBootstrapValidator:
    def validate(self, bundle: OperationalBootstrapEvidenceBundle) -> bool:
        return (
            bundle.execution_mode.value == "TEST_ONLY_BOOTSTRAP_VALIDATION"
            and not bundle.production_authorized
            and bundle.writers_activated == bundle.monitoring_activated
            == bundle.alerts_dispatched == 0
            and len(bundle.step_receipts) == len(ORDERED_STEPS)
        )
