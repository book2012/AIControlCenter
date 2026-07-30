from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.deployment.operational_bootstrap_preflight import (
    OperationalBootstrapCapacityEvidence,
    OperationalBootstrapClosedTrackEvidence,
    OperationalBootstrapHostEvidence,
    OperationalBootstrapHostPreflightConfig,
    OperationalBootstrapHostPreflightService,
    OperationalBootstrapPreflightDecision,
    OperationalBootstrapPreflightError,
    OperationalBootstrapTargetEvidence,
)

ROOT = "/Users/operator/AIControlCenter"
STATE = "/Users/operator/Library/Application Support/AIControlCenter"
TARGETS = {
    "audit_database": f"{STATE}/audit/audit-ledger.sqlite3",
    "audit_backup_root": f"{STATE}/audit/backups",
    "replay_database": f"{STATE}/security/permit-replay.sqlite3",
    "replay_backup_root": f"{STATE}/security/backups",
    "monitoring_root": f"{STATE}/monitoring",
}
NOW = "2026-07-30T10:00:00+09:00"
COMMIT = "a" * 40


def config(**changes):
    value = OperationalBootstrapHostPreflightConfig(
        approved_commit=COMMIT, application_support_root=STATE,
        repository_root=ROOT, expected_targets=TARGETS,
        minimum_available_bytes=1_000, minimum_available_percentage=10,
        estimated_audit_database_allocation=100,
        estimated_replay_database_allocation=100,
        estimated_baseline_backup_allocation=100,
        estimated_restore_validation_allocation=100, safety_reserve=100)
    return replace(value, **changes)


def host(**changes):
    value = OperationalBootstrapHostEvidence(
        "host-1", NOW, "Darwin", "arm64", 501, "/Users/operator", ROOT,
        "feature/deployment-package", COMMIT, True, 0, 0, 1600, 0, 427,
        300, 0, {"directories_created": 0, "databases_created": 0,
                 "permits_issued": 0, "bootstrap_executions": 0})
    return replace(value, **changes)


def targets(**changes):
    result = []
    for name, path in TARGETS.items():
        item = OperationalBootstrapTargetEvidence(
            name, path, False, False, False, "dev:1", True, False, False,
            False, False, False, 0o700 if name.endswith("root") else 0o600,
            "AIControlCenter Mac operator")
        result.append(replace(item, **changes))
    return tuple(result)


def closure(**changes):
    value = OperationalBootstrapClosedTrackEvidence(
        "CLOSED", "CLOSED", "CLOSED", "READY_WITH_RESTRICTIONS",
        True, True, True, True, True, True, True)
    return replace(value, **changes)


def evaluate(**changes):
    args = dict(config=config(), host=host(), targets=targets(),
                capacity=OperationalBootstrapCapacityEvidence("dev:1", 10_000, 5_000),
                closed_track=closure(), evaluated_at=NOW)
    args.update(changes)
    return OperationalBootstrapHostPreflightService().evaluate(**args)


def test_immutable_deterministic_ready_report():
    first = evaluate()
    second = evaluate()
    assert first == second
    assert first.decision is OperationalBootstrapPreflightDecision.READY_WITH_RESTRICTIONS
    assert first.report_id == second.report_id
    assert first.canonical_json == second.canonical_json
    assert all(not getattr(first, flag) for flag in (
        "permit_issued", "permit_claimed", "bootstrap_authorized",
        "bootstrap_executed", "writers_authorized", "monitoring_authorized",
        "external_dispatch_authorized", "production_authorized"))
    with pytest.raises(FrozenInstanceError):
        first.decision = OperationalBootstrapPreflightDecision.BLOCKED


@pytest.mark.parametrize("host_change", [
    {"operating_system": "Linux"}, {"user_id": 0},
    {"repository_branch": "main"}, {"repository_commit": "b" * 40},
    {"working_tree_clean": False}, {"upstream_ahead": 1},
    {"upstream_behind": 1}, {"full_regression_failed": 1},
    {"full_regression_warnings": 426},
    {"safety_counters": {"bootstrap_executions": 1}},
])
def test_host_default_denials(host_change):
    assert evaluate(host=host(**host_change)).decision is OperationalBootstrapPreflightDecision.BLOCKED


@pytest.mark.parametrize("target_change", [
    {"exists": True}, {"symlink": True}, {"parent_component_symlink": True},
    {"repository_overlap": True}, {"network": True, "local_filesystem": False},
    {"removable": True}, {"ubuntu_linux_owned": True},
    {"permission_mode": 0o777}, {"expected_owner_identity": "Ubuntu"},
])
def test_target_and_permission_default_denials(target_change):
    assert evaluate(targets=targets(**target_change)).decision is OperationalBootstrapPreflightDecision.BLOCKED


def test_capacity_and_closure_default_denials():
    assert evaluate(capacity=OperationalBootstrapCapacityEvidence("dev:1", 1000, 10)).decision is OperationalBootstrapPreflightDecision.BLOCKED
    assert evaluate(closed_track=closure(m3_a4b2a_status="OPEN")).decision is OperationalBootstrapPreflightDecision.BLOCKED


def test_authorization_execution_and_adapter_requests_rejected():
    for change in ({"production_authorized": True}, {"bootstrap_authorized": True},
                   {"permit_issuance_requested": True}, {"bootstrap_execution_requested": True}):
        with pytest.raises(OperationalBootstrapPreflightError):
            config(**change)
    with pytest.raises(OperationalBootstrapPreflightError):
        evaluate(adapter=object())
    with pytest.raises(OperationalBootstrapPreflightError):
        evaluate(write_requested=True)


def test_no_target_is_created(tmp_path):
    before = tuple(tmp_path.iterdir())
    evaluate()
    assert tuple(tmp_path.iterdir()) == before
