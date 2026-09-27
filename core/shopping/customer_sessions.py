"""Pure session lifecycle contracts, with no credential verification or authority.

ELIGIBLE means only that supplied records satisfy this policy at the injected
time. Even a well-formed private record can be fabricated. Trusted loading and
credential verification belong to a future adapter; no result here authenticates
a customer, issues a token, or authorizes an inquiry (including legacy tokens).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
import re
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator, model_validator

from core.shopping.customer_identity import (
    ClosedContract, ContactReference, Customer, CustomerId, CustomerState,
    UTCTimestamp, VerificationState, _current_customer, require_utc,
)


IDLE_LIFETIME = timedelta(minutes=30)
ABSOLUTE_LIFETIME = timedelta(hours=24)
SessionId = Annotated[str, Field(strict=True, min_length=39, max_length=39,
    pattern=r"^AG-SES-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")]


class CustomerSession(ClosedContract):
    """Secret-free lifecycle metadata. Version 1 fixes the 30m/24h lifetimes."""

    id: SessionId
    customer_id: CustomerId
    created_at: UTCTimestamp
    last_activity_at: UTCTimestamp
    idle_expires_at: UTCTimestamp
    absolute_expires_at: UTCTimestamp
    revoked_at: UTCTimestamp | None = None

    @model_validator(mode="after")
    def consistent_lifetime(self) -> CustomerSession:
        if not self.created_at <= self.last_activity_at < self.absolute_expires_at:
            raise ValueError("activity must be within the absolute session lifetime")
        try:
            absolute = self.created_at + ABSOLUTE_LIFETIME
            idle = self.last_activity_at + IDLE_LIFETIME
        except OverflowError:
            raise ValueError("session lifetime exceeds timestamp bounds") from None
        if self.absolute_expires_at != absolute or self.idle_expires_at != idle:
            raise ValueError("expiration timestamps must match the v1 lifetimes")
        if self.revoked_at is not None and self.revoked_at < self.last_activity_at:
            raise ValueError("revocation cannot precede the latest activity")
        return self


class PrivateSessionRecord(ClosedContract):
    """Server-side input only. Private fields are excluded from dumps and repr.

    The hash is opaque metadata, never compared to a credential here. Its shape
    and presence are necessary for policy eligibility, but prove no authenticity.
    """

    session: CustomerSession
    session_secret_hash: SecretStr = Field(exclude=True, repr=False)
    security_policy_version: Literal["1.0.0"] = Field(exclude=True, repr=False)
    credential_bound_at: UTCTimestamp = Field(exclude=True, repr=False)
    verified_contact_ref: ContactReference = Field(exclude=True, repr=False)
    contact_verified_at: UTCTimestamp = Field(exclude=True, repr=False)

    @field_validator("session_secret_hash")
    @classmethod
    def valid_hash_metadata(cls, value: SecretStr) -> SecretStr:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", value.get_secret_value()):
            raise ValueError("a versioned session hash is required")
        return value

    @model_validator(mode="after")
    def consistent_security_metadata(self) -> PrivateSessionRecord:
        if (self.credential_bound_at != self.session.created_at
                or self.contact_verified_at > self.credential_bound_at):
            raise ValueError("security metadata must be bound at session creation after verification")
        return self


class SafeSessionProjection(CustomerSession):
    """Explicit public field allowlist, containing no security metadata or authority."""


class SessionPolicyStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INVALID_RECORD = "INVALID_RECORD"
    INVALID_TIME = "INVALID_TIME"
    CUSTOMER_INACTIVE = "CUSTOMER_INACTIVE"
    CONTACT_UNVERIFIED = "CONTACT_UNVERIFIED"
    BINDING_MISMATCH = "BINDING_MISMATCH"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


def evaluate_session(record: object, customer: object, *, now: datetime) -> SessionPolicyStatus:
    """Fail closed, revalidating even model_construct/model_copy inputs.

    Mappings (including client JSON) and public projections cannot stand in for
    private records. This is lifecycle eligibility, never authentication proof.
    """
    try:
        require_utc(now)
    except (ValueError, TypeError, AttributeError, OverflowError):
        return SessionPolicyStatus.INVALID_TIME
    try:
        if type(record) is not PrivateSessionRecord or type(customer) is not Customer:
            return SessionPolicyStatus.INVALID_RECORD
        record = PrivateSessionRecord.model_validate(record)
        customer = _current_customer(customer, now)
        session = record.session
        if (session.created_at < customer.created_at or session.last_activity_at > now
                or (session.revoked_at is not None and session.revoked_at > now)):
            return SessionPolicyStatus.INVALID_TIME
        if session.customer_id != customer.id:
            return SessionPolicyStatus.BINDING_MISMATCH
        if customer.state is not CustomerState.ACTIVE:
            return SessionPolicyStatus.CUSTOMER_INACTIVE
        binding = customer.contact_binding
        if binding is None or binding.state is not VerificationState.VERIFIED:
            return SessionPolicyStatus.CONTACT_UNVERIFIED
        if (binding.contact_ref != record.verified_contact_ref
                or binding.verified_at != record.contact_verified_at):
            return SessionPolicyStatus.BINDING_MISMATCH
        if session.revoked_at is not None:
            return SessionPolicyStatus.REVOKED
        if now >= session.idle_expires_at or now >= session.absolute_expires_at:
            return SessionPolicyStatus.EXPIRED
        return SessionPolicyStatus.ELIGIBLE
    except (ValueError, TypeError, AttributeError, OverflowError):
        return SessionPolicyStatus.INVALID_RECORD


def safe_session_projection(record: object, customer: object, *,
                            now: datetime) -> SafeSessionProjection | None:
    """Project eligible metadata only; never serialize a private record as a response."""
    if evaluate_session(record, customer, now=now) is not SessionPolicyStatus.ELIGIBLE:
        return None
    session = PrivateSessionRecord.model_validate(record).session
    return SafeSessionProjection(
        id=session.id, customer_id=session.customer_id, created_at=session.created_at,
        last_activity_at=session.last_activity_at, idle_expires_at=session.idle_expires_at,
        absolute_expires_at=session.absolute_expires_at, revoked_at=session.revoked_at,
    )


def with_session_activity(record: PrivateSessionRecord, customer: Customer, *,
                          now: datetime) -> PrivateSessionRecord:
    """Return an updated inert record, without persistence or absolute-life extension.

    An expired session cannot be revived, and activity cannot move backwards.
    Credential verification must happen elsewhere before any future caller uses it.
    """
    if evaluate_session(record, customer, now=now) is not SessionPolicyStatus.ELIGIBLE:
        raise ValueError("session is not eligible for an activity update")
    record = PrivateSessionRecord.model_validate(record)
    session = CustomerSession.model_validate({
        **record.session.model_dump(), "last_activity_at": now,
        "idle_expires_at": now + IDLE_LIFETIME,
    })
    return PrivateSessionRecord.model_validate(record.model_copy(update={"session": session}))
