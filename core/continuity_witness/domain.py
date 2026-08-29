"""Immutable Continuity Witness domain values frozen by SEC-02."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar
from uuid import UUID


@dataclass(frozen=True, slots=True)
class _UuidV7Id:
    value: str
    label: ClassVar[str] = "identifier"

    def __post_init__(self) -> None:
        try:
            parsed = UUID(self.value)
        except (ValueError, AttributeError) as error:
            raise ValueError(f"{self.label} must be a canonical UUIDv7") from error
        if parsed.version != 7 or str(parsed) != self.value:
            raise ValueError(f"{self.label} must be a lowercase canonical UUIDv7")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ContinuityHostId(_UuidV7Id): label: ClassVar[str] = "continuity_host_id"
@dataclass(frozen=True, slots=True)
class ChallengeId(_UuidV7Id): label: ClassVar[str] = "challenge_id"
@dataclass(frozen=True, slots=True)
class IdentityEvaluationId(_UuidV7Id): label: ClassVar[str] = "evaluation_id"
@dataclass(frozen=True, slots=True)
class LifecycleApprovalId(_UuidV7Id): label: ClassVar[str] = "approval_id"
@dataclass(frozen=True, slots=True)
class LifecycleApprovalClaimId(_UuidV7Id): label: ClassVar[str] = "claim_id"
@dataclass(frozen=True, slots=True)
class LifecycleOperationId(_UuidV7Id): label: ClassVar[str] = "operation_id"
@dataclass(frozen=True, slots=True)
class TransitionId(_UuidV7Id): label: ClassVar[str] = "transition_id"
@dataclass(frozen=True, slots=True)
class CheckpointId(_UuidV7Id): label: ClassVar[str] = "checkpoint_id"


@dataclass(frozen=True, slots=True)
class KeyId:
    value: str
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("key_id must be a nonempty opaque string")


@dataclass(frozen=True, slots=True)
class KeyVersion:
    value: str
    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("key_version must be a nonempty opaque string")


@dataclass(frozen=True, slots=True)
class HardwareBindingIndex:
    """Privacy-preserving HMAC index; never a raw hardware identifier."""
    index: str
    key_id: KeyId
    key_version: KeyVersion

    def __post_init__(self) -> None:
        from .json_contracts import decode_base64url
        if len(decode_base64url(self.index)) != 32:
            raise ValueError("hardware_binding_index must be exactly 32 bytes")


class LifecycleOperation(str, Enum):
    GENESIS_ENROLLMENT = "GENESIS_ENROLLMENT"
    RECOVERY = "RECOVERY"
    DECOMMISSION = "DECOMMISSION"
    MIGRATION = "MIGRATION"


class ContinuityClassification(str, Enum):
    GENESIS_ELIGIBLE = "GENESIS_ELIGIBLE"
    CONTINUITY_VALID = "CONTINUITY_VALID"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    DECOMMISSIONED = "DECOMMISSIONED"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED = "MALFORMED"
    UNCERTAIN = "UNCERTAIN"


class ApprovalClaimState(str, Enum):
    AVAILABLE = "AVAILABLE"
    DURABLY_CLAIMED = "DURABLY_CLAIMED"
    COMMITTED = "COMMITTED"
    FAILED_CONSUMED = "FAILED_CONSUMED"
    UNCERTAIN_CONSUMED = "UNCERTAIN_CONSUMED"

    @property
    def reusable(self) -> bool:
        return self is ApprovalClaimState.AVAILABLE


DURABLE_CLAIM_ITSELF_PERMANENTLY_CONSUMES_AUTHORITY = True
CLAIM_STEALING_ALLOWED = False
AUTOMATIC_CLAIM_RECOVERY_ALLOWED = False
AUTOMATIC_RETRY_AUTHORITY = False


def fresh_mda_required(operation: LifecycleOperation) -> bool:
    return operation in {
        LifecycleOperation.GENESIS_ENROLLMENT,
        LifecycleOperation.RECOVERY,
        LifecycleOperation.MIGRATION,
    }


def mutation_post_retry_allowed(*, outcome_ambiguous: bool) -> bool:
    """Mutation replay never follows ambiguity (and is never automatic)."""
    return False
