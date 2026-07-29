"""Immutable, pure contracts for logical alert routing and deduplication."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.operational_monitoring import MonitoringDimension, MonitoringSeverity


class AlertRoutingError(ValueError):
    """Fail-closed alert-routing validation error."""


class AlertRoute(StrEnum):
    CONTROL_PLANE_DASHBOARD = "CONTROL_PLANE_DASHBOARD"
    OPERATOR_REVIEW_QUEUE = "OPERATOR_REVIEW_QUEUE"
    INCIDENT_RESPONSE_QUEUE = "INCIDENT_RESPONSE_QUEUE"
    SECURITY_REVIEW_QUEUE = "SECURITY_REVIEW_QUEUE"
    DOCUMENTATION_BACKLOG = "DOCUMENTATION_BACKLOG"


class AlertDisposition(StrEnum):
    ROUTE = "ROUTE"
    ESCALATE = "ESCALATE"
    SUPPRESS_DUPLICATE = "SUPPRESS_DUPLICATE"
    SUPPRESS_COOLDOWN = "SUPPRESS_COOLDOWN"
    SUPPRESS_RESOLVED = "SUPPRESS_RESOLVED"
    BLOCK = "BLOCK"


class AlertRoutingStatus(StrEnum):
    READY = "READY"
    BLOCKED = "BLOCKED"


class AlertEscalationLevel(StrEnum):
    NONE = "NONE"
    OPERATOR_REVIEW = "OPERATOR_REVIEW"
    INCIDENT_RESPONSE = "INCIDENT_RESPONSE"
    SECURITY_REVIEW = "SECURITY_REVIEW"


class AlertSuppressionReason(StrEnum):
    DUPLICATE = "DUPLICATE"
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"
    RESOLVED_NO_NEW_OCCURRENCE = "RESOLVED_NO_NEW_OCCURRENCE"


@dataclass(frozen=True, slots=True)
class AlertRoutingConfig:
    warning_cooldown_seconds: int
    warning_reminder_interval_seconds: int
    critical_cooldown_seconds: int
    critical_reminder_interval_seconds: int
    maximum_accepted_history_age_seconds: int
    maximum_history_records_per_deduplication_key: int
    recurrence_routing_enabled: bool = True
    severity_escalation_bypass_enabled: bool = True
    dispatch_authorized: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        values = (
            self.warning_cooldown_seconds, self.warning_reminder_interval_seconds,
            self.critical_cooldown_seconds, self.critical_reminder_interval_seconds,
            self.maximum_accepted_history_age_seconds,
            self.maximum_history_records_per_deduplication_key,
        )
        if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0
               for value in values):
            raise AlertRoutingError("routing durations and history limits must be positive")
        if self.warning_reminder_interval_seconds < self.warning_cooldown_seconds:
            raise AlertRoutingError("warning reminder must be at least its cooldown")
        if self.critical_reminder_interval_seconds < self.critical_cooldown_seconds:
            raise AlertRoutingError("critical reminder must be at least its cooldown")
        if self.dispatch_authorized or self.production_authorized:
            raise AlertRoutingError("dispatch and production authorization must remain false")


@dataclass(frozen=True, slots=True)
class AlertHistoryRecord:
    history_record_id: str
    deduplication_key: str
    prior_alert_candidate_id: str
    prior_candidate_digest: str
    prior_snapshot_id: str
    dimension: MonitoringDimension
    reason_code: str
    prior_severity: MonitoringSeverity
    first_observed_at: str
    last_observed_at: str
    observation_count: int
    last_routed_at: str | None
    last_escalated_at: str | None
    resolved: bool
    resolved_at: str | None
    production_authorized: bool = False


@dataclass(frozen=True, slots=True)
class AlertHistoryEvidence:
    records: tuple[AlertHistoryRecord, ...] = ()
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple):
            raise AlertRoutingError("history records must be an immutable tuple")


@dataclass(frozen=True, slots=True, order=True)
class AlertRoutingFinding:
    code: str
    candidate_id: str
    summary: str

    def as_dict(self) -> dict[str, str]:
        return {"candidate_id": self.candidate_id, "code": self.code, "summary": self.summary}


@dataclass(frozen=True, slots=True)
class AlertRoutingDecision:
    decision_id: str
    alert_candidate_id: str
    candidate_digest: str
    deduplication_key: str
    disposition: AlertDisposition
    routes: tuple[AlertRoute, ...]
    escalation_level: AlertEscalationLevel
    suppression_reason: AlertSuppressionReason | None
    matched_history_references: tuple[str, ...]
    first_observed_at: str
    evaluated_at: str
    recurrence: bool
    severity_change_evidence: str | None
    dispatch_authorized: bool
    dispatched: bool
    persisted: bool
    production_authorized: bool
    decision_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "alert_candidate_id": self.alert_candidate_id,
            "candidate_digest": self.candidate_digest,
            "deduplication_key": self.deduplication_key,
            "decision_digest": self.decision_digest,
            "decision_id": self.decision_id,
            "dispatch_authorized": self.dispatch_authorized,
            "dispatched": self.dispatched,
            "disposition": self.disposition.value,
            "escalation_level": self.escalation_level.value,
            "evaluated_at": self.evaluated_at,
            "first_observed_at": self.first_observed_at,
            "matched_history_references": list(self.matched_history_references),
            "persisted": self.persisted,
            "production_authorized": self.production_authorized,
            "recurrence": self.recurrence,
            "routes": [route.value for route in self.routes],
            "severity_change_evidence": self.severity_change_evidence,
            "suppression_reason": self.suppression_reason.value if self.suppression_reason else None,
        }


@dataclass(frozen=True, slots=True)
class AlertRoutingPlan:
    routing_plan_id: str
    monitoring_snapshot_id: str
    monitoring_snapshot_digest: str
    evaluated_at: str
    status: AlertRoutingStatus
    decisions: tuple[AlertRoutingDecision, ...]
    routes: tuple[AlertRoute, ...]
    suppressed_candidates: tuple[str, ...]
    escalated_candidates: tuple[str, ...]
    findings: tuple[AlertRoutingFinding, ...]
    restrictions: tuple[str, ...]
    candidate_count: int
    routed_count: int
    escalated_count: int
    suppressed_count: int
    blocked_count: int
    alerts_dispatched: int
    notifications_sent: int
    persistence_writes: int
    dispatch_authorized: bool
    production_authorized: bool
    routing_plan_digest: str

    def __post_init__(self) -> None:
        for field in ("decisions", "routes", "suppressed_candidates",
                      "escalated_candidates", "findings", "restrictions"):
            if not isinstance(getattr(self, field), tuple):
                raise AlertRoutingError(f"{field} must be an immutable tuple")

    def as_dict(self) -> dict[str, Any]:
        return {
            "alerts_dispatched": self.alerts_dispatched,
            "blocked_count": self.blocked_count,
            "candidate_count": self.candidate_count,
            "decisions": [item.as_dict() for item in self.decisions],
            "dispatch_authorized": self.dispatch_authorized,
            "escalated_candidates": list(self.escalated_candidates),
            "escalated_count": self.escalated_count,
            "evaluated_at": self.evaluated_at,
            "findings": [item.as_dict() for item in self.findings],
            "monitoring_snapshot_digest": self.monitoring_snapshot_digest,
            "monitoring_snapshot_id": self.monitoring_snapshot_id,
            "notifications_sent": self.notifications_sent,
            "persistence_writes": self.persistence_writes,
            "production_authorized": self.production_authorized,
            "restrictions": list(self.restrictions),
            "routed_count": self.routed_count,
            "routes": [item.value for item in self.routes],
            "routing_plan_digest": self.routing_plan_digest,
            "routing_plan_id": self.routing_plan_id,
            "status": self.status.value,
            "suppressed_candidates": list(self.suppressed_candidates),
            "suppressed_count": self.suppressed_count,
        }

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode("utf-8")


def digest(value: Any) -> str:
    return sha256_digest(value)
