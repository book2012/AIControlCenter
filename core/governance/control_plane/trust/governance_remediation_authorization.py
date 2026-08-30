"""Pure authorization contract for the exact governance-mode remediation.

This module models policy only.  It does not call Authorization Services, carry
execution inputs, or confer filesystem mutation authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .governance_remediation import (
    RemediationDecision,
    RemediationEligibility,
    validate_governance_remediation_plan,
)
from .pre_bootstrap_filesystem import PreBootstrapFilesystemPlan


class RemediationAuthorizationPurpose(Enum):
    GOVERNANCE_DIRECTORY_MODE_0755_TO_0700 = (
        "GOVERNANCE_DIRECTORY_MODE_0755_TO_0700"
    )


class RemediationAuthorizationRight(Enum):
    PURPOSE_SPECIFIC_MACOS_RIGHT = (
        "com.aicontrolcenter.governance-remediation.mode-0755-to-0700"
    )


class FreshApprovalEvidence(Enum):
    """What can be proved about fresh human approval for this invocation."""

    VERIFIED = "VERIFIED"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"
    DENIED = "DENIED"
    CANCELED = "CANCELED"
    ERROR = "ERROR"


class AuthorizationDisposition(Enum):
    AUTHORIZED = "AUTHORIZED"
    DENIED = "DENIED"


class AttemptState(Enum):
    AVAILABLE = "AVAILABLE"
    CLAIMED = "CLAIMED"
    CONSUMED = "CONSUMED"


class AttemptOutcome(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    UNCERTAIN = "UNCERTAIN"


@dataclass(frozen=True, slots=True)
class AuthorizationPresentation:
    """Repository representation of a future Authorization Services result."""

    purpose: RemediationAuthorizationPurpose
    right: RemediationAuthorizationRight
    fresh_approval_evidence: FreshApprovalEvidence
    preauthorized: bool = False
    shared: bool = False
    reusable: bool = False
    retry: bool = False


@dataclass(frozen=True, slots=True)
class RemediationAttemptAuthorization:
    """Payload-free, purpose-fixed authority for exactly one attempt."""

    purpose: RemediationAuthorizationPurpose
    right: RemediationAuthorizationRight
    state: AttemptState
    outcome: AttemptOutcome | None = None


@dataclass(frozen=True, slots=True)
class RemediationAuthorizationDecision:
    disposition: AuthorizationDisposition
    authorization: RemediationAttemptAuthorization | None = None


@dataclass(frozen=True, slots=True)
class BoundedRemediationPresentationValidation:
    """Non-authoritative result of exact bounded-presentation validation."""

    disposition: AuthorizationDisposition


def authorize_remediation_attempt(
    filesystem_plan: PreBootstrapFilesystemPlan,
    remediation: RemediationDecision,
    presentation: AuthorizationPresentation,
) -> RemediationAuthorizationDecision:
    """Accept only a fresh, dedicated approval for an exact eligible plan."""

    exact_presentation = (
        type(presentation) is AuthorizationPresentation
        and presentation.purpose
        is RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700
        and presentation.right
        is RemediationAuthorizationRight.PURPOSE_SPECIFIC_MACOS_RIGHT
        and presentation.fresh_approval_evidence is FreshApprovalEvidence.VERIFIED
        and presentation.preauthorized is False
        and presentation.shared is False
        and presentation.reusable is False
        and presentation.retry is False
    )
    exact_remediation = (
        type(remediation) is RemediationDecision
        and remediation.eligibility is RemediationEligibility.ELIGIBLE
        and remediation.plan is not None
        and validate_governance_remediation_plan(filesystem_plan, remediation.plan)
    )
    if not exact_presentation or not exact_remediation:
        return RemediationAuthorizationDecision(AuthorizationDisposition.DENIED)
    return RemediationAuthorizationDecision(
        AuthorizationDisposition.AUTHORIZED,
        RemediationAttemptAuthorization(
            presentation.purpose,
            presentation.right,
            AttemptState.AVAILABLE,
        ),
    )


def validate_bounded_remediation_authorization_presentation(
    filesystem_plan: PreBootstrapFilesystemPlan,
    remediation: RemediationDecision,
    presentation: AuthorizationPresentation,
) -> BoundedRemediationPresentationValidation:
    """Validate only the bounded Authorization Services presentation.

    This purpose-specific composite-path boundary does not treat Authorization
    Services as proof of fresh human presence.  Independent fresh-human evidence
    remains required, as does a durable replay claim, before an attempt authority
    may be created in the claimed state.
    """

    exact_presentation = (
        type(presentation) is AuthorizationPresentation
        and presentation.purpose
        is RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700
        and presentation.right
        is RemediationAuthorizationRight.PURPOSE_SPECIFIC_MACOS_RIGHT
        and presentation.fresh_approval_evidence
        in (FreshApprovalEvidence.VERIFIED, FreshApprovalEvidence.NOT_VERIFIABLE)
        and presentation.preauthorized is False
        and presentation.shared is False
        and presentation.reusable is False
        and presentation.retry is False
    )
    exact_remediation = (
        type(remediation) is RemediationDecision
        and remediation.eligibility is RemediationEligibility.ELIGIBLE
        and remediation.plan is not None
        and validate_governance_remediation_plan(filesystem_plan, remediation.plan)
    )
    if not exact_presentation or not exact_remediation:
        return BoundedRemediationPresentationValidation(
            AuthorizationDisposition.DENIED
        )
    return BoundedRemediationPresentationValidation(
        AuthorizationDisposition.AUTHORIZED
    )


def _create_claimed_bounded_remediation_attempt(
    validation: BoundedRemediationPresentationValidation,
    fresh_human_evidence_verified: bool,
    durable_claim_succeeded: bool,
) -> RemediationAttemptAuthorization | None:
    """Create the exact claimed attempt only after both independent gates."""

    if (
        type(validation) is not BoundedRemediationPresentationValidation
        or validation.disposition is not AuthorizationDisposition.AUTHORIZED
        or fresh_human_evidence_verified is not True
        or durable_claim_succeeded is not True
    ):
        return None
    return RemediationAttemptAuthorization(
        RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700,
        RemediationAuthorizationRight.PURPOSE_SPECIFIC_MACOS_RIGHT,
        AttemptState.CLAIMED,
    )


def claim_remediation_attempt(
    authorization: RemediationAttemptAuthorization,
) -> RemediationAttemptAuthorization | None:
    """Claim the sole attempt; an already claimed/consumed grant is unusable."""

    if (
        type(authorization) is not RemediationAttemptAuthorization
        or authorization.purpose
        is not RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700
        or authorization.right
        is not RemediationAuthorizationRight.PURPOSE_SPECIFIC_MACOS_RIGHT
        or authorization.state is not AttemptState.AVAILABLE
        or authorization.outcome is not None
    ):
        return None
    return RemediationAttemptAuthorization(
        authorization.purpose, authorization.right, AttemptState.CLAIMED
    )


def consume_remediation_attempt(
    authorization: RemediationAttemptAuthorization,
    outcome: AttemptOutcome,
) -> RemediationAttemptAuthorization | None:
    """Make every terminal result permanently consuming, including uncertainty."""

    if (
        type(authorization) is not RemediationAttemptAuthorization
        or type(outcome) is not AttemptOutcome
        or authorization.purpose
        is not RemediationAuthorizationPurpose.GOVERNANCE_DIRECTORY_MODE_0755_TO_0700
        or authorization.right
        is not RemediationAuthorizationRight.PURPOSE_SPECIFIC_MACOS_RIGHT
        or authorization.state is not AttemptState.CLAIMED
        or authorization.outcome is not None
    ):
        return None
    return RemediationAttemptAuthorization(
        authorization.purpose, authorization.right, AttemptState.CONSUMED, outcome
    )


__all__ = (
    "AttemptOutcome", "AttemptState", "FreshApprovalEvidence",
    "AuthorizationDisposition", "AuthorizationPresentation",
    "BoundedRemediationPresentationValidation", "RemediationAttemptAuthorization",
    "RemediationAuthorizationDecision",
    "RemediationAuthorizationPurpose", "RemediationAuthorizationRight",
    "authorize_remediation_attempt", "claim_remediation_attempt",
    "consume_remediation_attempt",
    "validate_bounded_remediation_authorization_presentation",
)
