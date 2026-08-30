from datetime import datetime, timedelta, timezone

from core.governance.control_plane.trust.fresh_human_evidence import (
    FreshHumanChallengeIssuer, FreshHumanEvidenceV1, FreshHumanVerificationResult,
)
from core.governance.control_plane.trust.governance_remediation_adapters import (
    AuthorizationAcquisitionResult, AuthorizationAcquisitionStatus,
    FakeAuthorizationServicesAdapter, FakePrivilegedGovernanceRemediationAdapter,
    PrivilegedAttemptStatus, orchestrate_fresh_human_governance_remediation,
)
from core.governance.control_plane.trust.governance_remediation_authorization import (
    AuthorizationPresentation, FreshApprovalEvidence,
)
from tests.governance.control_plane.trust.test_durable_remediation_orchestration import (
    FS_PLAN, ELIGIBLE, acquisition, journal, replay_key, success,
)

NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)
FINGERPRINT = "test-p256-key"


class Verifier:
    def __init__(self, result): self.result = result
    def verify(self, **_): return self.result


def run(tmp_path, result=FreshHumanVerificationResult.VERIFIED, store=None,
        evidence_transform=lambda value: value, verification_time=NOW,
        acquired=None, helper_result=None):
    issuer = FreshHumanChallengeIssuer(clock=lambda: NOW, entropy=lambda size: b"x" * size)
    provider = lambda challenge: evidence_transform(FreshHumanEvidenceV1(
        challenge, b"signature", FINGERPRINT))
    helper = FakePrivilegedGovernanceRemediationAdapter(helper_result or success())
    output = orchestrate_fresh_human_governance_remediation(
        FS_PLAN, ELIGIBLE, "request-1", FakeAuthorizationServicesAdapter(
            acquired if acquired is not None else acquisition()),
        issuer, provider, Verifier(result), FINGERPRINT, lambda: verification_time,
        store or journal(tmp_path), helper)
    return output, helper


def acquired_with(*, evidence=FreshApprovalEvidence.NOT_VERIFIABLE,
                  status=AuthorizationAcquisitionStatus.ACQUIRED,
                  purpose=None, right=None):
    exact = acquisition()
    presentation = AuthorizationPresentation(
        purpose if purpose is not None else exact.presentation.purpose,
        right if right is not None else exact.presentation.right,
        evidence,
    )
    return AuthorizationAcquisitionResult(status, presentation, exact.replay_key)


def test_no_verified_evidence_means_zero_helper_calls(tmp_path):
    output, helper = run(tmp_path, FreshHumanVerificationResult.DENIED)
    assert output.human_verification is FreshHumanVerificationResult.DENIED
    assert helper.calls == 0


def test_binding_mismatch_means_zero_helper_calls(tmp_path):
    from dataclasses import replace
    output, helper = run(tmp_path, evidence_transform=lambda evidence: replace(
        evidence, challenge=replace(evidence.challenge, request_identity="other")))
    assert helper.calls == 0


def test_expired_evidence_means_zero_helper_calls(tmp_path):
    output, helper = run(tmp_path, verification_time=NOW + timedelta(minutes=5))
    assert output.human_verification is FreshHumanVerificationResult.EXPIRED
    assert helper.calls == 0


def test_journal_provisioning_evidence_cannot_satisfy_remediation(tmp_path):
    from core.governance.control_plane.trust.pre_bootstrap_journal_provisioning import (
        JournalProvisioningAuthorization, JournalProvisioningPurpose,
    )
    provisioning = JournalProvisioningAuthorization(
        JournalProvisioningPurpose.CREATE_PRE_BOOTSTRAP_REMEDIATION_JOURNAL,
        "request-1")
    output, helper = run(tmp_path, evidence_transform=lambda _: provisioning)
    assert output.human_verification is FreshHumanVerificationResult.DENIED
    assert helper.calls == 0


def test_existing_durable_claim_means_zero_helper_calls(tmp_path):
    store = journal(tmp_path); store.claim_once(replay_key())
    output, helper = run(tmp_path, store=store)
    assert output.human_verification is FreshHumanVerificationResult.VERIFIED
    assert helper.calls == 0


def test_valid_first_evidence_means_exactly_one_helper_call(tmp_path):
    output, helper = run(tmp_path)
    assert output.human_verification is FreshHumanVerificationResult.VERIFIED
    assert output.consumed_authorization.state.name == "CONSUMED"
    assert helper.calls == 1


def test_not_verifiable_authorization_plus_valid_fhe_executes_exactly_once(tmp_path):
    acquired = acquired_with()
    original = acquired.presentation
    output, helper = run(tmp_path, acquired=acquired)
    assert output.human_verification is FreshHumanVerificationResult.VERIFIED
    assert output.fresh_approval_evidence is FreshApprovalEvidence.NOT_VERIFIABLE
    assert acquired.presentation is original
    assert acquired.presentation.fresh_approval_evidence is FreshApprovalEvidence.NOT_VERIFIABLE
    assert helper.calls == 1


def test_not_verifiable_authorization_plus_invalid_fhe_never_executes(tmp_path):
    output, helper = run(tmp_path, result=FreshHumanVerificationResult.DENIED,
                         acquired=acquired_with())
    assert output.fresh_approval_evidence is FreshApprovalEvidence.NOT_VERIFIABLE
    assert helper.calls == 0


def test_verified_authorization_without_fhe_never_executes(tmp_path):
    output, helper = run(tmp_path, acquired=acquired_with(
        evidence=FreshApprovalEvidence.VERIFIED), evidence_transform=lambda _: None)
    assert output.human_verification is FreshHumanVerificationResult.DENIED
    assert helper.calls == 0


def test_wrong_right_or_purpose_plus_valid_fhe_never_executes(tmp_path):
    for name in ("right", "purpose"):
        output, helper = run(tmp_path, acquired=acquired_with(**{name: object()}))
        assert output.human_verification is FreshHumanVerificationResult.DENIED
        assert helper.calls == 0


def test_denied_acquisition_plus_valid_fhe_never_executes(tmp_path):
    output, helper = run(tmp_path, acquired=acquired_with(
        status=AuthorizationAcquisitionStatus.DENIED))
    assert helper.calls == 0


def test_helper_exception_is_uncertain_consumed_and_never_retried(tmp_path):
    store = journal(tmp_path)
    output, helper = run(tmp_path, store=store, acquired=acquired_with(),
                         helper_result=RuntimeError("helper lost"))
    assert output.attempt_status is PrivilegedAttemptStatus.UNCERTAIN
    assert helper.calls == 1
    replay, replay_helper = run(tmp_path, store=store, acquired=acquired_with())
    assert replay.human_verification is FreshHumanVerificationResult.VERIFIED
    assert replay_helper.calls == 0
