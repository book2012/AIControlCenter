from __future__ import annotations

import ast
import dataclasses
import os
import sqlite3
import stat
from pathlib import Path

import pytest

from core.deployment.audit_sqlite import SQLiteAuditSchemaExpectation
from core.deployment.contracts import sha256_digest
from core.deployment.operational_activation_gate import (
    ActivationReadinessDecision, ActivationReadinessReport, ActivationRestriction,
    OperationalActivationStage, OperationalBootstrapPlan, OperationalBootstrapStep,
    OperationalPathPlan, OperationalPermissionPlan,
)
from core.deployment.operational_bootstrap import (
    ORDERED_STEPS, ControlledMacBootstrapExecutor, OperationalBootstrapError,
    OperationalBootstrapExecutionMode, OperationalBootstrapExecutionPlan,
    OperationalBootstrapExecutorConfig, OperationalBootstrapRequest,
    OperationalBootstrapValidator,
)
from core.deployment.operational_bootstrap.models import path_identity
from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapApproval, OperationalBootstrapAuthorizationConfig,
    OperationalBootstrapAuthorizationRequest, OperationalBootstrapAuthorizationService,
    OperationalBootstrapAuthorizationStage, OperationalBootstrapPlanBinding,
    OperationalBootstrapRestrictionAcknowledgement, OperationalBootstrapSafetySnapshot,
    OperationalBootstrapSchemaBinding, OperationalBootstrapTargetBinding, canonical_digest,
)
from core.deployment.permit_replay_sqlite import PermitReplaySchemaExpectation
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).parents[2]
NOW = "2026-07-30T12:00:00+09:00"
APPROVED = "2026-07-30T12:01:00+09:00"
ISSUED = "2026-07-30T12:02:00+09:00"
DONE = "2026-07-30T12:03:00+09:00"
EXPIRES = "2026-07-30T13:00:00+09:00"
COMMIT = "b" * 40
DIGEST = "sha256:" + "a" * 64
COUNTERS = {name: 0 for name in (
    "operational_directories_created", "operational_databases_created",
    "operational_backup_files_created", "operational_audit_writes",
    "operational_replay_writes", "writers_activated", "monitoring_activated",
    "alerts_dispatched", "notifications_sent", "n8n_invocations", "ubuntu_changes",
    "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
    "bootstrap_executions", "production_activations")}


class Registry:
    def __init__(self):
        self.claims = {}

    def inspect(self, permit_id):
        return self.claims.get(permit_id)

    def claim_unused(self, claim):
        if claim.permit_id in self.claims:
            raise ValueError("claimed")
        self.claims[claim.permit_id] = claim
        return claim


def readiness():
    restrictions = (ActivationRestriction(
        "READINESS_IS_NOT_AUTHORIZATION",
        "No bootstrap, writer, monitoring, dispatch or production authorization is granted."),)
    return ActivationReadinessReport(
        "report", OperationalActivationStage.PRE_ACTIVATION_READINESS,
        ActivationReadinessDecision.READY_WITH_RESTRICTIONS, NOW, ("e",), (DIGEST,),
        (), (), restrictions, OperationalPathPlan("/a", "/ab", "/r", "/rb", "/m"),
        OperationalPermissionPlan(),
        OperationalBootstrapPlan((OperationalBootstrapStep(1, "PREPARE", "prepare"),)),
        True, (), (), ("GIT",), DIGEST)


