"""Deterministic, evidence-only M3-A4A readiness evaluation."""

from __future__ import annotations

from typing import Iterable

from .models import (
    ActivationReadinessCheck,
    ActivationReadinessDecision,
    ActivationReadinessFinding,
    ActivationReadinessReport,
    ActivationReadinessStatus,
    ActivationRestriction,
    OperationalActivationError,
    OperationalActivationEvidence,
    OperationalActivationGateConfig,
    OperationalBootstrapPlan,
    OperationalPathPlan,
    OperationalPermissionPlan,
    OperationalRollbackPlan,
    digest,
    parse_timestamp,
)
from .validators import (
    OperationalBootstrapPlanValidator,
    OperationalPathPlanValidator,
    OperationalPermissionPlanValidator,
    validate_rollback_plan,
)


_CHECK_ORDER = (
    "CONTROL_PLANE_OWNERSHIP", "M2_CLOSURE", "M3_A1_CLOSURE", "M3_A2_CLOSURE",
    "M3_A3_CLOSURE", "TEST_HEALTH", "GIT_HEALTH", "DOCUMENTATION_HEALTH",
    "SAFETY_COUNTERS", "AUDIT_RECOVERY", "REPLAY_RECOVERY", "REPLAY_CONCURRENCY",
    "MONITORING_DRILL", "PATH_PLAN", "PERMISSION_PLAN", "BOOTSTRAP_PLAN",
    "ROLLBACK_PLAN", "PRODUCTION_AUTHORIZATION",
)


