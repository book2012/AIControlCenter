"""Pure immutable M3-A4B2B1A operational permit issuance review contracts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping


class OperationalPermitIssuanceError(ValueError):
    """Fail-closed error containing only a stable reason code."""


class OperationalPermitIssuanceStage(StrEnum):
    OPERATIONAL_PERMIT_ISSUANCE_REVIEW = "OPERATIONAL_PERMIT_ISSUANCE_REVIEW"


class OperationalPermitIssuanceStatus(StrEnum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


class OperationalPermitIssuanceDecision(StrEnum):
    READY_FOR_OPERATOR_AND_APPROVER_REVIEW = "READY_FOR_OPERATOR_AND_APPROVER_REVIEW"
    READY_WITH_RESTRICTIONS = "READY_WITH_RESTRICTIONS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_FORBIDDEN = re.compile(
    r"password|api.?key|access.?token|private.?key|cookie|authorization.?header|"
    r"raw.?environment|raw.?nonce|shell|command|argv|script|executable|"
    r"email|phone|webhook|https?://",
    re.I,
)


def parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise OperationalPermitIssuanceError("EXPLICIT_TIMESTAMP_REQUIRED") from exc
    if parsed.tzinfo is None:
        raise OperationalPermitIssuanceError("TIMESTAMP_TIMEZONE_REQUIRED")
    return parsed


def require_digest(value: str) -> None:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise OperationalPermitIssuanceError("CANONICAL_DIGEST_REQUIRED")


def validate_safe(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if (str(key) != "runtime_infrastructure_commands"
                    and _FORBIDDEN.search(str(key))):
                raise OperationalPermitIssuanceError("UNSAFE_EVIDENCE_REJECTED")
            validate_safe(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            validate_safe(child)
    elif isinstance(value, str):
        if _FORBIDDEN.search(value):
            raise OperationalPermitIssuanceError("UNSAFE_EVIDENCE_REJECTED")
    elif not isinstance(value, (int, bool, type(None), StrEnum)):
        raise OperationalPermitIssuanceError("UNSUPPORTED_EVIDENCE_REJECTED")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class OperationalPermitExecutionWindow:
    maximum_permit_ttl_seconds: int
    maximum_approval_to_issuance_seconds: int
    maximum_issuance_to_claim_seconds: int
    maximum_bootstrap_execution_seconds: int
    maximum_uses: int = 1
    environment: str = "CONTROLLED_NON_PRODUCTION"

    def __post_init__(self) -> None:
        durations = (
            self.maximum_permit_ttl_seconds,
            self.maximum_approval_to_issuance_seconds,
            self.maximum_issuance_to_claim_seconds,
            self.maximum_bootstrap_execution_seconds,
        )
        if any(not isinstance(item, int) or isinstance(item, bool) or not 0 < item <= 2_592_000
               for item in durations):
            raise OperationalPermitIssuanceError("EXECUTION_WINDOW_UNBOUNDED")
        if self.maximum_uses != 1:
            raise OperationalPermitIssuanceError("MAXIMUM_USES_MUST_EQUAL_ONE")
        if self.environment != "CONTROLLED_NON_PRODUCTION":
            raise OperationalPermitIssuanceError("NON_PRODUCTION_SCOPE_REQUIRED")


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceConfig:
    approved_branch: str
    approved_commit: str
    execution_window: OperationalPermitExecutionWindow
    stage: OperationalPermitIssuanceStage = (
        OperationalPermitIssuanceStage.OPERATIONAL_PERMIT_ISSUANCE_REVIEW
    )
    production_authorized: bool = False
    permit_issuance_requested: bool = False
    permit_claim_requested: bool = False
    bootstrap_execution_requested: bool = False

    def __post_init__(self) -> None:
        if self.stage is not OperationalPermitIssuanceStage.OPERATIONAL_PERMIT_ISSUANCE_REVIEW:
            raise OperationalPermitIssuanceError("PRIVILEGED_STAGE_REJECTED")
        if not self.approved_branch or self.approved_branch in {"main", "master", "production"}:
            raise OperationalPermitIssuanceError("APPROVED_FEATURE_BRANCH_REQUIRED")
        if not _COMMIT.fullmatch(self.approved_commit):
            raise OperationalPermitIssuanceError("APPROVED_COMMIT_REQUIRED")
        if self.production_authorized:
            raise OperationalPermitIssuanceError("PRODUCTION_AUTHORIZATION_REJECTED")
        if self.permit_issuance_requested:
            raise OperationalPermitIssuanceError("PERMIT_ISSUANCE_REQUEST_REJECTED")
        if self.permit_claim_requested:
            raise OperationalPermitIssuanceError("PERMIT_CLAIM_REQUEST_REJECTED")
        if self.bootstrap_execution_requested:
            raise OperationalPermitIssuanceError("BOOTSTRAP_EXECUTION_REQUEST_REJECTED")


@dataclass(frozen=True, slots=True)
class OperationalPermitRestrictionReview:
    restriction_id: str
    source_report_id: str
    source_report_digest: str
    reason_code: str
    canonical_summary_digest: str
    severity: str
    blocking: bool
    remediation_reference: str
    acknowledgement_required: bool = True
    acknowledgement_supplied: bool = False

    def __post_init__(self) -> None:
        require_digest(self.source_report_digest)
        require_digest(self.canonical_summary_digest)
        validate_safe(asdict(self))
        if not all((self.restriction_id, self.source_report_id, self.reason_code,
                    self.severity, self.remediation_reference)):
            raise OperationalPermitIssuanceError("RESTRICTION_BINDING_INCOMPLETE")
        if not self.acknowledgement_required or self.acknowledgement_supplied:
            raise OperationalPermitIssuanceError("HUMAN_ACKNOWLEDGEMENT_MUST_REMAIN_MISSING")


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceEvidence:
    evidence_id: str
    evidence_generated_at: str
    branch: str
    commit: str
    readiness_report_id: str
    readiness_report_digest: str
    readiness_decision: str
    authorization_closure_id: str
    authorization_closure_digest: str
    permit_contract_digest: str
    executor_report_id: str
    executor_report_digest: str
    executor_validation_passed: bool
    audit_bootstrap_validation_passed: bool
    replay_bootstrap_validation_passed: bool
    baseline_backup_restore_validation_passed: bool
    failure_cleanup_validation_passed: bool
    preflight_report_id: str
    preflight_report_digest: str
    preflight_decision: str
    darwin_control_plane: bool
    operational_targets_absent: bool
    filesystem_policy_passed: bool
    capacity_passed: bool
    permission_feasibility_passed: bool
    full_regression_passed: int
    full_regression_failed: int
    deployment_tests_passed: int
    deployment_tests_failed: int
    git_clean: bool
    upstream_ahead: int
    upstream_behind: int
    safety_counters: Mapping[str, int]
    binding_digests: Mapping[str, str]
    restrictions: tuple[OperationalPermitRestrictionReview, ...]
    permit_contract_available: bool = True
    ubuntu_participation: bool = False
    production_authorized: bool = False

    def __post_init__(self) -> None:
        parse_timestamp(self.evidence_generated_at)
        validate_safe(asdict(self))
        for value in (
            self.readiness_report_digest, self.authorization_closure_digest,
            self.permit_contract_digest, self.executor_report_digest,
            self.preflight_report_digest, *self.binding_digests.values(),
        ):
            require_digest(value)
        if not _COMMIT.fullmatch(self.commit):
            raise OperationalPermitIssuanceError("EVIDENCE_COMMIT_INVALID")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0
               for value in self.safety_counters.values()):
            raise OperationalPermitIssuanceError("SAFETY_COUNTER_INVALID")
        object.__setattr__(self, "safety_counters", dict(sorted(self.safety_counters.items())))
        object.__setattr__(self, "binding_digests", dict(sorted(self.binding_digests.items())))
        object.__setattr__(self, "restrictions", tuple(sorted(
            self.restrictions, key=lambda item: (item.restriction_id, item.reason_code))))


@dataclass(frozen=True, slots=True)
class OperationalPermitOperatorRequirement:
    code: str
    required: bool = True
    supplied: bool = False


@dataclass(frozen=True, slots=True)
class OperationalPermitApprovalRequirement:
    code: str
    required: bool = True
    supplied: bool = False


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceCheck:
    code: str
    status: OperationalPermitIssuanceStatus
    reason_codes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, order=True)
class OperationalPermitIssuanceFinding:
    code: str
    severity: str


OperationalPermitIssuanceRestriction = OperationalPermitRestrictionReview


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceReviewPackage:
    review_package_id: str
    stage: OperationalPermitIssuanceStage
    decision: OperationalPermitIssuanceDecision
    evaluated_at: str
    branch: str
    commit: str
    bound_report_ids_and_digests: Mapping[str, Mapping[str, str]]
    target_schema_plan_binding_digests: Mapping[str, str]
    checks: tuple[OperationalPermitIssuanceCheck, ...]
    findings: tuple[OperationalPermitIssuanceFinding, ...]
    restrictions: tuple[OperationalPermitRestrictionReview, ...]
    missing_human_approvals: tuple[str, ...]
    operator_requirements: tuple[OperationalPermitOperatorRequirement, ...]
    approver_requirements: tuple[OperationalPermitApprovalRequirement, ...]
    execution_window_policy: OperationalPermitExecutionWindow
    safety_snapshot: Mapping[str, int]
    canonical_package_digest: str
    permit_contract_available: bool = True
    operational_permit_issued: bool = False
    permit_claimed: bool = False
    bootstrap_authorized: bool = False
    bootstrap_executed: bool = False
    writers_authorized: bool = False
    monitoring_authorized: bool = False
    external_dispatch_authorized: bool = False
    production_authorized: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    @property
    def canonical_json(self) -> str:
        return canonical_json(self)


@dataclass(frozen=True, slots=True)
class OperationalPermitIssuanceValidationReport:
    status: OperationalPermitIssuanceStatus
    decision: OperationalPermitIssuanceDecision
    findings: tuple[OperationalPermitIssuanceFinding, ...]
    report_id: str
    report_digest: str
    operational_permit_issued: bool = False
    permit_claimed: bool = False
    bootstrap_authorized: bool = False
    bootstrap_executed: bool = False
    writers_authorized: bool = False
    monitoring_authorized: bool = False
    external_dispatch_authorized: bool = False
    production_authorized: bool = False
