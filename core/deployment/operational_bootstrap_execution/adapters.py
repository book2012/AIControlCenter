"""Separate test-only and controlled operational runtime adapters."""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

from core.deployment.operational_bootstrap.executor import MacSQLiteBootstrapAdapter

from .models import *


class _RuntimeAdapter:
    def __init__(self, *, failure_step: str | None = None) -> None:
        self.failure_step = failure_step

    def execute(self, *, request, paths, claim, plan):
        created: list[Path] = []
        receipts: list[OperationalBootstrapRuntimeStepReceipt] = [
            OperationalBootstrapRuntimeStepReceipt(
                step.sequence, step.code, True, canonical_digest(asdict(step)))
            for step in plan.steps if step.sequence <= 10
        ]
        try:
            for step in plan.steps:
                if step.sequence <= 10:
                    continue
                if self.failure_step == step.code:
                    raise OperationalBootstrapExecutionError("INJECTED_POST_CLAIM_FAILURE")
                if step.code == "CREATE_MAC_OPERATIONAL_DIRECTORY_LAYOUT":
                    missing_parents = []
                    current = paths.root.parent
                    while not current.exists():
                        missing_parents.append(current)
                        current = current.parent
                    for parent in reversed(missing_parents):
                        parent.mkdir()
                        os.chmod(parent, 0o700)
                        created.append(parent)
                    for path in (paths.root, paths.audit_database.parent, paths.audit_backups,
                                 paths.replay_database.parent, paths.replay_backups, paths.monitoring):
                        if path.exists():
                            if path == paths.root and paths.shared_parent_evidence.application_state_parent_preexisting:
                                continue
                            raise OperationalBootstrapExecutionError("MANAGED_TARGET_ALREADY_EXISTS")
                        path.mkdir()
                        os.chmod(path, 0o700)
                        created.append(path)
                elif step.code == "BOOTSTRAP_AUDIT_SQLITE_DATABASE":
                    created.append(paths.audit_database)
                    MacSQLiteBootstrapAdapter.create(
                        paths.audit_database, MacSQLiteBootstrapAdapter.AUDIT_DDL,
                        "audit_ledger_meta", "dpl/audit-sqlite/v1", 2000)
                elif step.code == "BOOTSTRAP_REPLAY_SQLITE_DATABASE":
                    created.append(paths.replay_database)
                    MacSQLiteBootstrapAdapter.create(
                        paths.replay_database, MacSQLiteBootstrapAdapter.REPLAY_DDL,
                        "permit_replay_meta", "dpl/permit-replay-sqlite/v1", 2000)
                elif step.code == "CREATE_AND_VALIDATE_BASELINE_AUDIT_BACKUP":
                    backup = paths.audit_backups / "baseline.sqlite3"
                    manifest = paths.audit_backups / "baseline.manifest.json"
                    created.extend((backup, manifest))
                    MacSQLiteBootstrapAdapter.backup(paths.audit_database, backup, manifest)
                    restore = paths.audit_backups / ".restore-validation.sqlite3"
                    restore_manifest = paths.audit_backups / ".restore.manifest.json"
                    created.extend((restore, restore_manifest))
                    MacSQLiteBootstrapAdapter.backup(backup, restore,
                                                     restore_manifest)
                    restore.unlink()
                    restore_manifest.unlink()
                elif step.code == "CREATE_AND_VALIDATE_BASELINE_REPLAY_BACKUP":
                    backup = paths.replay_backups / "baseline.sqlite3"
                    manifest = paths.replay_backups / "baseline.manifest.json"
                    created.extend((backup, manifest))
                    MacSQLiteBootstrapAdapter.backup(paths.replay_database, backup, manifest)
                    restore = paths.replay_backups / ".restore-validation.sqlite3"
                    restore_manifest = paths.replay_backups / ".restore.manifest.json"
                    created.extend((restore, restore_manifest))
                    MacSQLiteBootstrapAdapter.backup(backup, restore,
                                                     restore_manifest)
                    restore.unlink()
                    restore_manifest.unlink()
                receipts.append(OperationalBootstrapRuntimeStepReceipt(
                    step.sequence, step.code, True, canonical_digest(asdict(step))))
            content = {"request_id": request.request_id, "permit_id": claim.request.permit_id,
                       "claim_id": claim.claim_id, "mode": request.mode, "status": "COMPLETE",
                       "branch": request.branch, "commit": request.commit,
                       "completed_at": request.claim_at,
                       "step_receipts": [asdict(x) for x in receipts], "findings": [],
                       "artifact_references": [], "writers_activated": False,
                       "monitoring_activated": False, "external_dispatch_activated": False,
                       "production_authorized": False}
            digest = canonical_digest(content)
            return OperationalBootstrapRuntimeReceipt(
                "m3-a4b2b2a-receipt-" + digest[7:39], request.request_id,
                claim.request.permit_id, claim.claim_id, request.mode,
                OperationalBootstrapRuntimeStatus.COMPLETE, request.branch, request.commit,
                request.claim_at, tuple(receipts), (), (),)
        except Exception:
            for path in reversed(created):
                if path.is_file() or path.is_symlink():
                    path.unlink()
                elif path.is_dir() and not any(path.iterdir()):
                    path.rmdir()
            raise


class TestOnlyOperationalBootstrapRuntimeAdapter(_RuntimeAdapter):
    """Mutating adapter confined by the coordinator to the injected test root."""
    __test__ = False


class MacOperationalBootstrapRuntimeAdapter(_RuntimeAdapter):
    """Approved controlled adapter. Invocation requires all coordinator gates."""
