"""Immutable contracts for M3-A4C controlled activation readiness closeout."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


TASK = "M3-A4C"
BRANCH = "feature/deployment-package"
BOOTSTRAP_COMMIT = "f7a81b73b86c170300bb6b80f437dbb753362f7e"
RECOVERY_COMMIT = "0f23abdf362965c09db5f4f35483cbff47853643"


class ControlledActivationValidationError(ValueError):
    """Stable fail-closed validation error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class ControlledActivationInvariant(StrEnum):
    CONTROL_PLANE_OWNERSHIP = "CONTROL_PLANE_OWNERSHIP"
    MAC_BRAIN_ROLE = "MAC_BRAIN_ROLE"
    UBUNTU_EXCLUSION = "UBUNTU_EXCLUSION"
    GIT_BINDING = "GIT_BINDING"
    AUTHORIZATION_BINDING = "AUTHORIZATION_BINDING"
    PERMIT_AND_CLAIM = "PERMIT_AND_CLAIM"
    BOOTSTRAP_EVIDENCE = "BOOTSTRAP_EVIDENCE"
    RECOVERY_READINESS = "RECOVERY_READINESS"
    DATA_HEALTH = "DATA_HEALTH"
    MANAGED_FILESYSTEM = "MANAGED_FILESYSTEM"
    ACTIVATION_DEFAULT_DENY = "ACTIVATION_DEFAULT_DENY"
    LOCAL_VALIDATION_ONLY = "LOCAL_VALIDATION_ONLY"


class ControlledActivationReadinessDecision(StrEnum):
    READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION = (
        "READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION"
    )


@dataclass(frozen=True, slots=True)
class ControlledActivationValidationConfig:
    branch: str = BRANCH
    commit: str = RECOVERY_COMMIT
    bootstrap_commit: str = BOOTSTRAP_COMMIT
    control_plane_owner: str = "AIControlCenter"
    governance_owner: str = "AIControlCenter"
    authorization_owner: str = "AIControlCenter"
    permit_owner: str = "AIControlCenter"
    claim_owner: str = "AIControlCenter"
    evidence_owner: str = "AIControlCenter"
    deployment_controller: str = "AIControlCenter"
    host_role: str = "MAC_ALWAYS_ON_BRAIN"
    wordpress_business_logic_present: bool = False
    woocommerce_business_logic_present: bool = False
    n8n_control_present: bool = False
    external_component_control_present: bool = False
    ubuntu_participation: bool = False
    ubuntu_authorization_scope: bool = False
    ubuntu_state_ownership: bool = False
    linux_live_host: bool = False
    root_operator: bool = False
    environment_only_activation: bool = False
    authorization_present: bool = True
    authorization_valid: bool = True
    authorization_expired: bool = False
    permit_present: bool = True
    permit_expired: bool = False
    permit_consumed: bool = True
    permit_reused: bool = False
    claim_present: bool = True
    claim_count: int = 1
    evidence_chain_valid: bool = True
    bootstrap_evidence_present: bool = True
    bootstrap_evidence_valid: bool = True
    recovery_report_present: bool = True
    recovery_report_valid: bool = True
    recovery_validation_passed: bool = True
    audit_status: str = "HEALTHY"
    audit_event_count: int = 0
    replay_status: str = "HEALTHY"
    replay_event_count: int = 0
    managed_filesystem_ready: bool = True
    operational_root_safe: bool = True
    operational_root_arbitrary: bool = False
    writers_authorized: bool = False
    monitoring_authorized: bool = False
    external_dispatch_authorized: bool = False
    production_authorized: bool = False
    writers_active: bool = False
    monitoring_active: bool = False
    dispatch_active: bool = False
    validation_runner_write_requested: bool = False
    live_test_adapter_supplied: bool = False
    api_write_route_requested: bool = False


@dataclass(frozen=True, slots=True)
class FutureControlledActivationContract:
    """Requirements only; this is not a request, authorization, permit, or claim."""

    exact_branch_and_commit_required: bool = True
    explicit_capability_set_required: bool = True
    capabilities_default_false: bool = True
    independent_approver_required: bool = True
    requester_operator_approver_rules_required: bool = True
    bounded_authorization_ttl_required: bool = True
    single_use_permit_required: bool = True
    atomic_claim_required: bool = True
    bootstrap_evidence_binding_required: bool = True
    recovery_readiness_binding_required: bool = True
    audit_healthy_required: bool = True
    replay_healthy_required: bool = True
    per_capability_authorization_required: bool = True
    fail_closed_evidence_policy_required: bool = True
    ubuntu_participation: bool = False
    production_authorized: bool = False


@dataclass(frozen=True, slots=True)
class ControlledActivationValidationResult:
    invariants: tuple[ControlledActivationInvariant, ...]
    blockers: tuple[str, ...]
    risks: tuple[str, ...]
    decision: ControlledActivationReadinessDecision


@dataclass(frozen=True, slots=True)
class ControlledActivationCloseoutReport:
    task: str
    branch: str
    commit: str
    bootstrap_evidence_status: str
    recovery_validation_status: str
    audit_health: str
    audit_event_count: int
    replay_health: str
    replay_event_count: int
    consumed_permit_status: str
    single_claim_status: str
    managed_filesystem_readiness: str
    writers_active: bool
    monitoring_active: bool
    dispatch_active: bool
    ubuntu_participation: bool
    production_authorization: bool
    future_authorization_required: bool
    blockers: tuple[str, ...]
    risks: tuple[str, ...]
    readiness_decision: ControlledActivationReadinessDecision
    future_activation_contract: FutureControlledActivationContract
    report_digest: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["readiness_decision"] = self.readiness_decision.value
        return value

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


def digest(value: Any) -> str:
    if hasattr(value, "as_dict"):
        value = value.as_dict()
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
