"""Deterministic logical routing; never dispatches, persists, or acknowledges."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from core.deployment.operational_monitoring import (
    AlertCandidate, MonitoringDimension, MonitoringSeverity,
)

from .models import (
    AlertDisposition, AlertEscalationLevel, AlertHistoryEvidence, AlertHistoryRecord,
    AlertRoute, AlertRoutingConfig, AlertRoutingDecision, AlertRoutingFinding,
    AlertRoutingPlan, AlertRoutingStatus, AlertSuppressionReason, digest,
)

_RANK = {MonitoringSeverity.INFO: 0, MonitoringSeverity.WARNING: 1,
         MonitoringSeverity.CRITICAL: 2}
_ROUTE_ORDER = tuple(AlertRoute)
_SENSITIVE = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|webhook|"
    r"https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+?\d[\d ()-]{7,}\d",
    re.IGNORECASE,
)
_SECURITY_REASONS = {
    "PRODUCTION_AUTHORIZATION_CONTRADICTION", "NONZERO_SAFETY_COUNTER",
    "FORBIDDEN_CONTROL_PLANE_OWNER", "REPLAY_PROTECTION_NOT_RESTORED",
    "AUDIT_HASH_CHAIN_INVALID", "REPLAY_HASH_CHAIN_INVALID",
}


def _valid_digest(value: str | None) -> bool:
    return (isinstance(value, str) and value.startswith("sha256:")
            and len(value) == 71
            and all(char in "0123456789abcdef" for char in value[7:]))


def _instant(value: str | None) -> datetime:
    if not value:
        raise ValueError("timestamp missing")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone missing")
    return parsed.astimezone(timezone.utc)


def _routes(candidate: AlertCandidate) -> tuple[AlertRoute, ...]:
    routes = [AlertRoute.CONTROL_PLANE_DASHBOARD]
    if candidate.severity is MonitoringSeverity.WARNING:
        routes.append(AlertRoute.OPERATOR_REVIEW_QUEUE)
    elif candidate.severity is MonitoringSeverity.CRITICAL:
        routes.extend((AlertRoute.INCIDENT_RESPONSE_QUEUE,
                       AlertRoute.OPERATOR_REVIEW_QUEUE))
    if (candidate.dimension in (MonitoringDimension.PRODUCTION_AUTHORIZATION,
                                MonitoringDimension.SAFETY)
            or candidate.reason_code in _SECURITY_REASONS):
        routes.append(AlertRoute.SECURITY_REVIEW_QUEUE)
    if candidate.dimension is MonitoringDimension.DOCUMENTATION:
        routes.append(AlertRoute.DOCUMENTATION_BACKLOG)
    return tuple(route for route in _ROUTE_ORDER if route in routes)


class AlertDeduplicationEvaluator:
    def evaluate(self, candidate: AlertCandidate, records: tuple[AlertHistoryRecord, ...],
                 config: AlertRoutingConfig, now: datetime) -> tuple[
                     AlertDisposition, AlertSuppressionReason | None, bool, str | None]:
        if not records:
            return AlertDisposition.ROUTE, None, False, None
        latest = max(records, key=lambda item: (_instant(item.last_observed_at),
                                                item.history_record_id))
        prior_rank, current_rank = _RANK[latest.prior_severity], _RANK[candidate.severity]
        if current_rank > prior_rank and config.severity_escalation_bypass_enabled:
            return (AlertDisposition.ESCALATE, None, False,
                    f"{latest.prior_severity.value}->{candidate.severity.value}")
        if latest.resolved:
            if _instant(candidate.observed_at) <= _instant(latest.resolved_at):
                return (AlertDisposition.SUPPRESS_RESOLVED,
                        AlertSuppressionReason.RESOLVED_NO_NEW_OCCURRENCE, False, None)
            if config.recurrence_routing_enabled:
                disposition = (AlertDisposition.ESCALATE
                               if candidate.severity is MonitoringSeverity.CRITICAL
                               else AlertDisposition.ROUTE)
                return disposition, None, True, None
        anchor = latest.last_escalated_at or latest.last_routed_at or latest.last_observed_at
        age = (now - _instant(anchor)).total_seconds()
        cooldown = (config.critical_cooldown_seconds
                    if candidate.severity is MonitoringSeverity.CRITICAL
                    else config.warning_cooldown_seconds)
        reminder = (config.critical_reminder_interval_seconds
                    if candidate.severity is MonitoringSeverity.CRITICAL
                    else config.warning_reminder_interval_seconds)
        if age < cooldown:
            return (AlertDisposition.SUPPRESS_COOLDOWN,
                    AlertSuppressionReason.COOLDOWN_ACTIVE, False, None)
        if age < reminder:
            return (AlertDisposition.SUPPRESS_DUPLICATE,
                    AlertSuppressionReason.DUPLICATE, False, None)
        return AlertDisposition.ROUTE, None, False, None


class AlertEscalationEvaluator:
    def level(self, candidate: AlertCandidate, disposition: AlertDisposition,
              recurrence: bool) -> AlertEscalationLevel:
        if candidate.reason_code in _SECURITY_REASONS:
            return AlertEscalationLevel.SECURITY_REVIEW
        if candidate.severity is MonitoringSeverity.CRITICAL:
            return AlertEscalationLevel.INCIDENT_RESPONSE
        if candidate.severity is MonitoringSeverity.WARNING:
            return AlertEscalationLevel.OPERATOR_REVIEW
        return AlertEscalationLevel.NONE


class AlertRoutingService:
    def __init__(self, config: AlertRoutingConfig | None, *,
                 notification_adapter: object | None = None) -> None:
        self._config = config
        self._adapter_supplied = notification_adapter is not None
        self._dedup = AlertDeduplicationEvaluator()
        self._escalation = AlertEscalationEvaluator()

    def evaluate(self, *, monitoring_snapshot_id: str,
                 monitoring_snapshot_digest: str,
                 candidates: tuple[AlertCandidate, ...],
                 history: AlertHistoryEvidence,
                 evaluated_at: str | None,
                 requested_destinations: tuple[object, ...] = (),
                 dispatch_requested: bool = False,
                 production_authorized: bool = False) -> AlertRoutingPlan:
        try:
            now = _instant(evaluated_at)
        except (TypeError, ValueError):
            now = datetime(1970, 1, 1, tzinfo=timezone.utc)
            evaluated_at = evaluated_at or ""
            global_error = "EVALUATED_AT_INVALID"
        else:
            global_error = None
        if self._config is None:
            global_error = "CONFIGURATION_MISSING"
        elif (dispatch_requested or production_authorized or history.production_authorized
              or self._adapter_supplied):
            global_error = "AUTHORIZATION_OR_ADAPTER_BLOCKED"
        elif requested_destinations and any(
                not isinstance(item, AlertRoute) for item in requested_destinations):
            global_error = "ARBITRARY_DESTINATION_BLOCKED"
        elif not _valid_digest(monitoring_snapshot_digest):
            global_error = "SNAPSHOT_DIGEST_INVALID"

        grouped: dict[str, list[AlertHistoryRecord]] = {}
        history_error = global_error
        if not history_error and self._config:
            for record in history.records:
                grouped.setdefault(record.deduplication_key, []).append(record)
                try:
                    first, last = _instant(record.first_observed_at), _instant(record.last_observed_at)
                    routed = _instant(record.last_routed_at) if record.last_routed_at else None
                    escalated = _instant(record.last_escalated_at) if record.last_escalated_at else None
                    resolved = _instant(record.resolved_at) if record.resolved_at else None
                except (TypeError, ValueError):
                    history_error = "HISTORY_TIMESTAMP_INVALID"
                    break
                timestamps = tuple(item for item in (first, last, routed, escalated, resolved) if item)
                if (record.production_authorized or record.observation_count <= 0
                        or not record.deduplication_key
                        or not _valid_digest(record.prior_candidate_digest)
                        or last < first or any(item > now for item in timestamps)
                        or record.resolved != bool(record.resolved_at)):
                    history_error = "HISTORY_CONTRADICTION"
                    break
                if (now - last).total_seconds() > self._config.maximum_accepted_history_age_seconds:
                    grouped[record.deduplication_key].remove(record)
            if any(len(items) > self._config.maximum_history_records_per_deduplication_key
                   for items in grouped.values()):
                history_error = "HISTORY_LIMIT_EXCEEDED"

        decisions, findings = [], []
        if history_error and not candidates:
            findings.append(AlertRoutingFinding(
                history_error, "", "Routing blocked by invalid evidence."))
        for candidate in sorted(candidates, key=lambda item: (
                item.dimension.value, item.reason_code, item.alert_candidate_id)):
            error = history_error
            records = tuple(grouped.get(candidate.deduplication_key, ()))
            if not error:
                if (not candidate.deduplication_key or not _valid_digest(candidate.candidate_digest)
                        or candidate.monitoring_snapshot_id != monitoring_snapshot_id
                        or candidate.dispatch_authorized or candidate.dispatched
                        or candidate.production_authorized
                        or _SENSITIVE.search(candidate.redacted_summary)):
                    error = "MALFORMED_OR_SENSITIVE_CANDIDATE"
                elif any(record.dimension != candidate.dimension
                         or record.reason_code != candidate.reason_code
                         or record.deduplication_key != candidate.deduplication_key
                         for record in records):
                    error = "CONFLICTING_HISTORY"
            if error:
                disposition, suppression, recurrence, change = (
                    AlertDisposition.BLOCK, None, False, None)
                routes = ()
                findings.append(AlertRoutingFinding(
                    error, candidate.alert_candidate_id, "Routing blocked by invalid evidence."))
            else:
                disposition, suppression, recurrence, change = self._dedup.evaluate(
                    candidate, records, self._config, now)
                routes = _routes(candidate) if disposition in (
                    AlertDisposition.ROUTE, AlertDisposition.ESCALATE) else ()
            level = self._escalation.level(candidate, disposition, recurrence)
            content = {
                "alert_candidate_id": candidate.alert_candidate_id,
                "candidate_digest": candidate.candidate_digest,
                "deduplication_key": candidate.deduplication_key,
                "dispatch_authorized": False, "dispatched": False,
                "disposition": disposition.value, "escalation_level": level.value,
                "evaluated_at": evaluated_at, "first_observed_at": candidate.first_observed_at,
                "matched_history_references": sorted(item.history_record_id for item in records),
                "persisted": False, "production_authorized": False,
                "recurrence": recurrence, "routes": [item.value for item in routes],
                "severity_change_evidence": change,
                "suppression_reason": suppression.value if suppression else None,
            }
            decision_digest = digest(content)
            decisions.append(AlertRoutingDecision(
                decision_id="alert-decision-" + decision_digest[7:39],
                decision_digest=decision_digest, routes=routes, disposition=disposition,
                escalation_level=level, suppression_reason=suppression,
                matched_history_references=tuple(content["matched_history_references"]),
                **{key: content[key] for key in (
                    "alert_candidate_id", "candidate_digest", "deduplication_key",
                    "first_observed_at", "evaluated_at", "recurrence",
                    "severity_change_evidence", "dispatch_authorized", "dispatched",
                    "persisted", "production_authorized")},
            ))
        decisions_tuple = tuple(decisions)
        findings_tuple = tuple(sorted(findings))
        all_routes = tuple(route for route in _ROUTE_ORDER
                           if any(route in item.routes for item in decisions_tuple))
        suppressed = tuple(item.alert_candidate_id for item in decisions_tuple
                           if item.disposition.name.startswith("SUPPRESS"))
        escalated = tuple(item.alert_candidate_id for item in decisions_tuple
                          if item.disposition is AlertDisposition.ESCALATE)
        base = {
            "alerts_dispatched": 0,
            "blocked_count": (sum(item.disposition is AlertDisposition.BLOCK
                                  for item in decisions_tuple)
                              + int(bool(history_error and not decisions_tuple))),
            "candidate_count": len(decisions_tuple),
            "decisions": [item.as_dict() for item in decisions_tuple],
            "dispatch_authorized": False,
            "escalated_candidates": list(escalated), "escalated_count": len(escalated),
            "evaluated_at": evaluated_at,
            "findings": [item.as_dict() for item in findings_tuple],
            "monitoring_snapshot_digest": monitoring_snapshot_digest,
            "monitoring_snapshot_id": monitoring_snapshot_id,
            "notifications_sent": 0, "persistence_writes": 0,
            "production_authorized": False,
            "restrictions": ("EXTERNAL_DISPATCH_NOT_IMPLEMENTED",
                             "ROUTING_PERSISTENCE_NOT_IMPLEMENTED",
                             "PRODUCTION_ACTIVATION_NOT_AUTHORIZED"),
            "routed_count": sum(item.disposition is AlertDisposition.ROUTE for item in decisions_tuple),
            "routes": [item.value for item in all_routes],
            "status": ("BLOCKED" if history_error or any(
                item.disposition is AlertDisposition.BLOCK
                for item in decisions_tuple) else "READY"),
            "suppressed_candidates": list(suppressed), "suppressed_count": len(suppressed),
        }
        plan_digest = digest(base)
        return AlertRoutingPlan(
            routing_plan_id="alert-routing-plan-" + plan_digest[7:39],
            routing_plan_digest=plan_digest, decisions=decisions_tuple, routes=all_routes,
            suppressed_candidates=suppressed, escalated_candidates=escalated,
            findings=findings_tuple,
            status=AlertRoutingStatus(base["status"]),
            **{key: base[key] for key in (
                "monitoring_snapshot_id", "monitoring_snapshot_digest", "evaluated_at",
                "restrictions", "candidate_count", "routed_count", "escalated_count",
                "suppressed_count", "blocked_count", "alerts_dispatched",
                "notifications_sent", "persistence_writes", "dispatch_authorized",
                "production_authorized")},
        )
