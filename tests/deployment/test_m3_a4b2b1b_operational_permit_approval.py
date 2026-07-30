from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from core.deployment.operational_activation_gate import (
    ActivationReadinessDecision, ActivationReadinessReport, ActivationRestriction,
    OperationalActivationStage, OperationalBootstrapPlan, OperationalBootstrapStep,
    OperationalPathPlan, OperationalPermissionPlan,
)
from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapApproval, OperationalBootstrapAuthorizationRequest,
    OperationalBootstrapPlanBinding, OperationalBootstrapRestrictionAcknowledgement,
    OperationalBootstrapSafetySnapshot, OperationalBootstrapSchemaBinding,
    OperationalBootstrapTargetBinding,
)
from core.deployment.operational_permit_approval import *
from core.deployment.operational_permit_issuance import (
    OperationalPermitExecutionWindow as ReviewWindow,
    OperationalPermitIssuanceConfig, OperationalPermitIssuanceEvidence,
    OperationalPermitIssuanceGate, OperationalPermitRestrictionReview,
    REQUIRED_BINDINGS, REQUIRED_COUNTERS,
)
from core.deployment.policy import validate_dependency_boundaries

COMMIT = "f1416e9d65adfdd0a7f442560e4e54894286182c"
DIGEST = "sha256:" + "a" * 64
APPROVED = "2026-07-30T11:00:00+09:00"
ISSUED = "2026-07-30T11:01:00+09:00"
NOT_BEFORE = "2026-07-30T11:02:00+09:00"
DEADLINE = "2026-07-30T11:19:00+09:00"
EXPIRES = "2026-07-30T11:20:00+09:00"


def review_package(**evidence_changes):
    restriction = OperationalPermitRestrictionReview(
        "warnings-427", "preflight-1", DIGEST, "ACKNOWLEDGED_427_WARNINGS",
        DIGEST, "WARNING", False, "M3-A4B2B1B")
    values = dict(
        evidence_id="evidence-1", evidence_generated_at=APPROVED,
        branch="feature/deployment-package", commit=COMMIT,
        readiness_report_id="readiness-1", readiness_report_digest=DIGEST,
        readiness_decision="READY_WITH_RESTRICTIONS",
        authorization_closure_id="authorization-1", authorization_closure_digest=DIGEST,
        permit_contract_digest=DIGEST, executor_report_id="executor-1",
        executor_report_digest=DIGEST, executor_validation_passed=True,
        audit_bootstrap_validation_passed=True, replay_bootstrap_validation_passed=True,
        baseline_backup_restore_validation_passed=True, failure_cleanup_validation_passed=True,
        preflight_report_id="preflight-1", preflight_report_digest=DIGEST,
        preflight_decision="READY_WITH_RESTRICTIONS", darwin_control_plane=True,
        operational_targets_absent=True, filesystem_policy_passed=True,
        capacity_passed=True, permission_feasibility_passed=True,
        full_regression_passed=100, full_regression_failed=0,
        deployment_tests_passed=50, deployment_tests_failed=0, git_clean=True,
        upstream_ahead=0, upstream_behind=0,
        safety_counters={name: 0 for name in REQUIRED_COUNTERS},
        binding_digests={name: DIGEST for name in REQUIRED_BINDINGS},
        restrictions=(restriction,))
    values.update(evidence_changes)
    evidence = OperationalPermitIssuanceEvidence(**values)
    return OperationalPermitIssuanceGate().evaluate(
        config=OperationalPermitIssuanceConfig(
            "feature/deployment-package", COMMIT, ReviewWindow(1200, 300, 300, 1020)),
        evidence=evidence, evaluated_at=APPROVED)


def identity(role, name, **changes):
    values = dict(
        identity_id=name, identity_type="SYNTHETIC_TEST", local_account_binding=name,
        display_label=name, role=role, attested_by="pytest-fixture", attested_at=APPROVED,
        synthetic=True)
    values.update(changes)
    return OperationalPermitIdentity(**values)


def window(**changes):
    values = dict(
        approval_timestamp=APPROVED, issuance_timestamp=ISSUED,
        not_before_timestamp=NOT_BEFORE, expires_at_timestamp=EXPIRES,
        bootstrap_execution_deadline=DEADLINE, maximum_permit_ttl_seconds=1200,
        maximum_approval_to_issuance_seconds=300, maximum_issuance_to_claim_seconds=300,
        maximum_execution_duration_seconds=1020)
    values.update(changes)
    return OperationalPermitExecutionWindow(**values)


def acknowledgement(person, **changes):
    values = dict(
        restriction_id="warnings-427", source_report_id="preflight-1",
        source_report_digest=DIGEST, exact_summary_digest=DIGEST, severity="WARNING",
        remediation_reference="M3-A4B2B1B", acknowledging_identity_id=person,
        acknowledgement_decision=OperationalPermitApprovalDecision.APPROVED,
        acknowledged_at=APPROVED, synthetic=True)
    content = dict(values)
    values["canonical_acknowledgement_digest"] = canonical_digest(content)
    values.update(changes)
    return OperationalPermitRestrictionAcknowledgement(**values)


