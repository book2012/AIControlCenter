from __future__ import annotations

import dataclasses
import importlib
import socket
import subprocess
from pathlib import Path

import pytest

from core.deployment.alert_routing import (
    AlertDisposition, AlertEscalationLevel, AlertHistoryEvidence, AlertHistoryRecord,
    AlertRoute, AlertRoutingConfig, AlertRoutingError, AlertRoutingService,
    AlertRoutingStatus, AlertSuppressionReason,
)
from core.deployment.operational_monitoring import (
    AlertCandidate, AlertCandidateStatus, MonitoringDimension, MonitoringSeverity,
)
from core.deployment.policy import validate_dependency_boundaries

NOW = "2026-07-30T12:00:00+00:00"
DIGEST = "sha256:" + "a" * 64


@pytest.fixture
def config():
    return AlertRoutingConfig(300, 1800, 60, 600, 86400, 3)


def candidate(severity=MonitoringSeverity.WARNING, *,
              dimension=MonitoringDimension.GIT_HEALTH,
              reason="GIT_DIRTY", observed=NOW, summary="Git state requires review"):
    key = "sha256:" + ("b" if reason == "GIT_DIRTY" else "c") * 64
    return AlertCandidate(
        "candidate-" + reason.lower(), key, "snapshot-1", dimension, severity,
        reason, summary, ("evidence-1",), observed, observed,
        AlertCandidateStatus.CANDIDATE, False, False, False, DIGEST)


def history(item, *, severity=None, last="2026-07-30T11:59:00+00:00",
            resolved=False, resolved_at=None, record_id="history-1"):
    return AlertHistoryRecord(
        record_id, item.deduplication_key, item.alert_candidate_id, item.candidate_digest,
        item.monitoring_snapshot_id, item.dimension, item.reason_code,
        severity or item.severity, "2026-07-30T10:00:00+00:00", last, 2,
        last, None, resolved, resolved_at, False)


def route(config, item, records=(), **kwargs):
    return AlertRoutingService(config).evaluate(
        monitoring_snapshot_id="snapshot-1", monitoring_snapshot_digest=DIGEST,
        candidates=(item,), history=AlertHistoryEvidence(tuple(records)),
        evaluated_at=NOW, **kwargs)


def test_contracts_config_first_observation_and_determinism(config):
    item = candidate(MonitoringSeverity.INFO)
    first, second = route(config, item), route(config, item)
    assert first == second
    assert first.canonical_json() == second.canonical_json()
    assert first.routing_plan_id == second.routing_plan_id
    assert first.decisions[0].disposition is AlertDisposition.ROUTE
    assert first.routes == (AlertRoute.CONTROL_PLANE_DASHBOARD,)
    assert first.alerts_dispatched == first.notifications_sent == first.persistence_writes == 0
    with pytest.raises(dataclasses.FrozenInstanceError):
        first.status = AlertRoutingStatus.BLOCKED
    with pytest.raises(AlertRoutingError):
        AlertRoutingConfig(0, 1, 1, 1, 1, 1)
    with pytest.raises(AlertRoutingError):
        AlertRoutingConfig(2, 1, 1, 1, 1, 1)
    with pytest.raises(AlertRoutingError):
        AlertRoutingConfig(1, 1, 1, 1, 1, 1, dispatch_authorized=True)


@pytest.mark.parametrize(
    ("severity", "expected"),
    [
        (MonitoringSeverity.INFO, (AlertRoute.CONTROL_PLANE_DASHBOARD,)),
        (MonitoringSeverity.WARNING, (
            AlertRoute.CONTROL_PLANE_DASHBOARD, AlertRoute.OPERATOR_REVIEW_QUEUE)),
        (MonitoringSeverity.CRITICAL, (
            AlertRoute.CONTROL_PLANE_DASHBOARD, AlertRoute.OPERATOR_REVIEW_QUEUE,
            AlertRoute.INCIDENT_RESPONSE_QUEUE)),
    ])
def test_stable_default_routes(config, severity, expected):
    assert route(config, candidate(severity)).routes == expected


def test_duplicate_cooldown_warning_and_critical_reminders(config):
    warning = candidate()
    inside = route(config, warning, (history(warning),)).decisions[0]
    assert inside.disposition is AlertDisposition.SUPPRESS_COOLDOWN
    assert inside.suppression_reason is AlertSuppressionReason.COOLDOWN_ACTIVE
    middle = route(config, warning, (
        history(warning, last="2026-07-30T11:50:00+00:00"),)).decisions[0]
    assert middle.disposition is AlertDisposition.SUPPRESS_DUPLICATE
    assert route(config, warning, (
        history(warning, last="2026-07-30T11:20:00+00:00"),)).decisions[0].disposition is AlertDisposition.ROUTE
    critical = candidate(MonitoringSeverity.CRITICAL)
    assert route(config, critical, (
        history(critical, last="2026-07-30T11:40:00+00:00"),)).decisions[0].disposition is AlertDisposition.ROUTE


def test_severity_escalation_bypass(config):
    warning = candidate()
    info_up = route(config, warning, (
        history(warning, severity=MonitoringSeverity.INFO),)).decisions[0]
    assert info_up.disposition is AlertDisposition.ESCALATE
    assert info_up.escalation_level is AlertEscalationLevel.OPERATOR_REVIEW
    critical = candidate(MonitoringSeverity.CRITICAL)
    warning_up = route(config, critical, (
        history(critical, severity=MonitoringSeverity.WARNING),)).decisions[0]
    assert warning_up.disposition is AlertDisposition.ESCALATE
    assert warning_up.severity_change_evidence == "WARNING->CRITICAL"


def test_resolved_suppression_and_recurrence(config):
    item = candidate(observed="2026-07-30T11:00:00+00:00")
    resolved = history(item, resolved=True, resolved_at="2026-07-30T11:30:00+00:00")
    assert route(config, item, (resolved,)).decisions[0].disposition is AlertDisposition.SUPPRESS_RESOLVED
    recurrent = dataclasses.replace(item, observed_at=NOW)
    decision = route(config, recurrent, (resolved,)).decisions[0]
    assert decision.disposition is AlertDisposition.ROUTE and decision.recurrence
    critical = dataclasses.replace(recurrent, severity=MonitoringSeverity.CRITICAL)
    assert route(config, critical, (resolved,)).decisions[0].disposition is AlertDisposition.ESCALATE


def test_security_and_documentation_routes(config):
    security = candidate(
        MonitoringSeverity.CRITICAL,
        dimension=MonitoringDimension.PRODUCTION_AUTHORIZATION,
        reason="PRODUCTION_AUTHORIZATION_CONTRADICTION")
    decision = route(config, security).decisions[0]
    assert AlertRoute.SECURITY_REVIEW_QUEUE in decision.routes
    assert decision.escalation_level is AlertEscalationLevel.SECURITY_REVIEW
    documentation = candidate(
        dimension=MonitoringDimension.DOCUMENTATION, reason="DOCUMENTATION_INCOMPLETE")
    assert AlertRoute.DOCUMENTATION_BACKLOG in route(config, documentation).routes


@pytest.mark.parametrize("mutation", ["conflict", "future", "limit"])
def test_invalid_history_blocks(config, mutation):
    item = candidate()
    records = [history(item)]
    if mutation == "conflict":
        records[0] = dataclasses.replace(records[0], reason_code="OTHER")
    elif mutation == "future":
        records[0] = dataclasses.replace(
            records[0], last_observed_at="2026-07-31T00:00:00+00:00")
    else:
        records = [dataclasses.replace(
            records[0], history_record_id=f"h-{i}") for i in range(4)]
    plan = route(config, item, records)
    assert plan.status is AlertRoutingStatus.BLOCKED and plan.blocked_count == 1


def test_stale_history_is_ignored(config):
    item = candidate()
    stale = dataclasses.replace(
        history(item, last="2026-07-28T00:00:00+00:00"),
        first_observed_at="2026-07-27T00:00:00+00:00")
    assert route(config, item, (stale,)).decisions[0].disposition is AlertDisposition.ROUTE


@pytest.mark.parametrize("kwargs", [
    {"dispatch_requested": True}, {"production_authorized": True},
    {"requested_destinations": ("https://example.test/hook",)},
    {"requested_destinations": ("operator@example.test",)},
])
def test_dispatch_production_and_arbitrary_destinations_block(config, kwargs):
    assert route(config, candidate(), **kwargs).status is AlertRoutingStatus.BLOCKED


def test_missing_config_adapter_malformed_binding_and_secret_content_block(config):
    item = candidate()
    common = dict(monitoring_snapshot_id="snapshot-1", monitoring_snapshot_digest=DIGEST,
                  candidates=(item,), history=AlertHistoryEvidence(), evaluated_at=NOW)
    assert AlertRoutingService(None).evaluate(**common).status is AlertRoutingStatus.BLOCKED
    assert AlertRoutingService(None).evaluate(
        **{**common, "candidates": ()}).status is AlertRoutingStatus.BLOCKED
    assert AlertRoutingService(config, notification_adapter=object()).evaluate(
        **common).status is AlertRoutingStatus.BLOCKED
    assert route(config, dataclasses.replace(item, deduplication_key="")).status is AlertRoutingStatus.BLOCKED
    assert route(config, dataclasses.replace(item, candidate_digest="bad")).status is AlertRoutingStatus.BLOCKED
    assert route(config, dataclasses.replace(item, monitoring_snapshot_id="other")).status is AlertRoutingStatus.BLOCKED
    assert route(config, dataclasses.replace(
        item, redacted_summary="api_key=secret")).status is AlertRoutingStatus.BLOCKED


def test_no_commands_network_dynamic_import_or_persistence(config, monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: calls.append("command"))
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: calls.append("network"))
    monkeypatch.setattr(importlib, "import_module", lambda *a, **k: calls.append("import"))
    plan = route(config, candidate())
    assert calls == []
    assert plan.alerts_dispatched == plan.notifications_sent == plan.persistence_writes == 0


def test_dependency_policy_passes_and_classifies_alert_routing():
    report = validate_dependency_boundaries(
        repository_root=Path(__file__).resolve().parents[2])
    assert report["overall_result"] == "PASS", report["violations"]
    assert any("alert_routing" in path for path in report["analyzed_files"])
