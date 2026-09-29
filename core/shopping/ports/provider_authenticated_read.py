"""Provider-neutral authenticated read/evidence contracts for C5.

Only bounded, normalized evidence crosses this module.  A provider-specific
transport may use raw SDK data internally in a later package, but raw payloads
are not part of these contracts and cannot be returned, logged, or persisted
here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol, runtime_checkable

from pydantic import ConfigDict, Field, field_validator, model_validator

from core.shopping.customer_identity import ClosedContract, UTCTimestamp
from core.shopping.ports.phone_verification import (
    ProviderSourceIdentifier, ProviderVerificationIdentifier,
)
from core.shopping.ports.phone_verification_reconciliation import (
    ReconciliationResult, StartReconciliationCommand, VerifyReconciliationCommand,
    VerificationReconciliationCapability,
)
from .provider_activation import (
    AuthenticatedReadCapability, ProviderOperation, ProviderRequestIdentity,
    ProviderEvidenceCode, READ_OPERATIONS, _allowlisted_value, _require_utc_datetime,
)


class ProviderReadStatus(str, Enum):
    HEALTHY = "HEALTHY"
    AVAILABLE = "AVAILABLE"
    NOT_FOUND = "NOT_FOUND"
    REJECTED = "REJECTED"
    UNAVAILABLE = "UNAVAILABLE"
    MALFORMED = "MALFORMED"
    UNKNOWN_OUTCOME = "UNKNOWN_OUTCOME"


class ProviderReadError(RuntimeError):
    """Safe read failure with an allowlisted reason code only."""

    _ALLOWED = frozenset(status.value for status in ProviderReadStatus)

    def __init__(self, reason_code: str = "UNKNOWN_OUTCOME") -> None:
        code = reason_code if type(reason_code) is str and reason_code in self._ALLOWED else "UNKNOWN_OUTCOME"
        self.reason_code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"ProviderReadError(reason_code={self.reason_code!r})"


class ProviderReadRequest(ClosedContract):
    """Bounded read request with no URL, credential, phone, or raw payload."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )

    provider_source: ProviderSourceIdentifier
    operation: ProviderOperation
    identity: ProviderRequestIdentity
    lookup_reference: ProviderVerificationIdentifier | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_nested_values(cls, value: object) -> object:
        if isinstance(value, dict):
            payload = dict(value)
            if type(payload.get("provider_source")) is str:
                payload["provider_source"] = ProviderSourceIdentifier(
                    value=payload["provider_source"]
                )
            if isinstance(payload.get("identity"), dict):
                payload["identity"] = ProviderRequestIdentity.model_validate(
                    payload["identity"]
                )
            if type(payload.get("lookup_reference")) is str:
                payload["lookup_reference"] = ProviderVerificationIdentifier(
                    value=payload["lookup_reference"]
                )
            return payload
        return value

    @model_validator(mode="after")
    def read_operation_only(self) -> "ProviderReadRequest":
        if self.operation not in READ_OPERATIONS:
            raise ValueError("authenticated read operation is required")
        return self

    def __repr__(self) -> str:
        return (
            "ProviderReadRequest(provider_source=<bounded>, "
            f"operation={self.operation.value!r}, identity={self.identity!r})"
        )


