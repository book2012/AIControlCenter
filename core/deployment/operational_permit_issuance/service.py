"""Deterministic M3-A4B2B1A review orchestration; never issues a permit."""

from __future__ import annotations

from dataclasses import asdict

from .models import *

REQUIRED_BINDINGS = (
    "audit_database_target_identity", "audit_backup_root_identity",
    "replay_database_target_identity", "replay_backup_root_identity",
    "monitoring_root_identity", "audit_schema_expectation",
    "replay_schema_expectation", "path_plan", "permission_plan",
    "bootstrap_execution_plan", "rollback_cleanup_plan",
)
REQUIRED_COUNTERS = (
    "operational_permits_issued", "permit_claims",
    "operational_authorizations_granted", "operational_directories_created",
    "operational_databases_created", "operational_backups_created",
    "operational_restores", "filesystem_writes", "database_writes",
    "operational_audit_writes", "operational_replay_writes",
    "writers_activated", "monitoring_activated", "alerts_dispatched",
    "notifications_sent", "n8n_invocations", "ubuntu_changes",
    "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
    "bootstrap_executions", "production_activations",
)
CHECK_ORDER = (
    "CONFIGURATION", "EVIDENCE_INTEGRITY", "SOURCE_REPORTS", "GIT", "TESTS",
    "HOST_PREFLIGHT", "TARGETS", "BINDINGS", "RESTRICTIONS", "SAFETY",
    "HUMAN_APPROVALS",
)
OPERATOR_REQUIREMENTS = (
    "EXPLICIT_REQUESTER_IDENTITY", "EXPLICIT_MAC_OPERATOR_IDENTITY",
    "REQUESTER_OPERATOR_SELF_APPROVAL_PROHIBITED", "EXACT_BRANCH_COMMIT_ACKNOWLEDGEMENT",
    "EXACT_TARGET_SCHEMA_PLAN_ACKNOWLEDGEMENT", "CONTROLLED_NON_PRODUCTION_SCOPE",
)
APPROVER_REQUIREMENTS = (
    "EXPLICIT_INDEPENDENT_APPROVER_IDENTITY", "OPERATOR_APPROVER_DISTINCT",
    "APPROVAL_DECISION", "APPROVAL_TIMESTAMP", "RESTRICTION_ACKNOWLEDGEMENTS",
    "PRODUCTION_AUTHORIZED_FALSE",
)


