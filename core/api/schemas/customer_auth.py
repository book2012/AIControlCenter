"""Closed public contracts for the future customer-verification boundary.

Requests contain only opaque caller references.  Trusted issuer, identity,
verification and session authority remain internal to a future server-side
adapter and are deliberately absent from these models.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SCHEMA_VERSION = "1.0.0"
_OPAQUE = r"^[A-Z]{3}-[A-Z0-9-]{8,64}$"


class PublicAuthContract(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )
    schema_version: Literal["1.0.0"] = SCHEMA_VERSION


class VerificationReceiptConsumeRequest(PublicAuthContract):
    """Caller claims only; this cannot assert verification or identity."""

    receipt_id: str = Field(strict=True, min_length=8, max_length=80, pattern=_OPAQUE)
    browser_challenge: str = Field(strict=True, min_length=8, max_length=80, pattern=_OPAQUE)


class ReceiptResponseCode(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class VerificationReceiptConsumeResponse(PublicAuthContract):
    """Minimal outcome envelope; it carries no trusted evidence or secrets."""

    outcome: ReceiptResponseCode
    detail_code: str = Field(strict=True, min_length=1, max_length=64,
                             pattern=r"^[A-Z][A-Z0-9_]{0,63}$")


def public_response_fields(response: VerificationReceiptConsumeResponse) -> dict[str, object]:
    """Return the explicit public allowlist, never internal receipt evidence."""
    return response.model_dump()
