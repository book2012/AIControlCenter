"""Provider-neutral C5 activation and capability contracts.

This module is deliberately offline.  It contains policy data and opaque
capabilities only; it does not resolve secrets, construct transports, or
perform provider I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Protocol, runtime_checkable

from pydantic import field_validator, model_validator

from core.secrets.ports import EphemeralSecretLease, SecretReference
from core.shopping.customer_identity import ClosedContract
from core.shopping.ports.destination_resolution import DestinationHandle
from core.shopping.ports.phone_verification import ProviderSourceIdentifier


_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,158}[A-Za-z0-9]$|^[A-Za-z0-9]$"
_IDENTIFIER_RE = re.compile(_IDENTIFIER)
MAX_CORRELATION_LENGTH = 160


class ProviderEvidenceOutcome(str, Enum):
    """The only outcomes that may cross the provider evidence log boundary."""

    HEALTHY = "HEALTHY"
    AVAILABLE = "AVAILABLE"
    NOT_FOUND = "NOT_FOUND"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED = "MALFORMED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


class ProviderEvidenceCode(str, Enum):
    """Small, provider-neutral vocabulary for normalized evidence."""

    VERIFICATION_FOUND = "VERIFICATION_FOUND"
    VERIFICATION_NOT_FOUND = "VERIFICATION_NOT_FOUND"
    LOOKUP_FOUND = "LOOKUP_FOUND"
    LOOKUP_NOT_FOUND = "LOOKUP_NOT_FOUND"
    HEALTH_CHECK_OK = "HEALTH_CHECK_OK"
    PROVIDER_REJECTED = "PROVIDER_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_MALFORMED = "PROVIDER_MALFORMED"
    PROVIDER_UNKNOWN_OUTCOME = "PROVIDER_UNKNOWN_OUTCOME"


_ACTIVATION_REASON_CODES = frozenset({
    "AUTHORIZATION_REQUIRED",
    "AUTHORIZATION_GATE_STATE_MISMATCH",
    "DESTINATION_NOT_ALLOWLISTED",
    "INACTIVE_COMPOSITION_REJECTS_RUNTIME_DEPENDENCIES",
    "CONTROLLED_WRITE_DEFERRED",
    "AUTHENTICATED_READ_TRANSPORT_REQUIRED",
    "RECONCILIATION_COMMAND_REJECTED",
    "EVIDENCE_BINDING_REJECTED",
    "ACTIVATION_DISABLED",
    "CONTRACT_ONLY",
    "READ_CAPABILITY_REQUIRED",
    "WRITE_CAPABILITY_REQUIRED",
    "PROVIDER_NOT_ALLOWLISTED",
    "OPERATION_NOT_ALLOWLISTED",
    "NONPRODUCTION_REQUIRED",
    "DESTINATION_REQUIRED",
    "INVALID_REQUEST",
}) | frozenset(item.value for item in ProviderEvidenceOutcome)


def _require_utc_datetime(value: object, field_name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must be a timezone-aware UTC datetime")
    return value


def _allowlisted_value(value: object, enum_type: type[Enum], field_name: str) -> str:
    if isinstance(value, enum_type):
        return value.value  # type: ignore[return-value]
    if type(value) is str and value in {item.value for item in enum_type}:
        return value
    raise ValueError(f"{field_name} is not allowlisted")


class ProviderActivationState(str, Enum):
    """The only C5 activation states; production is intentionally absent."""

    DISABLED = "DISABLED"
    CONTRACT_ONLY = "CONTRACT_ONLY"
    AUTHENTICATED_READ_ONLY = "AUTHENTICATED_READ_ONLY"
    CONTROLLED_NONPROD_WRITE = "CONTROLLED_NONPROD_WRITE"


class ProviderEnvironment(str, Enum):
    """Closed environment vocabulary; production is intentionally absent."""

    CONTROLLED_NONPRODUCTION = "CONTROLLED_NON_PRODUCTION"


class ProviderOperation(str, Enum):
    """Provider operations visible to the authorization boundary."""

    READ_HEALTH = "READ_HEALTH"
    READ_LOOKUP = "READ_LOOKUP"
    READ_EVIDENCE = "READ_EVIDENCE"
    START_CHALLENGE = "START_CHALLENGE"
    VERIFY_CHALLENGE = "VERIFY_CHALLENGE"


# Compatibility spellings for the frozen contract vocabulary.
ActivationState = ProviderActivationState
ProviderReadOperation = ProviderOperation
ProviderWriteOperation = ProviderOperation


READ_OPERATIONS = frozenset({
    ProviderOperation.READ_HEALTH,
    ProviderOperation.READ_LOOKUP,
    ProviderOperation.READ_EVIDENCE,
})
WRITE_OPERATIONS = frozenset({
    ProviderOperation.START_CHALLENGE,
    ProviderOperation.VERIFY_CHALLENGE,
})


class ProviderActivationError(RuntimeError):
    """Safe, bounded activation/capability failure."""

    def __init__(self, reason_code: str = "AUTHORIZATION_REQUIRED") -> None:
        code = reason_code if type(reason_code) is str and reason_code in _ACTIVATION_REASON_CODES else "AUTHORIZATION_REQUIRED"
        self.reason_code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"ProviderActivationError(reason_code={self.reason_code!r})"


class _OpaqueCapability:
    __slots__ = ()

    def __new__(cls, *args: object, **kwargs: object) -> "_OpaqueCapability":
        raise TypeError("capabilities are composition-only")

    def __repr__(self) -> str:
        return f"{type(self).__name__}(<opaque>)"

    def __str__(self) -> str:
        return "<opaque provider capability>"

    def __reduce__(self):  # type: ignore[no-untyped-def]
        raise TypeError("provider capabilities are not serializable")

    def __copy__(self, memo):  # type: ignore[no-untyped-def]
        raise TypeError("provider capabilities are not copyable")

    __deepcopy__ = __copy__


class AuthenticatedReadCapability(_OpaqueCapability):
    """Opaque Control Plane capability required for authenticated reads."""


class ControlledNonProductionWriteCapability(_OpaqueCapability):
    """Opaque Control Plane capability required for bounded non-prod writes."""


# Descriptive aliases for callers using the shorter vocabulary.
ProviderReadCapability = AuthenticatedReadCapability
ProviderWriteCapability = ControlledNonProductionWriteCapability
AuthenticatedProviderReadCapability = AuthenticatedReadCapability
ControlledWriteCapability = ControlledNonProductionWriteCapability


class ProviderRequestIdentity(ClosedContract):
    """Bounded opaque request and correlation identity."""

    request_id: str
    correlation_id: str

    @field_validator("request_id", "correlation_id")
    @classmethod
    def validate_identity(cls, value: str) -> str:
        if type(value) is not str or not 1 <= len(value) <= MAX_CORRELATION_LENGTH:
            raise ValueError("request identity is invalid")
        if _IDENTIFIER_RE.fullmatch(value) is None:
            raise ValueError("request identity is invalid")
        return value


class ProviderAllowlist(ClosedContract):
    """Explicit provider-source allowlist; empty means deny all."""

    providers: tuple[ProviderSourceIdentifier, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def normalize_provider_values(cls, value: object) -> object:
        if isinstance(value, dict) and isinstance(value.get("providers"), (list, tuple)):
            payload = dict(value)
            payload["providers"] = tuple(
                item if isinstance(item, ProviderSourceIdentifier)
                else ProviderSourceIdentifier(value=item)
                for item in payload["providers"]
            )
            return payload
        return value

    def contains(self, provider_source: ProviderSourceIdentifier | str) -> bool:
        try:
            value = (provider_source if isinstance(provider_source, ProviderSourceIdentifier)
                     else ProviderSourceIdentifier(value=provider_source))
        except (TypeError, ValueError):
            return False
        return value in self.providers

    def __repr__(self) -> str:
        return "ProviderAllowlist(<opaque provider identities>)"


class OperationAllowlist(ClosedContract):
    """Explicit operation allowlist; empty means deny all."""

    operations: tuple[ProviderOperation, ...] = ()

    def contains(self, operation: ProviderOperation | str) -> bool:
        try:
            value = operation if isinstance(operation, ProviderOperation) else ProviderOperation(operation)
        except (TypeError, ValueError):
            return False
        return value in self.operations


class OpaqueDestinationAllowlist:
    """Process-local allowlist for opaque destination handles.

    The allowlist stores handle identity only.  It cannot accept or expose a
    raw phone number and has no serialization or logging representation.
    """

    __slots__ = ("_handles",)

    def __init__(self, handles: tuple[DestinationHandle, ...] = ()) -> None:
        if type(handles) is not tuple or any(type(handle) is not DestinationHandle for handle in handles):
            raise TypeError("opaque destination handles are required")
        self._handles = frozenset(handles)

    def contains(self, handle: object) -> bool:
        return type(handle) is DestinationHandle and handle in self._handles

    def require(self, handle: object) -> None:
        if not self.contains(handle):
            raise ProviderActivationError("DESTINATION_NOT_ALLOWLISTED")

    def __repr__(self) -> str:
        return "OpaqueDestinationAllowlist(<opaque>)"

    def __str__(self) -> str:
        return "<opaque destination allowlist>"

    def __reduce__(self):  # type: ignore[no-untyped-def]
        raise TypeError("destination allowlists are not serializable")


class SecretDeliveryContract(ClosedContract):
    """Value-free declaration of the future secret delivery path."""

    reference: SecretReference
    lease_required: bool = True
    lease_type: str = "EphemeralSecretLease"
    consumer_boundary: str = "PROVIDER_SPECIFIC_TRANSPORT_ONLY"

    def __repr__(self) -> str:
        return "SecretDeliveryContract(<metadata-only>)"


@runtime_checkable
class ProviderSecretLeaseConsumerPort(Protocol):
    """Only a provider-specific transport may consume a secret lease."""

    def execute_with_lease(self, lease: EphemeralSecretLease, request: object) -> object:
        ...


@dataclass(frozen=True, slots=True)
class ProviderEvidenceLogProjection:
    """Allowlisted logging projection with no payload or secret fields."""

    activation_state: ProviderActivationState
    operation: ProviderOperation
    provider_source: ProviderSourceIdentifier
    request_id: str
    correlation_id: str
    outcome: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if type(self.activation_state) is not ProviderActivationState:
            raise TypeError("activation state is invalid")
        if type(self.operation) is not ProviderOperation:
            raise TypeError("provider operation is invalid")
        if type(self.provider_source) is str:
            object.__setattr__(
                self, "provider_source", ProviderSourceIdentifier(value=self.provider_source),
            )
        if type(self.provider_source) is not ProviderSourceIdentifier:
            raise TypeError("provider source is invalid")
        if type(self.request_id) is not str or _IDENTIFIER_RE.fullmatch(self.request_id) is None:
            raise ValueError("request identity is invalid")
        if type(self.correlation_id) is not str or _IDENTIFIER_RE.fullmatch(self.correlation_id) is None:
            raise ValueError("correlation identity is invalid")
        object.__setattr__(
            self, "outcome",
            _allowlisted_value(self.outcome, ProviderEvidenceOutcome, "outcome"),
        )
        _require_utc_datetime(self.observed_at, "observed_at")

    def to_dict(self) -> dict[str, object]:
        return {
            "activation_state": self.activation_state.value,
            "operation": self.operation.value,
            "provider_source": str(self.provider_source),
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "outcome": self.outcome,
            "observed_at": self.observed_at.isoformat(),
        }

    def __repr__(self) -> str:
        return "ProviderEvidenceLogProjection(<bounded>)"


@runtime_checkable
class ProviderCapability(Protocol):
    """Marker protocol for opaque capabilities."""


__all__ = [
    "ActivationState",
    "AuthenticatedReadCapability", "AuthenticatedProviderReadCapability",
    "ControlledNonProductionWriteCapability",
    "ControlledWriteCapability", "MAX_CORRELATION_LENGTH", "OpaqueDestinationAllowlist",
    "OperationAllowlist", "ProviderActivationError", "ProviderActivationState",
    "ProviderAllowlist", "ProviderEnvironment",
    "ProviderEvidenceCode",
    "ProviderEvidenceLogProjection", "ProviderEvidenceOutcome", "ProviderOperation",
    "ProviderReadCapability", "ProviderRequestIdentity", "ProviderWriteCapability",
    "ProviderSecretLeaseConsumerPort", "READ_OPERATIONS", "SecretDeliveryContract",
    "ProviderReadOperation", "ProviderWriteOperation", "WRITE_OPERATIONS",
]
