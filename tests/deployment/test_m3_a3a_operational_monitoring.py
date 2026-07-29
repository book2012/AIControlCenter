from __future__ import annotations

import dataclasses
import importlib
import socket
import subprocess
from pathlib import Path

import pytest

from core.deployment.operational_monitoring import (
    AlertCandidateEvaluator,
    MonitoringDimension,
    MonitoringEvidence,
    MonitoringStatus,
    OperationalMonitoringConfig,
    OperationalMonitoringError,
    OperationalMonitoringService,
    OperationalStage,
)
from core.deployment.policy import validate_dependency_boundaries


ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-30T12:00:00+00:00"
FRESH = "2026-07-30T11:55:00+00:00"
DIGEST = "sha256:" + "a" * 64
SAFETY = {
    "operational_database_files_created": 0,
    "monitoring_database_writes": 0,
    "operational_audit_writes": 0,
    "operational_replay_writes": 0,
    "alerts_dispatched": 0,
    "notifications_sent": 0,
    "n8n_invocations": 0,
    "network_requests": 0,
    "ubuntu_changes": 0,
    "runtime_infrastructure_commands": 0,
    "service_restarts": 0,
    "api_write_routes": 0,
    "production_activations": 0,
}


@pytest.fixture
def config() -> OperationalMonitoringConfig:
    return OperationalMonitoringConfig(
        maximum_evidence_age_seconds=3600,
        audit_backup_warning_age_seconds=3600,
        audit_backup_critical_age_seconds=7200,
        audit_recovery_drill_warning_age_seconds=86400,
        audit_recovery_drill_critical_age_seconds=172800,
        replay_backup_warning_age_seconds=3600,
        replay_backup_critical_age_seconds=7200,
        replay_recovery_drill_warning_age_seconds=86400,
        replay_recovery_drill_critical_age_seconds=172800,
    )


@pytest.fixture
def healthy_evidence() -> MonitoringEvidence:
    return MonitoringEvidence(
        observed_at=NOW,
        audit_inspection_status="HEALTHY",
        audit_inspection_report_id="audit-inspection-1",
        audit_inspection_report_digest=DIGEST,
        audit_evidence_generated_at=FRESH,
        audit_schema_valid=True,
        audit_hash_chain_valid=True,
        audit_production_privacy_violations=0,
        audit_recovery_status="RECOVERY_VALID",
        audit_recovery_report_id="audit-recovery-1",
        audit_recovery_report_digest=DIGEST,
        audit_recovery_evidence_generated_at=FRESH,
        audit_backup_age_seconds=300,
        audit_recovery_drill_age_seconds=300,
        replay_inspection_status="HEALTHY",
        replay_inspection_report_id="replay-inspection-1",
        replay_inspection_report_digest=DIGEST,
        replay_evidence_generated_at=FRESH,
        replay_schema_valid=True,
        replay_hash_chain_valid=True,
        replay_state_machine_valid=True,
        replay_violation_count=0,
        replay_recovery_status="RECOVERY_VALID",
        replay_recovery_report_id="replay-recovery-1",
        replay_recovery_report_digest=DIGEST,
        replay_recovery_evidence_generated_at=FRESH,
        replay_backup_age_seconds=300,
        replay_recovery_drill_age_seconds=300,
        permit_states_restored=True,
        replay_protection_restored=True,
        post_recovery_concurrency_valid=True,
        m2_readiness_status="READY",
        m2_readiness_report_id="m2-readiness-1",
        m2_readiness_report_digest=DIGEST,
        m2_evidence_generated_at=FRESH,
        controlled_pilot_closeout_status="CLOSED",
        pilot_report_id="pilot-closeout-1",
        pilot_report_digest=DIGEST,
        pilot_evidence_generated_at=FRESH,
        regression_passed=100,
        regression_failed=0,
        regression_deselected=2,
        regression_warnings=0,
        git_clean=True,
        git_ahead=0,
        git_behind=0,
        documentation_complete=True,
        control_plane_owner="AIControlCenter/Mac",
        operational_audit_database_created=False,
        operational_replay_database_created=False,
        operational_writer_activated=False,
        operational_backup_schedule_activated=False,
        safety_counters=SAFETY,
        production_authorized=False,
    )


def evaluate(config: OperationalMonitoringConfig, evidence: MonitoringEvidence):
    return OperationalMonitoringService(config).evaluate(
        evidence, stage=OperationalStage.PRE_ACTIVATION)


def reason_codes(snapshot) -> set[str]:
    return {item.reason_code for item in snapshot.findings}


def test_contracts_are_immutable_and_only_pre_activation_is_supported(
    config, healthy_evidence
) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        healthy_evidence.git_clean = False
    with pytest.raises(OperationalMonitoringError, match="PRE_ACTIVATION"):
        OperationalMonitoringService(config).evaluate(
            healthy_evidence, stage="PRODUCTION")
    for stage in (None, "LIVE", "CUSTOMER_PRODUCTION", "UNKNOWN"):
        with pytest.raises(OperationalMonitoringError):
            OperationalMonitoringService(config).evaluate(
                healthy_evidence, stage=stage)


