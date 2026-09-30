from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import re
import secrets

from core.shopping.adapters.twilio_verify_read import (
    TWILIO_PROVIDER_SOURCE,
    TwilioServiceSid,
    TwilioVerificationSid,
)
from core.shopping.ports.provider_activation import (
    AuthenticatedReadCapability,
    ProviderOperation,
    ProviderRequestIdentity,
)


MAX_CAPABILITY_TTL_SECONDS = 60
AUTHORITY_RECORD_RETENTION_SECONDS = MAX_CAPABILITY_TTL_SECONDS

_PROVIDER_RE = re.compile(r"[A-Za-z0-9._-]{1,64}\Z")
_OPAQUE_ID_RE = re.compile(r"[A-Za-z0-9._-]{16,64}\Z")


class TwilioAuthorizationReason(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    CAPABILITY_REQUIRED = "CAPABILITY_REQUIRED"
    CAPABILITY_UNTRUSTED = "CAPABILITY_UNTRUSTED"
    CAPABILITY_EXPIRED = "CAPABILITY_EXPIRED"
    CAPABILITY_ALREADY_USED = "CAPABILITY_ALREADY_USED"
    PROVIDER_BINDING_REJECTED = "PROVIDER_BINDING_REJECTED"
    OPERATION_BINDING_REJECTED = "OPERATION_BINDING_REJECTED"
    IDENTITY_BINDING_REJECTED = "IDENTITY_BINDING_REJECTED"
    SERVICE_BINDING_REJECTED = "SERVICE_BINDING_REJECTED"
    VERIFICATION_BINDING_REJECTED = "VERIFICATION_BINDING_REJECTED"
    INVALID_REQUEST = "INVALID_REQUEST"


class TwilioAuthenticatedReadAuthorizationError(RuntimeError):
    """Bounded authorization failure with no secret or provider payload."""

    def __init__(
        self,
        reason: TwilioAuthorizationReason = (
            TwilioAuthorizationReason.INVALID_REQUEST
        ),
    ) -> None:
        if type(reason) is not TwilioAuthorizationReason:
            reason = TwilioAuthorizationReason.INVALID_REQUEST

        self.reason = reason
        super().__init__(reason.value)

    @property
    def reason_code(self) -> str:
        return self.reason.value

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadAuthorizationError("
            f"reason_code={self.reason.value!r})"
        )


class TwilioAuthenticatedReadCapability(
    AuthenticatedReadCapability
):
    """Opaque capability trusted only when present in authority state."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class TwilioAuthenticatedReadRequest:
    provider_source: str
    operation: ProviderOperation
    identity: ProviderRequestIdentity
    service_sid: TwilioServiceSid
    verification_sid: TwilioVerificationSid | None = None

    def __post_init__(self) -> None:
        if (
            type(self.provider_source) is not str
            or _PROVIDER_RE.fullmatch(self.provider_source) is None
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

        if type(self.operation) is not ProviderOperation:
            raise TwilioAuthenticatedReadAuthorizationError()

        if self.operation not in {
            ProviderOperation.READ_HEALTH,
            ProviderOperation.READ_EVIDENCE,
        }:
            raise TwilioAuthenticatedReadAuthorizationError()

        if type(self.identity) is not ProviderRequestIdentity:
            raise TwilioAuthenticatedReadAuthorizationError()

        if type(self.service_sid) is not TwilioServiceSid:
            raise TwilioAuthenticatedReadAuthorizationError()

        if (
            self.verification_sid is not None
            and type(self.verification_sid)
            is not TwilioVerificationSid
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

        if (
            self.operation is ProviderOperation.READ_HEALTH
            and self.verification_sid is not None
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

        if (
            self.operation is ProviderOperation.READ_EVIDENCE
            and self.verification_sid is None
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadRequest("
            f"provider_source={self.provider_source!r}, "
            f"operation={self.operation.value!r}, "
            "identity=<bounded>, service_sid=<bounded>, "
            "verification_sid=<bounded>)"
        )


@dataclass(frozen=True, slots=True)
class TwilioAuthenticatedReadDecision:
    allowed: bool
    reason: TwilioAuthorizationReason
    provider_source: str
    operation: ProviderOperation
    request_id: str
    correlation_id: str
    observed_at: datetime
    issuance_id: str | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if type(self.allowed) is not bool:
            raise TypeError("authorization decision is invalid")

        if type(self.reason) is not TwilioAuthorizationReason:
            raise TypeError("authorization reason is invalid")

        if self.allowed and self.reason is not TwilioAuthorizationReason.AUTHORIZED:
            raise ValueError("allowed decision requires AUTHORIZED")

        if not self.allowed and self.reason is TwilioAuthorizationReason.AUTHORIZED:
            raise ValueError("denied decision cannot be AUTHORIZED")

    @property
    def reason_code(self) -> str:
        return self.reason.value

    def to_log_dict(self) -> dict[str, object]:
        value: dict[str, object] = {
            "allowed": self.allowed,
            "reason_code": self.reason.value,
            "provider_source": self.provider_source,
            "operation": self.operation.value,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "observed_at": self.observed_at.isoformat(),
        }

        if self.issuance_id is not None:
            value["issuance_id"] = self.issuance_id

        if self.expires_at is not None:
            value["expires_at"] = self.expires_at.isoformat()

        return value

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadDecision("
            f"allowed={self.allowed!r}, "
            f"reason={self.reason.value!r}, "
            "resource=<bounded>)"
        )


@dataclass(frozen=True, slots=True)
class _IssuedCapabilityRecord:
    issuance_id: str
    request: TwilioAuthenticatedReadRequest
    issued_at: datetime
    expires_at: datetime


def _require_utc(value: object) -> datetime:
    if type(value) is not datetime:
        raise TwilioAuthenticatedReadAuthorizationError()

    if value.tzinfo is None or value.utcoffset() is None:
        raise TwilioAuthenticatedReadAuthorizationError()

    if value.utcoffset() != timedelta(0):
        raise TwilioAuthenticatedReadAuthorizationError()

    return value


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def _default_id_factory() -> str:
    return secrets.token_hex(16)


class TwilioAuthenticatedReadAuthority:
    """AIControlCenter-owned, offline provider-specific capability authority."""

    __slots__ = (
        "_clock",
        "_id_factory",
        "_issued",
        "_used",
    )

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._clock = clock or _default_clock
        self._id_factory = id_factory or _default_id_factory
        self._issued: dict[
            TwilioAuthenticatedReadCapability,
            _IssuedCapabilityRecord,
        ] = {}
        self._used: set[
            TwilioAuthenticatedReadCapability
        ] = set()

    def _now(self) -> datetime:
        return _require_utc(self._clock())

    @staticmethod
    def _validate_issuance_id(value: object) -> str:
        if (
            type(value) is not str
            or _OPAQUE_ID_RE.fullmatch(value) is None
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

        return value

    def _prune_retired(
        self,
        observed_at: datetime,
    ) -> None:
        retired = [
            capability
            for capability, record in self._issued.items()
            if observed_at
            >= record.expires_at
            + timedelta(
                seconds=AUTHORITY_RECORD_RETENTION_SECONDS
            )
        ]

        for capability in retired:
            self._issued.pop(
                capability,
                None,
            )
            self._used.discard(
                capability
            )

    def issue(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        ttl_seconds: int = MAX_CAPABILITY_TTL_SECONDS,
    ) -> TwilioAuthenticatedReadCapability:
        if type(request) is not TwilioAuthenticatedReadRequest:
            raise TwilioAuthenticatedReadAuthorizationError()

        if request.provider_source != TWILIO_PROVIDER_SOURCE:
            raise TwilioAuthenticatedReadAuthorizationError(
                TwilioAuthorizationReason.PROVIDER_BINDING_REJECTED
            )

        if (
            type(ttl_seconds) is not int
            or ttl_seconds < 1
            or ttl_seconds > MAX_CAPABILITY_TTL_SECONDS
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

        issued_at = self._now()
        self._prune_retired(
            issued_at
        )
        expires_at = issued_at + timedelta(
            seconds=ttl_seconds
        )

        issuance_id = self._validate_issuance_id(
            self._id_factory()
        )

        if any(
            record.issuance_id == issuance_id
            for record in self._issued.values()
        ):
            raise TwilioAuthenticatedReadAuthorizationError()

        capability = object.__new__(
            TwilioAuthenticatedReadCapability
        )

        self._issued[capability] = _IssuedCapabilityRecord(
            issuance_id=issuance_id,
            request=request,
            issued_at=issued_at,
            expires_at=expires_at,
        )

        return capability

    def _decision(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        allowed: bool,
        reason: TwilioAuthorizationReason,
        observed_at: datetime,
        record: _IssuedCapabilityRecord | None = None,
    ) -> TwilioAuthenticatedReadDecision:
        return TwilioAuthenticatedReadDecision(
            allowed=allowed,
            reason=reason,
            provider_source=request.provider_source,
            operation=request.operation,
            request_id=request.identity.request_id,
            correlation_id=request.identity.correlation_id,
            observed_at=observed_at,
            issuance_id=(
                record.issuance_id
                if record is not None
                else None
            ),
            expires_at=(
                record.expires_at
                if record is not None
                else None
            ),
        )

    def authorize_once(
        self,
        request: TwilioAuthenticatedReadRequest,
        *,
        capability: object | None,
    ) -> TwilioAuthenticatedReadDecision:
        if type(request) is not TwilioAuthenticatedReadRequest:
            raise TwilioAuthenticatedReadAuthorizationError()

        observed_at = self._now()
        self._prune_retired(
            observed_at
        )

        if capability is None:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.CAPABILITY_REQUIRED,
                observed_at=observed_at,
            )

        if type(capability) is not TwilioAuthenticatedReadCapability:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.CAPABILITY_UNTRUSTED,
                observed_at=observed_at,
            )

        record = self._issued.get(capability)

        if record is None:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.CAPABILITY_UNTRUSTED,
                observed_at=observed_at,
            )

        if capability in self._used:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.CAPABILITY_ALREADY_USED,
                observed_at=observed_at,
                record=record,
            )

        # Any first trusted authorization attempt consumes the capability.
        # This prevents correcting a failed binding and retrying it.
        self._used.add(capability)

        if observed_at >= record.expires_at:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.CAPABILITY_EXPIRED,
                observed_at=observed_at,
                record=record,
            )

        expected = record.request

        if request.provider_source != expected.provider_source:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.PROVIDER_BINDING_REJECTED,
                observed_at=observed_at,
                record=record,
            )

        if request.operation is not expected.operation:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.OPERATION_BINDING_REJECTED,
                observed_at=observed_at,
                record=record,
            )

        if (
            request.identity.request_id
            != expected.identity.request_id
            or request.identity.correlation_id
            != expected.identity.correlation_id
        ):
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.IDENTITY_BINDING_REJECTED,
                observed_at=observed_at,
                record=record,
            )

        if request.service_sid != expected.service_sid:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.SERVICE_BINDING_REJECTED,
                observed_at=observed_at,
                record=record,
            )

        if request.verification_sid != expected.verification_sid:
            return self._decision(
                request,
                allowed=False,
                reason=TwilioAuthorizationReason.VERIFICATION_BINDING_REJECTED,
                observed_at=observed_at,
                record=record,
            )

        return self._decision(
            request,
            allowed=True,
            reason=TwilioAuthorizationReason.AUTHORIZED,
            observed_at=observed_at,
            record=record,
        )

    @property
    def issued_count(self) -> int:
        return len(self._issued)

    @property
    def consumed_count(self) -> int:
        return len(self._used)

    @property
    def network_enabled(self) -> bool:
        return False

    @property
    def credential_resolution_enabled(self) -> bool:
        return False

    def __repr__(self) -> str:
        return (
            "TwilioAuthenticatedReadAuthority("
            "<trusted offline authority>)"
        )
