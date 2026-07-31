"""Immutable M4-A2 capability authorization contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.controlled_activation_architecture import (
    ControlledActivationCapability,
)


TASK = "M4-A2"
SCHEMA_VERSION = "m4-a2/v1"
BRANCH = "feature/deployment-package"
BASELINE_COMMIT = "cbeb20d41808ea615b08196b164d6b5578486ed8"
M3_READINESS = "READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION"
M4_A1_DECISION = "READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS"


class CapabilityAuthorizationError(ValueError):
    """Stable default-deny validation error."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class CapabilityAuthorizationDecision(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class CapabilityAuthorizationArchitectureDecision(StrEnum):
    READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION = (
        "READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION"
    )


@dataclass(frozen=True, slots=True)
class CanonicalContract:
    def as_dict(self) -> dict[str, Any]:
        return _normalize(asdict(self))

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()

    def digest(self) -> str:
        return sha256_digest(self.as_dict())


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationScope(CanonicalContract):
    environment: str
    control_plane_owner: str = "AIControlCenter"
    governance_authority: str = "AIControlCenter"
    state_owner: str = "AIControlCenter"
    production_authorized: bool = False
    ubuntu_participation: bool = False
    authorization_from_environment: bool = False
    api_route_authority: bool = False
    runtime_command_execution: bool = False


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationRestriction(CanonicalContract):
    independent_approval_required: bool = True
    single_capability_only: bool = True
    single_use_required: bool = True
    atomic_claim_required: bool = True
    rollback_evidence_required: bool = True
    evidence_required: bool = True
    production_denied: bool = True
    ubuntu_denied: bool = True
    implicit_escalation_denied: bool = True
    runtime_activation_denied: bool = True
    monitoring_does_not_authorize_alert_dispatch: bool = True
    alert_dispatch_does_not_authorize_external_notification: bool = True
    dependency_does_not_constitute_authorization: bool = True
    external_endpoint_details_excluded: bool = True


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationEvidence(CanonicalContract):
    m3_readiness_binding: str
    m4_a1_architecture_binding: str
    rollback_policy: str
    evidence_policy: str
    read_only_health_evidence: tuple[str, ...] = ()
    separately_authorized_capability_reference: str | None = None
    separately_authorized_capability_digest: str | None = None


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationRequest(CanonicalContract):
    schema_version: str
    request_id: str
    branch: str
    commit: str
    capability: ControlledActivationCapability | str | tuple[Any, ...]
    requester_identity: str
    operator_identity: str
    proposed_independent_approver_identity: str
    scope: CapabilityAuthorizationScope
    requested_at: datetime
    requested_not_before: datetime
    requested_expires_at: datetime
    requested_maximum_uses: int
    production_authorized: bool
    ubuntu_participation: bool
    evidence: CapabilityAuthorizationEvidence
    canonical_digest: str
    bundled_capability_escalation: bool = False
    monitoring_implies_alert_dispatch: bool = False
    alert_dispatch_implies_external_notification: bool = False

    def digest_payload(self) -> dict[str, Any]:
        value = self.as_dict()
        value["canonical_digest"] = ""
        return value

    def computed_digest(self) -> str:
        return sha256_digest(self.digest_payload())


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationApproval(CanonicalContract):
    schema_version: str
    approval_id: str
    request_id: str
    request_digest: str
    capability: ControlledActivationCapability | str
    independent_approver_identity: str
    decision: CapabilityAuthorizationDecision | str
    approval_timestamp: datetime
    authorization_not_before: datetime
    authorization_expires_at: datetime
    maximum_uses: int
    production_authorized: bool
    ubuntu_participation: bool
    acknowledged_restrictions: tuple[str, ...]
    cryptographic_identity_verified: bool
    canonical_digest: str

    def digest_payload(self) -> dict[str, Any]:
        value = self.as_dict()
        value["canonical_digest"] = ""
        return value

    def computed_digest(self) -> str:
        return sha256_digest(self.digest_payload())


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationValidationResult(CanonicalContract):
    valid: bool
    request_id: str
    capability: ControlledActivationCapability
    errors: tuple[str, ...]
    checked_at: datetime


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationGrant(CanonicalContract):
    grant_plan_id: str
    request_id: str
    request_digest: str
    approval_id: str
    approval_digest: str
    capability: ControlledActivationCapability
    branch: str
    commit: str
    not_before: datetime
    expires_at: datetime
    maximum_uses: int
    production_authorized: bool
    ubuntu_participation: bool
    cryptographic_identity_verified: bool
    authorization_created: bool
    permit_issued: bool
    claim_created: bool
    runtime_activation_authorized: bool


@dataclass(frozen=True, slots=True)
class CapabilityAuthorizationPlan(CanonicalContract):
    task: str
    validation: CapabilityAuthorizationValidationResult
    grant: CapabilityAuthorizationGrant
    required_restrictions: tuple[str, ...]
    activation_authorizations_created: int
    operational_permits_issued: int
    live_claims_created: int
    runtime_activations: int
    decision: CapabilityAuthorizationArchitectureDecision
    plan_digest: str

    def digest_payload(self) -> dict[str, Any]:
        value = self.as_dict()
        value["plan_digest"] = ""
        return value

    def computed_digest(self) -> str:
        return sha256_digest(self.digest_payload())


def _normalize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            return value.isoformat()
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {key: _normalize(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_normalize(child) for child in value]
    return value
