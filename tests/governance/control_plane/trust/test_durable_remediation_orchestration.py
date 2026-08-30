from pathlib import Path

import pytest

from core.governance.control_plane.trust.governance_remediation import (
    GovernanceRemediationPlan, RemediationDecision, RemediationEligibility,
    RemediationPostcondition,
)
from core.governance.control_plane.trust.governance_remediation_adapters import (
    AuthorizationAcquisitionResult, AuthorizationAcquisitionStatus,
    FakeAuthorizationServicesAdapter, FakePrivilegedGovernanceRemediationAdapter,
    PrivilegedAttemptResult, PrivilegedAttemptStatus,
    orchestrate_durable_governance_remediation,
)
from core.governance.control_plane.trust.governance_remediation_authorization import (
    AuthorizationPresentation, FreshApprovalEvidence, RemediationAuthorizationPurpose,
    RemediationAuthorizationRight,
)
from core.governance.control_plane.trust.pre_bootstrap_filesystem import (
    ExistingObjectKind, FilesystemObservation, GovernedPath,
    PreBootstrapFilesystemPlan, TrustedFilesystemIdentity,
)
from core.governance.control_plane.trust.pre_bootstrap_remediation_journal import (
    AuthorizationReplayKey, DurableAttemptState,
    SQLitePreBootstrapRemediationAttemptJournal,
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


def replay_key():
    return AuthorizationReplayKey.derive_from_ephemeral_capability(b"one capability")


def acquisition():
    return AuthorizationAcquisitionResult(
        AuthorizationAcquisitionStatus.ACQUIRED,
        AuthorizationPresentation(PURPOSE, RIGHT, FreshApprovalEvidence.VERIFIED),
        replay_key(),
    )


def success():
    return PrivilegedAttemptResult(
        PrivilegedAttemptStatus.SUCCESS,
        RemediationPostcondition(FilesystemObservation(
            GovernedPath.GOVERNANCE, object_kind=ExistingObjectKind.DIRECTORY,
            uid=501, gid=20, mode=0o700, descriptor_identity_proven=True
        )),
    )


def journal(tmp_path, fault=None):
    return SQLitePreBootstrapRemediationAttemptJournal(
        tmp_path / "journal.sqlite3", fault=fault
    )


def invoke(tmp_path, helper_result=None, store=None):
    auth = FakeAuthorizationServicesAdapter(acquisition())
    helper = FakePrivilegedGovernanceRemediationAdapter(helper_result or success())
    store = store or journal(tmp_path)
    result = orchestrate_durable_governance_remediation(FS_PLAN, ELIGIBLE, auth, store, helper)
    return result, helper, store


def test_durable_claim_precedes_exactly_one_helper_attempt(tmp_path):
    result, helper, store = invoke(tmp_path)
    assert helper.calls == 1
    assert result.attempt_status is PrivilegedAttemptStatus.SUCCESS
    assert store.read(replay_key()).state is DurableAttemptState.TERMINAL_SUCCESS


@pytest.mark.parametrize("state", list(DurableAttemptState))
def test_claimed_success_failure_or_uncertain_never_executes_again(tmp_path, state):
    store = journal(tmp_path)
    store.claim_once(replay_key())
    if state is not DurableAttemptState.DURABLY_CLAIMED:
        store.record_terminal(replay_key(), state)
    _, helper, _ = invoke(tmp_path, store=store)
    assert helper.calls == 0


def test_durable_claim_failure_means_zero_helper_calls(tmp_path):
    def fault(stage, _connection):
        if stage == "before_claim_commit":
            raise sqlite3.OperationalError("disk lost")
    import sqlite3
    _, helper, _ = invoke(tmp_path, store=journal(tmp_path, fault=fault))
    assert helper.calls == 0


def test_helper_exception_is_terminal_uncertain_and_never_retried(tmp_path):
    result, helper, store = invoke(tmp_path, RuntimeError("helper lost"))
    assert helper.calls == 1
    assert result.attempt_status is PrivilegedAttemptStatus.UNCERTAIN
    assert store.read(replay_key()).state is DurableAttemptState.TERMINAL_UNCERTAIN
    _, replay_helper, _ = invoke(tmp_path, store=store)
    assert replay_helper.calls == 0


def test_terminal_recording_failure_returns_uncertain_without_retry(tmp_path):
    def fault(stage, _connection):
        if stage == "before_terminal_commit":
            raise sqlite3.OperationalError("disk lost")
    import sqlite3
    result, helper, store = invoke(tmp_path, store=journal(tmp_path, fault=fault))
    assert helper.calls == 1
    assert result.attempt_status is PrivilegedAttemptStatus.UNCERTAIN
    assert store.read(replay_key()).state is DurableAttemptState.DURABLY_CLAIMED
    _, replay_helper, _ = invoke(tmp_path, store=store)
    assert replay_helper.calls == 0


def test_terminal_clock_failure_returns_uncertain_without_retry(tmp_path):
    from datetime import datetime, timezone
    calls = 0
    def clock():
        nonlocal calls
        calls += 1
        if calls == 1:
            return datetime.now(timezone.utc)
        raise RuntimeError("clock lost")
    store = SQLitePreBootstrapRemediationAttemptJournal(
        tmp_path / "clock-journal.sqlite3", clock=clock
    )
    result, helper, store = invoke(tmp_path, store=store)
    assert helper.calls == 1
    assert result.attempt_status is PrivilegedAttemptStatus.UNCERTAIN
    assert store.read(replay_key()).state is DurableAttemptState.DURABLY_CLAIMED
