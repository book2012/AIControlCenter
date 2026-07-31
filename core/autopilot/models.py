"""Immutable JSON-first contracts for AUTO-01."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, NewType

from core.deployment.contracts import canonical_json_bytes, sha256_digest

SprintTaskId = NewType("SprintTaskId", str)


class AutopilotPolicyError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class AutonomyLevel(StrEnum):
    L0_OBSERVE = "L0_OBSERVE"
    L1_PLAN = "L1_PLAN"
    L2_TEST_ONLY_IMPLEMENT = "L2_TEST_ONLY_IMPLEMENT"
    L3_GIT_CLOSEOUT = "L3_GIT_CLOSEOUT"
    L4_CONTROLLED_OPERATIONAL_WRITE = "L4_CONTROLLED_OPERATIONAL_WRITE"
    L5_PRODUCTION_ACTIVATION = "L5_PRODUCTION_ACTIVATION"


class DeliveryRunState(StrEnum):
    PLANNED = "PLANNED"
    PREFLIGHT = "PREFLIGHT"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    DOCUMENTING = "DOCUMENTING"
    COMMITTING = "COMMITTING"
    PUSHING = "PUSHING"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"
    FAILED_CLOSED = "FAILED_CLOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    CANCELLED = "CANCELLED"


class DeliveryGateType(StrEnum):
    GIT = "GIT"
    TEST = "TEST"
    DOCUMENTATION = "DOCUMENTATION"
    APPROVAL = "APPROVAL"
    EVIDENCE = "EVIDENCE"
    REMOTE_VERIFICATION = "REMOTE_VERIFICATION"


class ApprovalRequirement(StrEnum):
    NONE = "NONE"
    INDEPENDENT_HUMAN = "INDEPENDENT_HUMAN"
    OPERATIONAL_WRITE = "OPERATIONAL_WRITE"
    PRODUCTION = "PRODUCTION"
    POST_CLAIM_RECOVERY = "POST_CLAIM_RECOVERY"


class ApprovalState(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REQUIRED = "REQUIRED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CONSUMED = "CONSUMED"


class RetryClassification(StrEnum):
    SAFE_PREFLIGHT_RETRY = "SAFE_PREFLIGHT_RETRY"
    SAFE_PRE_CLAIM_RECOVERY = "SAFE_PRE_CLAIM_RECOVERY"
    MANUAL_POST_CLAIM_RECOVERY = "MANUAL_POST_CLAIM_RECOVERY"
    NO_RETRY = "NO_RETRY"


class AutonomousDeliveryArchitectureDecision(StrEnum):
    READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE = (
        "READY_FOR_PERSISTENT_RUNNER_ARCHITECTURE"
    )


@dataclass(frozen=True, slots=True)
class SprintDependency:
    task_id: SprintTaskId


@dataclass(frozen=True, slots=True)
class SprintBaseline:
    branch: str
    commit: str


@dataclass(frozen=True, slots=True)
class SprintScopePolicy:
    allowed_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    allowed_dependency_zones: tuple[str, ...]
    forbidden_dependency_zones: tuple[str, ...]
    wildcard_paths_explicitly_approved: bool = False


@dataclass(frozen=True, slots=True)
class GitGatePolicy:
    require_clean_tree: bool = True
    require_exact_baseline: bool = True
    require_upstream_sync: bool = True
    require_commit_evidence: bool = True
    require_remote_commit_verification: bool = True


@dataclass(frozen=True, slots=True)
class TestGatePolicy:
    required_commands: tuple[str, ...]
    require_zero_failures: bool = True


@dataclass(frozen=True, slots=True)
class DocumentationGatePolicy:
    required_documents: tuple[str, ...]
    require_status_documents: bool = True


@dataclass(frozen=True, slots=True)
class ApprovalGatePolicy:
    requirement: ApprovalRequirement = ApprovalRequirement.NONE
    state: ApprovalState = ApprovalState.NOT_REQUIRED
    independent_approver_required: bool = False
    environment_authorization_allowed: bool = False


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    preflight_retry_allowed: bool = True
    pre_claim_recovery_requires_evidence: bool = True
    automatic_post_claim_retry_allowed: bool = False
    post_claim_human_approval_required: bool = True


@dataclass(frozen=True, slots=True)
class EvidencePolicy:
    required_evidence: tuple[str, ...]
    immutable_transition_evidence: bool = True
    completion_requires_remote_verification: bool = True


@dataclass(frozen=True, slots=True)
class SprintManifest:
    schema_version: str
    task_id: SprintTaskId
    title: str
    milestone: str
    baseline: SprintBaseline
    dependencies: tuple[SprintDependency, ...]
    autonomy_level: AutonomyLevel
    maximum_autonomy_level: AutonomyLevel
    test_only: bool
    operational_write_allowed: bool
    production: bool
    ubuntu_participation: str
    scope: SprintScopePolicy
    git_gates: GitGatePolicy
    test_gates: TestGatePolicy
    documentation_gates: DocumentationGatePolicy
    approval: ApprovalGatePolicy
    retry: RetryPolicy
    evidence: EvidencePolicy
    commit_policy: str
    next_task_policy: str
    forbidden_operations: tuple[str, ...]
    control_plane_owner: str = "AIControlCenter"
    governance_authority: str = "AIControlCenter"
    approval_authority: str = "AIControlCenter"
    retry_authority: str = "AIControlCenter"
    executor_identity: str = "Codex"
    secret_dependencies: tuple[str, ...] = ()
    canonical_manifest_digest: str = ""

    def payload(self) -> dict[str, Any]:
        value = _json_value(self)
        value.pop("canonical_manifest_digest")
        return value

    def canonical_json(self) -> str:
        return canonical_json_bytes(_json_value(self)).decode()

    def calculated_digest(self) -> str:
        return sha256_digest(self.payload())


@dataclass(frozen=True, slots=True)
class SprintManifestValidationResult:
    valid: bool
    errors: tuple[str, ...]
    canonical_json: str
    digest: str


@dataclass(frozen=True, slots=True)
class DeliveryPlanStep:
    sequence: int
    task_id: SprintTaskId
    blocked: bool
    blockers: tuple[str, ...]
    approval_is_authorization: bool = False
    activation_authorized: bool = False


@dataclass(frozen=True, slots=True)
class DeliveryPlan:
    steps: tuple[DeliveryPlanStep, ...]
    decision: AutonomousDeliveryArchitectureDecision
    production_authorized: bool = False
    operational_actions_authorized: int = 0
    plan_digest: str = ""

    def payload(self) -> dict[str, Any]:
        value = _json_value(self)
        value.pop("plan_digest")
        return value

    def canonical_json(self) -> str:
        return canonical_json_bytes(_json_value(self)).decode()


@dataclass(frozen=True, slots=True)
class DeliveryTransition:
    from_state: DeliveryRunState
    to_state: DeliveryRunState
    evidence: tuple[str, ...]
    exact_baseline_verified: bool = False
    tests_passed: bool = False
    documentation_passed: bool = False
    commit_evidence_present: bool = False
    remote_commit_verified: bool = False
    automatic: bool = True


@dataclass(frozen=True, slots=True)
class DeliveryRunSnapshot:
    task_id: SprintTaskId
    state: DeliveryRunState
    transitions: tuple[DeliveryTransition, ...] = ()
    completed_gates: tuple[DeliveryGateType, ...] = ()


@dataclass(frozen=True, slots=True)
class DeliveryDecision:
    allowed: bool
    code: str
    next_state: DeliveryRunState


@dataclass(frozen=True, slots=True)
class ExecutorRequest:
    executor_identity: str
    task_id: SprintTaskId
    allowed_paths: tuple[str, ...]
    forbidden_operations: tuple[str, ...]
    expected_result_schema: str
    event_stream_reference: str


@dataclass(frozen=True, slots=True)
class ExecutorResult:
    executor_identity: str
    task_id: SprintTaskId
    succeeded: bool
    final_json: str
    event_stream_reference: str
    side_effects_claimed: tuple[str, ...] = ()


def _json_value(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: _json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
