"""Fail-closed, read-only n8n capability observation."""

from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError

from core.capabilities import CapabilityObservation, CapabilityStatus


ReadonlyObserver = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class N8nConfiguration:
    deployment_status: str = "NOT_DEPLOYED"
    configuration_configured: bool | None = None
    authentication_configured: bool | None = None
    runtime_kind: str | None = None
    transport_kind: str | None = None


class N8nAdapter:
    """Normalize injected facts without retaining values or providing actions."""

    CAPABILITIES = ("capability.status.read", "configuration.validate")

    def __init__(
        self,
        configuration: N8nConfiguration,
        observer: ReadonlyObserver | None = None,
    ) -> None:
        self._configuration = configuration
        self._observer = observer

    def observe(self) -> CapabilityObservation:
        config = self._configuration
        configuration = {
            "status": (
                "UNKNOWN" if config.configuration_configured is None
                else "CONFIGURED" if config.configuration_configured
                else "NOT_CONFIGURED"
            ),
            "configuration_configured": config.configuration_configured,
            "authentication_configured": config.authentication_configured,
        }
        runtime = {
            "kind": config.runtime_kind or "UNKNOWN",
            "transport": config.transport_kind or "UNKNOWN",
        }
        evidence: tuple[Mapping[str, Any], ...] = ({
            "type": "canonical_manifest",
            "deployment_status": config.deployment_status,
        },)
        if config.deployment_status == "NOT_DEPLOYED":
            return self._result(CapabilityStatus.NOT_DEPLOYED, configuration, runtime, evidence)
        if config.deployment_status not in {"DEPLOYED", "PRODUCTION"}:
            return self._result(
                CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence,
                error_type="IndeterminateDeploymentStatus",
            )
        if config.configuration_configured is False:
            return self._result(CapabilityStatus.NOT_CONFIGURED, configuration, runtime, evidence)
        if config.configuration_configured is None:
            return self._result(
                CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence,
                error_type="ConfigurationEvidenceUnknown",
            )
        if self._observer is None:
            return self._result(
                CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence,
                error_type="ObserverNotConfigured",
            )
        try:
            payload = self._observer()
        except (TimeoutError, socket.timeout):
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, error_type="TimeoutError")
        except (ConnectionError, HTTPError, URLError, OSError):
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, error_type="ConnectionError")
        except Exception:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, error_type="ObservationError")
        if not isinstance(payload, Mapping) or set(payload) != {"healthy", "ready"}:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, error_type="MalformedObservation")
        if type(payload["healthy"]) is not bool or type(payload["ready"]) is not bool:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, error_type="MalformedObservation")
        if payload["healthy"] and payload["ready"]:
            return self._result(CapabilityStatus.AVAILABLE, configuration, runtime, evidence)
        return self._result(
            CapabilityStatus.DEGRADED, configuration, runtime, evidence,
            healthy=payload["healthy"], ready=payload["ready"],
        )

    def _result(
        self,
        status: CapabilityStatus,
        configuration: Mapping[str, Any],
        runtime: Mapping[str, Any],
        evidence: tuple[Mapping[str, Any], ...],
        *,
        error_type: str | None = None,
        healthy: bool | None = None,
        ready: bool | None = None,
    ) -> CapabilityObservation:
        available = status is CapabilityStatus.AVAILABLE
        healthy = available if healthy is None else healthy
        ready = available if ready is None else ready
        return CapabilityObservation(
            provider="n8n", service_id="n8n", status=status,
            available=available, healthy=healthy, ready=ready,
            capabilities=self.CAPABILITIES, configuration=configuration,
            runtime=runtime, evidence=evidence,
            error={"error_type": error_type} if error_type else None,
        )
