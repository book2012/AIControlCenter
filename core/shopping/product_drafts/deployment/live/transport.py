"""Synchronous intercepted transport port; no network implementation exists."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

from .credentials import SecretSafeCredential
from .errors import TransportUnavailableError


@dataclass(frozen=True, slots=True)
class PreparedCommerceWriteRequest:
    provider: str
    method: str
    path: str
    query: tuple[tuple[str, str], ...]
    canonical_body: str
    correlation_id: str
    audit_reference: str


@dataclass(frozen=True, slots=True)
class CommerceTransportResponse:
    status_code: int
    payload: Mapping[str, object]


class CommerceWriteTransport(Protocol):
    def send(self, request: PreparedCommerceWriteRequest,
             credential: SecretSafeCredential, *, timeout_seconds: float
             ) -> CommerceTransportResponse: ...


class UnavailableCommerceWriteTransport:
    def send(self, request: PreparedCommerceWriteRequest,
             credential: SecretSafeCredential, *, timeout_seconds: float
             ) -> CommerceTransportResponse:
        raise TransportUnavailableError()
