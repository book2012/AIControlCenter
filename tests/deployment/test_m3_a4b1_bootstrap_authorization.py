from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from core.deployment.operational_activation_gate import (
    ActivationReadinessDecision, ActivationReadinessReport, ActivationRestriction,
    OperationalActivationStage, OperationalBootstrapPlan, OperationalBootstrapStep,
    OperationalPathPlan, OperationalPermissionPlan,
)
from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapApproval, OperationalBootstrapAuthorizationConfig,
    OperationalBootstrapAuthorizationError, OperationalBootstrapAuthorizationRequest,
    OperationalBootstrapAuthorizationService, OperationalBootstrapAuthorizationStage,
    OperationalBootstrapPermitUseGuard, OperationalBootstrapPermitValidator,
    OperationalBootstrapPlanBinding, OperationalBootstrapRestrictionAcknowledgement,
    OperationalBootstrapSafetySnapshot, OperationalBootstrapSchemaBinding,
    OperationalBootstrapTargetBinding, canonical_digest,
)
from core.deployment.policy import validate_dependency_boundaries

ROOT = Path(__file__).parents[2]
NOW = "2026-07-30T12:00:00+09:00"
APPROVED = "2026-07-30T12:01:00+09:00"
ISSUED = "2026-07-30T12:02:00+09:00"
EXPIRES = "2026-07-30T13:00:00+09:00"
DIGEST = "sha256:" + "a" * 64
COMMIT = "b" * 40
COUNTERS = {name: 0 for name in (
    "operational_directories_created", "operational_databases_created",
    "operational_backup_files_created", "operational_audit_writes",
    "operational_replay_writes", "writers_activated", "monitoring_activated",
    "alerts_dispatched", "notifications_sent", "n8n_invocations", "ubuntu_changes",
    "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
    "bootstrap_executions", "production_activations")}


def readiness(warnings: int = 427) -> ActivationReadinessReport:
    restrictions = (
        ActivationRestriction("DEPRECATION_WARNINGS_OUTSTANDING",
                              "Deprecation warnings require tracked remediation before activation."),
        ActivationRestriction("READINESS_IS_NOT_AUTHORIZATION",
                              "No bootstrap, writer, monitoring, dispatch or production authorization is granted."),
    )
    path = OperationalPathPlan("/x/a", "/x/ab", "/x/r", "/x/rb", "/x/m")
    permission = OperationalPermissionPlan()
    bootstrap = OperationalBootstrapPlan((OperationalBootstrapStep(1, "PREPARE", "prepare"),))
    content = dict(
        report_id="m3-a4a-report", operational_stage=OperationalActivationStage.PRE_ACTIVATION_READINESS,
        readiness_decision=ActivationReadinessDecision.READY_WITH_RESTRICTIONS,
        evaluated_at=NOW, evidence_ids=("evidence",), evidence_digests=(DIGEST,),
        checks=(), findings=(), restrictions=restrictions, path_plan=path,
        permission_plan=permission, bootstrap_plan=bootstrap, rollback_plan_valid=True,
        failed_checks=(), warning_checks=("TEST_HEALTH",), passed_checks=("GIT_HEALTH",),
        report_digest=DIGEST)
    return ActivationReadinessReport(**content)


def bindings():
    target = OperationalBootstrapTargetBinding(
        DIGEST, DIGEST, DIGEST, DIGEST, DIGEST,
        {name: True for name in ("audit_database", "audit_backup_root",
                                 "replay_database", "replay_backup_root", "monitoring_root")})
    schema = OperationalBootstrapSchemaBinding(DIGEST, DIGEST, DIGEST, DIGEST, DIGEST, DIGEST)
    plan = OperationalBootstrapPlanBinding(DIGEST, DIGEST, DIGEST, DIGEST,
                                           ("VALIDATE_GIT", "CREATE_FUTURE_TARGETS"))
    safety = OperationalBootstrapSafetySnapshot(
        COUNTERS, True, 0, 0, 1000, 0, 0, 427, True, True, True, NOW)
    return target, schema, plan, safety


def request(**changes):
    report = readiness()
    acknowledgements = tuple(
        OperationalBootstrapRestrictionAcknowledgement(
            item.code, canonical_digest(item.as_dict()), item.summary,
            "mac-operator-01", "security-approver-02", APPROVED)
        for item in report.restrictions)
    target, schema, plan, safety = bindings()
    values = dict(
        authorization_request_id="request-001", branch="feature/deployment-package",
        commit=COMMIT, readiness_report=report, readiness_report_digest=report.report_digest,
        target_binding=target, schema_binding=schema, plan_binding=plan,
        safety_snapshot=safety, requester_identity="release-requester-03",
        operator_identity="mac-operator-01", approver_identity="security-approver-02",
        requested_at=NOW, expires_at=EXPIRES,
        restriction_acknowledgements=acknowledgements)
    values.update(changes)
    return OperationalBootstrapAuthorizationRequest(**values)


def approval(**changes):
    values = dict(approved=True, operator_identity="mac-operator-01",
                  approver_identity="security-approver-02", approved_at=APPROVED,
                  branch="feature/deployment-package", commit=COMMIT)
    values.update(changes)
    return OperationalBootstrapApproval(**values)


