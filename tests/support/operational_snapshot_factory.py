"""Owned controlled operational/evidence snapshots for M3/M4 tests."""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from core.deployment.audit_sqlite import SQLiteAuditSchemaExpectation
from core.deployment.bootstrap_evidence_recovery import (
    BootstrapEvidenceRecoveryConfig, BootstrapEvidenceRecoveryValidator,
    ControlledBootstrapEvidenceGenerator, ControlledEvidenceInput,
    TrustedBootstrapEvidenceBinding,
)
from core.deployment.bootstrap_evidence_recovery.service import BRANCH, COMMIT
from core.deployment.contracts import sha256_digest
from core.deployment.operational_activation_gate import (
    ActivationReadinessDecision, ActivationReadinessReport, ActivationRestriction,
    OperationalActivationStage, OperationalBootstrapPlan, OperationalBootstrapStep,
    OperationalPathPlan, OperationalPermissionPlan,
)
from core.deployment.operational_bootstrap import (
    ControlledMacBootstrapExecutor, OperationalBootstrapExecutionMode,
    OperationalBootstrapExecutionPlan, OperationalBootstrapExecutorConfig,
    OperationalBootstrapRequest,
)
from core.deployment.operational_bootstrap.models import path_identity
from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapApproval, OperationalBootstrapAuthorizationConfig,
    OperationalBootstrapAuthorizationRequest, OperationalBootstrapAuthorizationService,
    OperationalBootstrapAuthorizationStage, OperationalBootstrapPlanBinding,
    OperationalBootstrapRestrictionAcknowledgement, OperationalBootstrapSafetySnapshot,
    OperationalBootstrapSchemaBinding, OperationalBootstrapTargetBinding,
    canonical_digest,
)
from core.deployment.permit_replay_sqlite import PermitReplaySchemaExpectation

ENVIRONMENT_KEYS = (
    "AICONTROLCENTER_M3_A4B3_OPERATIONAL_SNAPSHOT",
    "AICONTROLCENTER_M3_A4B3_EVIDENCE_SNAPSHOT",
    "AICONTROLCENTER_M3_A4B3_RECOVERY_WORK",
    "AICONTROLCENTER_M3_A4B3_TRUSTED_BINDING",
)
_NOW = "2026-07-30T12:00:00+00:00"
_APPROVED = "2026-07-30T12:01:00+00:00"
_ISSUED = "2026-07-30T12:02:00+00:00"
_DONE = "2026-07-30T12:03:00+00:00"
_EXPIRES = "2026-07-30T14:00:00+00:00"
_DIGEST = "sha256:" + "a" * 64
_COUNTERS = {name: 0 for name in (
    "operational_directories_created", "operational_databases_created",
    "operational_backup_files_created", "operational_audit_writes",
    "operational_replay_writes", "writers_activated", "monitoring_activated",
    "alerts_dispatched", "notifications_sent", "n8n_invocations", "ubuntu_changes",
    "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
    "bootstrap_executions", "production_activations")}


class _Registry:
    def __init__(self) -> None:
        self.claims: dict[str, Any] = {}

    def inspect(self, permit_id: str) -> Any:
        return self.claims.get(permit_id)

    def claim_unused(self, claim: Any) -> Any:
        if claim.permit_id in self.claims:
            raise ValueError("claimed")
        self.claims[claim.permit_id] = claim
        return claim


@dataclass(frozen=True, slots=True)
class OperationalSnapshotResult:
    root: Path
    operational_snapshot: Path
    evidence_snapshot: Path
    recovery_work: Path
    trusted_binding: TrustedBootstrapEvidenceBinding
    environment: Mapping[str, str]
    production_authorized: bool = False
    _owned: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "environment", MappingProxyType(dict(self.environment)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root), "operational_snapshot": str(self.operational_snapshot),
            "evidence_snapshot": str(self.evidence_snapshot),
            "recovery_work": str(self.recovery_work),
            "trusted_binding": self.trusted_binding.as_dict(),
            "environment": dict(self.environment), "production_authorized": False,
        }

    def cleanup(self) -> None:
        if self._owned and self.root.is_dir() and not self.root.is_symlink():
            if not str(self.root).startswith("/private/tmp/test-infra-02-"):
                raise RuntimeError("OWNED_ROOT_POLICY_INVALID")
            shutil.rmtree(self.root)

    def __enter__(self) -> "OperationalSnapshotResult":
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()


