from dataclasses import fields

import pytest

from core.governance.control_plane.trust.governance_remediation import (
    GovernanceRemediationPlan, RemediationDecision, RemediationEligibility,
)
from core.governance.control_plane.trust.governance_remediation_authorization import (
    AttemptOutcome, AttemptState, AuthorizationDisposition,
    AuthorizationPresentation, RemediationAttemptAuthorization,
    FreshApprovalEvidence,
    RemediationAuthorizationPurpose, RemediationAuthorizationRight,
    authorize_remediation_attempt, claim_remediation_attempt,
    consume_remediation_attempt,
)
from core.governance.control_plane.trust.pre_bootstrap_filesystem import (
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


def presentation(**overrides):
    values = dict(purpose=PURPOSE, right=RIGHT,
                  fresh_approval_evidence=FreshApprovalEvidence.VERIFIED)
    values.update(overrides)
    return AuthorizationPresentation(**values)


def authorized():
    decision = authorize_remediation_attempt(FS_PLAN, ELIGIBLE, presentation())
    assert decision.disposition is AuthorizationDisposition.AUTHORIZED
    return decision.authorization


def test_exact_purpose_specific_fresh_approval_is_accepted():
    grant = authorized()
    assert grant.state is AttemptState.AVAILABLE
    assert [field.name for field in fields(RemediationAttemptAuthorization)] == [
        "purpose", "right", "state", "outcome"
    ]


@pytest.mark.parametrize("override", [
    {"preauthorized": True}, {"shared": True}, {"reusable": True}, {"retry": True},
])
def test_preauthorized_shared_reusable_and_retry_representations_are_denied(override):
    assert authorize_remediation_attempt(
        FS_PLAN, ELIGIBLE, presentation(**override)
    ).disposition is AuthorizationDisposition.DENIED


def test_generic_or_caller_selected_right_and_purpose_are_unrepresentable():
    with pytest.raises(ValueError):
        RemediationAuthorizationRight("generic.execute")
    with pytest.raises(ValueError):
        RemediationAuthorizationPurpose("caller-purpose")


def test_authorization_artifacts_carry_no_execution_or_identity_payload():
    forbidden = {"path", "target", "mode", "uid", "gid", "command", "argv",
                 "environment", "shell", "subprocess", "api_payload", "executable"}
    for model in (AuthorizationPresentation, RemediationAttemptAuthorization):
        assert forbidden.isdisjoint(field.name for field in fields(model))
    with pytest.raises(TypeError):
        AuthorizationPresentation(PURPOSE, RIGHT, FreshApprovalEvidence.VERIFIED,
                                  path="/tmp", mode=0o777, uid=0, gid=0)


@pytest.mark.parametrize("decision", [
    RemediationDecision(RemediationEligibility.DENIED),
    RemediationDecision(RemediationEligibility.NOT_REQUIRED),
])
def test_noneligible_targets_including_trust_registry_and_databases_get_no_authority(decision):
    assert authorize_remediation_attempt(
        FS_PLAN, decision, presentation()
    ).disposition is AuthorizationDisposition.DENIED


@pytest.mark.parametrize("plan", [
    GovernanceRemediationPlan("/tmp/governance", 0o755, 0o700, 501, 20),
    GovernanceRemediationPlan(FS_PLAN.governance_path, 0o750, 0o700, 501, 20),
    GovernanceRemediationPlan(FS_PLAN.governance_path, 0o755, 0o777, 501, 20),
    GovernanceRemediationPlan(FS_PLAN.governance_path, 0o755, 0o700, 0, 20),
    GovernanceRemediationPlan(FS_PLAN.governance_path, 0o755, 0o700, 501, 0),
])
def test_forged_path_mode_uid_or_gid_never_receives_authority(plan):
    forged = RemediationDecision(RemediationEligibility.ELIGIBLE, plan)
    assert authorize_remediation_attempt(
        FS_PLAN, forged, presentation()
    ).disposition is AuthorizationDisposition.DENIED


def test_one_approval_allows_one_claim_only_and_no_stealing_or_recovery_reuse():
    grant = authorized()
    claim = claim_remediation_attempt(grant)
    assert claim.state is AttemptState.CLAIMED
    assert claim_remediation_attempt(claim) is None
    assert claim_remediation_attempt(
        RemediationAttemptAuthorization(PURPOSE, RIGHT, AttemptState.CONSUMED,
                                        AttemptOutcome.FAILURE)
    ) is None


@pytest.mark.parametrize("outcome", list(AttemptOutcome))
def test_success_failure_and_uncertainty_are_consuming_terminal_outcomes(outcome):
    consumed = consume_remediation_attempt(claim_remediation_attempt(authorized()), outcome)
    assert consumed == RemediationAttemptAuthorization(
        PURPOSE, RIGHT, AttemptState.CONSUMED, outcome
    )
    assert claim_remediation_attempt(consumed) is None
    assert consume_remediation_attempt(consumed, outcome) is None


def test_grant_exposes_no_bootstrap_feature_release_or_execution_authority():
    grant = authorized()
    names = {field.name for field in fields(grant)}
    assert {"bootstrap", "feature", "release", "issuer", "execute", "rollback"}.isdisjoint(names)