def test_default_deny_configuration_and_adapter(config) -> None:
    with pytest.raises(OperationalMonitoringError):
        OperationalMonitoringService(None)
    with pytest.raises(OperationalMonitoringError):
        OperationalMonitoringService(config, notification_adapter=object())
    with pytest.raises(OperationalMonitoringError):
        OperationalMonitoringConfig(
            1, 20, 10, 1, 2, 1, 2, 1, 2)


def test_healthy_snapshot_is_deterministic_and_expected_inactive_state_allowed(
    config, healthy_evidence
) -> None:
    first = evaluate(config, healthy_evidence)
    second = evaluate(config, healthy_evidence)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.snapshot_id == second.snapshot_id
    assert first.snapshot_digest == second.snapshot_digest
    assert first.overall_status is MonitoringStatus.HEALTHY
    assert first.dimensions == tuple(sorted(
        first.dimensions, key=lambda item: list(MonitoringDimension).index(item.dimension)))
    assert "OPERATIONAL_AUDIT_DATABASE_NOT_CREATED" in first.restrictions
    assert "OPERATIONAL_REPLAY_DATABASE_NOT_CREATED" in first.restrictions
    production = next(item for item in first.dimensions
                      if item.dimension is MonitoringDimension.PRODUCTION_AUTHORIZATION)
    assert production.status is MonitoringStatus.NOT_CONFIGURED_ALLOWED
    assert first.writes_performed == first.alerts_dispatched == first.notifications_sent == 0
    assert first.production_authorized is False


@pytest.mark.parametrize(
    ("changes", "code", "status"),
    [
        ({"audit_backup_age_seconds": 3600}, "AUDIT_BACKUP_STALE", MonitoringStatus.DEGRADED),
        ({"audit_backup_age_seconds": 7200}, "AUDIT_BACKUP_TOO_OLD", MonitoringStatus.CRITICAL),
        ({"replay_backup_age_seconds": 3600}, "REPLAY_BACKUP_STALE", MonitoringStatus.DEGRADED),
        ({"replay_backup_age_seconds": 7200}, "REPLAY_BACKUP_TOO_OLD", MonitoringStatus.CRITICAL),
        ({"audit_recovery_drill_age_seconds": 86400}, "AUDIT_RECOVERY_DRILL_STALE", MonitoringStatus.DEGRADED),
        ({"audit_recovery_drill_age_seconds": 172800}, "AUDIT_RECOVERY_DRILL_TOO_OLD", MonitoringStatus.CRITICAL),
        ({"replay_recovery_drill_age_seconds": 86400}, "REPLAY_RECOVERY_DRILL_STALE", MonitoringStatus.DEGRADED),
        ({"replay_recovery_drill_age_seconds": 172800}, "REPLAY_RECOVERY_DRILL_TOO_OLD", MonitoringStatus.CRITICAL),
        ({"audit_hash_chain_valid": False}, "AUDIT_HASH_CHAIN_INVALID", MonitoringStatus.CRITICAL),
        ({"replay_hash_chain_valid": False}, "REPLAY_HASH_CHAIN_INVALID", MonitoringStatus.CRITICAL),
        ({"replay_state_machine_valid": False}, "REPLAY_LIFECYCLE_INVALID", MonitoringStatus.CRITICAL),
        ({"replay_protection_restored": False}, "REPLAY_PROTECTION_NOT_RESTORED", MonitoringStatus.CRITICAL),
        ({"post_recovery_concurrency_valid": False}, "REPLAY_CONCURRENCY_INVALID", MonitoringStatus.CRITICAL),
        ({"regression_failed": 1}, "REGRESSION_FAILURE", MonitoringStatus.CRITICAL),
        ({"regression_warnings": 2}, "REGRESSION_WARNINGS", MonitoringStatus.DEGRADED),
        ({"git_clean": False}, "GIT_DIRTY", MonitoringStatus.BLOCKED),
        ({"git_ahead": 1}, "GIT_AHEAD", MonitoringStatus.BLOCKED),
        ({"git_behind": 1}, "GIT_BEHIND", MonitoringStatus.BLOCKED),
        ({"production_authorized": True}, "PRODUCTION_AUTHORIZATION_CONTRADICTION", MonitoringStatus.CRITICAL),
        ({"control_plane_owner": "Ubuntu"}, "FORBIDDEN_CONTROL_PLANE_OWNER", MonitoringStatus.CRITICAL),
    ],
)
def test_deterministic_monitoring_conditions(
    config, healthy_evidence, changes, code, status
) -> None:
    snapshot = evaluate(config, dataclasses.replace(healthy_evidence, **changes))
    assert code in reason_codes(snapshot)
    assert snapshot.overall_status is status
    candidates = [item for item in snapshot.alert_candidates if item.reason_code == code]
    assert len(candidates) == 1
    assert candidates[0].dispatch_authorized is False
    assert candidates[0].dispatched is False
    assert candidates[0].production_authorized is False


