"""Closed, provider-neutral transport contracts for phone verification."""
from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import ConfigDict, Field, field_validator

from core.shopping.customer_auth import VerificationPurpose
from core.shopping.customer_identity import ClosedContract, UTCTimestamp
from core.shopping.phone_normalization import OpaquePhoneBinding
from core.shopping.ports.phone_verification import (
    ProviderSourceIdentifier, ProviderVerificationIdentifier,
)


DEFAULT_PROVIDER_TIMEOUT_SECONDS = 10.0
MAX_PROVIDER_TIMEOUT_SECONDS = 30.0


class ProviderTransportFailureCode(str, Enum):
    """Stable, bounded failure meanings shared by transports and adapters."""

    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    REJECTED = "REJECTED"
    AMBIGUOUS_PROVIDER_IDENTIFIER = "AMBIGUOUS_PROVIDER_IDENTIFIER"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


_SAFE_FAILURE_MESSAGES = {
    ProviderTransportFailureCode.PROVIDER_UNAVAILABLE: "provider is unavailable",
    ProviderTransportFailureCode.TIMEOUT: "provider request timed out",
    ProviderTransportFailureCode.MALFORMED_RESPONSE: "provider response was malformed",
    ProviderTransportFailureCode.REJECTED: "provider rejected the request",
    ProviderTransportFailureCode.AMBIGUOUS_PROVIDER_IDENTIFIER: (
        "provider verification identifier was ambiguous"
    ),
    ProviderTransportFailureCode.UNKNOWN_OUTCOME: "provider outcome is unknown",
}


class ProviderTransportError(RuntimeError):
    """Transport failure whose public representation is allowlisted only."""

    def __init__(
        self,
        code: ProviderTransportFailureCode,
        *,
        operation: str | None = None,
    ) -> None:
        try:
            normalized = ProviderTransportFailureCode(code)
        except (TypeError, ValueError):
            normalized = ProviderTransportFailureCode.UNKNOWN_OUTCOME
        self.code = normalized
        self.failure_code = normalized
        self.reason_code = normalized
        self.operation = operation if operation in {"START", "VERIFY"} else None
        super().__init__(_SAFE_FAILURE_MESSAGES[normalized])

    def __str__(self) -> str:
        return f"{self.code.value}: {_SAFE_FAILURE_MESSAGES[self.code]}"

    def __repr__(self) -> str:
        operation = f", operation={self.operation!r}" if self.operation else ""
        return f"ProviderTransportError(code={self.code.value!r}{operation})"


class ProviderTransportStartStatus(str, Enum):
    STARTED = "STARTED"
    PENDING = "PENDING"


class ProviderTransportVerificationStatus(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


ProviderTransportStartState = ProviderTransportStartStatus
ProviderTransportVerifyStatus = ProviderTransportVerificationStatus


class _TransportContract(ClosedContract):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )


class _TimedTransportRequest(_TransportContract):
    timeout_seconds: float = Field(
        default=DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        gt=0,
        le=MAX_PROVIDER_TIMEOUT_SECONDS,
    )

    @field_validator("timeout_seconds", mode="before")
    @classmethod
    def reject_boolean_timeout(cls, value: object) -> float:
        if type(value) not in (int, float):
            raise ValueError("timeout must be a positive bounded number")
        return float(value)


class ProviderTransportStartRequest(_TimedTransportRequest):
    """The only start input is opaque binding metadata, never a raw phone."""

    provider_source: ProviderSourceIdentifier
    purpose: VerificationPurpose
    phone_binding: OpaquePhoneBinding


class ProviderTransportVerifyRequest(_TimedTransportRequest):
    """VERIFY is the sole transport contract allowed to carry an OTP."""

    provider_source: ProviderSourceIdentifier
    provider_verification_id: ProviderVerificationIdentifier
    otp: str = Field(strict=True, min_length=1, max_length=32, repr=False)

    def model_dump(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        excluded = set(kwargs.pop("exclude", set()) or ())
        excluded.add("otp")
        return super().model_dump(*args, exclude=excluded, **kwargs)

    def model_dump_json(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs["exclude"] = set(kwargs.pop("exclude", set()) or ()) | {"otp"}
        return super().model_dump_json(*args, **kwargs)

    def dict(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self.model_dump(*args, **kwargs)

    def json(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        return self.model_dump_json(*args, **kwargs)


class ProviderTransportStartResult(_TransportContract):
    provider_verification_id: ProviderVerificationIdentifier
    status: ProviderTransportStartStatus
    started_at: UTCTimestamp
    provider_expires_at: UTCTimestamp | None = None


class ProviderTransportVerifyResult(_TransportContract):
    provider_verification_id: ProviderVerificationIdentifier
    status: ProviderTransportVerificationStatus
    verified_at: UTCTimestamp
    provider_expires_at: UTCTimestamp | None = None


@runtime_checkable
class ProviderTransportPort(Protocol):
    """Typed START/VERIFY provider capability; raw payloads cannot cross it."""

    def start(
        self, request: ProviderTransportStartRequest,
    ) -> ProviderTransportStartResult:
        ...

    def verify(
        self, request: ProviderTransportVerifyRequest,
    ) -> ProviderTransportVerifyResult:
        ...


# Short aliases make the operation names visible to callers without opening
# a second contract vocabulary.
ProviderTransportStartRequestContract = ProviderTransportStartRequest
ProviderTransportVerifyRequestContract = ProviderTransportVerifyRequest
ProviderTransportStartResultContract = ProviderTransportStartResult
ProviderTransportVerifyResultContract = ProviderTransportVerifyResult
TransportFailureCode = ProviderTransportFailureCode
ProviderFailureCode = ProviderTransportFailureCode
ProviderTransportFailure = ProviderTransportError


__all__ = [
    "DEFAULT_PROVIDER_TIMEOUT_SECONDS",
    "MAX_PROVIDER_TIMEOUT_SECONDS",
    "ProviderTransportError",
    "ProviderTransportFailure",
    "ProviderTransportFailureCode",
    "ProviderTransportPort",
    "ProviderTransportStartRequest",
    "ProviderTransportStartRequestContract",
    "ProviderTransportStartResult",
    "ProviderTransportStartResultContract",
    "ProviderTransportStartStatus",
    "ProviderTransportStartState",
    "ProviderTransportVerificationStatus",
    "ProviderTransportVerifyStatus",
    "ProviderTransportVerifyRequest",
    "ProviderTransportVerifyRequestContract",
    "ProviderTransportVerifyResult",
    "ProviderTransportVerifyResultContract",
    "TransportFailureCode",
    "ProviderFailureCode",
]