class OperationalSnapshotFactory:
    def __init__(self, repository_root: Path) -> None:
        self.repository_root = Path(repository_root).resolve()

    def create(self, environment: Mapping[str, str] | None = None) -> OperationalSnapshotResult:
        supplied = dict(os.environ if environment is None else environment)
        present = [key in supplied for key in ENVIRONMENT_KEYS]
        if any(present):
            if not all(present):
                raise ValueError("SNAPSHOT_ENVIRONMENT_INCOMPLETE")
            binding = TrustedBootstrapEvidenceBinding(**json.loads(
                supplied[ENVIRONMENT_KEYS[3]]))
            operational, evidence, recovery = (
                Path(supplied[key]) for key in ENVIRONMENT_KEYS[:3])
            return OperationalSnapshotResult(
                recovery.parent, operational, evidence, recovery, binding,
                {key: supplied[key] for key in ENVIRONMENT_KEYS}, _owned=False)

        root = Path(tempfile.mkdtemp(prefix="test-infra-02-", dir="/private/tmp"))
        os.chmod(root, 0o700)
        try:
            executor_root = root / "executor"
            executor_root.mkdir(mode=0o700)
            previous = os.environ.get("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT")
            os.environ["AICONTROLCENTER_BOOTSTRAP_TEST_ROOT"] = str(executor_root)
            try:
                executor = ControlledMacBootstrapExecutor(
                    config=OperationalBootstrapExecutorConfig(
                        executor_root, self.repository_root,
                        OperationalBootstrapExecutionMode.TEST_ONLY_BOOTSTRAP_VALIDATION),
                    permit_registry=_Registry())
                auth_request, decision, permit = self._authorization(executor)
                executor.execute(
                    request=OperationalBootstrapRequest(
                        "test-infra-02-bootstrap", BRANCH, COMMIT, _ISSUED, _DONE,
                        "synthetic-bootstrap-operator", {}),
                    permit=permit, authorization_request=auth_request,
                    authorization_decision=decision)
            finally:
                if previous is None:
                    os.environ.pop("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT", None)
                else:
                    os.environ["AICONTROLCENTER_BOOTSTRAP_TEST_ROOT"] = previous
            operational = root / "operational"
            shutil.move(str(executor.paths.application_state), operational)
            shutil.rmtree(executor_root)
            self._normalize_operational(operational)
            evidence = root / "evidence"
            generated = ControlledBootstrapEvidenceGenerator().generate(
                ControlledEvidenceInput(
                    evidence, "synthetic-requester", "synthetic-operator",
                    "synthetic-independent-approver", "test-infra-02-canonical"))
            recovery = root / "recovery"
            recovery.mkdir(mode=0o700)
            binding_json = json.dumps(generated.trusted_binding.as_dict(),
                                      sort_keys=True, separators=(",", ":"))
            values = (str(operational), str(evidence), str(recovery), binding_json)
            env = dict(zip(ENVIRONMENT_KEYS, values, strict=True))
            result = OperationalSnapshotResult(
                root, operational, evidence, recovery, generated.trusted_binding, env)
            BootstrapEvidenceRecoveryValidator(BootstrapEvidenceRecoveryConfig(
                operational, evidence, recovery, generated.trusted_binding)).validate()
            return result
        except Exception:
            if root.exists():
                shutil.rmtree(root)
            raise

    def _authorization(self, executor: ControlledMacBootstrapExecutor) -> tuple[Any, Any, Any]:
        restriction = ActivationRestriction(
            "READINESS_IS_NOT_AUTHORIZATION", "Controlled non-production only.")
        report = ActivationReadinessReport(
            "test-infra-02-readiness", OperationalActivationStage.PRE_ACTIVATION_READINESS,
            ActivationReadinessDecision.READY_WITH_RESTRICTIONS, _NOW, ("e",), (_DIGEST,),
            (), (), (restriction,), OperationalPathPlan("/a", "/ab", "/r", "/rb", "/m"),
            OperationalPermissionPlan(),
            OperationalBootstrapPlan((OperationalBootstrapStep(1, "PREPARE", "prepare"),)),
            True, (), (), ("GIT",), _DIGEST)
        acknowledgements = tuple(OperationalBootstrapRestrictionAcknowledgement(
            item.code, canonical_digest(item.as_dict()), item.summary,
            "synthetic-operator", "synthetic-independent-approver", _APPROVED)
            for item in report.restrictions)
        paths = executor.paths
        target = OperationalBootstrapTargetBinding(
            path_identity(paths.audit_database), path_identity(paths.audit_backup_root),
            path_identity(paths.replay_database), path_identity(paths.replay_backup_root),
            path_identity(paths.monitoring_directory),
            {name: True for name in ("audit_database", "audit_backup_root",
                                     "replay_database", "replay_backup_root", "monitoring_root")})
        schema = OperationalBootstrapSchemaBinding(
            sha256_digest(dataclasses.asdict(SQLiteAuditSchemaExpectation())), _DIGEST,
            sha256_digest(dataclasses.asdict(PermitReplaySchemaExpectation())), _DIGEST,
            _DIGEST, _DIGEST)
        plan = OperationalBootstrapPlanBinding(
            _DIGEST, _DIGEST, OperationalBootstrapExecutionPlan.build().plan_digest,
            _DIGEST, ("VALIDATE_TARGET", "CREATE_SCHEMA"))
        safety = OperationalBootstrapSafetySnapshot(
            _COUNTERS, True, 0, 0, 1, 0, 0, 0, True, True, True, _NOW)
        request = OperationalBootstrapAuthorizationRequest(
            "test-infra-02-authorization-request", BRANCH, COMMIT, report,
            report.report_digest, target, schema, plan, safety, "synthetic-requester",
            "synthetic-operator", "synthetic-independent-approver", _NOW, _EXPIRES,
            acknowledgements)
        approval = OperationalBootstrapApproval(
            True, "synthetic-operator", "synthetic-independent-approver", _APPROVED,
            BRANCH, COMMIT)
        decision, permit = OperationalBootstrapAuthorizationService().authorize(
            config=OperationalBootstrapAuthorizationConfig(
                OperationalBootstrapAuthorizationStage.CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION),
            request=request, approval=approval, decided_at=_APPROVED, issued_at=_ISSUED)
        return request, decision, permit

    @staticmethod
    def _normalize_operational(root: Path) -> None:
        renames = {
            "audit/backups/baseline-audit.sqlite3": "audit/backups/baseline.sqlite3",
            "audit/backups/baseline-audit.manifest.json": "audit/backups/baseline.manifest.json",
            "security/backups/baseline-replay.sqlite3": "security/backups/baseline.sqlite3",
            "security/backups/baseline-replay.manifest.json": "security/backups/baseline.manifest.json",
        }
        for source, destination in renames.items():
            (root / source).rename(root / destination)
        for database in (root / "audit/audit-ledger.sqlite3",
                         root / "security/permit-replay.sqlite3",
                         root / "audit/backups/baseline.sqlite3",
                         root / "security/backups/baseline.sqlite3"):
            for suffix in ("-shm", "-wal"):
                sidecar = database.with_name(database.name + suffix)
                sidecar.touch(mode=0o600)
                os.chmod(sidecar, 0o600)
        for path in root.rglob("*"):
            os.chmod(path, 0o700 if path.is_dir() else 0o600)
