"""Deterministic M3-A4B2B0 policy evaluation; never performs I/O."""

from __future__ import annotations

from .models import *
from .validators import OperationalBootstrapCapacityValidator, OperationalBootstrapTargetEvidenceValidator

_ORDER = ("HOST", "GIT", "TESTS", "SAFETY", "TARGETS", "CAPACITY", "CLOSED_TRACK")


class OperationalBootstrapHostPreflightService:
    def evaluate(self, *, config: OperationalBootstrapHostPreflightConfig,
                 host: OperationalBootstrapHostEvidence,
                 targets: tuple[OperationalBootstrapTargetEvidence, ...],
                 capacity: OperationalBootstrapCapacityEvidence,
                 closed_track: OperationalBootstrapClosedTrackEvidence,
                 evaluated_at: str, adapter: object | None = None,
                 write_requested: bool = False) -> OperationalBootstrapPreflightReport:
        if any(value is None for value in (config, host, targets, capacity, closed_track)):
            raise OperationalBootstrapPreflightError("CONFIGURATION_AND_EVIDENCE_REQUIRED")
        if adapter is not None or write_requested:
            raise OperationalBootstrapPreflightError("WRITABLE_ADAPTER_REJECTED")
        evaluated = parse_timestamp(evaluated_at)
        collected = parse_timestamp(host.collected_at)
        reasons = {code: [] for code in _ORDER}
        if host.operating_system != "Darwin": reasons["HOST"].append("DARWIN_REQUIRED")
        if host.machine_architecture not in config.supported_architectures: reasons["HOST"].append("ARCHITECTURE_UNSUPPORTED")
        if host.user_id == 0: reasons["HOST"].append("ROOT_USER_REJECTED")
        if host.repository_root.startswith(config.application_support_root): reasons["HOST"].append("REPOSITORY_INSIDE_OPERATIONAL_ROOT")
        if host.repository_root != config.repository_root: reasons["GIT"].append("REPOSITORY_MISMATCH")
        if host.repository_branch != config.approved_branch: reasons["GIT"].append("BRANCH_MISMATCH")
        if host.repository_commit != config.approved_commit: reasons["GIT"].append("COMMIT_MISMATCH")
        if not host.working_tree_clean: reasons["GIT"].append("GIT_DIRTY")
        if host.upstream_ahead or host.upstream_behind: reasons["GIT"].append("GIT_UNSYNCHRONIZED")
        if host.full_regression_failed or host.deployment_tests_failed or not host.full_regression_passed or not host.deployment_tests_passed:
            reasons["TESTS"].append("TEST_FAILURE")
        if host.full_regression_warnings != config.acknowledged_warning_count:
            reasons["TESTS"].append("WARNING_COUNT_UNACKNOWLEDGED")
        if not host.safety_counters or any(host.safety_counters.values()):
            reasons["SAFETY"].append("SAFETY_COUNTER_NONZERO")
        by_name = {item.responsibility: item for item in targets}
        if set(by_name) != set(config.expected_targets):
            reasons["TARGETS"].append("TARGET_EVIDENCE_INCOMPLETE")
        validator = OperationalBootstrapTargetEvidenceValidator()
        for name in sorted(config.expected_targets):
            if name in by_name:
                reasons["TARGETS"].extend(validator.validate(name, by_name[name], config))
        audit = config.expected_targets.get("audit_database", "")
        replay = config.expected_targets.get("replay_database", "")
        if audit == config.expected_targets.get("audit_backup_root") or replay == config.expected_targets.get("replay_backup_root"):
            reasons["TARGETS"].append("DATABASE_BACKUP_OVERLAP")
        if audit.startswith(config.expected_targets.get("replay_backup_root", "") + "/") or replay.startswith(config.expected_targets.get("audit_backup_root", "") + "/"):
            reasons["TARGETS"].append("AUDIT_REPLAY_OVERLAP")
        reasons["CAPACITY"].extend(OperationalBootstrapCapacityValidator().validate(capacity, config))
        closure = (
            closed_track.m3_a4a_status == closed_track.m3_a4b1_status
            == closed_track.m3_a4b2a_status == "CLOSED"
            and closed_track.readiness_decision in ("READY_WITH_RESTRICTIONS", "READY_FOR_CONTROLLED_NON_PRODUCTION_BOOTSTRAP")
            and closed_track.authorization_capability_available
            and closed_track.executor_test_only_validation_passed
            and closed_track.audit_bootstrap_validation_passed
            and closed_track.replay_bootstrap_validation_passed
            and closed_track.backup_restore_validation_passed
            and closed_track.failure_cleanup_validation_passed
            and closed_track.warning_restriction_acknowledged
        )
        if not closure: reasons["CLOSED_TRACK"].append("CLOSED_TRACK_EVIDENCE_INCOMPLETE")
        if (closed_track.operational_permit_issued or closed_track.operational_authorization_granted
                or closed_track.operational_bootstrap_executed):
            reasons["CLOSED_TRACK"].append("OPERATIONAL_STATE_CONTRADICTION")
        if evaluated < collected: reasons["HOST"].append("TIMESTAMP_CONTRADICTION")
        checks = tuple(OperationalBootstrapPreflightCheck(
            code, OperationalBootstrapPreflightStatus.BLOCKED if reasons[code] else
            OperationalBootstrapPreflightStatus.PASS, tuple(sorted(set(reasons[code]))))
            for code in _ORDER)
        findings = tuple(sorted(OperationalBootstrapPreflightFinding(reason, "ERROR")
                                for code in _ORDER for reason in set(reasons[code])))
        restrictions = (OperationalBootstrapPreflightRestriction(
            "READ_ONLY_PREFLIGHT_IS_NOT_AUTHORIZATION",
            "No permit, bootstrap, writer, monitoring, dispatch or production authorization is granted."),
            OperationalBootstrapPreflightRestriction(
                "ACKNOWLEDGED_427_WARNINGS", "427 existing warnings remain restricted."))
        if any(reasons.values()):
            decision = (OperationalBootstrapPreflightDecision.INVALID
                        if "TIMESTAMP_CONTRADICTION" in reasons["HOST"]
                        or "OPERATIONAL_STATE_CONTRADICTION" in reasons["CLOSED_TRACK"]
                        else OperationalBootstrapPreflightDecision.BLOCKED)
        else:
            decision = OperationalBootstrapPreflightDecision.READY_WITH_RESTRICTIONS
        content = {"decision": decision.value, "evaluated_at": evaluated_at,
                   "checks": [asdict(item) for item in checks],
                   "findings": [asdict(item) for item in findings],
                   "restrictions": [asdict(item) for item in restrictions],
                   "permit_issued": False, "permit_claimed": False,
                   "bootstrap_authorized": False, "bootstrap_executed": False,
                   "writers_authorized": False, "monitoring_authorized": False,
                   "external_dispatch_authorized": False, "production_authorized": False,
                   "filesystem_writes": 0, "database_writes": 0}
        report_digest = digest(content)
        return OperationalBootstrapPreflightReport(
            report_id="m3-a4b2b0-" + report_digest[7:39], decision=decision,
            evaluated_at=evaluated_at, checks=checks, findings=findings,
            restrictions=restrictions, report_digest=report_digest)
