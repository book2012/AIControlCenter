"""Immutable contracts for the non-production M3-A3C operational drill."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from core.deployment.alert_routing import AlertHistoryEvidence, AlertRoute, AlertRoutingConfig, AlertRoutingPlan
from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.operational_monitoring import MonitoringEvidence, MonitoringSnapshot, OperationalMonitoringConfig


class MonitoringAlertDrillError(ValueError):
    """Fail-closed drill validation error."""


class MonitoringAlertDrillScenario(StrEnum):
    HEALTHY_NO_ALERTS = "HEALTHY_NO_ALERTS"
    FIRST_WARNING_ROUTE = "FIRST_WARNING_ROUTE"
    DUPLICATE_WARNING_SUPPRESSION = "DUPLICATE_WARNING_SUPPRESSION"
    WARNING_REMINDER = "WARNING_REMINDER"
    WARNING_TO_CRITICAL_ESCALATION = "WARNING_TO_CRITICAL_ESCALATION"
    CRITICAL_REMINDER = "CRITICAL_REMINDER"
    RESOLVED_CONDITION_SUPPRESSION = "RESOLVED_CONDITION_SUPPRESSION"
    RESOLVED_CRITICAL_RECURRENCE = "RESOLVED_CRITICAL_RECURRENCE"
    AUDIT_CHAIN_CRITICAL = "AUDIT_CHAIN_CRITICAL"
    REPLAY_CHAIN_CRITICAL = "REPLAY_CHAIN_CRITICAL"
    REPLAY_RECOVERY_FAILURE = "REPLAY_RECOVERY_FAILURE"
    PRODUCTION_WRITE_SAFETY_CRITICAL = "PRODUCTION_WRITE_SAFETY_CRITICAL"
    PRODUCTION_AUTHORIZATION_CONTRADICTION = "PRODUCTION_AUTHORIZATION_CONTRADICTION"
    FORBIDDEN_UBUNTU_OWNERSHIP = "FORBIDDEN_UBUNTU_OWNERSHIP"
    GIT_BLOCKED = "GIT_BLOCKED"
    REGRESSION_FAILURE = "REGRESSION_FAILURE"
    MISSING_EVIDENCE_BLOCK = "MISSING_EVIDENCE_BLOCK"
    ROUTING_PLAN_TAMPER = "ROUTING_PLAN_TAMPER"
    SIMULATED_SINK_FAILURE = "SIMULATED_SINK_FAILURE"


class MonitoringAlertDrillStatus(StrEnum):
    VALIDATED = "VALIDATED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


class MonitoringAlertDrillDecision(StrEnum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class MonitoringAlertDrillConfig:
    allowed_logical_routes: tuple[AlertRoute, ...]
    maximum_envelopes_per_drill: int
    maximum_candidates_per_drill: int
    fail_on_blocked_decision: bool = True
    require_zero_dispatched: bool = True
    require_zero_notifications: bool = True
    require_zero_network: bool = True
    require_zero_persistence: bool = True
    require_complete_receipt_binding: bool = True
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.allowed_logical_routes or not isinstance(self.allowed_logical_routes, tuple):
            raise MonitoringAlertDrillError("allowed logical routes must be a non-empty tuple")
        if len(set(self.allowed_logical_routes)) != len(self.allowed_logical_routes):
            raise MonitoringAlertDrillError("allowed logical routes must be unique")
        for value in (self.maximum_envelopes_per_drill, self.maximum_candidates_per_drill):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 < value <= 10_000:
                raise MonitoringAlertDrillError("drill maxima must be positive and bounded")
        if self.production_authorized:
            raise MonitoringAlertDrillError("production authorization must remain false")


@dataclass(frozen=True, slots=True)
class MonitoringAlertDrillRequest:
    drill_name: str
    scenario: MonitoringAlertDrillScenario
    monitoring_config: OperationalMonitoringConfig
    monitoring_evidence: MonitoringEvidence
    routing_config: AlertRoutingConfig
    alert_history: AlertHistoryEvidence
    evaluated_at: str
    envelope_created_at: str
    receipt_acknowledged_at: str
    dispatch_requested: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.scenario, MonitoringAlertDrillScenario):
            raise MonitoringAlertDrillError("unknown drill scenario")
        if not self.drill_name.strip():
            raise MonitoringAlertDrillError("drill name is required")
        if self.dispatch_requested or self.production_authorized:
            raise MonitoringAlertDrillError("external dispatch and production are prohibited")


@dataclass(frozen=True, slots=True)
class MonitoringAlertDrillStep:
    sequence: int
    code: str
    result: str
    evidence_reference: str

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "evidence_reference": self.evidence_reference,
                "result": self.result, "sequence": self.sequence}


@dataclass(frozen=True, slots=True)
class SimulatedAlertEnvelope:
    envelope_id: str
    drill_id: str
    routing_plan_id: str
    routing_decision_id: str
    alert_candidate_id: str
    logical_route: AlertRoute
    severity: str
    escalation_level: str
    redacted_summary: str
    evidence_references: tuple[str, ...]
    created_at: str
    simulated: bool
    dispatch_authorized: bool
    production_authorized: bool
    envelope_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {"alert_candidate_id": self.alert_candidate_id, "created_at": self.created_at,
                "dispatch_authorized": self.dispatch_authorized, "drill_id": self.drill_id,
                "escalation_level": self.escalation_level, "envelope_digest": self.envelope_digest,
                "envelope_id": self.envelope_id, "evidence_references": list(self.evidence_references),
                "logical_route": self.logical_route.value, "production_authorized": self.production_authorized,
                "redacted_summary": self.redacted_summary, "routing_decision_id": self.routing_decision_id,
                "routing_plan_id": self.routing_plan_id, "severity": self.severity, "simulated": self.simulated}


@dataclass(frozen=True, slots=True)
class SimulatedAlertDeliveryReceipt:
    receipt_id: str
    envelope_id: str
    envelope_digest: str
    logical_route: AlertRoute
    accepted_by_simulator: bool
    simulated: bool
    dispatched: bool
    delivered: bool
    persisted: bool
    network_used: bool
    acknowledged_at: str
    production_authorized: bool
    receipt_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {"accepted_by_simulator": self.accepted_by_simulator,
                "acknowledged_at": self.acknowledged_at, "delivered": self.delivered,
                "dispatched": self.dispatched, "envelope_digest": self.envelope_digest,
                "envelope_id": self.envelope_id, "logical_route": self.logical_route.value,
                "network_used": self.network_used, "persisted": self.persisted,
                "production_authorized": self.production_authorized,
                "receipt_digest": self.receipt_digest, "receipt_id": self.receipt_id,
                "simulated": self.simulated}


@dataclass(frozen=True, slots=True, order=True)
class MonitoringAlertDrillFinding:
    code: str
    summary: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "summary": self.summary}


@dataclass(frozen=True, slots=True)
class MonitoringAlertDrillPlan:
    drill_plan_id: str
    scenario: MonitoringAlertDrillScenario
    monitoring_snapshot: MonitoringSnapshot
    routing_plan: AlertRoutingPlan
    envelopes: tuple[SimulatedAlertEnvelope, ...]
    steps: tuple[MonitoringAlertDrillStep, ...]
    drill_plan_digest: str


@dataclass(frozen=True, slots=True)
class MonitoringAlertDrillValidationReport:
    report_id: str
    drill_plan_id: str
    scenario: MonitoringAlertDrillScenario
    status: MonitoringAlertDrillStatus
    decision: MonitoringAlertDrillDecision
    snapshot_id: str
    snapshot_digest: str
    routing_plan_id: str
    routing_plan_digest: str
    candidate_count: int
    routed_count: int
    escalated_count: int
    suppressed_count: int
    blocked_count: int
    expected_receipt_count: int
    accepted_receipt_count: int
    rejected_receipt_count: int
    envelopes: tuple[SimulatedAlertEnvelope, ...]
    receipts: tuple[SimulatedAlertDeliveryReceipt, ...]
    findings: tuple[MonitoringAlertDrillFinding, ...]
    steps: tuple[MonitoringAlertDrillStep, ...]
    alerts_dispatched: int
    actual_deliveries: int
    notifications_sent: int
    network_requests: int
    persistence_writes: int
    production_authorized: bool
    report_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted_receipt_count": self.accepted_receipt_count,
            "actual_deliveries": self.actual_deliveries, "alerts_dispatched": self.alerts_dispatched,
            "blocked_count": self.blocked_count, "candidate_count": self.candidate_count,
            "decision": self.decision.value, "drill_plan_id": self.drill_plan_id,
            "envelopes": [item.as_dict() for item in self.envelopes],
            "escalated_count": self.escalated_count,
            "expected_receipt_count": self.expected_receipt_count,
            "findings": [item.as_dict() for item in self.findings],
            "network_requests": self.network_requests, "notifications_sent": self.notifications_sent,
            "persistence_writes": self.persistence_writes,
            "production_authorized": self.production_authorized,
            "receipts": [item.as_dict() for item in self.receipts],
            "rejected_receipt_count": self.rejected_receipt_count,
            "report_digest": self.report_digest, "report_id": self.report_id,
            "routed_count": self.routed_count, "routing_plan_digest": self.routing_plan_digest,
            "routing_plan_id": self.routing_plan_id, "scenario": self.scenario.value,
            "snapshot_digest": self.snapshot_digest, "snapshot_id": self.snapshot_id,
            "status": self.status.value, "steps": [item.as_dict() for item in self.steps],
            "suppressed_count": self.suppressed_count,
        }

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()


def digest(value: Any) -> str:
    return sha256_digest(value)