class ProviderReadResult(ClosedContract):
    """Normalized provider read result; raw response data is impossible here."""

    provider_source: ProviderSourceIdentifier
    operation: ProviderOperation
    identity: ProviderRequestIdentity
    status: ProviderReadStatus
    observed_at: UTCTimestamp
    provider_verification_id: ProviderVerificationIdentifier | None = None
    provider_expires_at: UTCTimestamp | None = None
    evidence_code: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("observed_at", mode="before")
    @classmethod
    def require_observed_at_datetime(cls, value: object) -> object:
        return _require_utc_datetime(value, "observed_at")

    @field_validator("provider_expires_at", mode="before")
    @classmethod
    def require_expiry_datetime(cls, value: object) -> object:
        if value is None:
            return value
        return _require_utc_datetime(value, "provider_expires_at")

    @field_validator("evidence_code", mode="before")
    @classmethod
    def require_allowlisted_evidence_code(cls, value: object) -> object:
        if value is None:
            return value
        return _allowlisted_value(value, ProviderEvidenceCode, "evidence_code")

    @model_validator(mode="before")
    @classmethod
    def normalize_nested_values(cls, value: object) -> object:
        if isinstance(value, dict):
            payload = dict(value)
            if type(payload.get("provider_source")) is str:
                payload["provider_source"] = ProviderSourceIdentifier(
                    value=payload["provider_source"]
                )
            if isinstance(payload.get("identity"), dict):
                payload["identity"] = ProviderRequestIdentity.model_validate(
                    payload["identity"]
                )
            if type(payload.get("provider_verification_id")) is str:
                payload["provider_verification_id"] = ProviderVerificationIdentifier(
                    value=payload["provider_verification_id"]
                )
            return payload
        return value

    @model_validator(mode="after")
    def read_operation_only(self) -> "ProviderReadResult":
        if self.operation not in READ_OPERATIONS:
            raise ValueError("authenticated read operation is required")
        if self.status is ProviderReadStatus.HEALTHY and self.operation is not ProviderOperation.READ_HEALTH:
            raise ValueError("HEALTHY is reserved for provider health reads")
        return self

    def to_log_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "provider_source": str(self.provider_source),
            "operation": self.operation.value,
            "request_id": self.identity.request_id,
            "correlation_id": self.identity.correlation_id,
            "status": self.status.value,
            "observed_at": self.observed_at.isoformat(),
        }
        if self.evidence_code is not None:
            result["evidence_code"] = self.evidence_code
        return result

    def __repr__(self) -> str:
        return "ProviderReadResult(<bounded normalized evidence>)"


@dataclass(frozen=True, slots=True)
class NormalizedProviderEvidence:
    """Opaque provider evidence admitted after normalization."""

    provider_source: ProviderSourceIdentifier
    operation: ProviderOperation
    status: ProviderReadStatus
    observed_at: datetime
    provider_verification_id: ProviderVerificationIdentifier | None = None
    provider_expires_at: datetime | None = None
    evidence_code: str | None = None

    def __post_init__(self) -> None:
        if type(self.provider_source) is not ProviderSourceIdentifier:
            raise TypeError("provider source is invalid")
        if type(self.operation) is not ProviderOperation or self.operation not in READ_OPERATIONS:
            raise ValueError("authenticated read operation is required")
        if type(self.status) is not ProviderReadStatus:
            raise TypeError("provider read status is invalid")
        if (
            self.provider_verification_id is not None
            and type(self.provider_verification_id) is not ProviderVerificationIdentifier
        ):
            raise TypeError("provider verification identifier is invalid")
        _require_utc_datetime(self.observed_at, "observed_at")
        if self.provider_expires_at is not None:
            _require_utc_datetime(self.provider_expires_at, "provider_expires_at")
        if self.evidence_code is not None:
            object.__setattr__(
                self, "evidence_code",
                _allowlisted_value(self.evidence_code, ProviderEvidenceCode, "evidence_code"),
            )

    def to_log_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "provider_source": str(self.provider_source),
            "operation": self.operation.value,
            "status": self.status.value,
            "observed_at": self.observed_at.isoformat(),
        }
        if self.evidence_code is not None:
            value["evidence_code"] = self.evidence_code
        return value

    def __repr__(self) -> str:
        return "NormalizedProviderEvidence(<bounded>)"


@runtime_checkable
class AuthenticatedProviderReadPort(Protocol):
    """Future provider-specific authenticated read transport boundary."""

    def read(
        self,
        request: ProviderReadRequest,
        *,
        capability: AuthenticatedReadCapability,
    ) -> ProviderReadResult:
        ...


ProviderAuthenticatedReadPort = AuthenticatedProviderReadPort


@runtime_checkable
class ProviderEvidenceNormalizationPort(Protocol):
    """Normalize provider-specific observations before C4 admission."""

    def normalize(self, result: ProviderReadResult) -> NormalizedProviderEvidence:
        ...


class ProviderEvidenceNormalizationError(RuntimeError):
    """Safe normalization failure with no provider payload text."""

    _ALLOWED = frozenset({
        "EVIDENCE_REJECTED",
        "RECONCILIATION_COMMAND_REJECTED",
        "EVIDENCE_BINDING_REJECTED",
    })

    def __init__(self, reason_code: str = "EVIDENCE_REJECTED") -> None:
        code = reason_code if type(reason_code) is str and reason_code in self._ALLOWED else "EVIDENCE_REJECTED"
        self.reason_code = code
        super().__init__(code)

    def __repr__(self) -> str:
        return f"ProviderEvidenceNormalizationError(reason_code={self.reason_code!r})"


