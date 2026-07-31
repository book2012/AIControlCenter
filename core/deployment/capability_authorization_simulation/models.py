"""Immutable contracts for the M4-A3 test-only authorization simulation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from core.deployment.contracts import canonical_json_bytes, sha256_digest
from core.deployment.controlled_activation_architecture import ControlledActivationCapability

TASK = "M4-A3"
SCHEMA_VERSION = "m4-a3-test-only/v1"
BRANCH = "feature/deployment-package"
BASELINE_COMMIT = "05a6cd5d61bc16b973b2ea634aa435b020ef0705"
M3_BINDING = "READY_FOR_SEPARATELY_AUTHORIZED_CONTROLLED_ACTIVATION"
M4_A1_BINDING = "READY_FOR_CAPABILITY_AUTHORIZATION_CONTRACTS"
M4_A2_BINDING = "READY_FOR_TEST_ONLY_AUTHORIZATION_SIMULATION"
TEST_NAMESPACE = "m4-a3-test-only"
TEST_SOURCE = "deterministic-simulation"


class TestOnlyAuthorizationSimulationError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class TestOnlyAuthorizationStep(StrEnum):
    REQUESTED = "REQUESTED"
    INDEPENDENTLY_APPROVED = "INDEPENDENTLY_APPROVED"
    AUTHORIZATION_PLANNED = "AUTHORIZATION_PLANNED"
    SIMULATED_AUTHORIZED = "SIMULATED_AUTHORIZED"
    SIMULATED_PERMITTED = "SIMULATED_PERMITTED"
    SIMULATED_CLAIMED = "SIMULATED_CLAIMED"
    SIMULATION_VALIDATED = "SIMULATION_VALIDATED"


class TestOnlyAuthorizationSimulationDecision(StrEnum):
    BLOCKED = "BLOCKED"
    READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION = (
        "READY_FOR_READ_ONLY_OPERATIONAL_OBSERVATION"
    )


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


@dataclass(frozen=True, slots=True)
class CanonicalContract:
    def as_dict(self) -> dict[str, Any]:
        return _normalize(asdict(self))

    def canonical_json(self) -> str:
        return canonical_json_bytes(self.as_dict()).decode()

    def digest(self) -> str:
        return sha256_digest(self.as_dict())


@dataclass(frozen=True, slots=True)
class TestOnlyAuthorizationSimulationConfig(CanonicalContract):
    branch: str = BRANCH
    commit: str = BASELINE_COMMIT
    namespace: str = TEST_NAMESPACE
    source: str = TEST_SOURCE
    m3_binding: str = M3_BINDING
    m4_a1_binding: str = M4_A1_BINDING
    m4_a2_binding: str = M4_A2_BINDING
    test_only: bool = True
    operationally_valid: bool = False
    production_authorized: bool = False
    ubuntu_participation: bool = False
    runtime_activation_allowed: bool = False
    maximum_uses: int = 1
    environment_only_authorization: bool = False
    api_route_authority: bool = False
    external_governance_authority: str = "AIControlCenter"
    subprocess_execution: bool = False
    runtime_command_execution: bool = False
    network_access: bool = False


@dataclass(frozen=True, slots=True)
class TestOnlyAuthorizationSimulationRequest(CanonicalContract):
    simulation_id: str
    scenario_id: str
    scenario_seed: str
    capability: ControlledActivationCapability | str | tuple[Any, ...]
    branch: str
    commit: str
    requester_identity: str
    operator_identity: str
    independent_approver_identity: str
    request_digest: str
    approval_digest: str
    grant_plan_digest: str
    requested_at: datetime
    expires_at: datetime
    acknowledged_restrictions: tuple[str, ...]
    dependency_authorization_reference: str | None = None
    dependency_authorization_digest: str | None = None
    monitoring_implies_alert_dispatch: bool = False
    alert_dispatch_implies_external_notification: bool = False


@dataclass(frozen=True, slots=True)
class TestOnlyAuthorizationScenario(CanonicalContract):
    scenario_id: str
    scenario_seed: str
    capability: ControlledActivationCapability
    dependency_authorization_reference: str | None
    dependency_authorization_digest: str | None


@dataclass(frozen=True, slots=True)
class TestOnlyAuthorizationArtifact(CanonicalContract):
    authorization_id: str
    simulation_id: str
    scenario_id: str
    capability: ControlledActivationCapability
    request_digest: str
    approval_digest: str
    grant_plan_digest: str
    issued_at: datetime
    maximum_uses: int
    namespace: str = TEST_NAMESPACE
    source: str = TEST_SOURCE
    test_only: bool = True
    operationally_valid: bool = False
    production_authorized: bool = False
    ubuntu_participation: bool = False
    runtime_activation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class TestOnlyPermitArtifact(CanonicalContract):
    permit_id: str
    authorization_id: str
    authorization_digest: str
    simulation_id: str
    capability: ControlledActivationCapability
    request_digest: str
    approval_digest: str
    grant_plan_digest: str
    issued_at: datetime
    maximum_uses: int = 1
    namespace: str = TEST_NAMESPACE
    source: str = TEST_SOURCE
    test_only: bool = True
    operationally_valid: bool = False
    production_authorized: bool = False
    ubuntu_participation: bool = False
    runtime_activation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class TestOnlyClaimArtifact(CanonicalContract):
    claim_id: str
    permit_id: str
    permit_digest: str
    authorization_id: str
    authorization_digest: str
    simulation_id: str
    capability: ControlledActivationCapability
    request_digest: str
    approval_digest: str
    grant_plan_digest: str
    claimed_at: datetime
    namespace: str = TEST_NAMESPACE
    source: str = TEST_SOURCE
    test_only: bool = True
    operationally_valid: bool = False
    production_authorized: bool = False
    ubuntu_participation: bool = False
    runtime_activation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class TestOnlyAuthorizationSimulationEvidence(CanonicalContract):
    sequence: int
    simulation_id: str
    scenario_id: str
    branch: str
    commit: str
    capability: ControlledActivationCapability
    request_digest: str
    approval_digest: str
    grant_plan_digest: str
    prior_step_digest: str
    timestamp: datetime
    state: TestOnlyAuthorizationStep
    test_only: bool
    artifact_digest: str
    canonical_artifact_digest: str

    def digest_payload(self) -> dict[str, Any]:
        value = self.as_dict()
        value["canonical_artifact_digest"] = ""
        return value

    def computed_digest(self) -> str:
        return sha256_digest(self.digest_payload())


@dataclass(frozen=True, slots=True)
class TestOnlyAuthorizationSimulationResult(CanonicalContract):
    task: str
    simulation_id: str
    scenario: TestOnlyAuthorizationScenario
    evidence: tuple[TestOnlyAuthorizationSimulationEvidence, ...]
    authorization: TestOnlyAuthorizationArtifact | None
    permit: TestOnlyPermitArtifact | None
    claim: TestOnlyClaimArtifact | None
    errors: tuple[str, ...]
    decision: TestOnlyAuthorizationSimulationDecision
    operational_authorizations_created: int = 0
    operational_permits_issued: int = 0
    live_claims_created: int = 0
    runtime_activations: int = 0