def approval_input(**changes):
    requester = identity(OperationalPermitIdentityRole.REQUESTER, "synthetic-requester")
    operator = identity(OperationalPermitIdentityRole.MAC_OPERATOR, "synthetic-operator")
    approver = identity(
        OperationalPermitIdentityRole.INDEPENDENT_APPROVER, "synthetic-approver")
    values = dict(
        review_package=review_package(), requester=requester, mac_operator=operator,
        independent_approver=approver,
        approval_decision=OperationalPermitApprovalDecision.APPROVED,
        restriction_acknowledgements=(
            acknowledgement(operator.identity_id), acknowledgement(approver.identity_id)),
        execution_window=window(), evaluated_at=ISSUED)
    values.update(changes)
    return OperationalPermitApprovalInput(**values)


def readiness():
    restrictions = (
        ActivationRestriction("DEPRECATION_WARNINGS_OUTSTANDING",
                              "Deprecation warnings require tracked remediation before activation."),
        ActivationRestriction("READINESS_IS_NOT_AUTHORIZATION",
                              "No bootstrap, writer, monitoring, dispatch or production authorization is granted."),
    )
    return ActivationReadinessReport(
        "m3-a4a-report", OperationalActivationStage.PRE_ACTIVATION_READINESS,
        ActivationReadinessDecision.READY_WITH_RESTRICTIONS, APPROVED, ("evidence",),
        (DIGEST,), (), (), restrictions, OperationalPathPlan("/x/a", "/x/ab", "/x/r", "/x/rb", "/x/m"),
        OperationalPermissionPlan(), OperationalBootstrapPlan(
            (OperationalBootstrapStep(1, "PREPARE", "prepare"),)),
        True, (), ("TEST_HEALTH",), ("GIT_HEALTH",), DIGEST)


def authorization_request():
    report = readiness()
    auth_acks = tuple(OperationalBootstrapRestrictionAcknowledgement(
        item.code, canonical_digest(item.as_dict()), item.summary,
        "synthetic-operator", "synthetic-approver", APPROVED) for item in report.restrictions)
    target = OperationalBootstrapTargetBinding(
        DIGEST, DIGEST, DIGEST, DIGEST, DIGEST,
        {name: True for name in ("audit_database", "audit_backup_root",
                                 "replay_database", "replay_backup_root", "monitoring_root")})
    schema = OperationalBootstrapSchemaBinding(DIGEST, DIGEST, DIGEST, DIGEST, DIGEST, DIGEST)
    plan = OperationalBootstrapPlanBinding(
        DIGEST, DIGEST, DIGEST, DIGEST, ("VALIDATE_GIT", "CREATE_FUTURE_TARGETS"))
    counter_names = (
        "operational_directories_created", "operational_databases_created",
        "operational_backup_files_created", "operational_audit_writes",
        "operational_replay_writes", "writers_activated", "monitoring_activated",
        "alerts_dispatched", "notifications_sent", "n8n_invocations", "ubuntu_changes",
        "runtime_infrastructure_commands", "service_restarts", "api_write_routes",
        "bootstrap_executions", "production_activations")
    safety = OperationalBootstrapSafetySnapshot(
        {name: 0 for name in counter_names}, True, 0, 0, 100, 0, 0, 427,
        True, True, True, APPROVED)
    return OperationalBootstrapAuthorizationRequest(
        "synthetic-request", "feature/deployment-package", COMMIT, report,
        report.report_digest, target, schema, plan, safety, "synthetic-requester",
        "synthetic-operator", "synthetic-approver", APPROVED, EXPIRES, auth_acks)


def config():
    return OperationalPermitApprovalConfig("feature/deployment-package", COMMIT)


def test_contracts_stage_report_and_current_snapshot_are_deterministic_and_immutable():
    first = OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=approval_input())
    second = OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=approval_input())
    assert first == second
    assert first.status is OperationalPermitApprovalStatus.PASS
    assert first.effective_execution_window
    with pytest.raises(FrozenInstanceError):
        first.status = OperationalPermitApprovalStatus.BLOCKED
    current = OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=current_recommended_review(review_package()))
    assert current.decision is OperationalPermitApprovalDecision.DENIED
    assert {item.code for item in current.findings} >= {
        "MISSING_INDEPENDENT_APPROVER", "MISSING_INDEPENDENT_ACKNOWLEDGEMENT"}
    assert not current.effective_execution_window
    assert not current.operational_permit_issued and not current.bootstrap_authorized


@pytest.mark.parametrize("stage", [
    "AUTOMATIC_APPROVAL", "SELF_APPROVAL", "PERMIT_CLAIMED", "BOOTSTRAP_EXECUTING",
    "OPERATIONAL", "LIVE", "PRODUCTION", "CUSTOMER_PRODUCTION"])
def test_only_explicit_review_stage_is_supported(stage):
    with pytest.raises(OperationalPermitApprovalError):
        replace(config(), stage=stage)