def test_alert_ids_digests_and_deduplication_keys_are_stable(
    config, healthy_evidence
) -> None:
    evidence = dataclasses.replace(healthy_evidence, git_clean=False)
    first, second = evaluate(config, evidence), evaluate(config, evidence)
    assert first.alert_candidates == second.alert_candidates
    alert = first.alert_candidates[0]
    assert alert.alert_candidate_id == second.alert_candidates[0].alert_candidate_id
    assert alert.deduplication_key == second.alert_candidates[0].deduplication_key
    assert alert.candidate_digest == second.alert_candidates[0].candidate_digest


def test_missing_malformed_stale_and_contradictory_evidence(config, healthy_evidence) -> None:
    missing = evaluate(config, dataclasses.replace(
        healthy_evidence, audit_inspection_report_digest=None))
    assert missing.overall_status is MonitoringStatus.UNAVAILABLE
    assert "AUDIT_EVIDENCE_MISSING" in reason_codes(missing)
    malformed = evaluate(config, dataclasses.replace(
        healthy_evidence, audit_inspection_report_digest="not-a-digest"))
    assert malformed.overall_status is MonitoringStatus.BLOCKED
    assert "AUDIT_DIGEST_INVALID" in reason_codes(malformed)
    stale = evaluate(config, dataclasses.replace(
        healthy_evidence, audit_evidence_generated_at="2026-07-30T10:00:00+00:00"))
    assert "EVIDENCE_STALE" in reason_codes(stale)
    future = evaluate(config, dataclasses.replace(
        healthy_evidence, audit_evidence_generated_at="2026-07-30T13:00:00+00:00"))
    assert "EVIDENCE_TIMESTAMP_CONTRADICTION" in reason_codes(future)
    contradiction = evaluate(config, dataclasses.replace(
        healthy_evidence, audit_production_privacy_violations=1))
    assert "AUDIT_STATUS_COUNTER_CONTRADICTION" in reason_codes(contradiction)


@pytest.mark.parametrize("counter", sorted(SAFETY))
def test_every_safety_counter_is_critical(config, healthy_evidence, counter) -> None:
    counters = dict(SAFETY)
    counters[counter] = 1
    snapshot = evaluate(
        config, dataclasses.replace(healthy_evidence, safety_counters=counters))
    assert snapshot.overall_status is MonitoringStatus.CRITICAL
    assert "NONZERO_SAFETY_COUNTER" in reason_codes(snapshot)


def test_operational_activation_contradiction_is_critical(config, healthy_evidence) -> None:
    snapshot = evaluate(config, dataclasses.replace(
        healthy_evidence, operational_writer_activated=True))
    assert snapshot.overall_status is MonitoringStatus.CRITICAL
    assert "PRE_ACTIVATION_OPERATIONAL_STATE_CONTRADICTION" in reason_codes(snapshot)


def test_secret_fields_cannot_enter_contract_and_summaries_are_redacted(
    config, healthy_evidence
) -> None:
    with pytest.raises(TypeError):
        MonitoringEvidence(**{
            **{field.name: getattr(healthy_evidence, field.name)
               for field in dataclasses.fields(healthy_evidence)},
            "api_key": "secret",
        })
    snapshot = evaluate(config, dataclasses.replace(healthy_evidence, git_clean=False))
    serialized = snapshot.canonical_json().lower()
    assert "secret" not in serialized
    assert "/users/" not in serialized
    assert "authorization_header" not in serialized


def test_dispatch_requests_and_notification_adapters_are_denied(
    config, healthy_evidence
) -> None:
    with pytest.raises(OperationalMonitoringError, match="dispatch"):
        OperationalMonitoringService(config).evaluate(
            dataclasses.replace(healthy_evidence, git_clean=False),
            stage=OperationalStage.PRE_ACTIVATION, dispatch_requested=True)
    with pytest.raises(OperationalMonitoringError, match="adapter"):
        AlertCandidateEvaluator().evaluate(
            snapshot_id="x", findings=(), evidence_references=(),
            observed_at=NOW, notification_adapter=object())


def test_monitoring_evaluation_performs_no_commands_network_or_dynamic_import(
    config, healthy_evidence, monkeypatch
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: calls.append("command"))
    monkeypatch.setattr(socket, "create_connection",
                        lambda *args, **kwargs: calls.append("network"))
    monkeypatch.setattr(importlib, "import_module",
                        lambda *args, **kwargs: calls.append("import"))
    evaluate(config, healthy_evidence)
    assert calls == []


def test_dependency_policy_classifies_monitoring_and_passes() -> None:
    report = validate_dependency_boundaries(repository_root=ROOT)
    assert report["overall_result"] == "PASS", report["violations"]
    analyzed = [
        path for path in report["analyzed_files"]
        if "operational_monitoring" in path
    ]
    assert analyzed
