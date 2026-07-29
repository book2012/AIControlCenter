from __future__ import annotations

import dataclasses
import importlib
import socket
import subprocess
from pathlib import Path

import pytest

from core.deployment.alert_routing import (
    AlertHistoryEvidence, AlertHistoryRecord, AlertRoute, AlertRoutingConfig,
)
from core.deployment.monitoring_alert_drill import (
    InMemorySimulatedAlertSink, MonitoringAlertDrillConfig,
    MonitoringAlertDrillDecision, MonitoringAlertDrillError,
    MonitoringAlertDrillRequest, MonitoringAlertDrillScenario,
    MonitoringAlertDrillService, MonitoringAlertDrillStatus,
    MonitoringAlertDrillValidator,
)
from core.deployment.operational_monitoring import MonitoringEvidence
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).resolve().parents[2]
NOW = "2026-07-30T12:00:00+00:00"
FRESH = "2026-07-30T11:55:00+00:00"
DIGEST = "sha256:" + "a" * 64
SAFETY = {key: 0 for key in (
    "operational_database_files_created", "monitoring_database_writes",
    "operational_audit_writes", "operational_replay_writes", "alerts_dispatched",
    "notifications_sent", "n8n_invocations", "network_requests", "ubuntu_changes",
    "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
    "production_activations")}


@pytest.fixture
def monitoring_config():
    from core.deployment.operational_monitoring import OperationalMonitoringConfig
    return OperationalMonitoringConfig(3600, 3600, 7200, 86400, 172800,
                                       3600, 7200, 86400, 172800)


@pytest.fixture
def routing_config():
    return AlertRoutingConfig(300, 1800, 60, 600, 86400, 10)


@pytest.fixture
def drill_config():
    return MonitoringAlertDrillConfig(tuple(AlertRoute), 100, 100)


@pytest.fixture
def healthy_evidence():
    return MonitoringEvidence(
        observed_at=NOW, audit_inspection_status="HEALTHY",
        audit_inspection_report_id="audit-inspection-1",
        audit_inspection_report_digest=DIGEST, audit_evidence_generated_at=FRESH,
        audit_schema_valid=True, audit_hash_chain_valid=True,
        audit_production_privacy_violations=0, audit_recovery_status="RECOVERY_VALID",
        audit_recovery_report_id="audit-recovery-1", audit_recovery_report_digest=DIGEST,
        audit_recovery_evidence_generated_at=FRESH, audit_backup_age_seconds=300,
        audit_recovery_drill_age_seconds=300, replay_inspection_status="HEALTHY",
        replay_inspection_report_id="replay-inspection-1",
        replay_inspection_report_digest=DIGEST, replay_evidence_generated_at=FRESH,
        replay_schema_valid=True, replay_hash_chain_valid=True,
        replay_state_machine_valid=True, replay_violation_count=0,
        replay_recovery_status="RECOVERY_VALID", replay_recovery_report_id="replay-recovery-1",
        replay_recovery_report_digest=DIGEST, replay_recovery_evidence_generated_at=FRESH,
        replay_backup_age_seconds=300, replay_recovery_drill_age_seconds=300,
        permit_states_restored=True, replay_protection_restored=True,
        post_recovery_concurrency_valid=True, m2_readiness_status="READY",
        m2_readiness_report_id="m2-readiness-1", m2_readiness_report_digest=DIGEST,
        m2_evidence_generated_at=FRESH, controlled_pilot_closeout_status="CLOSED",
        pilot_report_id="pilot-closeout-1", pilot_report_digest=DIGEST,
        pilot_evidence_generated_at=FRESH, regression_passed=100, regression_failed=0,
        regression_deselected=0, regression_warnings=0, git_clean=True, git_ahead=0,
        git_behind=0, documentation_complete=True, control_plane_owner="AIControlCenter/Mac",
        operational_audit_database_created=False, operational_replay_database_created=False,
        operational_writer_activated=False, operational_backup_schedule_activated=False,
        safety_counters=SAFETY, production_authorized=False)


def request(scenario, monitoring_config, routing_config, evidence, history=AlertHistoryEvidence()):
    return MonitoringAlertDrillRequest(
        "M3-A3C", scenario, monitoring_config, evidence, routing_config, history,
        NOW, NOW, NOW)


def run(scenario, monitoring_config, routing_config, drill_config, evidence,
        history=AlertHistoryEvidence(), sink=None):
    return MonitoringAlertDrillService(
        drill_config, sink or InMemorySimulatedAlertSink()).run(
            request(scenario, monitoring_config, routing_config, evidence, history))