class OperationalActivationReadinessGate:
    """Evaluates explicit immutable evidence without probing or writing."""

    def evaluate(
        self, *, config: OperationalActivationGateConfig,
        evidence: OperationalActivationEvidence, evaluated_at: str,
        path_plan: OperationalPathPlan, permission_plan: OperationalPermissionPlan,
        bootstrap_plan: OperationalBootstrapPlan,
        rollback_plan: OperationalRollbackPlan,
        concrete_adapter: object | None = None, write_requested: bool = False,
    ) -> ActivationReadinessReport:
        if not all((config, evidence, evaluated_at, path_plan, permission_plan,
                    bootstrap_plan, rollback_plan)):
            raise OperationalActivationError("configuration and evidence are required")
        if concrete_adapter is not None or write_requested:
            raise OperationalActivationError("adapters and write requests are prohibited")
        evaluated = parse_timestamp(evaluated_at)
        generated = parse_timestamp(evidence.generated_at)
        reasons: dict[str, list[str]] = {code: [] for code in _CHECK_ORDER}
        warnings: dict[str, list[str]] = {code: [] for code in _CHECK_ORDER}

        self._require(reasons, "CONTROL_PLANE_OWNERSHIP",
                      evidence.control_plane_owner == "AIControlCenter Mac",
                      "MAC_CONTROL_PLANE_OWNERSHIP_REQUIRED")
        self._require(reasons, "CONTROL_PLANE_OWNERSHIP",
                      not evidence.ubuntu_ownership_present, "UBUNTU_OWNERSHIP_REJECTED")
        self._all(reasons, "M2_CLOSURE",
                  (evidence.m2_readiness_closed, evidence.m2_pilot_closed),
                  "M2_CLOSURE_MISSING")
        self._all(reasons, "M3_A1_CLOSURE",
                  (evidence.m3_a1a_closed, evidence.m3_a1b_closed,
                   evidence.m3_a1c_closed), "M3_A1_CLOSURE_MISSING")
        self._all(reasons, "M3_A2_CLOSURE",
                  (evidence.m3_a2a_closed, evidence.m3_a2b_closed,
                   evidence.m3_a2c_closed), "M3_A2_CLOSURE_MISSING")
        self._all(reasons, "M3_A3_CLOSURE",
                  (evidence.m3_a3a_closed, evidence.m3_a3b_closed,
                   evidence.m3_a3c_closed), "M3_A3_CLOSURE_MISSING")
        self._require(reasons, "TEST_HEALTH",
                      evidence.full_regression_passed > 0
                      and evidence.full_regression_failed == 0
                      and evidence.deployment_tests_passed > 0
                      and evidence.deployment_tests_failed == 0,
                      "TEST_FAILURE_OR_MISSING_RESULT")
        if evidence.full_regression_warnings:
            warnings["TEST_HEALTH"].append("DEPRECATION_WARNINGS_REQUIRE_REMEDIATION")
        self._require(reasons, "GIT_HEALTH",
                      evidence.git_branch == config.approved_branch, "GIT_BRANCH_INVALID")
        self._require(reasons, "GIT_HEALTH", evidence.git_clean, "GIT_DIRTY")
        self._require(reasons, "GIT_HEALTH",
                      evidence.upstream_ahead == evidence.upstream_behind == 0,
                      "GIT_NOT_SYNCHRONIZED")
        self._all(reasons, "DOCUMENTATION_HEALTH",
                  (evidence.documentation_closed, evidence.architecture_closed),
                  "DOCUMENTATION_OR_ARCHITECTURE_OPEN")
        self._require(reasons, "SAFETY_COUNTERS",
                      bool(evidence.safety_counters)
                      and all(value == 0 for value in evidence.safety_counters.values()),
                      "SAFETY_COUNTER_NONZERO")
        self._require(reasons, "AUDIT_RECOVERY", evidence.audit_recovery_drill_passed,
                      "AUDIT_RECOVERY_REQUIRED")
        self._require(reasons, "REPLAY_RECOVERY", evidence.replay_recovery_drill_passed,
                      "REPLAY_RECOVERY_REQUIRED")
        self._require(reasons, "REPLAY_CONCURRENCY",
                      evidence.post_recovery_concurrency_passed,
                      "REPLAY_CONCURRENCY_REQUIRED")
        self._require(reasons, "MONITORING_DRILL",
                      evidence.monitoring_alert_drill_passed,
                      "MONITORING_DRILL_REQUIRED")
        reasons["PATH_PLAN"].extend(OperationalPathPlanValidator().validate(
            path_plan, repository_root=config.repository_root, user_home=config.user_home))
        reasons["PERMISSION_PLAN"].extend(
            OperationalPermissionPlanValidator().validate(permission_plan))
        reasons["BOOTSTRAP_PLAN"].extend(
            OperationalBootstrapPlanValidator().validate(bootstrap_plan))
        reasons["ROLLBACK_PLAN"].extend(validate_rollback_plan(rollback_plan))

        if evaluated < generated:
            reasons["DOCUMENTATION_HEALTH"].append("EVIDENCE_TIMESTAMP_CONTRADICTORY")
        elif (evaluated - generated).total_seconds() > config.maximum_evidence_age_seconds:
            reasons["DOCUMENTATION_HEALTH"].append("EVIDENCE_STALE")
        if evidence.production_authorized or config.production_authorized:
            reasons["PRODUCTION_AUTHORIZATION"].append(
                "PRODUCTION_AUTHORIZATION_CONTRADICTION")
        path_exists = any(evidence.operational_paths_exist.values())
        if path_exists and not evidence.authorized_bootstrap_receipt:
            reasons["PATH_PLAN"].append("UNAUTHORIZED_PREEXISTING_OPERATIONAL_PATH")
        if evidence.operational_writers_active:
            reasons["BOOTSTRAP_PLAN"].append("UNAUTHORIZED_ACTIVE_WRITER")
        if evidence.operational_monitoring_active:
            reasons["BOOTSTRAP_PLAN"].append("UNAUTHORIZED_ACTIVE_MONITORING")
        if evidence.external_alert_dispatch_active:
            reasons["BOOTSTRAP_PLAN"].append("UNAUTHORIZED_EXTERNAL_DISPATCH")

        checks = tuple(self._check(code, reasons[code], warnings[code], evidence.evidence_id)
                       for code in _CHECK_ORDER)
        findings = self._findings(checks)
        restrictions = [ActivationRestriction(
            "READINESS_IS_NOT_AUTHORIZATION",
            "No bootstrap, writer, monitoring, dispatch or production authorization is granted.")]
        if evidence.full_regression_warnings:
            restrictions.append(ActivationRestriction(
                "DEPRECATION_WARNINGS_OUTSTANDING",
                "Deprecation warnings require tracked remediation before activation."))
        restrictions = sorted(restrictions)
        failed = tuple(check.code for check in checks if check.status in (
            ActivationReadinessStatus.FAIL, ActivationReadinessStatus.BLOCKED,
            ActivationReadinessStatus.INVALID))
        warning = tuple(check.code for check in checks
                        if check.status is ActivationReadinessStatus.WARNING)
        passed = tuple(check.code for check in checks
                       if check.status is ActivationReadinessStatus.PASS)
        decision = self._decision(failed, warning, config.block_on_warnings, checks)
        evidence_digest = digest(evidence)
        content = {
            "operational_stage": config.stage.value, "readiness_decision": decision.value,
            "evaluated_at": evaluated_at, "evidence_ids": [evidence.evidence_id],
            "evidence_digests": [evidence_digest],
            "checks": [check.as_dict() for check in checks],
            "findings": [finding.as_dict() for finding in findings],
            "restrictions": [item.as_dict() for item in restrictions],
            "path_plan": path_plan.as_dict(), "permission_plan": permission_plan.as_dict(),
            "bootstrap_plan": bootstrap_plan.as_dict(),
            "rollback_plan_valid": not reasons["ROLLBACK_PLAN"],
            "failed_checks": list(failed), "warning_checks": list(warning),
            "passed_checks": list(passed), "writes_performed": 0,
            "directories_created": 0, "databases_created": 0, "writers_activated": 0,
            "monitoring_activated": 0, "alerts_dispatched": 0,
            "bootstrap_authorized": False, "writers_authorized": False,
            "monitoring_activation_authorized": False,
            "external_dispatch_authorized": False, "production_authorized": False,
        }
        report_digest = digest(content)
        return ActivationReadinessReport(
            report_id="m3-a4a-" + report_digest[7:39], report_digest=report_digest,
            operational_stage=config.stage, readiness_decision=decision,
            evaluated_at=evaluated_at, evidence_ids=(evidence.evidence_id,),
            evidence_digests=(evidence_digest,), checks=checks, findings=findings,
            restrictions=tuple(restrictions), path_plan=path_plan,
            permission_plan=permission_plan, bootstrap_plan=bootstrap_plan,
            rollback_plan_valid=not reasons["ROLLBACK_PLAN"], failed_checks=failed,
            warning_checks=warning, passed_checks=passed)

    @staticmethod
    def _require(target: dict[str, list[str]], check: str, condition: bool,
                 reason: str) -> None:
        if not condition:
            target[check].append(reason)

    @classmethod
    def _all(cls, target: dict[str, list[str]], check: str,
             values: Iterable[bool], reason: str) -> None:
        cls._require(target, check, all(values), reason)

    @staticmethod
    def _check(code: str, failures: list[str], warnings: list[str],
               evidence_id: str) -> ActivationReadinessCheck:
        failures = sorted(set(failures))
        warnings = sorted(set(warnings))
        status = (ActivationReadinessStatus.BLOCKED if failures
                  else ActivationReadinessStatus.WARNING if warnings
                  else ActivationReadinessStatus.PASS)
        return ActivationReadinessCheck(code, status, (evidence_id,),
                                        tuple(failures or warnings))

    @staticmethod
    def _findings(checks: tuple[ActivationReadinessCheck, ...]
                  ) -> tuple[ActivationReadinessFinding, ...]:
        values = []
        for check in checks:
            severity = "ERROR" if check.status is ActivationReadinessStatus.BLOCKED else "WARNING"
            for reason in check.reason_codes:
                values.append(ActivationReadinessFinding(
                    reason, severity, f"{check.code} requires remediation."))
        return tuple(sorted(values))

    @staticmethod
    def _decision(failed: tuple[str, ...], warnings: tuple[str, ...],
                  block_on_warnings: bool,
                  checks: tuple[ActivationReadinessCheck, ...]
                  ) -> ActivationReadinessDecision:
        if failed:
            invalid_codes = {"PRODUCTION_AUTHORIZATION_CONTRADICTION",
                             "EVIDENCE_TIMESTAMP_CONTRADICTORY"}
            if any(invalid_codes.intersection(check.reason_codes) for check in checks):
                return ActivationReadinessDecision.INVALID
            return ActivationReadinessDecision.BLOCKED
        if warnings:
            return (ActivationReadinessDecision.NOT_READY if block_on_warnings
                    else ActivationReadinessDecision.READY_WITH_RESTRICTIONS)
        return ActivationReadinessDecision.READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP
