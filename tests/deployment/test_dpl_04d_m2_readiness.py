from __future__ import annotations

import ast
import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from core.deployment.m2_readiness import (
    M2ReadinessDecision,
    M2ReadinessEvidence,
    M2ReadinessEvidenceError,
    M2ReadinessGate,
    canonical_json,
)
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-07-29T15:00:00Z"


def passing_evidence() -> dict:
    return {
        "schema_version": "dpl/m2-readiness/v1",
        "observed_at": STAMP,
        "checks": {
            "CONTROL_PLANE_OWNERSHIP": {
                "control_plane_owner": "AIControlCenter", "control_plane_host_role": "Mac",
                "ubuntu_control_plane_ownership": False},
            "DEPLOYMENT_CONTRACTS": {
                "versioned_immutable_contracts_present": True, "canonical_json_supported": True,
                "schema_validation_passed": True},
            "MAC_INVENTORY_AND_INGRESS": {
                "mac_inventory_validation_passed": True, "caddy_readiness_available": True,
                "colima_readiness_available": True, "compose_readiness_available": True,
                "evidence_read_only": True, "runtime_mutation_performed": False},
            "DEPENDENCY_BOUNDARIES": {
                "dependency_policy_validation_passed": True,
                "protected_api_boundary_passed": True, "protected_worker_boundary_passed": True,
                "generic_command_execution_reachable": False},
            "DETERMINISTIC_PLANNING": {
                "deployment_plan_validation_passed": True, "package_binding_passed": True,
                "target_binding_passed": True, "environment_binding_passed": True,
                "scope_binding_passed": True, "plan_digest_present": True},
            "EXECUTION_AUTHORIZATION": {
                "authorization_validation_passed": True,
                "requester_approver_separation_passed": True,
                "nonce_expiry_policy_passed": True, "production_authorization": False,
                "maximum_authorization_uses": 1},
            "REPLAY_PROTECTION": {
                "first_simulated_use_passed": True, "replay_denial_passed": True,
                "failed_execution_fail_closed": True},
            "TYPED_EXECUTOR_PORT": {
                "typed_operation_allowlist_passed": True, "arbitrary_shell_rejected": True,
                "command_rejected": True, "argv_rejected": True, "default_deny_enabled": True,
                "real_executor_invocation_count": 0},
            "MAC_SANDBOX_ADAPTER": {
                "explicit_sandbox_root": True, "root_confinement_passed": True,
                "symlink_rejection_passed": True, "traversal_rejection_passed": True,
                "repository_runtime_writes": 0, "ubuntu_changes": 0, "runtime_commands": 0,
                "network_accesses": 0, "production_writes": 0},
            "AUDIT_ARCHITECTURE": {
                "aicontrolcenter_audit_ownership_accepted": True,
                "mac_control_plane_storage_accepted": True, "durable_audit_port_present": True,
                "canonical_audit_event_present": True, "hash_chain_contracts_present": True,
                "secret_bearing_fields_rejected": True,
                "persistent_sqlite_adapter_implemented": False, "persistent_audit_writes": 0},
            "TEST_EVIDENCE": {
                "targeted_tests_passed": True, "deployment_suite_passed": True,
                "full_regression_passed": True, "failed_test_count": 0,
                "full_regression_minimum_met": True, "full_regression_passed_count": 1247,
                "deselected_count": 5, "warning_count": 7},
            "GIT_AND_DOCUMENTATION": {
                "approved_feature_branch": True, "commit_created": True, "push_completed": True,
                "working_tree_clean": True, "ahead": 0, "behind": 0,
                "architecture_updated": True, "readme_updated": True,
                "changelog_updated": True, "master_updated": True, "roadmap_updated": True},
            "SAFETY_COUNTERS": {
                "production_business_writes": 0, "persistent_audit_writes": 0,
                "persistent_nonce_writes": 0, "real_executor_invocations": 0,
                "ubuntu_changes": 0, "runtime_commands": 0, "service_restarts": 0,
                "api_write_routes": 0, "production_activations": 0},
        },
    }


def report_with(category: str, field: str, value):
    evidence = passing_evidence()
    evidence["checks"][category][field] = value
    return M2ReadinessGate().evaluate(evidence, evaluated_at=STAMP)


def test_immutable_schema_and_canonical_determinism() -> None:
    evidence = M2ReadinessEvidence.from_mapping(passing_evidence())
    with pytest.raises(TypeError):
        evidence.checks["SAFETY_COUNTERS"]["runtime_commands"] = 1
    with pytest.raises(FrozenInstanceError):
        evidence.observed_at = "changed"
    first = M2ReadinessGate().evaluate(evidence, evaluated_at=STAMP)
    reordered = json.loads(json.dumps(passing_evidence(), sort_keys=True))
    second = M2ReadinessGate().evaluate(reordered, evaluated_at=STAMP)
    assert first == second
    assert canonical_json(first) == canonical_json(second)
    assert first.report_id == second.report_id
    assert first.report_digest == second.report_digest
    assert [item.category for item in first.checks] == list(passing_evidence()["checks"])


