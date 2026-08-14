"""Vendor-neutral, JSON-compatible read-only capability observation contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping, Protocol


class CapabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_DEPLOYED = "NOT_DEPLOYED"
    DEGRADED = "DEGRADED"


@dataclass(frozen=True)
class CapabilityGovernanceExtensions:
    """Bounded, boolean-only capability governance facts owned by core."""

    commerce_engine_only: bool | None = None
    automatic_retry: bool | None = None

    def __post_init__(self) -> None:
        for value in (self.commerce_engine_only, self.automatic_retry):
            if value is not None and type(value) is not bool:
                raise TypeError("governance extension values must be booleans")

    def to_dict(self) -> dict[str, bool]:
        return {
            key: value
            for key, value in (
                ("commerce_engine_only", self.commerce_engine_only),
                ("automatic_retry", self.automatic_retry),
            )
            if value is not None
        }


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
    governance_extensions: CapabilityGovernanceExtensions | None = None

    def __post_init__(self) -> None:
        if self.governance_extensions is not None and type(self.governance_extensions) is not CapabilityGovernanceExtensions:
            raise TypeError("governance extensions must use the core contract")

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
                "platform_business_policy_ownership": False,
                "action_execution": False,
                **(self.governance_extensions.to_dict() if self.governance_extensions else {}),
            },
        }
        return result


class CapabilityObserver(Protocol):
    """Observation only: this port intentionally defines no action method."""

    def observe(self) -> CapabilityObservation: ...


@dataclass(frozen=True)
class UnavailableCapabilityObserver:
    """Provider-neutral, discovery-free fail-closed capability observer."""

    provider: str
    service_id: str
    include_configuration_facts: bool = False
    include_transport: bool = False
    governance_extensions: CapabilityGovernanceExtensions | None = None

    def __post_init__(self) -> None:
        identity = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
        if not identity.fullmatch(self.provider) or not identity.fullmatch(self.service_id):
            raise ValueError("capability identity is invalid")
        if type(self.include_configuration_facts) is not bool or type(self.include_transport) is not bool:
            raise TypeError("fallback shape controls must be booleans")
        if self.governance_extensions is not None and type(self.governance_extensions) is not CapabilityGovernanceExtensions:
            raise TypeError("governance extensions must use the core contract")

    def observe(self) -> CapabilityObservation:
        configuration: dict[str, Any] = {"status": "UNKNOWN"}
        if self.include_configuration_facts:
            configuration.update(configuration_configured=None, authentication_configured=None)
        runtime = {"kind": "UNKNOWN"}
        if self.include_transport:
            runtime["transport"] = "UNKNOWN"
        return CapabilityObservation(
            provider=self.provider, service_id=self.service_id,
            status=CapabilityStatus.UNAVAILABLE, available=False, healthy=False, ready=False,
            capabilities=(), configuration=configuration, runtime=runtime, evidence=(),
            error={"error_type": "ObserverNotConfigured"},
            governance_extensions=self.governance_extensions,
        )