def test_immutable_configuration_and_unknown_scenario(drill_config, monitoring_config,
                                                       routing_config, healthy_evidence):
    with pytest.raises(dataclasses.FrozenInstanceError):
        drill_config.maximum_envelopes_per_drill = 2
    with pytest.raises(MonitoringAlertDrillError):
        MonitoringAlertDrillConfig(tuple(AlertRoute), 0, 1)
    with pytest.raises(ValueError):
        MonitoringAlertDrillScenario("UNKNOWN")
    with pytest.raises(MonitoringAlertDrillError):
        dataclasses.replace(request(MonitoringAlertDrillScenario.HEALTHY_NO_ALERTS,
                                    monitoring_config, routing_config, healthy_evidence),
                            dispatch_requested=True)


def test_healthy_no_alerts_is_deterministic(monitoring_config, routing_config,
                                             drill_config, healthy_evidence):
    first = run(MonitoringAlertDrillScenario.HEALTHY_NO_ALERTS, monitoring_config,
                routing_config, drill_config, healthy_evidence)
    second = run(MonitoringAlertDrillScenario.HEALTHY_NO_ALERTS, monitoring_config,
                 routing_config, drill_config, healthy_evidence)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.status is MonitoringAlertDrillStatus.VALIDATED
    assert first.candidate_count == first.expected_receipt_count == 0


@pytest.mark.parametrize(("scenario", "change"), [
    (MonitoringAlertDrillScenario.FIRST_WARNING_ROUTE, {"git_clean": False}),
    (MonitoringAlertDrillScenario.AUDIT_CHAIN_CRITICAL, {"audit_hash_chain_valid": False}),
    (MonitoringAlertDrillScenario.REPLAY_CHAIN_CRITICAL, {"replay_hash_chain_valid": False}),
    (MonitoringAlertDrillScenario.REPLAY_RECOVERY_FAILURE, {"replay_protection_restored": False}),
    (MonitoringAlertDrillScenario.PRODUCTION_AUTHORIZATION_CONTRADICTION, {"production_authorized": True}),
    (MonitoringAlertDrillScenario.FORBIDDEN_UBUNTU_OWNERSHIP, {"control_plane_owner": "Ubuntu"}),
    (MonitoringAlertDrillScenario.GIT_BLOCKED, {"git_behind": 1}),
    (MonitoringAlertDrillScenario.REGRESSION_FAILURE, {"regression_failed": 1}),
    (MonitoringAlertDrillScenario.MISSING_EVIDENCE_BLOCK, {"audit_inspection_report_digest": None}),
])
def test_monitoring_scenarios_route_only_to_simulator(
    scenario, change, monitoring_config, routing_config, drill_config, healthy_evidence
):
    report = run(scenario, monitoring_config, routing_config, drill_config,
                 dataclasses.replace(healthy_evidence, **change))
    assert report.status is MonitoringAlertDrillStatus.VALIDATED
    assert report.expected_receipt_count == report.accepted_receipt_count > 0
    assert all(not item.dispatched and not item.delivered and not item.network_used
               and not item.persisted for item in report.receipts)
    assert report.alerts_dispatched == report.actual_deliveries == 0
    assert report.notifications_sent == report.network_requests == report.persistence_writes == 0


def test_production_write_safety_and_all_scenarios_are_explicit(
    monitoring_config, routing_config, drill_config, healthy_evidence
):
    counters = dict(SAFETY)
    counters["monitoring_database_writes"] = 1
    report = run(MonitoringAlertDrillScenario.PRODUCTION_WRITE_SAFETY_CRITICAL,
                 monitoring_config, routing_config, drill_config,
                 dataclasses.replace(healthy_evidence, safety_counters=counters))
    assert report.status is MonitoringAlertDrillStatus.VALIDATED
    assert len(MonitoringAlertDrillScenario) == 19


