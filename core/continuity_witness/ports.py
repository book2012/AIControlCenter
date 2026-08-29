"""Purpose-specific Continuity Witness ports; none grants execution authority."""

from __future__ import annotations

from typing import Any, Protocol

from .contracts import ImmutableHistoryObservation, StoredCheckpoint, TransitionIntent
from .domain import HardwareBindingIndex, LifecycleOperation


class TransactionStorePort(Protocol):
    def durably_claim_approval(self, claim: Any) -> Any: ...
    def commit_lifecycle_transition(self, intent: TransitionIntent) -> Any: ...
    def get_operation(self, operation_id: Any) -> Any: ...


class ImmutableHistoryPort(Protocol):
    def publish_checkpoint(self, checkpoint: StoredCheckpoint) -> Any: ...
    def get_checkpoint(self, checkpoint_id: Any, immutable_version_id: str | None) -> Any: ...
    def prove_coverage(self, query: Any) -> ImmutableHistoryObservation: ...


class WitnessSigningPort(Protocol):
    def sign(self, canonical_envelope: bytes) -> Any: ...


class LifecycleApprovalVerifier(Protocol):
    """Verifies human-signed evidence only; never signs or consumes it."""
    def verify(self, approval_evidence: Any, expected_intent: TransitionIntent) -> Any: ...


class HardwareIndexPort(Protocol):
    def index_validated_hardware(self, transient_attested_udid: str, transient_attested_serial_number: str) -> HardwareBindingIndex: ...


class MDAEvidencePort(Protocol):
    """DeviceInformation evidence boundary for operations requiring fresh MDA."""
    transport: str
    def collect_and_validate(self, request: Any) -> Any: ...


CONTINUITY_WITNESS_MDA_TRANSPORT = "DEVICE_INFORMATION"
MAC_MINI_M4_IS_SOLE_CONTROL_PLANE = True
CONTINUITY_WITNESS_IS_SECOND_CONTROL_PLANE = False
UBUNTU_IMPLEMENTATION_ROLE = False
