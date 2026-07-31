"""Immutable M4-A1 controlled activation architecture contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from core.deployment.contracts import canonical_json_bytes


TASK = "M4-A1"
BRANCH = "feature/deployment-package"
BASELINE_COMMIT = "89d10da82545e6cfd173085719076bb71e14c120"
M3_READINESS = "READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION"


class ControlledActivationArchitectureError(ValueError):
    """Stable default-deny architecture validation error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ControlledActivationCapability(StrEnum):
    AUDIT_WRITER = "AUDIT_WRITER"
    REPLAY_WRITER = "REPLAY_WRITER"
    MONITORING_RUNTIME = "MONITORING_RUNTIME"
    ALERT_DISPATCH = "ALERT_DISPATCH"
    EXTERNAL_NOTIFICATION = "EXTERNAL_NOTIFICATION"


class ControlledActivationState(StrEnum):
    INACTIVE = "INACTIVE"
    REQUESTED = "REQUESTED"
    INDEPENDENTLY_APPROVED = "INDEPENDENTLY_APPROVED"
    AUTHORIZED = "AUTHORIZED"
    PERMITTED = "PERMITTED"
    CLAIMED = "CLAIMED"
    CONTROLLED_ACTIVE = "CONTROLLED_ACTIVE"
    VALIDATED = "VALIDATED"
    DEACTIVATED = "DEACTIVATED"
    BLOCKED = "BLOCKED"
    FAILED_CLOSED = "FAILED_CLOSED"


class ControlledActivationArchitectureDecision(StrEnum):
    READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS = (
        "READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS"
    )


@dataclass(frozen=True, slots=True)
class ControlledActivationCapabilityDefinition:
    identifier: ControlledActivationCapability
    control_plane_owner: str
    default_state: ControlledActivationState
    default_authorized: bool
    risk_classification: str
    requires_independent_approval: bool
    requires_single_use_permit: bool
    requires_atomic_claim: bool
    requires_rollback_evidence: bool
    production_eligible: bool
    ubuntu_eligible: bool
    external_side_effect_classification: str
    dependency_requirements: tuple[ControlledActivationCapability, ...]
    read_only_health_dependencies: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return _as_json_dict(self)

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()


@dataclass(frozen=True, slots=True)
class ControlledActivationArchitectureConfig:
    branch: str = BRANCH
    commit: str = BASELINE_COMMIT
    m3_readiness_binding: str = M3_READINESS
    production_authorized: bool = False
    ubuntu_participation: bool = False
    control_plane_owner: str = "AIControlCenter"
    authorization_owner: str = "AIControlCenter"
    state_owner: str = "AIControlCenter"
    live_control_scope: str = "MAC_CONTROLLED_NON_PRODUCTION"
    activation_authority: str = "AIControlCenter"
    governance_authority: str = "AIControlCenter"
    business_logic_authority: str = "AIControlCenter"
    environment_only_activation: bool = False
    arbitrary_command_execution: bool = False
    runtime_subprocess_execution: bool = False


@dataclass(frozen=True, slots=True)
class ControlledActivationArchitecturePolicy:
    capabilities_default_inactive: bool = True
    capabilities_default_unauthorized: bool = True
    independent_capability_authorization_required: bool = True
    implicit_capability_escalation_prohibited: bool = True
    dependency_satisfaction_is_authorization: bool = False
    exact_git_binding_required: bool = True
    required_evidence_per_transition: bool = True
    single_use_permit_required: bool = True
    atomic_claim_required: bool = True
    rollback_evidence_required: bool = True
    production_scope_prohibited: bool = True
    ubuntu_delegation_prohibited: bool = True
    environment_only_activation_prohibited: bool = True
    api_route_activation_authority_prohibited: bool = True
    external_governance_authority_prohibited: bool = True
    runtime_execution_prohibited: bool = True


@dataclass(frozen=True, slots=True)
class ControlledActivationPlanRequest:
    branch: str
    commit: str
    requested_capabilities: tuple[ControlledActivationCapability | str, ...]
    requester_identity: str
    operator_identity: str
    proposed_independent_approver_identity: str
    scope: str
    m3_readiness_binding: str
    production_authorized: bool = False
    ubuntu_participation: bool = False
    caller_supplied_capability_order: tuple[str, ...] = ()
    authorization_expired: bool = False
    permit_single_use: bool = True
    duplicate_claim_representation: bool = False
    rollback_required: bool = True
    evidence_required: bool = True
    bundled_implicit_escalation: bool = False
    monitoring_implies_alert_dispatch: bool = False
    alert_dispatch_implies_external_notification: bool = False
    environment_only_activation: bool = False
    activation_authority: str = "AIControlCenter"
    governance_authority: str = "AIControlCenter"
    business_logic_authority: str = "AIControlCenter"
    state_owner: str = "AIControlCenter"
    arbitrary_command_execution: bool = False
    runtime_subprocess_execution: bool = False


@dataclass(frozen=True, slots=True)
class ControlledActivationPlanStep:
    sequence: int
    capability: ControlledActivationCapability
    required_gates: tuple[str, ...]
    required_authorization_contracts: tuple[str, ...]
    permit_boundary: str
    claim_boundary: str
    required_evidence_artifacts: tuple[str, ...]
    rollback_requirement: str
    fail_closed_requirement: str
    dependencies: tuple[ControlledActivationCapability, ...]
    prohibited_transitions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ControlledActivationPlan:
    task: str
    branch: str
    commit: str
    scope: str
    requester_identity: str
    operator_identity: str
    proposed_independent_approver_identity: str
    capability_order: tuple[ControlledActivationCapability, ...]
    steps: tuple[ControlledActivationPlanStep, ...]
    production_authorized: bool
    ubuntu_participation: bool
    activation_authorizations_created: int
    operational_permits_issued: int
    live_claims_created: int
    runtime_side_effects: int
    decision: ControlledActivationArchitectureDecision
    plan_digest: str

    def as_dict(self) -> dict[str, Any]:
        return _as_json_dict(self)

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()


@dataclass(frozen=True, slots=True)
class ControlledActivationTransition:
    capability: ControlledActivationCapability
    from_state: ControlledActivationState
    to_state: ControlledActivationState
    branch: str
    commit: str
    evidence_artifacts: tuple[str, ...]
    independent_approval_present: bool = False
    authorization_valid: bool = False
    authorization_expired: bool = False
    single_use_permit_present: bool = False
    permit_reusable: bool = False
    atomic_claim_count: int = 0
    rollback_evidence_present: bool = False
    production_transition: bool = False
    ubuntu_delegation: bool = False
    environment_only: bool = False

    def as_dict(self) -> dict[str, Any]:
        return _as_json_dict(self)

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()


@dataclass(frozen=True, slots=True)
class ControlledActivationValidationResult:
    valid: bool
    capability: ControlledActivationCapability
    from_state: ControlledActivationState
    to_state: ControlledActivationState
    evidence_artifacts: tuple[str, ...]
    decision: str

    def as_dict(self) -> dict[str, Any]:
        return _as_json_dict(self)

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()


def _as_json_dict(value: Any) -> dict[str, Any]:
    def normalize(item: Any) -> Any:
        if isinstance(item, StrEnum):
            return item.value
        if isinstance(item, dict):
            return {key: normalize(child) for key, child in item.items()}
        if isinstance(item, (tuple, list)):
            return [normalize(child) for child in item]
        return item

    return normalize(asdict(value))
