"""Inert v1 customer records and pure policies, never authentication evidence.

Only a future trusted adapter may establish verification provenance. Parsing a
client's claims into these models does not establish identity or inquiry access.
Opaque IDs must be independently allocated, never computed from phone numbers;
syntax validation cannot establish their provenance. No contact data is stored.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator


SCHEMA_VERSION = "1.0.0"
# Shopping's AG-* namespace, with a bounded UUID4-shaped opaque suffix.
_OPAQUE_SUFFIX = r"[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$"
CustomerId = Annotated[str, Field(strict=True, min_length=39, max_length=39,
                                  pattern=r"^AG-CUS-" + _OPAQUE_SUFFIX)]
ContactReference = Annotated[str, Field(strict=True, min_length=39, max_length=39,
                                        pattern=r"^AG-CON-" + _OPAQUE_SUFFIX)]
PolicyVersion = Annotated[str, Field(strict=True, min_length=1, max_length=64,
                                     pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]


def _timestamp_input(value: object) -> object:
    if (not isinstance(value, (datetime, str)) or
            (isinstance(value, str) and ("T" not in value or not value.endswith(("Z", "+00:00"))))):
        raise ValueError("timestamp must be an explicit UTC datetime or ISO timestamp")
    return value


def require_utc(value: datetime) -> datetime:
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() != timedelta(0)):
        raise ValueError("timestamp must be timezone-aware UTC")
    return value


UTCTimestamp = Annotated[datetime, BeforeValidator(_timestamp_input), AfterValidator(require_utc)]


class ClosedContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_default=True,
                              revalidate_instances="always", hide_input_in_errors=True)
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION


class CustomerState(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class VerificationState(str, Enum):
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    REVERIFICATION_REQUIRED = "REVERIFICATION_REQUIRED"
    REVOKED = "REVOKED"


class ConsentState(str, Enum):
    NOT_GRANTED = "NOT_GRANTED"
    GRANTED = "GRANTED"
    WITHDRAWN = "WITHDRAWN"


class ConsentPurpose(str, Enum):
    SMS_VERIFICATION = "SMS_VERIFICATION"
    SMS_NOTIFICATION = "SMS_NOTIFICATION"
    SMS_MARKETING = "SMS_MARKETING"


class VerifiedContactBinding(ClosedContract):
    customer_id: CustomerId
    state: VerificationState
    created_at: UTCTimestamp
    updated_at: UTCTimestamp
    contact_ref: ContactReference | None = None
    verified_at: UTCTimestamp | None = None
    revoked_at: UTCTimestamp | None = None

    @model_validator(mode="after")
    def consistent_binding(self) -> VerifiedContactBinding:
        if self.updated_at < self.created_at:
            raise ValueError("binding update precedes creation")
        if self.state is VerificationState.UNVERIFIED:
            if any(value is not None for value in
                   (self.contact_ref, self.verified_at, self.revoked_at)):
                raise ValueError("unverified binding cannot claim a verified contact")
        else:
            if self.contact_ref is None or self.verified_at is None:
                raise ValueError("previous verification and an opaque contact reference are required")
            if not self.created_at <= self.verified_at <= self.updated_at:
                raise ValueError("verification timestamp is outside the binding lifetime")
            if self.state is VerificationState.REVOKED:
                if self.revoked_at is None or not self.verified_at <= self.revoked_at <= self.updated_at:
                    raise ValueError("revoked binding requires a consistent revocation timestamp")
            elif self.revoked_at is not None:
                raise ValueError("only a revoked binding may have a revocation timestamp")
        return self


class PurposeSpecificConsent(ClosedContract):
    """One current decision per purpose, with explicit time and policy version."""

    customer_id: CustomerId
    purpose: ConsentPurpose
    state: ConsentState
    decided_at: UTCTimestamp
    policy_version: PolicyVersion


class Customer(ClosedContract):
    id: CustomerId
    state: CustomerState
    created_at: UTCTimestamp
    updated_at: UTCTimestamp
    contact_binding: VerifiedContactBinding | None = None
    consents: tuple[PurposeSpecificConsent, ...] = Field(default=(), max_length=3)

    @model_validator(mode="after")
    def consistent_identity(self) -> Customer:
        if self.updated_at < self.created_at:
            raise ValueError("customer update precedes creation")
        binding = self.contact_binding
        if binding is not None:
            if binding.customer_id != self.id:
                raise ValueError("contact binding belongs to another customer")
            if not self.created_at <= binding.created_at <= binding.updated_at <= self.updated_at:
                raise ValueError("contact binding timestamps are outside the customer lifetime")
            if (self.state is CustomerState.CLOSED and binding.state not in
                    (VerificationState.UNVERIFIED, VerificationState.REVOKED)):
                raise ValueError("closed customer cannot retain an unrevoked verified binding")
        purposes = set()
        for consent in self.consents:
            if consent.customer_id != self.id or consent.purpose in purposes:
                raise ValueError("consent must belong to this customer and have a unique purpose")
            if not self.created_at <= consent.decided_at <= self.updated_at:
                raise ValueError("consent timestamp is outside the customer lifetime")
            purposes.add(consent.purpose)
        return self


def _current_customer(customer: object, now: datetime) -> Customer:
    require_utc(now)
    if type(customer) is not Customer:
        raise ValueError("a customer contract is required")
    customer = Customer.model_validate(customer)
    if customer.updated_at > now:
        raise ValueError("customer record is in the future")
    return customer


def customer_is_session_eligible(customer: object, *, now: datetime) -> bool:
    """Record consistency only; True is not proof of customer authentication."""
    try:
        current = _current_customer(customer, now)
        return (current.state is CustomerState.ACTIVE and current.contact_binding is not None
                and current.contact_binding.state is VerificationState.VERIFIED)
    except (ValueError, TypeError, AttributeError, OverflowError):
        return False


def has_current_consent(customer: object, purpose: ConsentPurpose, *,
                        policy_version: str, now: datetime) -> bool:
    """Missing, withdrawn, stale-policy or ambiguous decisions never grant consent.

    Verification, notification and marketing are separate purposes. A positive
    result describes a supplied record; it neither verifies its source nor sends SMS.
    """
    try:
        current = _current_customer(customer, now)
        if current.state is not CustomerState.ACTIVE or type(purpose) is not ConsentPurpose:
            return False
        return any(consent.purpose is purpose and consent.state is ConsentState.GRANTED
                   and consent.policy_version == policy_version for consent in current.consents)
    except (ValueError, TypeError, AttributeError, OverflowError):
        return False
