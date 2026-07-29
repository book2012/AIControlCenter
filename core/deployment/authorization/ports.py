"""Pure capability ports for DPL-03C authorization."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Protocol, Any


class Clock(Protocol):
    def now(self) -> datetime: ...


class ApprovalEvidenceVerifier(Protocol):
    def verify(self, decision: Mapping[str, Any]) -> bool: ...


class NonceReplayGuard(Protocol):
    def was_consumed(self, nonce: str) -> bool: ...


class AuthorizationConsumer(Protocol):
    def consume(self, authorization: Mapping[str, Any]) -> bool: ...


__all__ = (
    "ApprovalEvidenceVerifier",
    "AuthorizationConsumer",
    "Clock",
    "NonceReplayGuard",
)
