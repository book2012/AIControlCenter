"""Replaceable, non-operational adapters for SEC-02 bounded remediation.

There is deliberately no native Authorization Services, XPC, SMAppService, or
filesystem implementation here.  Both ports expose only the one fixed ceremony.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .governance_remediation import (
    RemediationDecision,
    RemediationEligibility,
    RemediationPostcondition,
    validate_governance_remediation_plan,
    validate_remediation_postcondition,
)
from .governance_remediation_authorization import (
    AttemptOutcome,
    AttemptState,
    AuthorizationDisposition,
    AuthorizationPresentation,
    FreshApprovalEvidence,
    RemediationAttemptAuthorization,
    authorize_remediation_attempt,
    claim_remediation_attempt,
    consume_remediation_attempt,
    _create_claimed_bounded_remediation_attempt,
    validate_bounded_remediation_authorization_presentation,
)
from .pre_bootstrap_filesystem import PreBootstrapFilesystemPlan
from .pre_bootstrap_remediation_journal import (
    AuthorizationReplayKey,
    DurableAttemptState,
    DurableJournalError,
    PreBootstrapRemediationAttemptJournal,
    ReplayDenied,
)
from .fresh_human_evidence import (
    FreshHumanChallengeIssuer, FreshHumanEvidenceV1, FreshHumanSignatureVerifier,
    FreshHumanVerificationResult, verify_fresh_human_evidence,
)


class AuthorizationAcquisitionStatus(Enum):
    ACQUIRED = "ACQUIRED"
    DENIED = "DENIED"
    CANCELED = "CANCELED"
    ERROR = "ERROR"


class PrivilegedAttemptStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True, slots=True)
class AuthorizationAcquisitionResult:
    status: AuthorizationAcquisitionStatus
    presentation: AuthorizationPresentation | None = None
    replay_key: AuthorizationReplayKey | None = None


@dataclass(frozen=True, slots=True)
class PrivilegedAttemptResult:
    status: PrivilegedAttemptStatus
    postcondition: RemediationPostcondition | None = None


@dataclass(frozen=True, slots=True)
class RemediationOrchestrationResult:
    authorization_status: AuthorizationAcquisitionStatus
    fresh_approval_evidence: FreshApprovalEvidence
    attempt_status: PrivilegedAttemptStatus | None
    consumed_authorization: RemediationAttemptAuthorization | None
    postcondition_satisfied: bool
    human_verification: FreshHumanVerificationResult | None = None


class AuthorizationServicesPort(Protocol):
    """Acquire only the fixed remediation right, without preauthorization."""

    def acquire_exact_remediation_authorization(
        self,
    ) -> AuthorizationAcquisitionResult: ...


class PrivilegedGovernanceRemediationPort(Protocol):
    """Invoke the fixed helper operation; no mutation parameters are accepted."""

    def restrict_governance_directory_mode_0755_to_0700(
        self,
    ) -> PrivilegedAttemptResult: ...


class FakeAuthorizationServicesAdapter:
    """Intercepted test adapter.  It never invokes Authorization Services."""

    def __init__(self, result: AuthorizationAcquisitionResult) -> None:
        if type(result) is not AuthorizationAcquisitionResult:
            raise TypeError("result must be an AuthorizationAcquisitionResult")
        self._result = result
        self.calls = 0

    def acquire_exact_remediation_authorization(self) -> AuthorizationAcquisitionResult:
        self.calls += 1
        return self._result


class FakePrivilegedGovernanceRemediationAdapter:
    """Intercepted test adapter.  It performs no filesystem operation."""

    def __init__(
        self,
        result: PrivilegedAttemptResult | Exception,
    ) -> None:
        if not isinstance(result, (PrivilegedAttemptResult, Exception)):
            raise TypeError("result must be a PrivilegedAttemptResult or exception")
        self._result = result
        self.calls = 0

    def restrict_governance_directory_mode_0755_to_0700(self) -> PrivilegedAttemptResult:
        self.calls += 1
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


def orchestrate_bounded_governance_remediation(
    filesystem_plan: PreBootstrapFilesystemPlan,
    remediation: RemediationDecision,
    authorization_port: AuthorizationServicesPort,
    privileged_port: PrivilegedGovernanceRemediationPort,
) -> RemediationOrchestrationResult:
    """Validate, authorize, claim, attempt once, consume, and fail closed."""

    exact_eligible_plan = (
        type(remediation) is RemediationDecision
        and remediation.eligibility is RemediationEligibility.ELIGIBLE
        and remediation.plan is not None
        and validate_governance_remediation_plan(filesystem_plan, remediation.plan)
    )
    if not exact_eligible_plan:
        return _no_attempt(
            AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR
        )

    acquisition = authorization_port.acquire_exact_remediation_authorization()
    if type(acquisition) is not AuthorizationAcquisitionResult:
        return _no_attempt(AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR)
    presentation = acquisition.presentation
    evidence = (
        presentation.fresh_approval_evidence
        if type(presentation) is AuthorizationPresentation
        else _evidence_for_status(acquisition.status)
    )
    if acquisition.status is not AuthorizationAcquisitionStatus.ACQUIRED or presentation is None:
        return _no_attempt(acquisition.status, evidence)
    decision = authorize_remediation_attempt(filesystem_plan, remediation, presentation)
    if decision.disposition is not AuthorizationDisposition.AUTHORIZED:
        return _no_attempt(acquisition.status, evidence)
    claimed = claim_remediation_attempt(decision.authorization)
    if claimed is None:
        return _no_attempt(AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR)
    try:
        attempted = privileged_port.restrict_governance_directory_mode_0755_to_0700()
        if type(attempted) is not PrivilegedAttemptResult:
            raise TypeError("invalid privileged adapter result")
        outcome = AttemptOutcome[attempted.status.name]
        postcondition_ok = (
            attempted.status is PrivilegedAttemptStatus.SUCCESS
            and attempted.postcondition is not None
            and validate_remediation_postcondition(filesystem_plan, attempted.postcondition)
        )
        if attempted.status is PrivilegedAttemptStatus.SUCCESS and not postcondition_ok:
            outcome = AttemptOutcome.UNCERTAIN
            attempt_status = PrivilegedAttemptStatus.UNCERTAIN
        else:
            attempt_status = attempted.status
    except Exception:
        outcome = AttemptOutcome.UNCERTAIN
        attempt_status = PrivilegedAttemptStatus.UNCERTAIN
        postcondition_ok = False
    consumed = consume_remediation_attempt(claimed, outcome)
    return RemediationOrchestrationResult(
        acquisition.status, evidence, attempt_status, consumed, postcondition_ok
    )


def orchestrate_durable_governance_remediation(
    filesystem_plan: PreBootstrapFilesystemPlan,
    remediation: RemediationDecision,
    authorization_port: AuthorizationServicesPort,
    journal: PreBootstrapRemediationAttemptJournal,
    privileged_port: PrivilegedGovernanceRemediationPort,
) -> RemediationOrchestrationResult:
    """Execute only after a purpose-fixed durable claim; never retry mutation."""

    exact_eligible_plan = (
        type(remediation) is RemediationDecision
        and remediation.eligibility is RemediationEligibility.ELIGIBLE
        and remediation.plan is not None
        and validate_governance_remediation_plan(filesystem_plan, remediation.plan)
    )
    if not exact_eligible_plan:
        return _no_attempt(AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR)
    acquisition = authorization_port.acquire_exact_remediation_authorization()
    if type(acquisition) is not AuthorizationAcquisitionResult:
        return _no_attempt(AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR)
    presentation = acquisition.presentation
    evidence = (
        presentation.fresh_approval_evidence
        if type(presentation) is AuthorizationPresentation
        else _evidence_for_status(acquisition.status)
    )
    if (
        acquisition.status is not AuthorizationAcquisitionStatus.ACQUIRED
        or type(presentation) is not AuthorizationPresentation
        or type(acquisition.replay_key) is not AuthorizationReplayKey
    ):
        return _no_attempt(acquisition.status, evidence)
    decision = authorize_remediation_attempt(filesystem_plan, remediation, presentation)
    if decision.disposition is not AuthorizationDisposition.AUTHORIZED:
        return _no_attempt(acquisition.status, evidence)
    try:
        journal.claim_once(acquisition.replay_key)
    except (DurableJournalError, ReplayDenied, ValueError):
        return _no_attempt(AuthorizationAcquisitionStatus.ERROR, evidence)
    claimed = claim_remediation_attempt(decision.authorization)
    if claimed is None:
        return _no_attempt(AuthorizationAcquisitionStatus.ERROR, FreshApprovalEvidence.ERROR)
    try:
        attempted = privileged_port.restrict_governance_directory_mode_0755_to_0700()
    except Exception:
        attempted = PrivilegedAttemptResult(PrivilegedAttemptStatus.UNCERTAIN)
    if type(attempted) is not PrivilegedAttemptResult:
        attempted = PrivilegedAttemptResult(PrivilegedAttemptStatus.UNCERTAIN)
    postcondition_ok = (
        attempted.status is PrivilegedAttemptStatus.SUCCESS
        and attempted.postcondition is not None
        and validate_remediation_postcondition(filesystem_plan, attempted.postcondition)
    )
    status = attempted.status
    if status is PrivilegedAttemptStatus.SUCCESS and not postcondition_ok:
        status = PrivilegedAttemptStatus.UNCERTAIN
    outcome = AttemptOutcome[status.name]
    durable_state = DurableAttemptState[f"TERMINAL_{status.name}"]
    try:
        journal.record_terminal(acquisition.replay_key, durable_state)
    except (DurableJournalError, ValueError):
        status = PrivilegedAttemptStatus.UNCERTAIN
        outcome = AttemptOutcome.UNCERTAIN
        postcondition_ok = False
    consumed = consume_remediation_attempt(claimed, outcome)
    return RemediationOrchestrationResult(
        acquisition.status, evidence, status, consumed, postcondition_ok
    )


def orchestrate_fresh_human_governance_remediation(
    filesystem_plan: PreBootstrapFilesystemPlan,
    remediation: RemediationDecision,
    request_identity: str,
    authorization_port: AuthorizationServicesPort,
    challenge_issuer: FreshHumanChallengeIssuer,
    evidence_provider,
    signature_verifier: FreshHumanSignatureVerifier,
    expected_public_key_fingerprint: str,
    clock,
    journal: PreBootstrapRemediationAttemptJournal,
    privileged_port: PrivilegedGovernanceRemediationPort,
) -> RemediationOrchestrationResult:
    """Freeze eligibility -> authorization -> challenge -> evidence -> claim -> helper."""
    exact = (type(remediation) is RemediationDecision
             and remediation.eligibility is RemediationEligibility.ELIGIBLE
             and remediation.plan is not None
             and validate_governance_remediation_plan(filesystem_plan, remediation.plan))
    if not exact:
        return _no_human_attempt(AuthorizationAcquisitionStatus.ERROR,
                                 FreshHumanVerificationResult.DENIED,
                                 FreshApprovalEvidence.ERROR)
    acquisition = authorization_port.acquire_exact_remediation_authorization()
    if (type(acquisition) is not AuthorizationAcquisitionResult
            or acquisition.status is not AuthorizationAcquisitionStatus.ACQUIRED
            or type(acquisition.presentation) is not AuthorizationPresentation
            or type(acquisition.replay_key) is not AuthorizationReplayKey):
        status = acquisition.status if type(acquisition) is AuthorizationAcquisitionResult else AuthorizationAcquisitionStatus.ERROR
        return _no_human_attempt(status, FreshHumanVerificationResult.DENIED,
                                 _evidence_for_status(status))
    presentation_evidence = acquisition.presentation.fresh_approval_evidence
    decision = validate_bounded_remediation_authorization_presentation(
        filesystem_plan, remediation, acquisition.presentation)
    if decision.disposition is not AuthorizationDisposition.AUTHORIZED:
        return _no_human_attempt(acquisition.status, FreshHumanVerificationResult.DENIED,
                                 presentation_evidence)
    try:
        challenge = challenge_issuer.issue(request_identity=request_identity,
                                           replay_key=acquisition.replay_key)
        evidence = evidence_provider(challenge)
        verification = verify_fresh_human_evidence(
            evidence, expected_challenge=challenge,
            expected_replay_key=acquisition.replay_key,
            expected_public_key_fingerprint=expected_public_key_fingerprint,
            verifier=signature_verifier, now=clock(),
        )
    except Exception:
        return _no_human_attempt(acquisition.status, FreshHumanVerificationResult.ERROR,
                                 presentation_evidence)
    if verification is not FreshHumanVerificationResult.VERIFIED:
        return _no_human_attempt(acquisition.status, verification, presentation_evidence)
    try:
        journal.claim_once(acquisition.replay_key)
    except (DurableJournalError, ReplayDenied, ValueError):
        return _no_human_attempt(acquisition.status, verification, presentation_evidence)
    claimed = _create_claimed_bounded_remediation_attempt(
        decision, verification is FreshHumanVerificationResult.VERIFIED, True
    )
    if claimed is None:
        return _no_human_attempt(AuthorizationAcquisitionStatus.ERROR, verification,
                                 presentation_evidence)
    try:
        attempted = privileged_port.restrict_governance_directory_mode_0755_to_0700()
    except Exception:
        attempted = PrivilegedAttemptResult(PrivilegedAttemptStatus.UNCERTAIN)
    if type(attempted) is not PrivilegedAttemptResult:
        attempted = PrivilegedAttemptResult(PrivilegedAttemptStatus.UNCERTAIN)
    postcondition_ok = (attempted.status is PrivilegedAttemptStatus.SUCCESS
                        and attempted.postcondition is not None
                        and validate_remediation_postcondition(filesystem_plan, attempted.postcondition))
    status = attempted.status
    if status is PrivilegedAttemptStatus.SUCCESS and not postcondition_ok:
        status = PrivilegedAttemptStatus.UNCERTAIN
    try:
        journal.record_terminal(acquisition.replay_key,
                                DurableAttemptState[f"TERMINAL_{status.name}"])
    except (DurableJournalError, ValueError):
        status = PrivilegedAttemptStatus.UNCERTAIN
        postcondition_ok = False
    consumed = consume_remediation_attempt(claimed, AttemptOutcome[status.name])
    return RemediationOrchestrationResult(acquisition.status,
        acquisition.presentation.fresh_approval_evidence, status, consumed,
        postcondition_ok, verification)


def _no_human_attempt(status, verification, evidence):
    return RemediationOrchestrationResult(status, evidence,
                                          None, None, False, verification)


def _evidence_for_status(status: AuthorizationAcquisitionStatus) -> FreshApprovalEvidence:
    return {
        AuthorizationAcquisitionStatus.DENIED: FreshApprovalEvidence.DENIED,
        AuthorizationAcquisitionStatus.CANCELED: FreshApprovalEvidence.CANCELED,
        AuthorizationAcquisitionStatus.ERROR: FreshApprovalEvidence.ERROR,
    }.get(status, FreshApprovalEvidence.NOT_VERIFIABLE)


def _no_attempt(
    status: AuthorizationAcquisitionStatus,
    evidence: FreshApprovalEvidence,
) -> RemediationOrchestrationResult:
    return RemediationOrchestrationResult(status, evidence, None, None, False)


__all__ = (
    "AuthorizationAcquisitionResult", "AuthorizationAcquisitionStatus",
    "AuthorizationServicesPort", "FakeAuthorizationServicesAdapter",
    "FakePrivilegedGovernanceRemediationAdapter",
    "PrivilegedAttemptResult", "PrivilegedAttemptStatus",
    "PrivilegedGovernanceRemediationPort", "RemediationOrchestrationResult",
    "orchestrate_bounded_governance_remediation", "orchestrate_durable_governance_remediation",
    "orchestrate_fresh_human_governance_remediation",
)