def test_duplicate_suppression_reminder_escalation_and_resolved_recurrence(
    monitoring_config, routing_config, drill_config, healthy_evidence
):
    first = run(MonitoringAlertDrillScenario.FIRST_WARNING_ROUTE, monitoring_config,
                routing_config, drill_config, dataclasses.replace(healthy_evidence, git_clean=False))
    candidate = first.envelopes[0].alert_candidate_id
    # Recreate the source candidate deterministically from the first drill's snapshot binding.
    from core.deployment.operational_monitoring import OperationalMonitoringService, OperationalStage
    snapshot = OperationalMonitoringService(monitoring_config).evaluate(
        dataclasses.replace(healthy_evidence, git_clean=False), stage=OperationalStage.PRE_ACTIVATION)
    item = next(value for value in snapshot.alert_candidates if value.alert_candidate_id == candidate)
    history = AlertHistoryRecord("history-1", item.deduplication_key, item.alert_candidate_id,
        item.candidate_digest, item.monitoring_snapshot_id, item.dimension, item.reason_code,
        item.severity, "2026-07-30T10:00:00+00:00", "2026-07-30T11:59:00+00:00",
        2, "2026-07-30T11:59:00+00:00", None, False, None)
    suppressed = run(MonitoringAlertDrillScenario.DUPLICATE_WARNING_SUPPRESSION,
        monitoring_config, routing_config, drill_config,
        dataclasses.replace(healthy_evidence, git_clean=False), AlertHistoryEvidence((history,)))
    assert suppressed.suppressed_count == 1 and suppressed.envelopes == ()
    reminder = dataclasses.replace(history, last_observed_at="2026-07-30T11:20:00+00:00",
                                   last_routed_at="2026-07-30T11:20:00+00:00")
    assert run(MonitoringAlertDrillScenario.WARNING_REMINDER, monitoring_config,
               routing_config, drill_config, dataclasses.replace(
                   healthy_evidence, git_clean=False), AlertHistoryEvidence((reminder,))
               ).accepted_receipt_count > 0
    prior_info = dataclasses.replace(history, prior_severity=type(item.severity).INFO)
    escalated = run(MonitoringAlertDrillScenario.WARNING_TO_CRITICAL_ESCALATION,
        monitoring_config, routing_config, drill_config,
        dataclasses.replace(healthy_evidence, git_clean=False), AlertHistoryEvidence((prior_info,)))
    assert escalated.escalated_count == 1
    resolved = dataclasses.replace(history, resolved=True,
        resolved_at="2026-07-30T12:01:00+00:00", last_observed_at="2026-07-30T11:00:00+00:00",
        last_routed_at="2026-07-30T11:00:00+00:00")
    suppressed_resolved = run(MonitoringAlertDrillScenario.RESOLVED_CONDITION_SUPPRESSION,
        monitoring_config, routing_config, drill_config,
        dataclasses.replace(healthy_evidence, git_clean=False), AlertHistoryEvidence((resolved,)))
    assert suppressed_resolved.envelopes == ()


def test_controlled_sink_failure_prevents_partial_success_claim(
    monitoring_config, routing_config, drill_config, healthy_evidence
):
    report = run(MonitoringAlertDrillScenario.SIMULATED_SINK_FAILURE,
                 monitoring_config, routing_config, drill_config,
                 dataclasses.replace(healthy_evidence, git_clean=False),
                 sink=InMemorySimulatedAlertSink(fail_on_submission=2))
    assert report.status is MonitoringAlertDrillStatus.FAILED
    assert report.decision is MonitoringAlertDrillDecision.FAIL
    assert report.accepted_receipt_count == 1
    assert report.rejected_receipt_count == report.expected_receipt_count - 1
    assert report.actual_deliveries == report.alerts_dispatched == 0


def test_routing_plan_tamper_and_unsafe_envelopes_fail_closed(
    monitoring_config, routing_config, drill_config, healthy_evidence
):
    service = MonitoringAlertDrillService(drill_config, InMemorySimulatedAlertSink())
    source = request(MonitoringAlertDrillScenario.ROUTING_PLAN_TAMPER,
                     monitoring_config, routing_config,
                     dataclasses.replace(healthy_evidence, git_clean=False))
    plan = service.prepare(source)
    tampered = dataclasses.replace(
        plan, routing_plan=dataclasses.replace(
            plan.routing_plan, routing_plan_digest="sha256:" + "0" * 64))
    report = MonitoringAlertDrillValidator().validate(
        plan=tampered, receipts=(), config=drill_config)
    assert report.status is MonitoringAlertDrillStatus.BLOCKED
    assert {item.code for item in report.findings} >= {
        "ROUTING_PLAN_DIGEST_INVALID", "RECEIPT_MISSING"}
    envelope = plan.envelopes[0]
    sink = InMemorySimulatedAlertSink()
    with pytest.raises(MonitoringAlertDrillError):
        sink.submit(dataclasses.replace(
            envelope, redacted_summary="api_key=secret"), acknowledged_at=NOW)
    with pytest.raises(MonitoringAlertDrillError):
        sink.submit(dataclasses.replace(
            envelope, logical_route="WEBHOOK"), acknowledged_at=NOW)
    with pytest.raises(MonitoringAlertDrillError):
        sink.submit(dataclasses.replace(
            envelope, dispatch_authorized=True), acknowledged_at=NOW)


def test_no_commands_network_import_persistence_and_dependency_policy(
    monkeypatch, monitoring_config, routing_config, drill_config, healthy_evidence
):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append("subprocess"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: calls.append("network"))
    monkeypatch.setattr(importlib, "import_module", lambda *a, **k: calls.append("import"))
    run(MonitoringAlertDrillScenario.HEALTHY_NO_ALERTS, monitoring_config,
        routing_config, drill_config, healthy_evidence)
    assert calls == []
    policy = validate_dependency_boundaries(repository_root=ROOT)
    assert policy["overall_result"] == "PASS", policy["violations"]
    assert any("monitoring_alert_drill" in path for path in policy["analyzed_files"])