class OperationalPermitIssuanceGate:
    def evaluate(self, *, config: OperationalPermitIssuanceConfig,
                 evidence: OperationalPermitIssuanceEvidence, evaluated_at: str,
                 adapter: object | None = None, persistence_adapter: object | None = None,
                 filesystem_adapter: object | None = None,
                 database_adapter: object | None = None,
                 notification_adapter: object | None = None) -> OperationalPermitIssuanceReviewPackage:
        if config is None or evidence is None:
            raise OperationalPermitIssuanceError("CONFIGURATION_AND_EVIDENCE_REQUIRED")
        if any(item is not None for item in (
            adapter, persistence_adapter, filesystem_adapter, database_adapter,
            notification_adapter,
        )):
            raise OperationalPermitIssuanceError("OPERATIONAL_ADAPTER_REJECTED")
        evaluated = parse_timestamp(evaluated_at)
        generated = parse_timestamp(evidence.evidence_generated_at)
        reasons = {code: [] for code in CHECK_ORDER}
        if evaluated < generated:
            reasons["EVIDENCE_INTEGRITY"].append("TIMESTAMP_CONTRADICTION")
        if evidence.branch != config.approved_branch:
            reasons["GIT"].append("BRANCH_MISMATCH")
        if evidence.commit != config.approved_commit:
            reasons["GIT"].append("COMMIT_MISMATCH")
        if not evidence.git_clean:
            reasons["GIT"].append("GIT_DIRTY")
        if evidence.upstream_ahead or evidence.upstream_behind:
            reasons["GIT"].append("GIT_UNSYNCHRONIZED")
        if (not evidence.full_regression_passed or evidence.full_regression_failed
                or not evidence.deployment_tests_passed or evidence.deployment_tests_failed):
            reasons["TESTS"].append("TEST_FAILURE")
        if evidence.readiness_decision != "READY_WITH_RESTRICTIONS":
            reasons["SOURCE_REPORTS"].append("READINESS_NOT_READY")
        if not evidence.permit_contract_available:
            reasons["SOURCE_REPORTS"].append("PERMIT_CONTRACT_UNAVAILABLE")
        validations = (
            evidence.executor_validation_passed,
            evidence.audit_bootstrap_validation_passed,
            evidence.replay_bootstrap_validation_passed,
            evidence.baseline_backup_restore_validation_passed,
            evidence.failure_cleanup_validation_passed,
        )
        if not all(validations):
            reasons["SOURCE_REPORTS"].append("EXECUTOR_VALIDATION_INCOMPLETE")
        if evidence.preflight_decision != "READY_WITH_RESTRICTIONS":
            reasons["HOST_PREFLIGHT"].append("PREFLIGHT_NOT_READY")
        if not evidence.darwin_control_plane:
            reasons["HOST_PREFLIGHT"].append("DARWIN_CONTROL_PLANE_REQUIRED")
        if evidence.ubuntu_participation:
            reasons["HOST_PREFLIGHT"].append("UBUNTU_PARTICIPATION_REJECTED")
        if not evidence.operational_targets_absent:
            reasons["TARGETS"].append("OPERATIONAL_TARGET_EXISTS")
        if not evidence.filesystem_policy_passed:
            reasons["TARGETS"].append("FILESYSTEM_POLICY_FAILED")
        if not evidence.capacity_passed:
            reasons["TARGETS"].append("CAPACITY_INSUFFICIENT")
        if not evidence.permission_feasibility_passed:
            reasons["TARGETS"].append("PERMISSION_FEASIBILITY_FAILED")
        missing_bindings = sorted(set(REQUIRED_BINDINGS) - set(evidence.binding_digests))
        if missing_bindings:
            reasons["BINDINGS"].append("TARGET_SCHEMA_PLAN_BINDING_INCOMPLETE")
        if not evidence.restrictions:
            reasons["RESTRICTIONS"].append("RESTRICTION_EVIDENCE_OMITTED")
        if not any(item.reason_code == "ACKNOWLEDGED_427_WARNINGS"
                   for item in evidence.restrictions):
            reasons["RESTRICTIONS"].append("WARNING_427_RESTRICTION_OMITTED")
        if any(item.blocking for item in evidence.restrictions):
            reasons["RESTRICTIONS"].append("BLOCKING_RESTRICTION_EXISTS")
        missing_counters = sorted(set(REQUIRED_COUNTERS) - set(evidence.safety_counters))
        if missing_counters:
            reasons["SAFETY"].append("SAFETY_SNAPSHOT_INCOMPLETE")
        if any(evidence.safety_counters.values()):
            reasons["SAFETY"].append("SAFETY_COUNTER_NONZERO")
        if evidence.production_authorized:
            reasons["SAFETY"].append("PRODUCTION_AUTHORIZATION_REJECTED")
        reasons["HUMAN_APPROVALS"].append("HUMAN_INPUTS_NOT_PROVIDED")
        checks = tuple(
            OperationalPermitIssuanceCheck(
                code,
                (OperationalPermitIssuanceStatus.WARNING if code == "HUMAN_APPROVALS"
                 else OperationalPermitIssuanceStatus.BLOCKED if reasons[code]
                 else OperationalPermitIssuanceStatus.PASS),
                tuple(sorted(set(reasons[code]))),
            )
            for code in CHECK_ORDER
        )
        technical = {code: values for code, values in reasons.items()
                     if code != "HUMAN_APPROVALS" and values}
        findings = tuple(sorted(
            OperationalPermitIssuanceFinding(reason, "ERROR")
            for values in technical.values() for reason in set(values)
        ))
        if "TIMESTAMP_CONTRADICTION" in reasons["EVIDENCE_INTEGRITY"]:
            decision = OperationalPermitIssuanceDecision.INVALID
        elif "BLOCKING_RESTRICTION_EXISTS" in reasons["RESTRICTIONS"]:
            decision = OperationalPermitIssuanceDecision.BLOCKED
        elif technical:
            decision = OperationalPermitIssuanceDecision.NOT_READY
        elif evidence.restrictions:
            decision = OperationalPermitIssuanceDecision.READY_WITH_RESTRICTIONS
        else:
            decision = OperationalPermitIssuanceDecision.READY_FOR_OPERATOR_AND_APPROVER_REVIEW
        reports = {
            "m3_a4a_readiness": {"id": evidence.readiness_report_id,
                                 "digest": evidence.readiness_report_digest},
            "m3_a4b1_authorization_closure": {"id": evidence.authorization_closure_id,
                                              "digest": evidence.authorization_closure_digest},
            "m3_a4b2a_executor_validation": {"id": evidence.executor_report_id,
                                             "digest": evidence.executor_report_digest},
            "m3_a4b2b0_host_preflight": {"id": evidence.preflight_report_id,
                                         "digest": evidence.preflight_report_digest},
        }
        missing = tuple((*OPERATOR_REQUIREMENTS, *APPROVER_REQUIREMENTS))
        operator_requirements = tuple(OperationalPermitOperatorRequirement(code)
                                      for code in OPERATOR_REQUIREMENTS)
        approver_requirements = tuple(OperationalPermitApprovalRequirement(code)
                                      for code in APPROVER_REQUIREMENTS)
        content = {
            "stage": config.stage, "decision": decision, "evaluated_at": evaluated_at,
            "branch": evidence.branch, "commit": evidence.commit,
            "bound_report_ids_and_digests": reports,
            "target_schema_plan_binding_digests": evidence.binding_digests,
            "checks": [asdict(item) for item in checks],
            "findings": [asdict(item) for item in findings],
            "restrictions": [asdict(item) for item in evidence.restrictions],
            "missing_human_approvals": missing,
            "operator_requirements": [asdict(item) for item in operator_requirements],
            "approver_requirements": [asdict(item) for item in approver_requirements],
            "execution_window_policy": asdict(config.execution_window),
            "safety_snapshot": evidence.safety_counters,
            "permit_contract_available": evidence.permit_contract_available,
            "operational_permit_issued": False, "permit_claimed": False,
            "bootstrap_authorized": False, "bootstrap_executed": False,
            "writers_authorized": False, "monitoring_authorized": False,
            "external_dispatch_authorized": False, "production_authorized": False,
        }
        package_digest = canonical_digest(content)
        return OperationalPermitIssuanceReviewPackage(
            review_package_id="m3-a4b2b1a-" + package_digest[7:39],
            stage=config.stage, decision=decision, evaluated_at=evaluated_at,
            branch=evidence.branch, commit=evidence.commit,
            bound_report_ids_and_digests=reports,
            target_schema_plan_binding_digests=evidence.binding_digests,
            checks=checks, findings=findings, restrictions=evidence.restrictions,
            missing_human_approvals=missing,
            operator_requirements=operator_requirements,
            approver_requirements=approver_requirements,
            execution_window_policy=config.execution_window,
            safety_snapshot=evidence.safety_counters,
            canonical_package_digest=package_digest,
            permit_contract_available=evidence.permit_contract_available,
        )


