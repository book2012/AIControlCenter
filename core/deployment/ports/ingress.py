"""Typed read-only boundaries for ingress readiness."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class IngressContractPort(Protocol):
    def read_ingress_contract(self) -> Mapping[str, Any]: ...


class IngressEvidencePort(Protocol):
    def observe(self) -> Mapping[str, Any]: ...


__all__ = ("IngressContractPort", "IngressEvidencePort")