def authorize(req=None, app=None):
    return OperationalBootstrapAuthorizationService().authorize(
        config=OperationalBootstrapAuthorizationConfig(
            OperationalBootstrapAuthorizationStage.CONTROLLED_NON_PRODUCTION_BOOTSTRAP_AUTHORIZATION),
        request=req or request(), approval=app or approval(), decided_at=APPROVED,
        issued_at=ISSUED)


def test_authorization_and_permit_are_deterministic_and_immutable():
    first = authorize()
    second = authorize()
    assert first == second and first[1] is not None
    assert first[1].bootstrap_authorized
    assert not any((first[1].writers_authorized, first[1].monitoring_authorized,
                    first[1].external_dispatch_authorized, first[1].production_authorized))
    with pytest.raises(dataclasses.FrozenInstanceError):
        first[1].maximum_uses = 2


@pytest.mark.parametrize("stage", ["OPERATIONAL", "ACTIVE", "LIVE", "PRODUCTION",
                                   "CUSTOMER_PRODUCTION", "UNKNOWN"])
def test_privileged_stages_are_rejected(stage):
    with pytest.raises(OperationalBootstrapAuthorizationError):
        OperationalBootstrapAuthorizationConfig(stage)


def test_complete_exact_restriction_acknowledgement_including_427_warning_is_required():
    req = request(restriction_acknowledgements=())
    decision, permit = authorize(req)
    assert permit is None
    assert "RESTRICTION_ACKNOWLEDGEMENT_INCOMPLETE" in decision.reason_codes
    original = request()
    unknown = dataclasses.replace(original.restriction_acknowledgements[0],
                                  restriction_code="UNKNOWN")
    decision, permit = authorize(dataclasses.replace(
        original, restriction_acknowledgements=(unknown, *original.restriction_acknowledgements[1:])))
    assert permit is None


def test_approval_denial_and_identity_policy_fail_closed():
    decision, permit = authorize(app=approval(approved=False))
    assert permit is None and decision.decision.value == "DENIED"
    with pytest.raises(OperationalBootstrapAuthorizationError):
        approval(approver_identity="mac-operator-01")
    with pytest.raises(OperationalBootstrapAuthorizationError):
        approval(approver_identity="person@example.com")


def test_target_schema_plan_safety_and_git_contracts_fail_closed():
    with pytest.raises(OperationalBootstrapAuthorizationError):
        OperationalBootstrapTargetBinding(
            DIGEST, DIGEST, DIGEST, DIGEST, DIGEST,
            {"audit_database": False})
    with pytest.raises(OperationalBootstrapAuthorizationError):
        OperationalBootstrapSchemaBinding("bad", DIGEST, DIGEST, DIGEST, DIGEST, DIGEST)
    with pytest.raises(OperationalBootstrapAuthorizationError):
        OperationalBootstrapPlanBinding(DIGEST, DIGEST, DIGEST, DIGEST, ("SERVICE_RESTART",))
    with pytest.raises(OperationalBootstrapAuthorizationError):
        OperationalBootstrapSafetySnapshot(
            {**COUNTERS, "ubuntu_changes": 1}, True, 0, 0, 1, 0, 0, 427,
            True, True, True, NOW)


def test_permit_validation_rejects_tampering_and_expiry():
    req = request()
    decision, permit = authorize(req)
    assert permit is not None
    validator = OperationalBootstrapPermitValidator()
    valid_report = validator.validate(permit=permit, request=req, decision=decision,
                                      validated_at=ISSUED, branch=req.branch, commit=req.commit)
    assert valid_report.valid, valid_report.reason_codes
    tampered = dataclasses.replace(permit, writers_authorized=True)
    assert not validator.validate(permit=tampered, request=req, decision=decision,
                                  validated_at=ISSUED, branch=req.branch, commit=req.commit).valid
    assert not validator.validate(permit=permit, request=req, decision=decision,
                                  validated_at=EXPIRES, branch=req.branch, commit=req.commit).valid


class FakeRegistry:
    def __init__(self):
        self.claims = {}

    def inspect(self, permit_id):
        return self.claims.get(permit_id)

    def claim_unused(self, claim):
        if claim.permit_id in self.claims:
            raise OperationalBootstrapAuthorizationError("conflicting claim")
        self.claims[claim.permit_id] = claim
        return claim


def test_single_use_guard_first_claim_succeeds_second_and_conflict_fail():
    req = request()
    decision, permit = authorize(req)
    registry = FakeRegistry()
    guard = OperationalBootstrapPermitUseGuard(registry)
    claim = guard.claim(permit=permit, request=req, decision=decision,
                        claimant_identity="bootstrap-operator-04", claimed_at=ISSUED,
                        branch=req.branch, commit=req.commit)
    assert claim == registry.inspect(permit.permit_id)
    with pytest.raises(OperationalBootstrapAuthorizationError):
        guard.claim(permit=permit, request=req, decision=decision,
                    claimant_identity="bootstrap-operator-04", claimed_at=ISSUED,
                    branch=req.branch, commit=req.commit)


def test_no_io_executor_api_worker_or_network_dependency_and_policy_passes():
    forbidden = {"subprocess", "socket", "requests", "paramiko", "sqlite3",
                 "core.api", "core.worker"}
    imports = set()
    for source in (ROOT / "core/deployment/operational_bootstrap_authorization").glob("*.py"):
        tree = ast.parse(source.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
    assert not any(name == item or name.startswith(item + ".")
                   for name in imports for item in forbidden)
    assert validate_dependency_boundaries(repository_root=ROOT)["overall_result"] == "PASS"