class OperationalPermitIssuanceReviewPackageBuilder(OperationalPermitIssuanceGate):
    """Named builder façade for the deterministic gate."""

    build = OperationalPermitIssuanceGate.evaluate


class OperationalPermitIssuanceValidator:
    def validate(self, package: OperationalPermitIssuanceReviewPackage
                 ) -> OperationalPermitIssuanceValidationReport:
        if not isinstance(package, OperationalPermitIssuanceReviewPackage):
            raise OperationalPermitIssuanceError("REVIEW_PACKAGE_REQUIRED")
        content = package.as_dict()
        claimed = content.pop("review_package_id")
        supplied_digest = content.pop("canonical_package_digest")
        expected_digest = canonical_digest(content)
        findings: list[OperationalPermitIssuanceFinding] = []
        if claimed != "m3-a4b2b1a-" + supplied_digest[7:39]:
            findings.append(OperationalPermitIssuanceFinding("PACKAGE_ID_MISMATCH", "ERROR"))
        if supplied_digest != expected_digest:
            findings.append(OperationalPermitIssuanceFinding("PACKAGE_DIGEST_MISMATCH", "ERROR"))
        flags = (
            package.operational_permit_issued, package.permit_claimed,
            package.bootstrap_authorized, package.bootstrap_executed,
            package.writers_authorized, package.monitoring_authorized,
            package.external_dispatch_authorized, package.production_authorized,
        )
        if any(flags):
            findings.append(OperationalPermitIssuanceFinding(
                "OPERATIONAL_STATE_CONTRADICTION", "ERROR"))
        status = (OperationalPermitIssuanceStatus.PASS if not findings
                  else OperationalPermitIssuanceStatus.INVALID)
        digest = canonical_digest({"status": status, "decision": package.decision,
                                   "findings": [asdict(item) for item in sorted(findings)]})
        return OperationalPermitIssuanceValidationReport(
            status=status, decision=package.decision, findings=tuple(sorted(findings)),
            report_id="m3-a4b2b1a-validation-" + digest[7:39],
            report_digest=digest,
        )
