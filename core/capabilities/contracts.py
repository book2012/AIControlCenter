"""Vendor-neutral, JSON-compatible read-only capability observation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol


class CapabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_DEPLOYED = "NOT_DEPLOYED"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class CapabilityObservation:
    provider: str
    service_id: str
    status: CapabilityStatus
    available: bool
    healthy: bool
    ready: bool
    capabilities: tuple[str, ...]
    configuration: Mapping[str, Any]
    runtime: Mapping[str, Any]
    evidence: tuple[Mapping[str, Any], ...]
    error: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": "1.0",
            "provider": self.provider,
            "service_id": self.service_id,
            "status": self.status.value,
            "available": self.available,
            "healthy": self.healthy,
            "ready": self.ready,
            "capabilities": list(self.capabilities),
            "configuration": dict(self.configuration),
            "runtime": dict(self.runtime),
            "evidence": [dict(item) for item in self.evidence],
            "error": dict(self.error) if self.error is not None else None,
            "governance": {
                "authority": "AICONTROLCENTER",
                "read_only": True,
                "production_authorization": False,
                "infrastructure_mutation": False,
                "action_execution": False,
            },
        }
        return result


class CapabilityObserver(Protocol):
    """Observation only: this port intentionally defines no action method."""

    def observe(self) -> CapabilityObservation: ...
