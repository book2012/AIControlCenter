"""Deterministic immutable Continuity Witness contract models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from .domain import ContinuityHostId, IdentityEvaluationId, LifecycleOperation, LifecycleOperationId
from .json_contracts import canonical_digest, canonical_signed_bytes, canonicalize, decode_base64url


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    return value


_POSTCONDITIONS = {
    LifecycleOperation.GENESIS_ENROLLMENT: (["TARGET"], True, True, "WITNESS_ASSIGN_NEW", "SET_TO_ONE", None, "ACTIVE", None, False),
    LifecycleOperation.RECOVERY: (["TARGET"], False, True, "PRESERVE_EXISTING", "PRESERVE_EXISTING", None, "ACTIVE", None, False),
    LifecycleOperation.DECOMMISSION: (["TARGET"], False, False, "PRESERVE_EXISTING", "PRESERVE_EXISTING", None, "DECOMMISSIONED", None, False),
    LifecycleOperation.MIGRATION: (["PREDECESSOR", "SUCCESSOR"], False, True, "WITNESS_ASSIGN_DISTINCT_SUCCESSOR", "SUCCESSOR_SET_TO_ONE", "DECOMMISSIONED", None, "ACTIVE", True),
}


@dataclass(frozen=True, slots=True)
class TransitionIntent:
    operation_id: LifecycleOperationId
    evaluation_id: IdentityEvaluationId
    operation_type: LifecycleOperation
    expected_continuity_host_id: ContinuityHostId | None
    expected_predecessor_continuity_host_id: ContinuityHostId | None
    expected_record_generation: int | None
    validated_hardware_evidence_binding_digest: str | None

    def __post_init__(self) -> None:
        if self.expected_record_generation is not None and self.expected_record_generation < 1:
            raise ValueError("expected_record_generation must be positive")
        if self.validated_hardware_evidence_binding_digest is not None:
            if len(decode_base64url(self.validated_hardware_evidence_binding_digest)) != 32:
                raise ValueError("hardware evidence binding digest must be 32 bytes")
        if self.operation_type is LifecycleOperation.GENESIS_ENROLLMENT:
            if any((self.expected_continuity_host_id, self.expected_predecessor_continuity_host_id, self.expected_record_generation)):
                raise ValueError("GENESIS cannot bind a caller-selected or prior host")
        elif self.operation_type in {LifecycleOperation.RECOVERY, LifecycleOperation.DECOMMISSION}:
            if self.expected_continuity_host_id is None or self.expected_predecessor_continuity_host_id is not None or self.expected_record_generation is None:
                raise ValueError("operation must bind the exact current host and generation")
        elif self.expected_continuity_host_id is not None or self.expected_predecessor_continuity_host_id is None or self.expected_record_generation is None:
            raise ValueError("MIGRATION must bind only the exact predecessor and generation")
        if self.operation_type is LifecycleOperation.DECOMMISSION:
            if self.validated_hardware_evidence_binding_digest is not None:
                raise ValueError("DECOMMISSION requires no fresh MDA digest")
        elif self.validated_hardware_evidence_binding_digest is None:
            raise ValueError("GENESIS, RECOVERY, and MIGRATION require fresh MDA binding")

    def as_dict(self) -> dict[str, Any]:
        roles, absence, mda, host, enrollment, predecessor, target, successor, lineage = _POSTCONDITIONS[self.operation_type]
        return {
            "schema_version": "1", "domain": "CONTINUITY_LIFECYCLE_TRANSITION_INTENT",
            "operation_id": str(self.operation_id), "evaluation_id": str(self.evaluation_id),
            "operation_type": self.operation_type.value,
            "expected_continuity_host_id": None if self.expected_continuity_host_id is None else str(self.expected_continuity_host_id),
            "expected_predecessor_continuity_host_id": None if self.expected_predecessor_continuity_host_id is None else str(self.expected_predecessor_continuity_host_id),
            "expected_record_generation": self.expected_record_generation,
            "validated_hardware_evidence_binding_digest": self.validated_hardware_evidence_binding_digest,
            "transition_cardinality": len(roles),
            "required_postconditions": {
                "transition_roles": roles, "require_complete_verified_historical_absence": absence,
                "require_fresh_mda": mda, "host_identity_rule": host,
                "enrollment_generation_rule": enrollment, "predecessor_final_state": predecessor,
                "target_final_state": target, "successor_final_state": successor,
                "successor_lineage_must_bind_predecessor": lineage, "version_maxima_rule": "NONDECREASING",
            },
        }

    @property
    def expected_transition_intent_digest(self) -> str:
        return canonical_digest(self.as_dict())


@dataclass(frozen=True, slots=True)
class CheckpointPayload:
    fields: Mapping[str, Any]
    def __post_init__(self) -> None:
        frozen = _freeze(self.fields)
        object.__setattr__(self, "fields", frozen)
        plain = _plain(frozen)
        if plain.get("schema_version") != "1" or plain.get("domain") != "CONTINUITY_CHECKPOINT_PAYLOAD":
            raise ValueError("checkpoint payload requires exact version and domain")
        forbidden = {"application_payload_digest", "signature", "object_digest", "canonical_bytes_digest"}
        if forbidden.intersection(plain):
            raise ValueError("checkpoint payload contains circular/signing metadata")
        canonicalize(plain)
    def as_dict(self) -> dict[str, Any]: return _plain(self.fields)
    @property
    def application_payload_digest(self) -> str: return canonical_digest(self.as_dict())


@dataclass(frozen=True, slots=True)
class WitnessCheckpointSigningEnvelope:
    fields: Mapping[str, Any]
    def __post_init__(self) -> None:
        frozen = _freeze(self.fields); object.__setattr__(self, "fields", frozen)
        plain = _plain(frozen)
        if plain.get("schema_version") != "1" or plain.get("domain") != "WITNESS_PROTOCOL_EVIDENCE" or plain.get("evidence_type") != "IMMUTABLE_CONTINUITY_CHECKPOINT":
            raise ValueError("checkpoint envelope requires exact version/domain/type")
        signature = plain.get("signature")
        if signature is None: raise ValueError("checkpoint signature is required")
        if len(decode_base64url(signature)) != 64:
            raise ValueError("checkpoint signature must be exactly 64 bytes")
        canonical_signed_bytes({key: value for key, value in plain.items() if key != "signature"})
    def as_dict(self) -> dict[str, Any]: return _plain(self.fields)


@dataclass(frozen=True, slots=True)
class StoredCheckpoint:
    payload: CheckpointPayload
    signed_evidence: WitnessCheckpointSigningEnvelope
    def __post_init__(self) -> None:
        bound_digest = self.signed_evidence.as_dict().get("application_payload_digest")
        if bound_digest != self.payload.application_payload_digest:
            raise ValueError("signed evidence does not bind the application payload digest")
    def as_dict(self) -> dict[str, Any]:
        return {"schema_version": "1", "payload": self.payload.as_dict(), "signed_evidence": self.signed_evidence.as_dict()}
    @property
    def canonical_bytes(self) -> bytes: return canonicalize(self.as_dict())
    @property
    def object_digest(self) -> str: return canonical_digest(self.as_dict())


class HistoryCoverage(str, Enum):
    COMPLETE_PRESENT = "COMPLETE_PRESENT"
    COMPLETE_ABSENT = "COMPLETE_ABSENT"
    INCOMPLETE = "INCOMPLETE"
    CONFLICTING = "CONFLICTING"
    UNAVAILABLE = "UNAVAILABLE"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True, slots=True)
class ImmutableHistoryObservation:
    coverage: HistoryCoverage
    version_aware: bool
    delete_marker_observed: bool = False
    latest_key_not_found: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.coverage, HistoryCoverage):
            raise ValueError("coverage must be a closed HistoryCoverage value")
        for field_name in (
            "version_aware",
            "delete_marker_observed",
            "latest_key_not_found",
        ):
            if type(getattr(self, field_name)) is not bool:
                raise ValueError(f"{field_name} must be exactly bool")

    @property
    def proves_historical_absence(self) -> bool:
        return self.coverage == HistoryCoverage.COMPLETE_ABSENT and self.version_aware and not self.delete_marker_observed and not self.latest_key_not_found
