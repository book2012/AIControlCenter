"""Deterministic in-memory monitoring and logical-alert operational drill."""

from __future__ import annotations

from dataclasses import replace
from typing import Protocol
import re

from core.deployment.alert_routing import AlertDisposition, AlertRoute, AlertRoutingService, AlertRoutingStatus
from core.deployment.operational_monitoring import OperationalMonitoringService, OperationalStage

from .models import (
    MonitoringAlertDrillConfig, MonitoringAlertDrillDecision, MonitoringAlertDrillError,
    MonitoringAlertDrillFinding, MonitoringAlertDrillPlan, MonitoringAlertDrillRequest,
    MonitoringAlertDrillStatus, MonitoringAlertDrillStep, MonitoringAlertDrillValidationReport,
    SimulatedAlertDeliveryReceipt, SimulatedAlertEnvelope, digest,
)

_SENSITIVE = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|webhook|https?://|"
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|\+?\d[\d ()-]{7,}\d", re.IGNORECASE)


def _without(mapping: dict, *keys: str) -> dict:
    return {key: value for key, value in mapping.items() if key not in keys}


class SimulatedAlertDeliveryPort(Protocol):
    def submit(self, envelope: SimulatedAlertEnvelope, *, acknowledged_at: str) -> SimulatedAlertDeliveryReceipt: ...


class InMemorySimulatedAlertSink:
    """Object-scoped simulator: no filesystem, database, network, or dispatch."""

    def __init__(self, *, fail_on_submission: int | None = None) -> None:
        if fail_on_submission is not None and fail_on_submission <= 0:
            raise MonitoringAlertDrillError("failure injection index must be positive")
        self._fail_on = fail_on_submission
        self._attempts = 0
        self._receipts: list[SimulatedAlertDeliveryReceipt] = []

    @property
    def receipts(self) -> tuple[SimulatedAlertDeliveryReceipt, ...]:
        return tuple(self._receipts)

    def submit(self, envelope: SimulatedAlertEnvelope, *, acknowledged_at: str) -> SimulatedAlertDeliveryReceipt:
        self._attempts += 1
        if self._fail_on == self._attempts:
            raise MonitoringAlertDrillError(f"simulated sink rejected submission {self._attempts}")
        if not isinstance(envelope.logical_route, AlertRoute):
            raise MonitoringAlertDrillError("arbitrary simulated route is prohibited")
        payload = envelope.as_dict()
        expected = digest(_without(payload, "envelope_digest", "envelope_id"))
        expected_id = "simulated-envelope-" + expected[7:39]
        if (envelope.envelope_digest != expected or envelope.envelope_id != expected_id
                or not envelope.simulated or envelope.dispatch_authorized
                or envelope.production_authorized or _SENSITIVE.search(envelope.redacted_summary)):
            raise MonitoringAlertDrillError("invalid or unsafe simulated envelope")
        base = {"accepted_by_simulator": True, "acknowledged_at": acknowledged_at,
                "delivered": False, "dispatched": False, "envelope_digest": envelope.envelope_digest,
                "envelope_id": envelope.envelope_id, "logical_route": envelope.logical_route.value,
                "network_used": False, "persisted": False, "production_authorized": False,
                "simulated": True}
        receipt_digest = digest(base)
        receipt = SimulatedAlertDeliveryReceipt(
            receipt_id="simulated-receipt-" + receipt_digest[7:39],
            receipt_digest=receipt_digest, logical_route=envelope.logical_route,
            **_without(base, "logical_route"))
        self._receipts.append(receipt)
        return receipt