class ProviderEvidenceReconciliationAdapter:
    """C4 admission seam that has no persistence or SQLite authority.

    The adapter accepts only normalized C5 evidence and forwards an existing
    C4 command to the injected reconciliation port.  The port, not this
    adapter or a provider, remains the sole durable reconciliation writer.
    """

    __slots__ = ("_reconciliation",)

    def __init__(self, reconciliation_port: object) -> None:
        if not callable(getattr(reconciliation_port, "reconcile_start", None)) or not callable(
            getattr(reconciliation_port, "reconcile_verify", None)
        ):
            raise TypeError("a reconciliation port is required")
        self._reconciliation = reconciliation_port

    @staticmethod
    def normalize(result: ProviderReadResult) -> NormalizedProviderEvidence:
        if type(result) is not ProviderReadResult:
            raise ProviderEvidenceNormalizationError()
        try:
            return NormalizedProviderEvidence(
                provider_source=result.provider_source,
                operation=result.operation,
                status=result.status,
                observed_at=result.observed_at,
                provider_verification_id=result.provider_verification_id,
                provider_expires_at=result.provider_expires_at,
                evidence_code=result.evidence_code,
            )
        except (TypeError, ValueError):
            raise ProviderEvidenceNormalizationError() from None

    def reconcile(
        self,
        command: StartReconciliationCommand | VerifyReconciliationCommand,
        *,
        capability: VerificationReconciliationCapability,
    ) -> ReconciliationResult:
        if type(command) is StartReconciliationCommand:
            return self._reconciliation.reconcile_start(command, capability=capability)
        if type(command) is VerifyReconciliationCommand:
            return self._reconciliation.reconcile_verify(command, capability=capability)
        raise ProviderEvidenceNormalizationError("RECONCILIATION_COMMAND_REJECTED")

    def admit(
        self,
        evidence: NormalizedProviderEvidence,
        command: StartReconciliationCommand | VerifyReconciliationCommand,
        *,
        capability: VerificationReconciliationCapability,
    ) -> ReconciliationResult:
        """Admit only normalized, command-bound evidence into C4."""
        if type(evidence) is not NormalizedProviderEvidence:
            raise ProviderEvidenceNormalizationError()
        if type(command) not in {StartReconciliationCommand, VerifyReconciliationCommand}:
            raise ProviderEvidenceNormalizationError("RECONCILIATION_COMMAND_REJECTED")
        if (
            evidence.status is ProviderReadStatus.UNKNOWN_OUTCOME
            or evidence.evidence_code == ProviderEvidenceCode.PROVIDER_UNKNOWN_OUTCOME.value
        ):
            raise ProviderEvidenceNormalizationError("EVIDENCE_REJECTED")
        if evidence.provider_source != command.provider_source:
            raise ProviderEvidenceNormalizationError("EVIDENCE_BINDING_REJECTED")
        evidence_provider_id = evidence.provider_verification_id
        command_provider_id = getattr(command, "provider_verification_id", None)
        if (
            evidence_provider_id is not None
            and type(evidence_provider_id) is not ProviderVerificationIdentifier
        ) or (
            command_provider_id is not None
            and type(command_provider_id) is not ProviderVerificationIdentifier
        ):
            raise ProviderEvidenceNormalizationError("EVIDENCE_BINDING_REJECTED")
        if evidence_provider_id != command_provider_id:
            raise ProviderEvidenceNormalizationError("EVIDENCE_BINDING_REJECTED")
        return self.reconcile(command, capability=capability)


__all__ = [
    "AuthenticatedProviderReadPort", "NormalizedProviderEvidence",
    "ProviderAuthenticatedReadPort", "ProviderEvidenceNormalizationError",
    "ProviderEvidenceNormalizationPort", "ProviderEvidenceReconciliationAdapter",
    "ProviderReadError", "ProviderReadRequest", "ProviderReadResult",
    "ProviderReadStatus",
]
