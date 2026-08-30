from datetime import datetime, timedelta, timezone

from core.governance.control_plane.trust.fresh_human_evidence import (
    FreshHumanChallengeIssuer, FreshHumanEvidenceV1, FreshHumanVerificationResult,
)
from core.governance.control_plane.trust.governance_remediation_adapters import (
    FakeAuthorizationServicesAdapter, FakePrivilegedGovernanceRemediationAdapter,
    orchestrate_fresh_human_governance_remediation,
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
        evidence_transform=lambda value: value, verification_time=NOW):
    issuer = FreshHumanChallengeIssuer(clock=lambda: NOW, entropy=lambda size: b"x" * size)
    provider = lambda challenge: evidence_transform(FreshHumanEvidenceV1(
        challenge, b"signature", FINGERPRINT))
    helper = FakePrivilegedGovernanceRemediationAdapter(success())
    output = orchestrate_fresh_human_governance_remediation(
        FS_PLAN, ELIGIBLE, "request-1", FakeAuthorizationServicesAdapter(acquisition()),
        issuer, provider, Verifier(result), FINGERPRINT, lambda: verification_time,
        store or journal(tmp_path), helper)
    return output, helper


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
    assert helper.calls == 1
