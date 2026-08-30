"""Pure, fail-closed SEC-02 fresh-human-evidence contracts.

This module performs no authentication or keychain operation. Evidence is a
verification prerequisite only; it carries no execution or provisioning authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import secrets
from typing import Callable, Protocol

from .canonical import canonicalize
from .pre_bootstrap_remediation_journal import AuthorizationReplayKey

SCHEMA_VERSION = "FRESH_HUMAN_CHALLENGE_V1"
PURPOSE = "GOVERNANCE_DIRECTORY_MODE_0755_TO_0700"
BOUNDED_MUTATION = "SEC02_GOVERNANCE_DIRECTORY_MODE_0755_TO_0700"
ALGORITHM = "SECURE_ENCLAVE_P256_SHA256_USER_PRESENCE_V1"
NONCE_BYTES = 32
MAX_VALIDITY = timedelta(minutes=5)


class FreshHumanVerificationResult(Enum):
    VERIFIED = "VERIFIED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    NOT_READY = "NOT_READY"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class FreshHumanChallengeV1:
    schema_version: str
    purpose: str
    bounded_mutation: str
    request_identity: str
    authorization_replay_key: str
    nonce: str
    issued_at: datetime
    expires_at: datetime

    def canonical_bytes(self) -> bytes:
        return canonicalize({
            "authorization_replay_key": self.authorization_replay_key,
            "bounded_mutation": self.bounded_mutation,
            "expires_at": _timestamp(self.expires_at),
            "issued_at": _timestamp(self.issued_at),
            "nonce": self.nonce,
            "purpose": self.purpose,
            "request_identity": self.request_identity,
            "schema_version": self.schema_version,
        })


@dataclass(frozen=True, slots=True)
class FreshHumanEvidenceV1:
    challenge: FreshHumanChallengeV1
    signature: bytes
    public_key_fingerprint: str
    algorithm: str = ALGORITHM


class FreshHumanSignatureVerifier(Protocol):
    def verify(self, *, public_key_fingerprint: str, message: bytes,
               signature: bytes, algorithm: str) -> FreshHumanVerificationResult: ...


class FreshHumanChallengeIssuer:
    """Control-plane issuer; injected entropy exists only for deterministic tests."""

    def __init__(self, *, clock: Callable[[], datetime] | None = None,
                 entropy: Callable[[int], bytes] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._entropy = entropy or secrets.token_bytes

    def issue(self, *, request_identity: str, replay_key: AuthorizationReplayKey,
              validity: timedelta = MAX_VALIDITY) -> FreshHumanChallengeV1:
        now = self._clock()
        if not _aware(now) or type(request_identity) is not str or not request_identity:
            raise ValueError("exact request identity and timezone-aware clock required")
        if type(replay_key) is not AuthorizationReplayKey or not timedelta(0) < validity <= MAX_VALIDITY:
            raise ValueError("exact replay key and bounded validity required")
        nonce = self._entropy(NONCE_BYTES)
        if type(nonce) is not bytes or len(nonce) != NONCE_BYTES:
            raise ValueError("issuer entropy must return exactly 32 bytes")
        return FreshHumanChallengeV1(
            SCHEMA_VERSION, PURPOSE, BOUNDED_MUTATION, request_identity,
            replay_key.value, nonce.hex(), now, now + validity,
        )


def verify_fresh_human_evidence(
    evidence: object, *, expected_challenge: FreshHumanChallengeV1,
    expected_replay_key: AuthorizationReplayKey, expected_public_key_fingerprint: str,
    verifier: FreshHumanSignatureVerifier, now: datetime,
) -> FreshHumanVerificationResult:
    """Verify every exact binding before any durable journal claim."""
    if type(evidence) is not FreshHumanEvidenceV1 or type(expected_challenge) is not FreshHumanChallengeV1:
        return FreshHumanVerificationResult.DENIED
    challenge = evidence.challenge
    try:
        if challenge != expected_challenge:
            return FreshHumanVerificationResult.DENIED
        if (challenge.schema_version != SCHEMA_VERSION or challenge.purpose != PURPOSE or
                challenge.bounded_mutation != BOUNDED_MUTATION or
                challenge.authorization_replay_key != expected_replay_key.value or
                type(challenge.request_identity) is not str or not challenge.request_identity or
                type(challenge.nonce) is not str or len(challenge.nonce) != NONCE_BYTES * 2):
            return FreshHumanVerificationResult.DENIED
        bytes.fromhex(challenge.nonce)
        if not _aware(now) or not _aware(challenge.issued_at) or not _aware(challenge.expires_at):
            return FreshHumanVerificationResult.ERROR
        if challenge.expires_at <= challenge.issued_at or challenge.expires_at - challenge.issued_at > MAX_VALIDITY:
            return FreshHumanVerificationResult.DENIED
        if now < challenge.issued_at:
            return FreshHumanVerificationResult.DENIED
        if now >= challenge.expires_at:
            return FreshHumanVerificationResult.EXPIRED
        if evidence.algorithm != ALGORITHM:
            return FreshHumanVerificationResult.NOT_READY
        if evidence.public_key_fingerprint != expected_public_key_fingerprint:
            return FreshHumanVerificationResult.DENIED
        if type(evidence.signature) is not bytes or not evidence.signature:
            return FreshHumanVerificationResult.DENIED
        result = verifier.verify(public_key_fingerprint=evidence.public_key_fingerprint,
                                 message=challenge.canonical_bytes(),
                                 signature=evidence.signature, algorithm=evidence.algorithm)
        return result if type(result) is FreshHumanVerificationResult else FreshHumanVerificationResult.ERROR
    except (TypeError, ValueError, OverflowError):
        return FreshHumanVerificationResult.ERROR


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _timestamp(value: datetime) -> str:
    if not _aware(value):
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


__all__ = ("ALGORITHM", "BOUNDED_MUTATION", "FreshHumanChallengeIssuer",
           "FreshHumanChallengeV1", "FreshHumanEvidenceV1", "FreshHumanSignatureVerifier",
           "FreshHumanVerificationResult", "MAX_VALIDITY", "NONCE_BYTES", "PURPOSE",
           "SCHEMA_VERSION", "verify_fresh_human_evidence")
