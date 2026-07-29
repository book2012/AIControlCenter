from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from core.deployment.operational_activation_gate import (
    ActivationReadinessDecision,
    OperationalActivationError,
    OperationalActivationEvidence,
    OperationalActivationGateConfig,
    OperationalActivationReadinessGate,
    OperationalActivationStage,
    OperationalBootstrapPlan,
    OperationalPathPlan,
    OperationalPermissionPlan,
    OperationalRollbackPlan,
    canonical_bootstrap_plan,
)
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).parents[2]
HOME = "/Users/operator"
NOW = "2026-07-30T12:00:00+09:00"
SAFETY = {
    name: 0 for name in (
        "operational_directories_created", "operational_database_files_created",
        "operational_backup_files_created", "operational_audit_writes",
        "operational_replay_writes", "writers_activated", "monitoring_activated",
        "alerts_dispatched", "notifications_sent", "n8n_invocations",
        "network_requests", "ubuntu_changes", "runtime_infrastructure_commands",
        "service_restarts", "api_write_routes", "bootstrap_executions",
        "production_activations",
    )
}


def evidence(**changes):
    values = dict(
        evidence_id="evidence-m3-a4a-001", generated_at=NOW,
        m2_readiness_closed=True, m2_pilot_closed=True,
        m3_a1a_closed=True, m3_a1b_closed=True, m3_a1c_closed=True,
        m3_a2a_closed=True, m3_a2b_closed=True, m3_a2c_closed=True,
        m3_a3a_closed=True, m3_a3b_closed=True, m3_a3c_closed=True,
        full_regression_passed=1000, full_regression_failed=0,
        full_regression_deselected=0, full_regression_warnings=0,
        deployment_tests_passed=300, deployment_tests_failed=0,
        git_branch="feature/deployment-package", git_commit="a" * 40,
        git_clean=True, upstream_ahead=0, upstream_behind=0,
        documentation_closed=True, architecture_closed=True,
        audit_recovery_drill_passed=True, replay_recovery_drill_passed=True,
        post_recovery_concurrency_passed=True, monitoring_alert_drill_passed=True,
        safety_counters=SAFETY,
        operational_paths_exist={
            "audit_database": False, "audit_backup_root": False,
            "permit_replay_database": False, "permit_replay_backup_root": False,
            "monitoring_evidence_root": False,
        },
        operational_writers_active=False, operational_monitoring_active=False,
        external_alert_dispatch_active=False, authorized_bootstrap_receipt=False,
    )
    values.update(changes)
    return OperationalActivationEvidence(**values)


def plans():
    base = f"{HOME}/Library/Application Support/AIControlCenter"
    return (
        OperationalPathPlan(
            f"{base}/audit/audit-ledger.sqlite3", f"{base}/audit/backups",
            f"{base}/security/permit-replay.sqlite3", f"{base}/security/backups",
            f"{base}/monitoring"),
        OperationalPermissionPlan(),
        canonical_bootstrap_plan(),
        OperationalRollbackPlan(*([True] * 10)),
    )


def evaluate(ev=None, **kwargs):
    path, permission, bootstrap, rollback = plans()
    values = dict(
        config=OperationalActivationGateConfig(
            OperationalActivationStage.PRE_ACTIVATION_READINESS,
            str(ROOT), HOME),
        evidence=ev or evidence(), evaluated_at=NOW, path_plan=path,
        permission_plan=permission, bootstrap_plan=bootstrap,
        rollback_plan=rollback,
    )
    values.update(kwargs)
    return OperationalActivationReadinessGate().evaluate(**values)


def replace_evidence(**changes):
    return dataclasses.replace(evidence(), **changes)