class MonitoringAlertDrillValidator:
    def validate(self, *, plan: MonitoringAlertDrillPlan,
                 receipts: tuple[SimulatedAlertDeliveryReceipt, ...],
                 config: MonitoringAlertDrillConfig,
                 sink_failed: bool = False) -> MonitoringAlertDrillValidationReport:
        findings: list[MonitoringAlertDrillFinding] = []
        snapshot, routing = plan.monitoring_snapshot, plan.routing_plan

        def fail(code: str, summary: str) -> None:
            findings.append(MonitoringAlertDrillFinding(code, summary))

        snapshot_payload = snapshot.as_dict()
        if digest(_without(snapshot_payload, "snapshot_digest")) != snapshot.snapshot_digest:
            fail("SNAPSHOT_DIGEST_INVALID", "Monitoring snapshot digest does not match.")
        for candidate in snapshot.alert_candidates:
            payload = candidate.as_dict()
            expected = digest(_without(payload, "candidate_digest", "alert_candidate_id"))
            if candidate.candidate_digest != expected or candidate.alert_candidate_id != "alert-candidate-" + expected[7:39]:
                fail("CANDIDATE_DIGEST_INVALID", "Alert candidate identity does not match.")
        routing_payload = routing.as_dict()
        if digest(_without(routing_payload, "routing_plan_digest", "routing_plan_id")) != routing.routing_plan_digest:
            fail("ROUTING_PLAN_DIGEST_INVALID", "Routing plan digest does not match.")
        candidates = {item.alert_candidate_id: item for item in snapshot.alert_candidates}
        for decision in routing.decisions:
            payload = decision.as_dict()
            expected = digest(_without(payload, "decision_digest", "decision_id"))
            candidate = candidates.get(decision.alert_candidate_id)
            if (decision.decision_digest != expected
                    or decision.decision_id != "alert-decision-" + expected[7:39]
                    or candidate is None or candidate.candidate_digest != decision.candidate_digest):
                fail("DECISION_BINDING_INVALID", "Routing decision identity or candidate binding does not match.")
        expected_pairs = [(decision, route) for decision in routing.decisions
                          if decision.disposition in (AlertDisposition.ROUTE, AlertDisposition.ESCALATE)
                          for route in decision.routes]
        actual_pairs = [(item.routing_decision_id, item.logical_route) for item in plan.envelopes]
        if actual_pairs != [(item.decision_id, route) for item, route in expected_pairs]:
            fail("ENVELOPE_CORRESPONDENCE_INVALID", "Envelope routing correspondence is incomplete.")
        if any(item.logical_route not in config.allowed_logical_routes for item in plan.envelopes):
            fail("ARBITRARY_ROUTE_BLOCKED", "Envelope route is not explicitly allowed.")
        if len(plan.envelopes) > config.maximum_envelopes_per_drill:
            fail("ENVELOPE_LIMIT_EXCEEDED", "Envelope maximum exceeded.")
        if len(snapshot.alert_candidates) > config.maximum_candidates_per_drill:
            fail("CANDIDATE_LIMIT_EXCEEDED", "Candidate maximum exceeded.")
        if len({item.envelope_id for item in plan.envelopes}) != len(plan.envelopes):
            fail("DUPLICATE_ENVELOPE_ID", "Envelope identifiers must be unique.")
        if len({item.receipt_id for item in receipts}) != len(receipts):
            fail("DUPLICATE_RECEIPT_ID", "Receipt identifiers must be unique.")
        envelope_by_id = {item.envelope_id: item for item in plan.envelopes}
        for receipt in receipts:
            envelope = envelope_by_id.get(receipt.envelope_id)
            expected = digest(_without(receipt.as_dict(), "receipt_digest", "receipt_id"))
            if (envelope is None or receipt.envelope_digest != envelope.envelope_digest
                    or receipt.logical_route != envelope.logical_route
                    or receipt.receipt_digest != expected
                    or receipt.receipt_id != "simulated-receipt-" + expected[7:39]):
                fail("RECEIPT_BINDING_INVALID", "Receipt does not bind exactly to its envelope.")
            if (receipt.dispatched or receipt.delivered or receipt.network_used
                    or receipt.persisted or receipt.production_authorized):
                fail("UNSAFE_RECEIPT_CLAIM", "Receipt claims a prohibited side effect.")
        if config.require_complete_receipt_binding and len(receipts) != len(plan.envelopes):
            fail("RECEIPT_MISSING", "Every envelope requires one simulator receipt.")
        if config.fail_on_blocked_decision and routing.blocked_count:
            fail("BLOCKED_ROUTING_DECISION", "Routing contains a blocked decision.")
        if routing.alerts_dispatched or routing.notifications_sent or routing.persistence_writes:
            fail("ROUTING_SIDE_EFFECT_CLAIM", "Routing plan claims a prohibited side effect.")
        if sink_failed:
            fail("SIMULATED_SINK_FAILURE", "Simulator rejected an envelope; no delivery is claimed.")

        status = MonitoringAlertDrillStatus.FAILED if sink_failed else (
            MonitoringAlertDrillStatus.BLOCKED if findings else MonitoringAlertDrillStatus.VALIDATED)
        decision = MonitoringAlertDrillDecision.FAIL if sink_failed else (
            MonitoringAlertDrillDecision.BLOCK if findings else MonitoringAlertDrillDecision.PASS)
        base = {
            "accepted_receipt_count": sum(item.accepted_by_simulator for item in receipts),
            "actual_deliveries": 0, "alerts_dispatched": 0,
            "blocked_count": routing.blocked_count, "candidate_count": routing.candidate_count,
            "decision": decision.value, "drill_plan_id": plan.drill_plan_id,
            "envelopes": [item.as_dict() for item in plan.envelopes],
            "escalated_count": routing.escalated_count,
            "expected_receipt_count": len(plan.envelopes),
            "findings": [item.as_dict() for item in sorted(findings)],
            "network_requests": 0, "notifications_sent": 0, "persistence_writes": 0,
            "production_authorized": False, "receipts": [item.as_dict() for item in receipts],
            "rejected_receipt_count": len(plan.envelopes) - len(receipts),
            "routing_plan_digest": routing.routing_plan_digest,
            "routing_plan_id": routing.routing_plan_id, "scenario": plan.scenario.value,
            "snapshot_digest": snapshot.snapshot_digest, "snapshot_id": snapshot.snapshot_id,
            "status": status.value, "steps": [item.as_dict() for item in plan.steps],
            "suppressed_count": routing.suppressed_count, "routed_count": routing.routed_count,
        }
        report_digest = digest(base)
        return MonitoringAlertDrillValidationReport(
            report_id="monitoring-alert-drill-report-" + report_digest[7:39],
            report_digest=report_digest, status=status, decision=decision,
            scenario=plan.scenario, steps=plan.steps,
            findings=tuple(sorted(findings)), receipts=receipts, envelopes=plan.envelopes,
            **{key: base[key] for key in (
                "drill_plan_id", "snapshot_id", "snapshot_digest",
                "routing_plan_id", "routing_plan_digest", "candidate_count", "routed_count",
                "escalated_count", "suppressed_count", "blocked_count",
                "expected_receipt_count", "accepted_receipt_count", "rejected_receipt_count",
                "alerts_dispatched", "actual_deliveries", "notifications_sent",
                "network_requests", "persistence_writes", "production_authorized")}
        )