def test_complete_evidence_is_ready_with_explicit_restrictions_and_warning() -> None:
    report = M2ReadinessGate().evaluate(passing_evidence(), evaluated_at=STAMP)
    assert report.decision is M2ReadinessDecision.READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX
    assert len(report.checks) == 13
    assert all(item.passed for item in report.checks)
    assert "no persistent SQLite audit adapter" in report.restrictions
    assert "pilot activation not performed" in report.restrictions
    assert {item.code for item in report.findings} == {
        "PERSISTENT_SQLITE_ADAPTER_ABSENT", "TEST_WARNINGS_REPORTED"
    }


def test_missing_malformed_and_contradictory_evidence_are_blocked() -> None:
    missing = passing_evidence()
    del missing["checks"]["REPLAY_PROTECTION"]
    assert M2ReadinessGate().evaluate(missing, evaluated_at=STAMP).decision.value == "BLOCKED"
    malformed = passing_evidence()
    malformed["checks"]["SAFETY_COUNTERS"]["runtime_commands"] = "zero"
    assert M2ReadinessGate().evaluate(malformed, evaluated_at=STAMP).decision.value == "BLOCKED"
    malformed["checks"]["SAFETY_COUNTERS"]["unknown"] = True
    assert M2ReadinessGate().evaluate(malformed, evaluated_at=STAMP).decision.value == "BLOCKED"
    contradictory = passing_evidence()
    contradictory["checks"]["MAC_INVENTORY_AND_INGRESS"]["runtime_mutation_performed"] = True
    assert M2ReadinessGate().evaluate(
        contradictory, evaluated_at=STAMP
    ).decision.value == "BLOCKED"


@pytest.mark.parametrize(
    ("category", "field", "value"),
    [
        ("EXECUTION_AUTHORIZATION", "production_authorization", True),
        ("SAFETY_COUNTERS", "production_business_writes", 1),
        ("SAFETY_COUNTERS", "persistent_audit_writes", 1),
        ("SAFETY_COUNTERS", "real_executor_invocations", 1),
        ("CONTROL_PLANE_OWNERSHIP", "ubuntu_control_plane_ownership", True),
        ("MAC_SANDBOX_ADAPTER", "ubuntu_changes", 1),
        ("SAFETY_COUNTERS", "runtime_commands", 1),
        ("SAFETY_COUNTERS", "api_write_routes", 1),
        ("GIT_AND_DOCUMENTATION", "working_tree_clean", False),
        ("GIT_AND_DOCUMENTATION", "ahead", 1),
        ("GIT_AND_DOCUMENTATION", "behind", 1),
        ("TEST_EVIDENCE", "failed_test_count", 1),
        ("TEST_EVIDENCE", "full_regression_passed_count", 1246),
    ],
)
def test_failed_mandatory_conditions_are_not_ready(category, field, value) -> None:
    assert report_with(category, field, value).decision is M2ReadinessDecision.NOT_READY


@pytest.mark.parametrize(
    "field",
    [
        "password", "access_token", "api_key", "private_key", "cookie",
        "authorization_header", "shell", "command", "argv", "script",
        "raw_environment",
    ],
)
def test_secret_and_executable_fields_are_rejected(field: str) -> None:
    evidence = passing_evidence()
    evidence["checks"]["CONTROL_PLANE_OWNERSHIP"][field] = "redacted"
    with pytest.raises(M2ReadinessEvidenceError):
        M2ReadinessEvidence.from_mapping(evidence)


def test_no_runtime_probe_network_api_worker_or_persistent_adapter_dependency() -> None:
    forbidden = {
        "subprocess", "socket", "requests", "paramiko", "sqlite3",
        "core.api", "core.worker", "core.deployment.sandbox_adapter",
    }
    for source in (ROOT / "core/deployment/m2_readiness").glob("*.py"):
        text = source.read_text("utf-8")
        tree = ast.parse(text)
        imports = {
            node.names[0].name if isinstance(node, ast.Import) else (node.module or "")
            for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))
        }
        assert not any(
            item == prefix or item.startswith(prefix + ".")
            for item in imports for prefix in forbidden
        )
        assert not any(marker in text for marker in ("Path(", "open(", "urlopen(", "connect("))
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]


def test_json_fixtures_have_expected_decisions() -> None:
    fixture_dir = ROOT / "tests/fixtures/deployment"
    expected = {
        "m2-readiness-passing.json": "READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX",
        "m2-readiness-missing.json": "BLOCKED",
        "m2-readiness-failed-safety.json": "NOT_READY",
        "m2-readiness-contradictory.json": "BLOCKED",
    }
    base = passing_evidence()
    for name, decision in expected.items():
        fixture = json.loads((fixture_dir / name).read_text("utf-8"))
        if name == "m2-readiness-passing.json":
            evidence = fixture
        else:
            evidence = copy.deepcopy(base)
        if fixture.get("mode") == "missing":
            del evidence["checks"][fixture["category"]]
        elif fixture.get("mode") == "override":
            evidence["checks"][fixture["category"]][fixture["field"]] = fixture["value"]
        assert M2ReadinessGate().evaluate(
            evidence, evaluated_at=STAMP
        ).decision.value == decision
