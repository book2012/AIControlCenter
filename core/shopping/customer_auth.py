"""Pure trusted-verification receipt contracts for the future auth boundary.

These models describe evidence that a trusted verifier may hand to a future
session service.  Constructing a model, or passing lifecycle checks, never
authenticates a caller.  Acceptance additionally requires an injected,
server-side trusted binding context; durable single-use belongs to persistence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from core.shopping.customer_identity import (
    ClosedContract, CustomerId, UTCTimestamp, require_utc,
)


SCHEMA_VERSION = "1.0.0"
RECEIPT_MAX_LIFETIME = timedelta(minutes=5)


class VerificationPurpose(str, Enum):
    SESSION_ISSUANCE = "SESSION_ISSUANCE"


class ReceiptLifecycle(str, Enum):
    ISSUED = "ISSUED"
    CONSUMED = "CONSUMED"
    REVOKED = "REVOKED"


class ReceiptValidationResult(str, Enum):
    ACCEPTED = "ACCEPTED"
    INVALID_RECEIPT = "INVALID_RECEIPT"
    UNSUPPORTED_PURPOSE = "UNSUPPORTED_PURPOSE"
    CHALLENGE_MISMATCH = "CHALLENGE_MISMATCH"
    UNTRUSTED_PROVENANCE = "UNTRUSTED_PROVENANCE"
    INVALID_TIME = "INVALID_TIME"
    EXPIRED = "EXPIRED"
    INVALID_LIFECYCLE = "INVALID_LIFECYCLE"
    REPLAYED = "REPLAYED"
    AMBIGUOUS_BINDING = "AMBIGUOUS_BINDING"


class TrustedVerificationReceipt(ClosedContract):
    """Immutable internal evidence; it is not a credential or public response."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )

    receipt_id: str = Field(strict=True, min_length=39, max_length=39,
                            pattern=r"^AG-VRF-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")
    purpose: VerificationPurpose
    browser_challenge: str = Field(strict=True, min_length=39, max_length=39,
                                    pattern=r"^AG-CHL-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")
    issuer_ref: str = Field(strict=True, min_length=39, max_length=39,
                            pattern=r"^AG-ISS-[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$")
    customer_id: CustomerId
    issued_at: UTCTimestamp
    expires_at: UTCTimestamp
    lifecycle: ReceiptLifecycle = ReceiptLifecycle.ISSUED

    @model_validator(mode="after")
    def consistent_lifetime(self) -> TrustedVerificationReceipt:
        if self.expires_at <= self.issued_at:
            raise ValueError("receipt expiration must follow issuance")
        if self.expires_at - self.issued_at > RECEIPT_MAX_LIFETIME:
            raise ValueError("receipt lifetime exceeds the bounded policy")
        return self


@dataclass(frozen=True)
class TrustedReceiptBinding:
    """Server-side assertion that a verifier accepted one exact receipt."""

    receipt_id: str
    issuer_ref: str
    customer_id: str


@dataclass(frozen=True)
class TrustedVerificationContext:
    """Injected trust boundary; callers cannot create authority from a receipt alone.

    A production verifier will supply this context after authenticating its own
    evidence.  The pure package intentionally provides no issuer or key.
    """

    accepted_bindings: frozenset[TrustedReceiptBinding] = frozenset()
    consumed_receipt_ids: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not isinstance(self.accepted_bindings, frozenset):
            raise TypeError("accepted_bindings must be a frozenset")
        if not isinstance(self.consumed_receipt_ids, frozenset):
            raise TypeError("consumed_receipt_ids must be a frozenset")
        by_receipt: dict[str, TrustedReceiptBinding] = {}
        for binding in self.accepted_bindings:
            if not isinstance(binding, TrustedReceiptBinding):
                raise TypeError("trusted bindings must use the closed binding type")
            prior = by_receipt.get(binding.receipt_id)
            if prior is not None and prior != binding:
                raise ValueError("one receipt cannot have ambiguous trusted bindings")
            by_receipt[binding.receipt_id] = binding
        if any(type(value) is not str or not value for value in self.consumed_receipt_ids):
            raise ValueError("consumed receipt references must be non-empty strings")


def validate_trusted_receipt(
    receipt: object,
    *,
    now: datetime,
    expected_challenge: str,
    context: TrustedVerificationContext,
) -> ReceiptValidationResult:
    """Evaluate receipt policy at an injected time; all failures deny.

    The accepted binding is the server-side provenance check.  Matching an
    issuer string, customer ID, or client-provided receipt shape alone is not
    sufficient.  Atomic consume/replay prevention remains a later service
    boundary responsibility.
    """
    try:
        require_utc(now)
        if type(expected_challenge) is not str:
            return ReceiptValidationResult.CHALLENGE_MISMATCH
        if not isinstance(context, TrustedVerificationContext):
            return ReceiptValidationResult.UNTRUSTED_PROVENANCE
        if type(receipt) is not TrustedVerificationReceipt:
            return ReceiptValidationResult.INVALID_RECEIPT
        current = TrustedVerificationReceipt.model_validate(receipt)
    except (TypeError, ValueError, AttributeError, OverflowError):
        return ReceiptValidationResult.INVALID_RECEIPT

    if current.purpose is not VerificationPurpose.SESSION_ISSUANCE:
        return ReceiptValidationResult.UNSUPPORTED_PURPOSE
    if current.browser_challenge != expected_challenge:
        return ReceiptValidationResult.CHALLENGE_MISMATCH
    if current.expires_at <= current.issued_at or current.expires_at - current.issued_at > RECEIPT_MAX_LIFETIME:
        return ReceiptValidationResult.INVALID_TIME
    if now < current.issued_at:
        return ReceiptValidationResult.INVALID_TIME
    if now >= current.expires_at:
        return ReceiptValidationResult.EXPIRED
    if current.lifecycle is ReceiptLifecycle.CONSUMED or current.lifecycle is ReceiptLifecycle.REVOKED:
        return ReceiptValidationResult.INVALID_LIFECYCLE
    if current.receipt_id in context.consumed_receipt_ids:
        return ReceiptValidationResult.REPLAYED
    matches = [binding for binding in context.accepted_bindings
               if binding.receipt_id == current.receipt_id]
    if len(matches) > 1:
        return ReceiptValidationResult.AMBIGUOUS_BINDING
    if not matches:
        return ReceiptValidationResult.UNTRUSTED_PROVENANCE
    binding = matches[0]
    if (binding.issuer_ref != current.issuer_ref
            or binding.customer_id != current.customer_id):
        return ReceiptValidationResult.UNTRUSTED_PROVENANCE
    return ReceiptValidationResult.ACCEPTED


def receipt_is_accepted(*args: object, **kwargs: object) -> bool:
    """Boolean convenience wrapper; it never implies durable consumption."""
    return validate_trusted_receipt(*args, **kwargs) is ReceiptValidationResult.ACCEPTED