def authorization(root: Path):
    paths = ControlledMacBootstrapExecutor(
        config=OperationalBootstrapExecutorConfig(
            root, ROOT, OperationalBootstrapExecutionMode.TEST_ONLY_BOOTSTRAP_VALIDATION),
        permit_registry=Registry()).paths
    report = readiness()
    ack = tuple(OperationalBootstrapRestrictionAcknowledgement(
        item.code, canonical_digest(item.as_dict()), item.summary,
        "mac-operator-01", "security-approver-02", APPROVED)
        for item in report.restrictions)
    target = OperationalBootstrapTargetBinding(
        path_identity(paths.audit_database), path_identity(paths.audit_backup_root),
        path_identity(paths.replay_database), path_identity(paths.replay_backup_root),
        path_identity(paths.monitoring_directory),
        {name: True for name in ("audit_database", "audit_backup_root",
                                 "replay_database", "replay_backup_root", "monitoring_root")})
    schema = OperationalBootstrapSchemaBinding(
        sha256_digest(dataclasses.asdict(SQLiteAuditSchemaExpectation())), DIGEST,
        sha256_digest(dataclasses.asdict(PermitReplaySchemaExpectation())), DIGEST,
        DIGEST, DIGEST)
    plan = OperationalBootstrapPlanBinding(
        DIGEST, DIGEST, OperationalBootstrapExecutionPlan.build().plan_digest, DIGEST,
        ("VALIDATE_TARGET", "CREATE_SCHEMA"))
    safety = OperationalBootstrapSafetySnapshot(
        COUNTERS, True, 0, 0, 1, 0, 0, 0, True, True, True, NOW)
    request = OperationalBootstrapAuthorizationRequest(
        "authorization-request", "feature/deployment-package", COMMIT, report,
        report.report_digest, target, schema, plan, safety, "release-requester-03",
        "mac-operator-01", "security-approver-02", NOW, EXPIRES, ack)
    approval = OperationalBootstrapApproval(
        True, "mac-operator-01", "security-approver-02", APPROVED,
        "feature/deployment-package", COMMIT)
    decision, permit = OperationalBootstrapAuthorizationService().authorize(
        config=OperationalBootstrapAuthorizationConfig(
            OperationalBootstrapAuthorizationStage.CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION),
        request=request, approval=approval, decided_at=APPROVED, issued_at=ISSUED)
    return request, decision, permit


def execute(root: Path, *, registry=None, failure_step=None):
    registry = registry or Registry()
    auth_request, decision, permit = authorization(root)
    executor = ControlledMacBootstrapExecutor(
        config=OperationalBootstrapExecutorConfig(
            root, ROOT, OperationalBootstrapExecutionMode.TEST_ONLY_BOOTSTRAP_VALIDATION,
            failure_step=failure_step), permit_registry=registry)
    request = OperationalBootstrapRequest(
        "bootstrap-request", "feature/deployment-package", COMMIT, ISSUED, DONE,
        "bootstrap-operator-04", {})
    return executor.execute(request=request, permit=permit,
                            authorization_request=auth_request,
                            authorization_decision=decision), registry, executor


@pytest.fixture
def test_root(tmp_path, monkeypatch):
    configured = Path(os.environ["AICONTROLCENTER_BOOTSTRAP_TEST_ROOT"])
    root = configured / tmp_path.parent.name / tmp_path.name
    root.mkdir(parents=True)
    monkeypatch.setenv("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT", str(root))
    return root