class MonitoringAlertDrillService:
    def __init__(self, config: MonitoringAlertDrillConfig,
                 sink: SimulatedAlertDeliveryPort) -> None:
        if sink is None:
            raise MonitoringAlertDrillError("an injected simulated sink is required")
        self._config, self._sink = config, sink
        self._validator = MonitoringAlertDrillValidator()

    def run(self, request: MonitoringAlertDrillRequest) -> MonitoringAlertDrillValidationReport:
        plan = self.prepare(request)
        receipts = []
        failed = False
        for envelope in plan.envelopes:
            try:
                receipts.append(self._sink.submit(
                    envelope, acknowledged_at=request.receipt_acknowledged_at))
            except MonitoringAlertDrillError:
                failed = True
                break
        return self._validator.validate(
            plan=plan, receipts=tuple(receipts), config=self._config, sink_failed=failed)

    def prepare(self, request: MonitoringAlertDrillRequest) -> MonitoringAlertDrillPlan:
        """Build a deterministic drill plan without submitting any envelope."""
        snapshot = OperationalMonitoringService(request.monitoring_config).evaluate(
            request.monitoring_evidence, stage=OperationalStage.PRE_ACTIVATION)
        routing = AlertRoutingService(request.routing_config).evaluate(
            monitoring_snapshot_id=snapshot.snapshot_id,
            monitoring_snapshot_digest=snapshot.snapshot_digest,
            candidates=snapshot.alert_candidates, history=request.alert_history,
            evaluated_at=request.evaluated_at)
        drill_identity = digest({"drill_name": request.drill_name,
                                 "scenario": request.scenario.value,
                                 "snapshot_id": snapshot.snapshot_id,
                                 "routing_plan_id": routing.routing_plan_id})
        drill_id = "monitoring-alert-drill-" + drill_identity[7:39]
        candidates = {item.alert_candidate_id: item for item in snapshot.alert_candidates}
        envelopes = []
        for decision in routing.decisions:
            if decision.disposition not in (AlertDisposition.ROUTE, AlertDisposition.ESCALATE):
                continue
            candidate = candidates[decision.alert_candidate_id]
            for route in decision.routes:
                base = {"alert_candidate_id": candidate.alert_candidate_id,
                        "created_at": request.envelope_created_at,
                        "dispatch_authorized": False, "drill_id": drill_id,
                        "escalation_level": decision.escalation_level.value,
                        "evidence_references": list(candidate.evidence_references),
                        "logical_route": route.value, "production_authorized": False,
                        "redacted_summary": candidate.redacted_summary,
                        "routing_decision_id": decision.decision_id,
                        "routing_plan_id": routing.routing_plan_id,
                        "severity": candidate.severity.value, "simulated": True}
                envelope_digest = digest(base)
                envelopes.append(SimulatedAlertEnvelope(
                    envelope_id="simulated-envelope-" + envelope_digest[7:39],
                    envelope_digest=envelope_digest, logical_route=route,
                    evidence_references=candidate.evidence_references, **{
                        key: base[key] for key in (
                            "alert_candidate_id", "created_at", "dispatch_authorized",
                            "drill_id", "escalation_level", "production_authorized",
                            "redacted_summary", "routing_decision_id", "routing_plan_id",
                            "severity", "simulated")}))
        steps = (
            MonitoringAlertDrillStep(1, "MONITORING_SNAPSHOT", "PRODUCED", snapshot.snapshot_id),
            MonitoringAlertDrillStep(2, "ALERT_ROUTING_PLAN", routing.status.value, routing.routing_plan_id),
            MonitoringAlertDrillStep(3, "SIMULATED_ENVELOPES", "PREPARED", str(len(envelopes))),
        )
        plan_base = {"drill_id": drill_id, "envelope_digests": [item.envelope_digest for item in envelopes],
                     "routing_plan_digest": routing.routing_plan_digest,
                     "scenario": request.scenario.value, "snapshot_digest": snapshot.snapshot_digest,
                     "steps": [item.as_dict() for item in steps]}
        plan_digest = digest(plan_base)
        plan = MonitoringAlertDrillPlan(
            "monitoring-alert-drill-plan-" + plan_digest[7:39], request.scenario,
            snapshot, routing, tuple(envelopes), steps, plan_digest)
        return plan