def test_identity_independence_and_decisions_fail_closed():
    base = approval_input()
    cases = (
        replace(base, independent_approver=None),
        replace(base, independent_approver=base.mac_operator),
        replace(base, independent_approver=replace(
            base.independent_approver, local_account_binding=base.mac_operator.local_account_binding)),
        replace(base, independent_approver=replace(
            base.independent_approver, identity_id=base.requester.identity_id)),
        replace(base, approval_decision=OperationalPermitApprovalDecision.DENIED),
        replace(base, approval_decision=OperationalPermitApprovalDecision.PENDING),
    )
    for value in cases:
        assert OperationalPermitApprovalGate().evaluate(
            config=config(), approval_input=value).status is not OperationalPermitApprovalStatus.PASS
    with pytest.raises(OperationalPermitApprovalError):
        identity(OperationalPermitIdentityRole.INDEPENDENT_APPROVER, "UNASSIGNED")
    with pytest.raises(OperationalPermitApprovalError):
        identity(OperationalPermitIdentityRole.INDEPENDENT_APPROVER, "x", placeholder=True)


def test_dual_exact_acknowledgement_and_427_warning_are_required():
    value = approval_input()
    assert OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=value).status is OperationalPermitApprovalStatus.PASS
    requester_only = replace(
        value, restriction_acknowledgements=(acknowledgement(value.requester.identity_id),))
    report = OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=requester_only)
    assert "MISSING_INDEPENDENT_ACKNOWLEDGEMENT" in {item.code for item in report.findings}
    rewritten = replace(value.restriction_acknowledgements[0], exact_summary_digest=DIGEST[:-1] + "b")
    report = OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=replace(
            value, restriction_acknowledgements=(rewritten, value.restriction_acknowledgements[1])))
    assert "RESTRICTION_ACKNOWLEDGEMENT_INVALID" in {item.code for item in report.findings}


def test_execution_window_git_safety_targets_and_adapters_fail_closed(tmp_path):
    with pytest.raises(OperationalPermitApprovalError):
        window(expires_at_timestamp=APPROVED)
    expired = replace(approval_input(), evaluated_at=EXPIRES)
    assert OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=expired).status is not OperationalPermitApprovalStatus.PASS
    mismatch = replace(config(), approved_commit="b" * 40)
    assert OperationalPermitApprovalGate().evaluate(
        config=mismatch, approval_input=approval_input()).status is not OperationalPermitApprovalStatus.PASS
    counters = {name: 0 for name in REQUIRED_COUNTERS}
    counters["filesystem_writes"] = 1
    unsafe = replace(approval_input(), review_package=review_package(safety_counters=counters))
    assert OperationalPermitApprovalGate().evaluate(
        config=config(), approval_input=unsafe).status is not OperationalPermitApprovalStatus.PASS
    assert review_package(operational_targets_absent=False).decision.value == "NOT_READY"
    request = issuance_request()
    before = tuple(tmp_path.iterdir())
    for name in ("adapter", "filesystem_adapter", "database_adapter",
                 "registry_adapter", "notification_adapter"):
        with pytest.raises(OperationalPermitApprovalError):
            OperationalPermitIssuanceCoordinator().issue(
                config=config(), request=request, **{name: object()})
    assert tuple(tmp_path.iterdir()) == before


def issuance_request(**changes):
    values = dict(
        approval_input=approval_input(), authorization_request=authorization_request(),
        authorization_approval=OperationalBootstrapApproval(
            True, "synthetic-operator", "synthetic-approver", APPROVED,
            "feature/deployment-package", COMMIT),
        decided_at=APPROVED, issued_at=ISSUED)
    values.update(changes)
    return OperationalPermitIssuanceRequest(**values)


def test_synthetic_permit_is_deterministic_in_memory_and_never_claimed():
    coordinator = OperationalPermitIssuanceCoordinator()
    first = coordinator.issue(config=config(), request=issuance_request())
    second = coordinator.issue(config=config(), request=issuance_request())
    assert first == second and first.synthetic_permit is not None
    assert first.synthetic_permit.permit_digest == second.synthetic_permit.permit_digest
    assert not first.operational_permit_issued and not first.permit_claimed
    assert not first.bootstrap_executed and not first.production_authorized
    for field in ("permit_claim_requested", "bootstrap_execution_requested",
                  "production_authorized"):
        with pytest.raises(OperationalPermitApprovalError):
            coordinator.issue(config=config(), request=replace(
                issuance_request(), **{field: True}))


def test_dependency_policy_and_forbidden_imports():
    root = Path(__file__).parents[2]
    paths = sorted(str(path.relative_to(root)) for path in
                   (root / "core/deployment/operational_permit_approval").glob("*.py"))
    assert validate_dependency_boundaries(
        repository_root=root, paths=paths)["overall_result"] == "PASS"
    source = "\n".join((root / path).read_text() for path in paths)
    for forbidden in ("subprocess", "socket", "requests", "core.api", "core.worker",
                      "sqlite3", "UbuntuWorkerClient"):
        assert forbidden not in source