def test_valid_closed_track_evidence_is_deterministic_and_read_only():
    first = evaluate()
    second = evaluate()
    assert first == second
    assert first.readiness_decision is (
        ActivationReadinessDecision.READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP)
    assert first.report_id == second.report_id
    assert first.report_digest == second.report_digest
    assert first.canonical_json == second.canonical_json
    assert [step.sequence for step in first.bootstrap_plan.steps] == list(range(1, 19))
    assert [check.code for check in first.checks] == [
        "CONTROL_PLANE_OWNERSHIP", "M2_CLOSURE", "M3_A1_CLOSURE", "M3_A2_CLOSURE",
        "M3_A3_CLOSURE", "TEST_HEALTH", "GIT_HEALTH", "DOCUMENTATION_HEALTH",
        "SAFETY_COUNTERS", "AUDIT_RECOVERY", "REPLAY_RECOVERY", "REPLAY_CONCURRENCY",
        "MONITORING_DRILL", "PATH_PLAN", "PERMISSION_PLAN", "BOOTSTRAP_PLAN",
        "ROLLBACK_PLAN", "PRODUCTION_AUTHORIZATION"]
    assert (first.writes_performed, first.directories_created, first.databases_created,
            first.writers_activated, first.monitoring_activated,
            first.alerts_dispatched) == (0, 0, 0, 0, 0, 0)
    assert not any((first.bootstrap_authorized, first.writers_authorized,
                    first.monitoring_activation_authorized,
                    first.external_dispatch_authorized, first.production_authorized))


def test_contracts_are_frozen_and_stage_is_explicit():
    assert dataclasses.is_dataclass(evidence())
    with pytest.raises(dataclasses.FrozenInstanceError):
        evidence().git_clean = False
    with pytest.raises(OperationalActivationError):
        OperationalActivationGateConfig("PRODUCTION", str(ROOT), HOME)
    with pytest.raises(OperationalActivationError):
        OperationalActivationGateConfig(
            OperationalActivationStage.PRE_ACTIVATION_READINESS,
            str(ROOT), HOME, production_authorized=True)


@pytest.mark.parametrize("changes,reason", [
    ({"m2_pilot_closed": False}, "M2_CLOSURE_MISSING"),
    ({"m3_a1b_closed": False}, "M3_A1_CLOSURE_MISSING"),
    ({"m3_a2c_closed": False}, "M3_A2_CLOSURE_MISSING"),
    ({"m3_a3c_closed": False}, "M3_A3_CLOSURE_MISSING"),
    ({"full_regression_failed": 1}, "TEST_FAILURE_OR_MISSING_RESULT"),
    ({"git_clean": False}, "GIT_DIRTY"),
    ({"upstream_ahead": 1}, "GIT_NOT_SYNCHRONIZED"),
    ({"upstream_behind": 1}, "GIT_NOT_SYNCHRONIZED"),
    ({"ubuntu_ownership_present": True}, "UBUNTU_OWNERSHIP_REJECTED"),
    ({"operational_writers_active": True}, "UNAUTHORIZED_ACTIVE_WRITER"),
    ({"operational_monitoring_active": True}, "UNAUTHORIZED_ACTIVE_MONITORING"),
    ({"external_alert_dispatch_active": True}, "UNAUTHORIZED_EXTERNAL_DISPATCH"),
    ({"audit_recovery_drill_passed": False}, "AUDIT_RECOVERY_REQUIRED"),
    ({"replay_recovery_drill_passed": False}, "REPLAY_RECOVERY_REQUIRED"),
    ({"post_recovery_concurrency_passed": False}, "REPLAY_CONCURRENCY_REQUIRED"),
    ({"monitoring_alert_drill_passed": False}, "MONITORING_DRILL_REQUIRED"),
])
def test_default_deny_failures(changes, reason):
    report = evaluate(replace_evidence(**changes))
    assert report.readiness_decision is ActivationReadinessDecision.BLOCKED
    assert reason in {finding.code for finding in report.findings}


@pytest.mark.parametrize("counter", sorted(SAFETY))
def test_every_safety_counter_blocks(counter):
    counters = dict(SAFETY)
    counters[counter] = 1
    report = evaluate(replace_evidence(safety_counters=counters))
    assert report.readiness_decision is ActivationReadinessDecision.BLOCKED
    assert "SAFETY_COUNTER_NONZERO" in {finding.code for finding in report.findings}


