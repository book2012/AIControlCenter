"""Immutable M3-A4B2B1B human-approval and permit-issuance contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import re
from typing import Any, Mapping

from core.deployment.operational_bootstrap_authorization import (
    OperationalBootstrapApproval,
    OperationalBootstrapAuthorizationRequest,
    OperationalBootstrapPermit,
)
from core.deployment.operational_permit_issuance import (
    OperationalPermitIssuanceReviewPackage,
    canonical_digest,
    parse_timestamp,
)


class OperationalPermitApprovalError(ValueError):
    """Fail-closed error containing a stable, non-sensitive reason."""


class OperationalPermitApprovalStage(StrEnum):
    HUMAN_APPROVAL_AND_PERMIT_ISSUANCE_REVIEW = "HUMAN_APPROVAL_AND_PERMIT_ISSUANCE_REVIEW"


class OperationalPermitIdentityRole(StrEnum):
    REQUESTER = "REQUESTER"
    MAC_OPERATOR = "MAC_OPERATOR"
    INDEPENDENT_APPROVER = "INDEPENDENT_APPROVER"


class OperationalPermitApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


class OperationalPermitApprovalStatus(StrEnum):
    PASS = "PASS"
    DENIED = "DENIED"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_PLACEHOLDER = re.compile(r"^(anonymous|unknown|none|null|n/?a|unassigned)$", re.I)
_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|executable|email|"
    r"phone|webhook|https?://", re.I,
)


def _digest(value: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise OperationalPermitApprovalError("CANONICAL_DIGEST_REQUIRED")


def _safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) != "runtime_infrastructure_commands" and _FORBIDDEN.search(str(key)):
                raise OperationalPermitApprovalError("UNSAFE_INPUT_REJECTED")
            _safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            _safe(child)
    elif isinstance(value, str) and _FORBIDDEN.search(value):
        raise OperationalPermitApprovalError("UNSAFE_INPUT_REJECTED")


@dataclass(frozen=True, slots=True, order=True)
class OperationalPermitIdentity:
    identity_id: str
    identity_type: str
    local_account_binding: str | None
    display_label: str
    role: OperationalPermitIdentityRole
    attested_by: str
    attested_at: str
    placeholder: bool = False
    synthetic: bool = False

    def __post_init__(self) -> None:
        parse_timestamp(self.attested_at)
        _safe(asdict(self))
        if (not self.identity_id or not self.identity_type or not self.display_label
                or not self.attested_by or self.placeholder
                or _PLACEHOLDER.fullmatch(self.identity_id.strip())):
            raise OperationalPermitApprovalError("IDENTITY_INVALID")


@dataclass(frozen=True, slots=True, order=True)
class OperationalPermitRestrictionAcknowledgement:
    restriction_id: str
    source_report_id: str
    source_report_digest: str
    exact_summary_digest: str
    severity: str
    remediation_reference: str
    acknowledging_identity_id: str
    acknowledgement_decision: OperationalPermitApprovalDecision
    acknowledged_at: str
    canonical_acknowledgement_digest: str
    synthetic: bool = False

    def __post_init__(self) -> None:
        parse_timestamp(self.acknowledged_at)
        _digest(self.source_report_digest)
        _digest(self.exact_summary_digest)
        _digest(self.canonical_acknowledgement_digest)
        _safe(asdict(self))
        if self.acknowledgement_decision is not OperationalPermitApprovalDecision.APPROVED:
            raise OperationalPermitApprovalError("ACKNOWLEDGEMENT_NOT_APPROVED")

    def content(self) -> dict[str, Any]:
        value = asdict(self)
        value.pop("canonical_acknowledgement_digest")
        return value


@dataclass(frozen=True, slots=True)
class OperationalPermitExecutionWindow:
    approval_timestamp: str
    issuance_timestamp: str
    not_before_timestamp: str
    expires_at_timestamp: str
    bootstrap_execution_deadline: str
    maximum_permit_ttl_seconds: int
    maximum_approval_to_issuance_seconds: int
    maximum_issuance_to_claim_seconds: int
    maximum_execution_duration_seconds: int
    maximum_uses: int = 1

    def __post_init__(self) -> None:
        times = tuple(parse_timestamp(getattr(self, name)) for name in (
            "approval_timestamp", "issuance_timestamp", "not_before_timestamp",
            "expires_at_timestamp", "bootstrap_execution_deadline"))
        durations = (
            self.maximum_permit_ttl_seconds, self.maximum_approval_to_issuance_seconds,
            self.maximum_issuance_to_claim_seconds, self.maximum_execution_duration_seconds)
        if any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in durations):
            raise OperationalPermitApprovalError("EXECUTION_WINDOW_UNBOUNDED")
        if self.maximum_uses != 1:
            raise OperationalPermitApprovalError("MAXIMUM_USES_MUST_EQUAL_ONE")
        approved, issued, not_before, expires, deadline = times
        if not (approved <= issued <= not_before < deadline <= expires):
            raise OperationalPermitApprovalError("EXECUTION_WINDOW_CONTRADICTORY")
        if ((issued - approved).total_seconds() > self.maximum_approval_to_issuance_seconds
                or (expires - issued).total_seconds() > self.maximum_permit_ttl_seconds
                or (deadline - not_before).total_seconds() > self.maximum_execution_duration_seconds):
            raise OperationalPermitApprovalError("EXECUTION_WINDOW_EXCEEDS_POLICY")


@dataclass(frozen=True, slots=True)
class OperationalPermitApprovalConfig:
    approved_branch: str
    approved_commit: str
    required_warning_restriction_id: str = "warnings-427"
    stage: OperationalPermitApprovalStage = (
        OperationalPermitApprovalStage.HUMAN_APPROVAL_AND_PERMIT_ISSUANCE_REVIEW)
    environment: str = "CONTROLLED_NON_PRODUCTION"
    maximum_uses: int = 1
    production_authorized: bool = False

    def __post_init__(self) -> None:
        if self.stage is not OperationalPermitApprovalStage.HUMAN_APPROVAL_AND_PERMIT_ISSUANCE_REVIEW:
            raise OperationalPermitApprovalError("PRIVILEGED_STAGE_REJECTED")
        if (self.approved_branch != "feature/deployment-package"
                or not _COMMIT.fullmatch(self.approved_commit)
                or self.environment != "CONTROLLED_NON_PRODUCTION"
                or self.maximum_uses != 1 or self.production_authorized):
            raise OperationalPermitApprovalError("CONFIGURATION_REJECTED")


@dataclass(frozen=True, slots=True)
class OperationalPermitApprovalInput:
    review_package: OperationalPermitIssuanceReviewPackage
    requester: OperationalPermitIdentity
    mac_operator: OperationalPermitIdentity
    independent_approver: OperationalPermitIdentity | None
    approval_decision: OperationalPermitApprovalDecision
    restriction_acknowledgements: tuple[OperationalPermitRestrictionAcknowledgement, ...]
    execution_window: OperationalPermitExecutionWindow | None
    evaluated_at: str


@dataclass(frozen=True, slots=True, order=True)
class OperationalPermitApprovalCheck:
    code: str
    status: OperationalPermitApprovalStatus


@dataclass(frozen=True, slots=True, order=True)
class OperationalPermitApprovalFinding:
    code: str
    severity: str = "ERROR"


@dataclass(frozen=True, slots=True)
class OperationalPermitApprovalReport:
    report_id: str
    report_digest: str
    stage: OperationalPermitApprovalStage
    decision: OperationalPermitApprovalDecision
    status: OperationalPermitApprovalStatus
    checks: tuple[OperationalPermitApprovalCheck, ...]
    findings: tuple[OperationalPermitApprovalFinding, ...]
    identity_ids: tuple[str, ...]
    acknowledgement_digests: tuple[str, ...]
    effective_execution_window: bool
    operational_permit_issued: bool = False
    bootstrap_authorized: bool = False
    production_authorized: bool = False


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceRequest:
    approval_input: OperationalPermitApprovalInput
    authorization_request: OperationalBootstrapAuthorizationRequest
    authorization_approval: OperationalBootstrapApproval
    decided_at: str
    issued_at: str
    permit_claim_requested: bool = False
    bootstrap_execution_requested: bool = False
    production_authorized: bool = False


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceResult:
    approval_report: OperationalPermitApprovalReport
    authorization_decision_id: str | None
    synthetic_permit: OperationalBootstrapPermit | None
    operational_permit_issued: bool = False
    permit_claimed: bool = False
    bootstrap_executed: bool = False
    production_authorized: bool = False
