"""Immutable factual models for SEC-02 signed authorization verification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping


class TrustError(ValueError):
    """A trust boundary denied an artifact."""


class VerificationError(TrustError):
    pass


class IntakeError(TrustError):
    pass


class PathPolicyError(TrustError):
    pass


class OperatorIdentityError(TrustError):
    pass


@dataclass(frozen=True, slots=True)
class ParsedAuthorizationEnvelope:
    protected: Mapping[str, Any]
    signature: str


@dataclass(frozen=True, slots=True)
class VerifiedAuthorizationEvidence:
    """Authenticity evidence only; deliberately contains no authority methods."""

    protected: Mapping[str, Any]
    key_id: str
    issuer_id: str
    registry_digest: str
    verified_at: datetime


@dataclass(frozen=True, slots=True)
class TrustedAuthorizationFacts:
    authorization: Any
    mutation_budget: Any
    execution_request: Any
    expected_operator: Any
    evidence: VerifiedAuthorizationEvidence


def immutable_mapping(value: dict[str, Any]) -> Mapping[str, Any]:
    """Recursively freeze signed evidence so verified facts cannot be altered."""
    def freeze(item: Any) -> Any:
        if isinstance(item, dict):
            return MappingProxyType({key: freeze(child) for key, child in item.items()})
        if isinstance(item, list):
            return tuple(freeze(child) for child in item)
        return item
    return freeze(value)