def test_warnings_create_restriction_but_do_not_automatically_block():
    report = evaluate(replace_evidence(full_regression_warnings=3))
    assert report.readiness_decision is ActivationReadinessDecision.READY_WITH_RESTRICTIONS
    assert "TEST_HEALTH" in report.warning_checks
    assert "DEPRECATION_WARNINGS_OUTSTANDING" in {
        restriction.code for restriction in report.restrictions}
    assert "DEPRECATION_WARNINGS_REQUIRE_REMEDIATION" in {
        finding.code for finding in report.findings}


def test_expected_absent_paths_pass_but_unauthorized_existing_path_blocks():
    assert evaluate().readiness_decision is (
        ActivationReadinessDecision.READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP)
    exists = dict(evidence().operational_paths_exist)
    exists["audit_database"] = True
    report = evaluate(replace_evidence(operational_paths_exist=exists))
    assert report.readiness_decision is ActivationReadinessDecision.BLOCKED


def test_path_permission_bootstrap_and_rollback_plans_fail_closed():
    path, permission, bootstrap, rollback = plans()
    bad_path = dataclasses.replace(path, audit_database="relative.sqlite3")
    assert evaluate(path_plan=bad_path).readiness_decision is ActivationReadinessDecision.BLOCKED
    assert evaluate(permission_plan=dataclasses.replace(
        permission, sqlite_database_mode=0o666)).readiness_decision is (
            ActivationReadinessDecision.BLOCKED)
    bad_bootstrap = OperationalBootstrapPlan(tuple(reversed(bootstrap.steps)))
    assert evaluate(bootstrap_plan=bad_bootstrap).readiness_decision is (
        ActivationReadinessDecision.BLOCKED)
    activating = dataclasses.replace(bootstrap, writer_activation=True)
    assert evaluate(bootstrap_plan=activating).readiness_decision is (
        ActivationReadinessDecision.BLOCKED)
    assert evaluate(rollback_plan=dataclasses.replace(
        rollback, restore_validation_required=False)).readiness_decision is (
            ActivationReadinessDecision.BLOCKED)


def test_stale_and_contradictory_evidence_and_production_are_invalid_or_blocked():
    stale = evaluate(replace_evidence(generated_at="2026-07-28T12:00:00+09:00"))
    assert stale.readiness_decision is ActivationReadinessDecision.BLOCKED
    contradictory = evaluate(replace_evidence(
        generated_at="2026-07-31T12:00:00+09:00"))
    assert contradictory.readiness_decision is ActivationReadinessDecision.INVALID
    production = evaluate(replace_evidence(production_authorized=True))
    assert production.readiness_decision is ActivationReadinessDecision.INVALID


def test_unsafe_evidence_and_adapters_or_writes_are_rejected():
    with pytest.raises(OperationalActivationError):
        evidence(safety_counters={"api_key": 0})
    with pytest.raises(OperationalActivationError):
        evaluate(concrete_adapter=object())
    with pytest.raises(OperationalActivationError):
        evaluate(write_requested=True)


def test_package_has_no_runtime_io_api_worker_or_external_dependency():
    package = ROOT / "core/deployment/operational_activation_gate"
    forbidden = {
        "subprocess", "socket", "requests", "paramiko", "sqlite3",
        "core.api", "core.worker",
    }
    imports = set()
    for source in package.glob("*.py"):
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    assert not any(any(name == item or name.startswith(item + ".")
                       for item in forbidden) for name in imports)
    policy = validate_dependency_boundaries(repository_root=ROOT)
    assert policy["overall_result"] == "PASS"
    assert any(item["module"] == "core.deployment.operational_activation_gate.gate"
               and item["zone"] == "operational_activation_gate"
               for item in policy["classified_modules"])
