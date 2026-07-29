"""Pure deterministic evaluation of immutable operational monitoring evidence."""

from __future__ import annotations

from datetime import datetime, timezone

from core.deployment.operational_monitoring.models import (
    AlertCandidate,
    AlertCandidateStatus,
    MonitoringDecision,
    MonitoringDimension,
    MonitoringEvidence,
    MonitoringFinding,
    MonitoringSeverity,
    MonitoringSnapshot,
    MonitoringStatus,
    OperationalMonitoringConfig,
    OperationalMonitoringError,
    OperationalStage,
    digest_payload,
    valid_digest,
)


_STATUS_RANK = {
    MonitoringStatus.NOT_CONFIGURED_ALLOWED: 0,
    MonitoringStatus.HEALTHY: 0,
    MonitoringStatus.DEGRADED: 1,
    MonitoringStatus.UNAVAILABLE: 2,
    MonitoringStatus.BLOCKED: 3,
    MonitoringStatus.CRITICAL: 4,
}


def _instant(value: str | None, field: str) -> datetime:
    if not value:
        raise OperationalMonitoringError(f"{field} timestamp is missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise OperationalMonitoringError(f"{field} timestamp is invalid") from exc
    if parsed.tzinfo is None:
        raise OperationalMonitoringError(f"{field} timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def _severity(status: MonitoringStatus) -> MonitoringSeverity:
    if status is MonitoringStatus.CRITICAL:
        return MonitoringSeverity.CRITICAL
    if status in (MonitoringStatus.BLOCKED, MonitoringStatus.UNAVAILABLE,
                  MonitoringStatus.DEGRADED):
        return MonitoringSeverity.WARNING
    return MonitoringSeverity.INFO


class AlertCandidateEvaluator:
    """Build immutable candidates; dispatch and notification are impossible."""

    def evaluate(
        self,
        *,
        snapshot_id: str,
        findings: tuple[MonitoringFinding, ...],
        evidence_references: tuple[str, ...],
        observed_at: str,
        dispatch_requested: bool = False,
        notification_adapter: object | None = None,
    ) -> tuple[AlertCandidate, ...]:
        if dispatch_requested:
            raise OperationalMonitoringError("alert dispatch is not authorized")
        if notification_adapter is not None:
            raise OperationalMonitoringError("notification adapters are not accepted")
        candidates = []
        for finding in findings:
            if finding.severity is MonitoringSeverity.INFO:
                continue
            dedup = digest_payload({
                "dimension": finding.dimension.value,
                "reason_code": finding.reason_code,
            })
            content = {
                "candidate_status": AlertCandidateStatus.CANDIDATE.value,
                "deduplication_key": dedup,
                "dimension": finding.dimension.value,
                "dispatch_authorized": False,
                "dispatched": False,
                "evidence_references": list(evidence_references),
                "first_observed_at": observed_at,
                "monitoring_snapshot_id": snapshot_id,
                "observed_at": observed_at,
                "production_authorized": False,
                "reason_code": finding.reason_code,
                "redacted_summary": finding.summary,
                "severity": finding.severity.value,
            }
            digest = digest_payload(content)
            candidates.append(AlertCandidate(
                alert_candidate_id="alert-candidate-" + digest[7:39],
                candidate_digest=digest,
                **{**content, "candidate_status": AlertCandidateStatus.CANDIDATE,
                   "dimension": finding.dimension, "severity": finding.severity,
                   "evidence_references": evidence_references},
            ))
        return tuple(sorted(candidates, key=lambda item: (
            item.dimension.value, item.reason_code, item.alert_candidate_id)))


class OperationalMonitoringService:
    """AIControlCenter's read-only, evidence-only monitoring authority."""

    def __init__(
        self,
        config: OperationalMonitoringConfig | None,
        *,
        alert_evaluator: AlertCandidateEvaluator | None = None,
        notification_adapter: object | None = None,
    ) -> None:
        if config is None:
            raise OperationalMonitoringError("monitoring configuration is required")
        if notification_adapter is not None:
            raise OperationalMonitoringError("notification adapters are not accepted")
        self._config = config
        self._alerts = alert_evaluator or AlertCandidateEvaluator()

    def evaluate(
        self,
        evidence: MonitoringEvidence,
        *,
        stage: OperationalStage | str | None,
        dispatch_requested: bool = False,
    ) -> MonitoringSnapshot:
        if stage != OperationalStage.PRE_ACTIVATION:
            raise OperationalMonitoringError("only PRE_ACTIVATION is supported")
        observed = _instant(evidence.observed_at, "observed_at")
        findings: list[MonitoringFinding] = []
        decisions: list[MonitoringDecision] = []

        def decide(dimension: MonitoringDimension, status: MonitoringStatus,
                   code: str, summary: str) -> None:
            decisions.append(MonitoringDecision(dimension, status, (code,)))
            if status not in (MonitoringStatus.HEALTHY,
                              MonitoringStatus.NOT_CONFIGURED_ALLOWED):
                findings.append(MonitoringFinding(
                    dimension, _severity(status), code, summary))

        if evidence.control_plane_owner != "AIControlCenter/Mac":
            status = (MonitoringStatus.CRITICAL if evidence.control_plane_owner == "Ubuntu"
                      else MonitoringStatus.BLOCKED)
            decide(MonitoringDimension.CONTROL_PLANE, status,
                   "FORBIDDEN_CONTROL_PLANE_OWNER",
                   "Monitoring authority is not bound to AIControlCenter on Mac.")
        else:
            decide(MonitoringDimension.CONTROL_PLANE, MonitoringStatus.HEALTHY,
                   "CONTROL_PLANE_OWNED_BY_MAC", "Control Plane ownership is valid.")

        self._integrity(evidence, observed, findings, decisions, audit=True)
        self._recovery(evidence, observed, findings, decisions, audit=True)
        self._integrity(evidence, observed, findings, decisions, audit=False)
        self._recovery(evidence, observed, findings, decisions, audit=False)

        decide(MonitoringDimension.REPLAY_CONCURRENCY,
               MonitoringStatus.HEALTHY if evidence.post_recovery_concurrency_valid
               else (MonitoringStatus.UNAVAILABLE
                     if evidence.post_recovery_concurrency_valid is None
                     else MonitoringStatus.CRITICAL),
               "REPLAY_CONCURRENCY_VALID" if evidence.post_recovery_concurrency_valid
               else "REPLAY_CONCURRENCY_INVALID",
               "Post-recovery replay concurrency evidence is valid."
               if evidence.post_recovery_concurrency_valid
               else "Post-recovery replay concurrency evidence is missing or invalid.")

        readiness_ok = (evidence.m2_readiness_status == "READY"
                        and evidence.controlled_pilot_closeout_status == "CLOSED")
        decide(MonitoringDimension.DEPLOYMENT_READINESS,
               MonitoringStatus.HEALTHY if readiness_ok else MonitoringStatus.BLOCKED,
               "DEPLOYMENT_READINESS_VALID" if readiness_ok
               else "DEPLOYMENT_READINESS_MISSING",
               "M2 readiness and controlled pilot closeout are valid."
               if readiness_ok else "Required readiness or closeout evidence is absent.")

        failed = evidence.regression_failed
        if failed is None or evidence.regression_passed is None:
            test_status, test_code = MonitoringStatus.UNAVAILABLE, "REGRESSION_EVIDENCE_MISSING"
        elif failed > self._config.maximum_tolerated_failed_tests:
            test_status, test_code = MonitoringStatus.CRITICAL, "REGRESSION_FAILURE"
        elif evidence.regression_warnings and self._config.warnings_degrade:
            test_status, test_code = MonitoringStatus.DEGRADED, "REGRESSION_WARNINGS"
        else:
            test_status, test_code = MonitoringStatus.HEALTHY, "REGRESSION_HEALTHY"
        decide(MonitoringDimension.TEST_HEALTH, test_status, test_code,
               "Regression evidence evaluated without exposing test payloads.")

        if evidence.git_clean is None or evidence.git_ahead is None or evidence.git_behind is None:
            git_status, git_code = MonitoringStatus.UNAVAILABLE, "GIT_EVIDENCE_MISSING"
        elif not evidence.git_clean:
            git_status, git_code = MonitoringStatus.BLOCKED, "GIT_DIRTY"
        elif evidence.git_ahead > self._config.git_ahead_tolerance:
            git_status, git_code = MonitoringStatus.BLOCKED, "GIT_AHEAD"
        elif evidence.git_behind > self._config.git_behind_tolerance:
            git_status, git_code = MonitoringStatus.BLOCKED, "GIT_BEHIND"
        else:
            git_status, git_code = MonitoringStatus.HEALTHY, "GIT_SYNCHRONIZED"
        decide(MonitoringDimension.GIT_HEALTH, git_status, git_code,
               "Git cleanliness and upstream synchronization evidence evaluated.")

        nonzero = tuple(key for key, value in evidence.safety_counters.items() if value)
        decide(MonitoringDimension.SAFETY,
               MonitoringStatus.CRITICAL if nonzero else MonitoringStatus.HEALTHY,
               "NONZERO_SAFETY_COUNTER" if nonzero else "SAFETY_COUNTERS_ZERO",
               "One or more deployment safety counters are nonzero."
               if nonzero else "All deployment safety counters are zero.")
        decide(MonitoringDimension.DOCUMENTATION,
               MonitoringStatus.HEALTHY if evidence.documentation_complete
               else MonitoringStatus.BLOCKED,
               "DOCUMENTATION_COMPLETE" if evidence.documentation_complete
               else "DOCUMENTATION_INCOMPLETE",
               "Monitoring documentation evidence is complete."
               if evidence.documentation_complete else "Required documentation is incomplete.")
        decide(MonitoringDimension.PRODUCTION_AUTHORIZATION,
               MonitoringStatus.CRITICAL if evidence.production_authorized
               else MonitoringStatus.NOT_CONFIGURED_ALLOWED,
               "PRODUCTION_AUTHORIZATION_CONTRADICTION"
               if evidence.production_authorized else "PRODUCTION_NOT_AUTHORIZED",
               "Production authorization contradicts PRE_ACTIVATION."
               if evidence.production_authorized else "Production remains not authorized.")

        self._validate_cross_evidence(evidence, observed, findings, decisions)
        restrictions = (
            "OPERATIONAL_AUDIT_DATABASE_NOT_CREATED",
            "OPERATIONAL_REPLAY_DATABASE_NOT_CREATED",
            "OPERATIONAL_WRITER_NOT_ACTIVATED",
            "OPERATIONAL_BACKUP_SCHEDULE_NOT_ACTIVATED",
            "PRODUCTION_ACTIVATION_NOT_AUTHORIZED",
        )
        if any((evidence.operational_audit_database_created,
                evidence.operational_replay_database_created,
                evidence.operational_writer_activated,
                evidence.operational_backup_schedule_activated)):
            findings.append(MonitoringFinding(
                MonitoringDimension.SAFETY, MonitoringSeverity.CRITICAL,
                "PRE_ACTIVATION_OPERATIONAL_STATE_CONTRADICTION",
                "Operational state is active during PRE_ACTIVATION."))

        decisions = self._coalesce(decisions, findings)
        findings_tuple = tuple(sorted(set(findings), key=lambda item: (
            item.dimension.value, item.reason_code, item.severity.value, item.summary)))
        overall = max((item.status for item in decisions), key=_STATUS_RANK.get)
        base = {
            "evidence_digests": list(evidence.evidence_digests()),
            "evidence_ids": list(evidence.evidence_references()),
            "findings": [item.as_dict() for item in findings_tuple],
            "observed_at": evidence.observed_at,
            "operational_stage": OperationalStage.PRE_ACTIVATION.value,
            "overall_status": overall.value,
        }
        identity = digest_payload(base)
        snapshot_id = "monitoring-snapshot-" + identity[7:39]
        alerts = self._alerts.evaluate(
            snapshot_id=snapshot_id, findings=findings_tuple,
            evidence_references=evidence.evidence_references(),
            observed_at=evidence.observed_at, dispatch_requested=dispatch_requested)
        content = {
            **base,
            "alert_candidates": [item.as_dict() for item in alerts],
            "alerts_dispatched": 0,
            "dimensions": [item.as_dict() for item in decisions],
            "git_summary": {"ahead": evidence.git_ahead or 0,
                            "behind": evidence.git_behind or 0,
                            "clean": bool(evidence.git_clean)},
            "notifications_sent": 0,
            "production_authorized": False,
            "regression_summary": {
                "deselected": evidence.regression_deselected or 0,
                "failed": evidence.regression_failed or 0,
                "passed": evidence.regression_passed or 0,
                "warnings": evidence.regression_warnings or 0,
            },
            "restrictions": list(restrictions),
            "safety_counters": dict(evidence.safety_counters),
            "snapshot_id": snapshot_id,
            "writes_performed": 0,
        }
        snapshot_digest = digest_payload(content)
        return MonitoringSnapshot(
            snapshot_id=snapshot_id, operational_stage=OperationalStage.PRE_ACTIVATION,
            overall_status=overall, observed_at=evidence.observed_at,
            evidence_ids=evidence.evidence_references(),
            evidence_digests=evidence.evidence_digests(),
            dimensions=tuple(decisions), findings=findings_tuple,
            restrictions=restrictions, alert_candidates=alerts,
            safety_counters=evidence.safety_counters,
            regression_summary=content["regression_summary"],
            git_summary=content["git_summary"], snapshot_digest=snapshot_digest)

    def _integrity(self, evidence: MonitoringEvidence, observed: datetime,
                   findings: list[MonitoringFinding],
                   decisions: list[MonitoringDecision], *, audit: bool) -> None:
        prefix = "audit" if audit else "replay"
        dimension = (MonitoringDimension.AUDIT_INTEGRITY if audit
                     else MonitoringDimension.REPLAY_INTEGRITY)
        status = getattr(evidence, f"{prefix}_inspection_status")
        digest = getattr(evidence, f"{prefix}_inspection_report_digest")
        generated = getattr(evidence, f"{prefix}_evidence_generated_at")
        schema = getattr(evidence, f"{prefix}_schema_valid")
        chain = getattr(evidence, f"{prefix}_hash_chain_valid")
        missing = any(item is None for item in (status, digest, generated, schema, chain))
        if missing:
            result, code = MonitoringStatus.UNAVAILABLE, f"{prefix.upper()}_EVIDENCE_MISSING"
        elif not valid_digest(digest):
            result, code = MonitoringStatus.BLOCKED, f"{prefix.upper()}_DIGEST_INVALID"
        elif not chain:
            result, code = MonitoringStatus.CRITICAL, f"{prefix.upper()}_HASH_CHAIN_INVALID"
        elif not schema:
            result, code = MonitoringStatus.CRITICAL, f"{prefix.upper()}_SCHEMA_INVALID"
        elif not audit and not evidence.replay_state_machine_valid:
            result, code = MonitoringStatus.CRITICAL, "REPLAY_LIFECYCLE_INVALID"
        elif status not in ("HEALTHY", "VALID"):
            result, code = MonitoringStatus.BLOCKED, f"{prefix.upper()}_STATUS_CONTRADICTION"
        else:
            result, code = MonitoringStatus.HEALTHY, f"{prefix.upper()}_INTEGRITY_HEALTHY"
        decisions.append(MonitoringDecision(dimension, result, (code,)))
        if result not in (MonitoringStatus.HEALTHY, MonitoringStatus.NOT_CONFIGURED_ALLOWED):
            findings.append(MonitoringFinding(
                dimension, _severity(result), code,
                f"{prefix.title()} integrity evidence is missing, invalid, or contradictory."))

    def _recovery(self, evidence: MonitoringEvidence, observed: datetime,
                  findings: list[MonitoringFinding],
                  decisions: list[MonitoringDecision], *, audit: bool) -> None:
        prefix = "audit" if audit else "replay"
        dimension = (MonitoringDimension.AUDIT_RECOVERY if audit
                     else MonitoringDimension.REPLAY_RECOVERY)
        status = getattr(evidence, f"{prefix}_recovery_status")
        digest = getattr(evidence, f"{prefix}_recovery_report_digest")
        generated = getattr(evidence, f"{prefix}_recovery_evidence_generated_at")
        backup_age = getattr(evidence, f"{prefix}_backup_age_seconds")
        drill_age = getattr(evidence, f"{prefix}_recovery_drill_age_seconds")
        if any(item is None for item in (status, digest, generated, backup_age, drill_age)):
            result, code = MonitoringStatus.UNAVAILABLE, f"{prefix.upper()}_RECOVERY_EVIDENCE_MISSING"
        elif not valid_digest(digest):
            result, code = MonitoringStatus.BLOCKED, f"{prefix.upper()}_RECOVERY_DIGEST_INVALID"
        elif not audit and not evidence.replay_protection_restored:
            result, code = MonitoringStatus.CRITICAL, "REPLAY_PROTECTION_NOT_RESTORED"
        elif not audit and not evidence.permit_states_restored:
            result, code = MonitoringStatus.CRITICAL, "PERMIT_STATES_NOT_RESTORED"
        else:
            bw = getattr(self._config, f"{prefix}_backup_warning_age_seconds")
            bc = getattr(self._config, f"{prefix}_backup_critical_age_seconds")
            dw = getattr(self._config, f"{prefix}_recovery_drill_warning_age_seconds")
            dc = getattr(self._config, f"{prefix}_recovery_drill_critical_age_seconds")
            if backup_age >= bc:
                result, code = MonitoringStatus.CRITICAL, f"{prefix.upper()}_BACKUP_TOO_OLD"
            elif drill_age >= dc:
                result, code = MonitoringStatus.CRITICAL, f"{prefix.upper()}_RECOVERY_DRILL_TOO_OLD"
            elif backup_age >= bw:
                result, code = MonitoringStatus.DEGRADED, f"{prefix.upper()}_BACKUP_STALE"
            elif drill_age >= dw:
                result, code = MonitoringStatus.DEGRADED, f"{prefix.upper()}_RECOVERY_DRILL_STALE"
            elif status not in ("RECOVERY_VALID", "VALID"):
                result, code = MonitoringStatus.BLOCKED, f"{prefix.upper()}_RECOVERY_INVALID"
            else:
                result, code = MonitoringStatus.HEALTHY, f"{prefix.upper()}_RECOVERY_HEALTHY"
        decisions.append(MonitoringDecision(dimension, result, (code,)))
        if result not in (MonitoringStatus.HEALTHY, MonitoringStatus.NOT_CONFIGURED_ALLOWED):
            findings.append(MonitoringFinding(
                dimension, _severity(result), code,
                f"{prefix.title()} backup or recovery-drill evidence requires attention."))

    def _validate_cross_evidence(
        self, evidence: MonitoringEvidence, observed: datetime,
        findings: list[MonitoringFinding], decisions: list[MonitoringDecision],
    ) -> None:
        timestamps = (
            evidence.audit_evidence_generated_at,
            evidence.audit_recovery_evidence_generated_at,
            evidence.replay_evidence_generated_at,
            evidence.replay_recovery_evidence_generated_at,
            evidence.m2_evidence_generated_at,
            evidence.pilot_evidence_generated_at,
        )
        for value in timestamps:
            try:
                generated = _instant(value, "evidence")
            except OperationalMonitoringError:
                findings.append(MonitoringFinding(
                    MonitoringDimension.SAFETY, MonitoringSeverity.WARNING,
                    "EVIDENCE_TIMESTAMP_MISSING", "Required evidence timestamp is missing."))
                continue
            age = (observed - generated).total_seconds()
            if age < 0:
                findings.append(MonitoringFinding(
                    MonitoringDimension.SAFETY, MonitoringSeverity.CRITICAL,
                    "EVIDENCE_TIMESTAMP_CONTRADICTION",
                    "Evidence generation time is later than observation time."))
            elif age > self._config.maximum_evidence_age_seconds:
                findings.append(MonitoringFinding(
                    MonitoringDimension.SAFETY, MonitoringSeverity.WARNING,
                    "EVIDENCE_STALE", "Required evidence exceeds maximum age."))
        numeric = (
            evidence.audit_production_privacy_violations,
            evidence.replay_violation_count,
        )
        if any(item is not None and item < 0 for item in numeric):
            findings.append(MonitoringFinding(
                MonitoringDimension.SAFETY, MonitoringSeverity.CRITICAL,
                "COUNTER_CONTRADICTION", "Evidence counter is contradictory."))
        if (evidence.audit_inspection_status == "HEALTHY"
                and evidence.audit_production_privacy_violations):
            findings.append(MonitoringFinding(
                MonitoringDimension.AUDIT_INTEGRITY, MonitoringSeverity.CRITICAL,
                "AUDIT_STATUS_COUNTER_CONTRADICTION",
                "Healthy audit status contradicts violation counters."))
        if (evidence.replay_inspection_status == "HEALTHY"
                and evidence.replay_violation_count):
            findings.append(MonitoringFinding(
                MonitoringDimension.REPLAY_INTEGRITY, MonitoringSeverity.CRITICAL,
                "REPLAY_STATUS_COUNTER_CONTRADICTION",
                "Healthy replay status contradicts violation counters."))

    @staticmethod
    def _coalesce(
        decisions: list[MonitoringDecision], findings: list[MonitoringFinding],
    ) -> list[MonitoringDecision]:
        by_dimension = {item.dimension: item for item in decisions}
        for finding in findings:
            status = (MonitoringStatus.CRITICAL
                      if finding.severity is MonitoringSeverity.CRITICAL
                      else MonitoringStatus.DEGRADED)
            current = by_dimension.get(finding.dimension)
            if current is None or _STATUS_RANK[status] > _STATUS_RANK[current.status]:
                by_dimension[finding.dimension] = MonitoringDecision(
                    finding.dimension, status, (finding.reason_code,))
        return [by_dimension[item] for item in MonitoringDimension]
