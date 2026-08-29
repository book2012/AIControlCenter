"""Strict deterministic JSON helpers for Continuity Witness contracts."""

from __future__ import annotations

import base64
import hashlib
import re
from typing import Any, Mapping

from core.governance.control_plane.trust.canonical import (
    CanonicalizationError,
    canonicalize,
    parse_canonical_json,
    parse_json_bytes,
)

SCHEMA_VERSION = "1"
CANONICAL_SIGNED_ENVELOPE_MAX_BYTES = 4096
_BASE64URL = re.compile(r"^[A-Za-z0-9_-]*$")


class ContractValidationError(ValueError):
    pass


def decode_base64url(value: str) -> bytes:
    if not isinstance(value, str) or not _BASE64URL.fullmatch(value) or "=" in value:
        raise ContractValidationError("value must be strict unpadded base64url")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as error:
        raise ContractValidationError("value must be strict unpadded base64url") from error
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise ContractValidationError("value is not canonical unpadded base64url")
    return decoded


def encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def sha256_digest(value: bytes) -> str:
    return encode_base64url(hashlib.sha256(value).digest())


def canonical_digest(value: Any) -> str:
    return sha256_digest(canonicalize(value))


def canonical_signed_bytes(envelope_without_signature: Mapping[str, Any]) -> bytes:
    if envelope_without_signature.get("schema_version") != SCHEMA_VERSION:
        raise ContractValidationError("explicit schema_version 1 is required")
    domain = envelope_without_signature.get("domain")
    if not isinstance(domain, str) or not domain:
        raise ContractValidationError("explicit domain separation is required")
    if "signature" in envelope_without_signature:
        raise ContractValidationError("signing input must exclude only signature")
    encoded = canonicalize(dict(envelope_without_signature))
    if len(encoded) > CANONICAL_SIGNED_ENVELOPE_MAX_BYTES:
        raise ContractValidationError("canonical signed envelope exceeds 4096 bytes")
    return encoded


__all__ = (
    "CanonicalizationError", "ContractValidationError", "canonicalize",
    "parse_canonical_json", "parse_json_bytes", "canonical_digest",
    "canonical_signed_bytes", "decode_base64url", "encode_base64url",
    "sha256_digest",
)