def test_complete_bootstrap_layout_permissions_schema_backup_restore_and_evidence(test_root):
    bundle, registry, executor = execute(test_root)
    assert OperationalBootstrapValidator().validate(bundle)
    assert tuple(item.code for item in bundle.step_receipts) == ORDERED_STEPS
    assert len(registry.claims) == 1
    paths = executor.paths
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o700 for path in (
        paths.application_state, paths.audit_directory, paths.audit_backup_root,
        paths.security_directory, paths.replay_backup_root, paths.monitoring_directory))
    files = tuple(paths.audit_backup_root.iterdir()) + tuple(paths.replay_backup_root.iterdir())
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in files)
    assert not paths.restore_validation_root.exists()
    for database, required in (
        (paths.audit_database, {"audit_ledger_meta", "audit_events"}),
        (paths.replay_database, {"permit_replay_meta", "permit_use_events"})):
        connection = sqlite3.connect(database)
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert required <= {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type='table'")}
        connection.close()
        assert stat.S_IMODE(database.stat().st_mode) == 0o600
    assert bundle.writers_activated == bundle.monitoring_activated == 0
    assert bundle.alerts_dispatched == 0 and not bundle.production_authorized


def test_deterministic_plan_and_semantic_receipts(test_root, monkeypatch):
    first = test_root / "first"
    second = test_root / "second"
    first.mkdir()
    second.mkdir()
    assert OperationalBootstrapExecutionPlan.build() == OperationalBootstrapExecutionPlan.build()
    monkeypatch.setenv("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT", str(first))
    one, _, _ = execute(first)
    monkeypatch.setenv("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT", str(second))
    two, _, _ = execute(second)
    assert one.receipt_id.startswith("m3-a4b2a-receipt-")
    assert two.receipt_id.startswith("m3-a4b2a-receipt-")


@pytest.mark.parametrize("mode", [
    "CONTROLLED_OPERATIONAL_BOOTSTRAP", "OPERATIONAL", "ACTIVE", "LIVE",
    "PRODUCTION", "CUSTOMER_PRODUCTION", "UNKNOWN"])
def test_privileged_and_unknown_modes_rejected(test_root, mode):
    with pytest.raises(OperationalBootstrapError):
        OperationalBootstrapExecutorConfig(test_root, ROOT, mode)


def test_existing_target_and_second_claim_fail_closed(test_root):
    registry = Registry()
    _, registry, executor = execute(test_root, registry=registry)
    auth_request, decision, permit = authorization(test_root)
    request = OperationalBootstrapRequest(
        "second", "feature/deployment-package", COMMIT, ISSUED, DONE,
        "bootstrap-operator-04", {})
    with pytest.raises(Exception):
        ControlledMacBootstrapExecutor(
            config=executor.config, permit_registry=registry).execute(
                request=request, permit=permit, authorization_request=auth_request,
                authorization_decision=decision)


@pytest.mark.parametrize("step", [
    "VALIDATE_EXECUTION_CONFIGURATION", "CREATE_APPLICATION_STATE_DIRECTORIES",
    "APPLY_AUDIT_SCHEMA_AND_PROTECTIONS", "APPLY_REPLAY_SCHEMA_AND_PROTECTIONS",
    "CREATE_BASELINE_AUDIT_BACKUP", "CREATE_BASELINE_REPLAY_BACKUP",
    "VALIDATE_REPLAY_RESTORE"])
def test_failure_injection_cleanup_and_permit_non_reuse(test_root, step):
    registry = Registry()
    with pytest.raises(OperationalBootstrapError):
        execute(test_root, registry=registry, failure_step=step)
    if ORDERED_STEPS.index(step) >= ORDERED_STEPS.index("CLAIM_SYNTHETIC_PERMIT"):
        assert len(registry.claims) == 1
    assert not (test_root / "application-state").exists()


def test_path_confinement_rejects_repository_application_support_and_symlink(tmp_path, monkeypatch):
    candidates = (
        ROOT / "bootstrap", Path.home() / "Library/Application Support/AIControlCenter",
        Path("/private/tmp") / ".." / "etc")
    for candidate in candidates:
        monkeypatch.setenv("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT", str(candidate))
        with pytest.raises(OperationalBootstrapError):
            ControlledMacBootstrapExecutor(
                config=OperationalBootstrapExecutorConfig(
                    candidate, ROOT, OperationalBootstrapExecutionMode.TEST_ONLY_BOOTSTRAP_VALIDATION),
                permit_registry=Registry())._validate_root()
    parent = tmp_path / "parent"
    parent.mkdir()
    link = parent / "link"
    link.symlink_to(tmp_path)
    monkeypatch.setenv("AICONTROLCENTER_BOOTSTRAP_TEST_ROOT", str(link / "child"))
    with pytest.raises(OperationalBootstrapError):
        ControlledMacBootstrapExecutor(
            config=OperationalBootstrapExecutorConfig(
                link / "child", ROOT,
                OperationalBootstrapExecutionMode.TEST_ONLY_BOOTSTRAP_VALIDATION),
            permit_registry=Registry())._validate_root()


def test_no_forbidden_dependencies_api_route_or_operational_registry():
    forbidden = {"subprocess", "socket", "requests", "paramiko", "core.api",
                 "core.worker", "core.deployment.audit_sqlite_writer",
                 "core.deployment.permit_replay_sqlite_writer"}
    imports = set()
    for source in (ROOT / "core/deployment/operational_bootstrap").glob("*.py"):
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    assert not any(name == item or name.startswith(item + ".")
                   for name in imports for item in forbidden)
    assert validate_dependency_boundaries(repository_root=ROOT)["overall_result"] == "PASS"
