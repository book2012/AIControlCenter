from dataclasses import FrozenInstanceError, fields
import inspect

import pytest

from core.governance.control_plane.trust.governance_remediation import (
    GovernanceRemediationPlan, RemediationDecision, RemediationEligibility,
    RemediationOperation, RemediationPostcondition,
)
from core.governance.control_plane.trust.governance_remediation_adapters import (
    AuthorizationAcquisitionResult, AuthorizationAcquisitionStatus,
    AuthorizationServicesPort, FakeAuthorizationServicesAdapter,
    FakePrivilegedGovernanceRemediationAdapter, PrivilegedAttemptResult,
    PrivilegedAttemptStatus, PrivilegedGovernanceRemediationPort,
    RemediationOrchestrationResult, orchestrate_bounded_governance_remediation,
)
from core.governance.control_plane.trust.governance_remediation_authorization import (
    AttemptOutcome, AttemptState, AuthorizationPresentation,
    FreshApprovalEvidence, RemediationAuthorizationPurpose,
    RemediationAuthorizationRight,
)
from core.governance.control_plane.trust.pre_bootstrap_filesystem import (
    ExistingObjectKind, FilesystemObservation, GovernedPath,
    PreBootstrapFilesystemPlan, TrustedFilesystemIdentity,
)

PURPOSE = RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700
RIGHT = RemediationAuthorizationRight.PURPOSE_SPECIFIC_MACOS_RIGHT
FS_PLAN = PreBootstrapFilesystemPlan(
    TrustedFilesystemIdentity(501, 20, "/fixed"),
    "/fixed/Library/Application Support/AIControlCenter/governance",
    "/fixed/Library/Application Support/AIControlCenter/governance/trust",
)
ELIGIBLE = RemediationDecision(
    RemediationEligibility.ELIGIBLE,
    GovernanceRemediationPlan(FS_PLAN.governance_path, 0o755, 0o700, 501, 20),
)


def acquisition(evidence=FreshApprovalEvidence.VERIFIED):
    return AuthorizationAcquisitionResult(
        AuthorizationAcquisitionStatus.ACQUIRED,
        AuthorizationPresentation(PURPOSE, RIGHT, evidence),
    )


def safe_postcondition():
    return RemediationPostcondition(FilesystemObservation(
        GovernedPath.GOVERNANCE, object_kind=ExistingObjectKind.DIRECTORY,
        mode=0o700, uid=501, gid=20, descriptor_identity_proven=True,
    ))


def run(auth_result=None, helper_result=None, remediation=ELIGIBLE):
    auth = FakeAuthorizationServicesAdapter(auth_result or acquisition())
    helper = FakePrivilegedGovernanceRemediationAdapter(
        helper_result or PrivilegedAttemptResult(
            PrivilegedAttemptStatus.SUCCESS, safe_postcondition()
        )
    )
    result = orchestrate_bounded_governance_remediation(
        FS_PLAN, remediation, auth, helper
    )
    return result, auth, helper


def test_ports_expose_only_fixed_zero_argument_operations():
    assert list(inspect.signature(
        AuthorizationServicesPort.acquire_exact_remediation_authorization
    ).parameters) == ["self"]
    assert list(inspect.signature(
        PrivilegedGovernanceRemediationPort.restrict_governance_directory_mode_0755_to_0700
    ).parameters) == ["self"]
    forbidden = {"path", "mode", "uid", "gid", "owner", "group", "command",
                 "argv", "environment", "shell", "executable", "operation",
                 "recursive", "retry", "rollback"}
    for model in (AuthorizationAcquisitionResult, PrivilegedAttemptResult):
        assert forbidden.isdisjoint(field.name for field in fields(model))


@pytest.mark.parametrize("evidence", [
    FreshApprovalEvidence.NOT_VERIFIABLE, FreshApprovalEvidence.DENIED,
    FreshApprovalEvidence.CANCELED, FreshApprovalEvidence.ERROR,
])
def test_only_verified_fresh_evidence_can_reach_helper(evidence):
    result, auth, helper = run(acquisition(evidence))
    assert auth.calls == 1
    assert helper.calls == 0
    assert result.attempt_status is None
    assert result.consumed_authorization is None


@pytest.mark.parametrize("status,evidence", [
    (AuthorizationAcquisitionStatus.DENIED, FreshApprovalEvidence.DENIED),
    (AuthorizationAcquisitionStatus.CANCELED, FreshApprovalEvidence.CANCELED),
    (AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR),
])
def test_terminal_authorization_results_cannot_execute(status, evidence):
    result, _, helper = run(AuthorizationAcquisitionResult(status))
    assert helper.calls == 0
    assert result.fresh_approval_evidence is evidence


