"""Provider-neutral phone-verification contracts and application port."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import ConfigDict, Field

from core.shopping.customer_auth import VerificationPurpose
from core.shopping.customer_identity import ClosedContract, UTCTimestamp
from core.shopping.phone_normalization import OpaquePhoneBinding, PhoneBinding


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

    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )
    phone_binding: OpaquePhoneBinding


class ChallengeStatus(str, Enum):
    STARTED = "STARTED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class VerificationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class ChallengeStartRequest(ClosedContract):
    provider_source: ProviderSourceIdentifier
    purpose: VerificationPurpose
    challenge_reference: ChallengeReference
    replay_reference: ReplayReference
    subject: ChallengeSubject


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
    "ChallengeVerificationRequest",
    "ChallengeVerificationResult",
    "ChallengeStartEvidence",
    "IdempotencyReference",
    "OpaquePhoneBinding",
    "PhoneBinding",
    "PhoneVerificationPort",
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
