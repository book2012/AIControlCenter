"""Pure deterministic evaluation for DPL-04D operational readiness."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import (
    M2ReadinessCheck,
    M2ReadinessDecision,
    M2ReadinessEvidence,
    M2ReadinessEvidenceError,
    M2ReadinessFinding,
    M2ReadinessReport,
    sha256_digest,
)

_CHECKS: tuple[tuple[str, tuple[tuple[str, Any], ...]], ...] = (
    ("CONTROL_PLANE_OWNERSHIP", (
        ("control_plane_owner", "AIControlCenter"), ("control_plane_host_role", "Mac"),
        ("ubuntu_control_plane_ownership", False))),
    ("DEPLOYMENT_CONTRACTS", (
        ("versioned_immutable_contracts_present", True), ("canonical_json_supported", True),
        ("schema_validation_passed", True))),
    ("MAC_INVENTORY_AND_INGRESS", (
        ("mac_inventory_validation_passed", True), ("caddy_readiness_available", True),
        ("colima_readiness_available", True), ("compose_readiness_available", True),
        ("evidence_read_only", True), ("runtime_mutation_performed", False))),
    ("DEPENDENCY_BOUNDARIES", (
        ("dependency_policy_validation_passed", True), ("protected_api_boundary_passed", True),
        ("protected_worker_boundary_passed", True), ("generic_command_execution_reachable", False))),
    ("DETERMINISTIC_PLANNING", (
        ("deployment_plan_validation_passed", True), ("package_binding_passed", True),
        ("target_binding_passed", True), ("environment_binding_passed", True),
        ("scope_binding_passed", True), ("plan_digest_present", True))),
    ("EXECUTION_AUTHORIZATION", (
        ("authorization_validation_passed", True), ("requester_approver_separation_passed", True),
        ("nonce_expiry_policy_passed", True), ("production_authorization", False),
        ("maximum_authorization_uses", 1))),
    ("REPLAY_PROTECTION", (
        ("first_simulated_use_passed", True), ("replay_denial_passed", True),
        ("failed_execution_fail_closed", True))),
    ("TYPED_EXECUTOR_PORT", (
        ("typed_operation_allowlist_passed", True), ("arbitrary_shell_rejected", True),
        ("command_rejected", True), ("argv_rejected", True), ("default_deny_enabled", True),
        ("real_executor_invocation_count", 0))),
    ("MAC_SANDBOX_ADAPTER", (
        ("explicit_sandbox_root", True), ("root_confinement_passed", True),
        ("symlink_rejection_passed", True), ("traversal_rejection_passed", True),
        ("repository_runtime_writes", 0), ("ubuntu_changes", 0), ("runtime_commands", 0),
        ("network_accesses", 0), ("production_writes", 0))),
    ("AUDIT_ARCHITECTURE", (
        ("aicontrolcenter_audit_ownership_accepted", True),
        ("mac_control_plane_storage_accepted", True), ("durable_audit_port_present", True),
        ("canonical_audit_event_present", True), ("hash_chain_contracts_present", True),
        ("secret_bearing_fields_rejected", True), ("persistent_sqlite_adapter_implemented", False),
        ("persistent_audit_writes", 0))),
    ("TEST_EVIDENCE", (
        ("targeted_tests_passed", True), ("deployment_suite_passed", True),
        ("full_regression_passed", True), ("failed_test_count", 0), ("full_regression_minimum_met", True))),
    ("GIT_AND_DOCUMENTATION", (
        ("approved_feature_branch", True), ("commit_created", True), ("push_completed", True),
        ("working_tree_clean", True), ("ahead", 0), ("behind", 0),
        ("architecture_updated", True), ("readme_updated", True), ("changelog_updated", True),
        ("master_updated", True), ("roadmap_updated", True))),
    ("SAFETY_COUNTERS", (
        ("production_business_writes", 0), ("persistent_audit_writes", 0),
        ("persistent_nonce_writes", 0), ("real_executor_invocations", 0),
        ("ubuntu_changes", 0), ("runtime_commands", 0), ("service_restarts", 0),
        ("api_write_routes", 0), ("production_activations", 0))),
)

_RESTRICTIONS = (
    "sandbox-only", "Mac Control Plane only", "non-production only",
    "no real infrastructure executor", "no Ubuntu execution",
    "no production authorization", "no public write API",
    "no persistent SQLite audit adapter", "operator authorization still required",
    "pilot activation not performed",
)


class M2ReadinessGate:
    """Evaluate supplied evidence without probing a runtime or infrastructure."""

    def evaluate(
        self, evidence: M2ReadinessEvidence | Mapping[str, Any], *, evaluated_at: str
    ) -> M2ReadinessReport:
        try:
            parsed = (
                evidence if isinstance(evidence, M2ReadinessEvidence)
                else M2ReadinessEvidence.from_mapping(evidence)
            )
        except (M2ReadinessEvidenceError, TypeError):
            return self._blocked(evaluated_at, "MALFORMED_EVIDENCE")

        categories = parsed.checks
        expected_names = {name for name, _ in _CHECKS}
        missing = sorted(expected_names - set(categories))
        unknown = sorted(set(categories) - expected_names)
        if missing or unknown:
            codes = tuple(
                [f"MISSING_CATEGORY:{item}" for item in missing]
                + [f"UNKNOWN_CATEGORY:{item}" for item in unknown]
            )
            return self._blocked(evaluated_at, *codes, evidence_digest=sha256_digest(parsed))

        if self._contradictory(categories):
            return self._blocked(
                evaluated_at, "CONTRADICTORY_EVIDENCE",
                evidence_digest=sha256_digest(parsed),
            )

        checks: list[M2ReadinessCheck] = []
        findings: list[M2ReadinessFinding] = []
        malformed = False
        for category, requirements in _CHECKS:
            supplied = categories[category]
            if not isinstance(supplied, Mapping):
                malformed = True
                break
            missing_fields = sorted(key for key, _ in requirements if key not in supplied)
            allowed = {key for key, _ in requirements}
            if category == "TEST_EVIDENCE":
                allowed.update({"full_regression_passed_count", "deselected_count", "warning_count"})
            unknown_fields = sorted(set(supplied) - allowed)
            if missing_fields or unknown_fields:
                malformed = True
                break
            if any(
                not isinstance(supplied[key], type(expected))
                or (
                    isinstance(expected, int)
                    and not isinstance(expected, bool)
                    and isinstance(supplied[key], bool)
                )
                for key, expected in requirements
            ):
                malformed = True
                break
            reasons = [
                f"{key.upper()}_FAILED"
                for key, expected in requirements if supplied[key] != expected
            ]
            if category == "TEST_EVIDENCE":
                count = supplied.get("full_regression_passed_count")
                if not isinstance(count, int) or isinstance(count, bool):
                    malformed = True
                    break
                if count < 1247 and "FULL_REGRESSION_MINIMUM_MET_FAILED" not in reasons:
                    reasons.append("FULL_REGRESSION_COUNT_BELOW_MINIMUM")
                warnings = supplied.get("warning_count")
                deselected = supplied.get("deselected_count")
                if not all(isinstance(item, int) and not isinstance(item, bool) and item >= 0
                           for item in (warnings, deselected)):
                    malformed = True
                    break
                if warnings:
                    findings.append(M2ReadinessFinding(
                        category, "WARNING", "TEST_WARNINGS_REPORTED",
                        f"Regression evidence reports {warnings} warnings.",
                    ))
            checks.append(M2ReadinessCheck(category, not reasons, tuple(sorted(reasons))))

        if malformed:
            return self._blocked(
                evaluated_at, "MALFORMED_EVIDENCE",
                evidence_digest=sha256_digest(parsed),
            )

        findings.append(M2ReadinessFinding(
            "AUDIT_ARCHITECTURE", "RESTRICTION", "PERSISTENT_SQLITE_ADAPTER_ABSENT",
            "Persistent SQLite audit is required before any broader mutable deployment milestone.",
        ))
        decision = (
            M2ReadinessDecision.READY_FOR_AUTHORIZED_NON_PRODUCTION_SANDBOX
            if all(item.passed for item in checks) else M2ReadinessDecision.NOT_READY
        )
        return self._report(
            evaluated_at=evaluated_at,
            evidence_digest=sha256_digest(parsed),
            decision=decision,
            checks=tuple(checks),
            findings=tuple(sorted(findings, key=lambda item: (item.category, item.severity, item.code))),
        )

    @staticmethod
    def _contradictory(categories: Mapping[str, Any]) -> bool:
        ingress = categories.get("MAC_INVENTORY_AND_INGRESS", {})
        auth = categories.get("EXECUTION_AUTHORIZATION", {})
        safety = categories.get("SAFETY_COUNTERS", {})
        return bool(
            isinstance(ingress, Mapping)
            and ingress.get("evidence_read_only") is True
            and ingress.get("runtime_mutation_performed") is True
        ) or bool(
            isinstance(auth, Mapping) and isinstance(safety, Mapping)
            and auth.get("production_authorization") is False
            and safety.get("production_activations", 0) > 0
        )

    def _blocked(
        self, evaluated_at: str, *codes: str, evidence_digest: str | None = None
    ) -> M2ReadinessReport:
        findings = tuple(
            M2ReadinessFinding("EVIDENCE", "ERROR", code, "Evidence cannot be verified deterministically.")
            for code in sorted(codes)
        )
        return self._report(
            evaluated_at=evaluated_at,
            evidence_digest=evidence_digest or sha256_digest({"invalid": True}),
            decision=M2ReadinessDecision.BLOCKED,
            checks=(),
            findings=findings,
        )

    @staticmethod
    def _report(
        *, evaluated_at: str, evidence_digest: str, decision: M2ReadinessDecision,
        checks: tuple[M2ReadinessCheck, ...], findings: tuple[M2ReadinessFinding, ...],
    ) -> M2ReadinessReport:
        semantic = {
            "schema_version": "dpl/m2-readiness-report/v1",
            "evaluated_at": evaluated_at,
            "evidence_digest": evidence_digest,
            "decision": decision.value,
            "checks": [item.to_dict() for item in checks],
            "findings": [item.to_dict() for item in findings],
            "restrictions": list(_RESTRICTIONS),
        }
        digest = sha256_digest(semantic)
        return M2ReadinessReport(
            schema_version=semantic["schema_version"],
            report_id="m2r-" + digest[7:39],
            report_digest=digest,
            evaluated_at=evaluated_at,
            evidence_digest=evidence_digest,
            decision=decision,
            checks=checks,
            findings=findings,
            restrictions=_RESTRICTIONS,
        )