def test_verified_exact_plan_reaches_fake_once_and_success_consumes():
    result, auth, helper = run()
    assert (auth.calls, helper.calls) == (1, 1)
    assert result.attempt_status is PrivilegedAttemptStatus.SUCCESS
    assert result.postcondition_satisfied
    assert result.consumed_authorization.state is AttemptState.CONSUMED
    assert result.consumed_authorization.outcome is AttemptOutcome.SUCCESS


@pytest.mark.parametrize("status,outcome", [
    (PrivilegedAttemptStatus.FAILURE, AttemptOutcome.FAILURE),
    (PrivilegedAttemptStatus.UNCERTAIN, AttemptOutcome.UNCERTAIN),
])
def test_failure_and_uncertainty_consume_without_retry(status, outcome):
    result, _, helper = run(helper_result=PrivilegedAttemptResult(status))
    assert helper.calls == 1
    assert result.consumed_authorization.outcome is outcome


def test_adapter_exception_is_uncertain_consumed_and_not_retried():
    result, _, helper = run(helper_result=RuntimeError("helper lost"))
    assert helper.calls == 1
    assert result.attempt_status is PrivilegedAttemptStatus.UNCERTAIN
    assert result.consumed_authorization.outcome is AttemptOutcome.UNCERTAIN


def test_success_without_exact_postcondition_is_uncertain_consumed():
    result, _, helper = run(
        helper_result=PrivilegedAttemptResult(PrivilegedAttemptStatus.SUCCESS)
    )
    assert helper.calls == 1
    assert result.attempt_status is PrivilegedAttemptStatus.UNCERTAIN
    assert result.consumed_authorization.outcome is AttemptOutcome.UNCERTAIN


@pytest.mark.parametrize("remediation", [
    RemediationDecision(RemediationEligibility.DENIED),
    RemediationDecision(RemediationEligibility.NOT_REQUIRED),
    RemediationDecision(RemediationEligibility.ELIGIBLE,
        GovernanceRemediationPlan(FS_PLAN.trust_path, 0o755, 0o700, 501, 20)),
    RemediationDecision(RemediationEligibility.ELIGIBLE,
        GovernanceRemediationPlan(FS_PLAN.governance_path, 0o755, 0o700, 501, 20,
                                  operation="forged")),
])
def test_ineligible_trust_registry_database_or_forged_operations_cannot_execute(remediation):
    result, auth, helper = run(remediation=remediation)
    assert auth.calls == 0
    assert helper.calls == 0
    assert result.consumed_authorization is None


def test_models_are_immutable_and_bool_is_not_an_integer_authority():
    model = acquisition()
    with pytest.raises(FrozenInstanceError):
        model.status = AuthorizationAcquisitionStatus.ERROR
    forged = RemediationDecision(RemediationEligibility.ELIGIBLE,
        GovernanceRemediationPlan(FS_PLAN.governance_path, True, 0o700, 501, 20))
    _, auth, helper = run(remediation=forged)
    assert (auth.calls, helper.calls) == (0, 0)
    assert getattr(RemediationOrchestrationResult, "__dataclass_params__").frozen


@pytest.mark.parametrize("changes", [
    {"target": "/forged"},
    {"target": FS_PLAN.trust_path},
    {"observed_mode": 0o700},
    {"required_mode": 0o755},
    {"owner_uid": 0},
    {"owner_gid": 0},
    {"operation": "forged"},
    {"owner_uid": True},
    {"owner_gid": False},
])
def test_every_inexact_plan_is_rejected_before_authorization(changes):
    values = dict(
        target=FS_PLAN.governance_path, observed_mode=0o755,
        required_mode=0o700, owner_uid=501, owner_gid=20,
        operation=RemediationOperation.RESTRICT_GOVERNANCE_MODE_0755_TO_0700,
    )
    values.update(changes)
    forged = RemediationDecision(
        RemediationEligibility.ELIGIBLE, GovernanceRemediationPlan(**values)
    )
    _, auth, helper = run(remediation=forged)
    assert (auth.calls, helper.calls) == (0, 0)


def test_malformed_decision_and_missing_plan_are_rejected_before_authorization():
    for remediation in (
        object(), RemediationDecision(RemediationEligibility.ELIGIBLE),
    ):
        _, auth, helper = run(remediation=remediation)
        assert (auth.calls, helper.calls) == (0, 0)
