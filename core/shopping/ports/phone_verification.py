"""Provider-neutral phone-verification contracts and application port."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import ConfigDict, Field

from core.shopping.customer_auth import VerificationPurpose
from core.shopping.customer_identity import ClosedContract, UTCTimestamp
from core.shopping.phone_normalization import OpaquePhoneBinding, PhoneBinding
from core.shopping.ports.destination_resolution import DestinationHandle


_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,126}[A-Za-z0-9]$|^[A-Za-z0-9]$"


class _Identifier(ClosedContract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )
    value: str = Field(strict=True, min_length=1, max_length=128, pattern=_IDENTIFIER)

    def __str__(self) -> str:
        return self.value


class ProviderSourceIdentifier(_Identifier):
    """Bounded provider-source identity; it is not a vendor enumeration."""


class ProviderVerificationIdentifier(_Identifier):
    pass


class ChallengeReference(_Identifier):
    pass


class ReplayReference(_Identifier):
    pass


class ChallengeSubject(ClosedContract):
    """Only an opaque phone binding crosses into a provider adapter."""

    phone_binding: OpaquePhoneBinding


class ChallengeStatus(str, Enum):
    # START_CLAIMED is durable ownership, not provider evidence.  It is
    # intentionally not exposed as a successful start result.
    START_CLAIMED = "START_CLAIMED"
    START_UNKNOWN = "START_UNKNOWN"
    STARTED = "STARTED"
    PENDING = "PENDING"
    VERIFY_UNKNOWN = "VERIFY_UNKNOWN"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class VerificationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class ChallengeStartRequest(ClosedContract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
        arbitrary_types_allowed=True,
    )

    provider_source: ProviderSourceIdentifier
    purpose: VerificationPurpose
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    subject: ChallengeSubject
    destination_handle: DestinationHandle | None = Field(
        default=None, repr=False, exclude=True,
    )


class ChallengeStartResult(ClosedContract):
    provider_source: ProviderSourceIdentifier
    provider_verification_id: ProviderVerificationIdentifier
    purpose: VerificationPurpose
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    phone_binding: OpaquePhoneBinding
    status: ChallengeStatus
    started_at: UTCTimestamp
    provider_expires_at: UTCTimestamp | None = None


class ChallengeVerificationRequest(ClosedContract):
    provider_source: ProviderSourceIdentifier
    provider_verification_id: ProviderVerificationIdentifier
    purpose: VerificationPurpose
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    phone_binding: OpaquePhoneBinding
    # Field repr suppression prevents an OTP from entering normal diagnostics.
    otp: str = Field(strict=True, min_length=1, max_length=32, repr=False)


class ChallengeVerificationResult(ClosedContract):
    provider_source: ProviderSourceIdentifier
    provider_verification_id: ProviderVerificationIdentifier
    purpose: VerificationPurpose
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    phone_binding: OpaquePhoneBinding
    status: VerificationStatus
    verified_at: UTCTimestamp
    provider_expires_at: UTCTimestamp | None = None


@runtime_checkable
class PhoneVerificationPort(Protocol):
    """Semantic adapter boundary; raw payloads and credentials never cross it."""

    def start_challenge(self, request: ChallengeStartRequest) -> ChallengeStartResult:
        ...

    def verify_challenge(
        self, request: ChallengeVerificationRequest,
    ) -> ChallengeVerificationResult:
        ...


@runtime_checkable
class DurableVerificationRepository(Protocol):
    """Approved persistence seam for Control Plane verification authority.

    Implementations own only storage access.  The service owns TX1 policy and
    must keep provider invocation outside its transaction.
    """

    database_path: str | Path
    busy_timeout_ms: int

    def open(self):
        """Return a schema-validated SQLite connection."""
        ...


# Explicit port spelling for callers that describe the boundary as storage.
VerificationPersistencePort = DurableVerificationRepository
PhoneVerificationPersistencePort = DurableVerificationRepository

# Descriptive aliases keep the boundary easy to adopt without changing its
# closed underlying contracts.
ProviderSourceId = ProviderSourceIdentifier
ProviderVerificationId = ProviderVerificationIdentifier
IdempotencyReference = ReplayReference
ChallengeStartEvidence = ChallengeStartResult
VerificationRequest = ChallengeVerificationRequest
VerificationResult = ChallengeVerificationResult
VerificationEvidence = ChallengeVerificationResult
PhoneVerificationPurpose = VerificationPurpose


__all__ = [
    "ChallengeReference",
    "ChallengeStartRequest",
    "ChallengeStartResult",
    "ChallengeStatus",
    "ChallengeSubject",
    "DestinationHandle",
    "ChallengeVerificationRequest",
    "ChallengeVerificationResult",
    "ChallengeStartEvidence",
    "IdempotencyReference",
    "OpaquePhoneBinding",
    "PhoneBinding",
    "PhoneVerificationPort",
    "DurableVerificationRepository",
    "VerificationPersistencePort",
    "PhoneVerificationPersistencePort",
    "PhoneVerificationPurpose",
    "ProviderSourceIdentifier",
    "ProviderSourceId",
    "ProviderVerificationIdentifier",
    "ProviderVerificationId",
    "ReplayReference",
    "VerificationEvidence",
    "VerificationPurpose",
    "VerificationRequest",
    "VerificationResult",
    "VerificationStatus",
]
