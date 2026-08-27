"""Ed25519-only verification of canonical SEC-02 authorization envelopes."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import re
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .canonical import CanonicalizationError, canonicalize, parse_canonical_json
from .models import ParsedAuthorizationEnvelope, VerificationError, VerifiedAuthorizationEvidence, immutable_mapping

DOMAIN_SEPARATOR = b"AICONTROLCENTER-SEC02-AUTHORIZATION-V1"
ALGORITHM = "Ed25519"
_ASCII_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$", re.ASCII)
_ENVELOPE_FIELDS = frozenset({"protected", "signature"})
_REGISTRY_FIELDS = frozenset({"schema_version", "registry_version", "registry_digest", "issuers"})
_ISSUER_FIELDS = frozenset({"schema_version", "registry_version", "key_id", "issuer_id", "issuer_type", "public_key", "algorithm", "status", "not_before", "not_after", "revocation_effective_at"})


def _exact(value: Any, fields: frozenset[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or frozenset(value) != fields:
        raise VerificationError(f"{name} fields are not exact")
    return value


def _ascii_id(value: Any, name: str) -> str:
    if not isinstance(value, str) or _ASCII_ID.fullmatch(value) is None:
        raise VerificationError(f"{name} is not a canonical ASCII authority identifier")
    return value


def _time(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise VerificationError(f"{name} must be canonical UTC time")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise VerificationError(f"{name} is invalid") from error
    if parsed.utcoffset() != timedelta(0):
        raise VerificationError(f"{name} must be UTC")
    return parsed.astimezone(timezone.utc)


def decode_base64url(value: Any, length: int, name: str) -> bytes:
    if not isinstance(value, str) or "=" in value or not value:
        raise VerificationError(f"{name} must be unpadded base64url")
    if re.fullmatch(r"[A-Za-z0-9_-]+", value, re.ASCII) is None:
        raise VerificationError(f"{name} has malformed base64url")
    try:
        decoded = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except (ValueError, base64.binascii.Error) as error:
        raise VerificationError(f"{name} has malformed base64url") from error
    if len(decoded) != length or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise VerificationError(f"{name} has noncanonical base64url or wrong length")
    return decoded


def parse_authorization_envelope(raw: bytes) -> ParsedAuthorizationEnvelope:
    try:
        envelope = _exact(parse_canonical_json(raw), _ENVELOPE_FIELDS, "envelope")
    except CanonicalizationError as error:
        raise VerificationError(str(error)) from error
    if not isinstance(envelope["protected"], dict) or not isinstance(envelope["signature"], str):
        raise VerificationError("envelope types are invalid")
    return ParsedAuthorizationEnvelope(envelope["protected"], envelope["signature"])


def parse_registry(raw: bytes) -> dict[str, Any]:
    try:
        registry = _exact(parse_canonical_json(raw), _REGISTRY_FIELDS, "registry")
    except CanonicalizationError as error:
        raise VerificationError(str(error)) from error
    digest = registry["registry_digest"]
    body = {key: value for key, value in registry.items() if key != "registry_digest"}
    expected = "sha256:" + hashlib.sha256(canonicalize(body)).hexdigest()
    if not isinstance(digest, str) or digest != expected:
        raise VerificationError("registry digest mismatch")
    if registry["schema_version"] != "governance-trusted-issuer-registry/v1":
        raise VerificationError("registry version is invalid")
    registry_version = _ascii_id(registry["registry_version"], "registry_version")
    if not isinstance(registry["issuers"], list):
        raise VerificationError("registry issuers must be an array")
    seen: set[str] = set()
    for issuer in registry["issuers"]:
        _exact(issuer, _ISSUER_FIELDS, "issuer")
        key_id = _ascii_id(issuer["key_id"], "key_id")
        _ascii_id(issuer["issuer_id"], "issuer_id")
        _ascii_id(issuer["issuer_type"], "issuer_type")
        if key_id in seen:
            raise VerificationError("duplicate registry key_id")
        seen.add(key_id)
        if issuer["schema_version"] != registry["schema_version"] or issuer["registry_version"] != registry_version:
            raise VerificationError("issuer registry binding mismatch")
        if issuer["algorithm"] != ALGORITHM or issuer["status"] not in {"ACTIVE", "REVOKED"}:
            raise VerificationError("issuer algorithm or status is invalid")
        decode_base64url(issuer["public_key"], 32, "public_key")
        not_before = _time(issuer["not_before"], "not_before")
        not_after = _time(issuer["not_after"], "not_after")
        if not_before >= not_after:
            raise VerificationError("issuer validity interval is empty or reversed")
        revoked_at = issuer["revocation_effective_at"]
        if issuer["status"] == "REVOKED" and revoked_at is None:
            raise VerificationError("revoked issuer requires revocation_effective_at")
        if revoked_at is not None:
            effective = _time(revoked_at, "revocation_effective_at")
            if effective < not_before or effective > not_after:
                raise VerificationError("revocation time is outside issuer validity")
    return registry


def verify_authorization_envelope(raw: bytes, registry_raw: bytes, *, now: datetime) -> VerifiedAuthorizationEvidence:
    envelope = parse_authorization_envelope(raw)
    registry = parse_registry(registry_raw)
    protected = dict(envelope.protected)
    for field in ("envelope_version", "key_id", "issuer_id", "algorithm", "expires_at"):
        if field not in protected:
            raise VerificationError(f"protected object lacks {field}")
    if protected["envelope_version"] != "governance-signed-authorization-envelope/v1":
        raise VerificationError("wrong envelope version")
    if protected["algorithm"] != ALGORITHM:
        raise VerificationError("wrong algorithm")
    key_id = _ascii_id(protected["key_id"], "key_id")
    issuer_id = _ascii_id(protected["issuer_id"], "issuer_id")
    candidates = [item for item in registry["issuers"] if item["key_id"] == key_id]
    if len(candidates) != 1:
        raise VerificationError("unknown key")
    issuer = candidates[0]
    if issuer["issuer_id"] != issuer_id:
        raise VerificationError("issuer binding mismatch")
    current = now.astimezone(timezone.utc) if isinstance(now, datetime) and now.tzinfo else None
    if current is None or now.utcoffset() != timedelta(0):
        raise VerificationError("verification time must be aware UTC")
    if issuer["status"] == "REVOKED":
        raise VerificationError("revoked key")
    not_before, not_after = _time(issuer["not_before"], "not_before"), _time(issuer["not_after"], "not_after")
    if current < not_before or current >= not_after:
        raise VerificationError("key outside validity interval")
    revoked_at = issuer["revocation_effective_at"]
    if revoked_at is not None and current >= _time(revoked_at, "revocation_effective_at"):
        raise VerificationError("key revocation is effective")
    if current >= _time(protected["expires_at"], "expires_at"):
        raise VerificationError("authorization expired")
    signature = decode_base64url(envelope.signature, 64, "signature")
    signed = DOMAIN_SEPARATOR + b"\x00" + canonicalize(protected)
    try:
        Ed25519PublicKey.from_public_bytes(decode_base64url(issuer["public_key"], 32, "public_key")).verify(signature, signed)
    except InvalidSignature as error:
        raise VerificationError("invalid Ed25519 signature") from error
    return VerifiedAuthorizationEvidence(immutable_mapping(protected), key_id, issuer_id, registry["registry_digest"], current)
