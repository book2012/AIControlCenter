"""Fail-closed OpenClaw configuration and health observer.

PA-02 v1 permits GET observation only. This adapter exposes no tool, prompt,
authorization, deployment, lifecycle, or infrastructure mutation operation.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError

from core.capabilities import CapabilityObservation, CapabilityStatus


ReadonlyObserver = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class OpenClawConfiguration:
    deployment_status: str = "NOT_DEPLOYED"
    endpoint_configured: bool | None = None
    authentication_configured: bool | None = None
    runtime_kind: str | None = None


class OpenClawAdapter:
    """Normalize injected read-only evidence without retaining secret values."""

    CAPABILITIES = ("capability.status.read", "configuration.validate")

    def __init__(
        self,
        configuration: OpenClawConfiguration,
        observer: ReadonlyObserver | None = None,
    ) -> None:
        self._configuration = configuration
        self._observer = observer

    def observe(self) -> CapabilityObservation:
        config = self._configuration
        configuration = {
            "status": (
                "UNKNOWN" if config.endpoint_configured is None
                else "CONFIGURED" if config.endpoint_configured
                else "NOT_CONFIGURED"
            ),
            "endpoint_configured": config.endpoint_configured,
            "authentication_configured": config.authentication_configured,
        }
        runtime = {"kind": config.runtime_kind or "UNKNOWN"}
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
        if config.endpoint_configured is False:
            return self._result(CapabilityStatus.NOT_CONFIGURED, configuration, runtime, evidence)
        if config.endpoint_configured is None:
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
        return self._result(CapabilityStatus.DEGRADED, configuration, runtime, evidence)

    def _result(
        self,
        status: CapabilityStatus,
        configuration: Mapping[str, Any],
        runtime: Mapping[str, Any],
        evidence: tuple[Mapping[str, Any], ...],
        *,
        error_type: str | None = None,
    ) -> CapabilityObservation:
        ready = status is CapabilityStatus.AVAILABLE
        return CapabilityObservation(
            provider="openclaw", service_id="openclaw", status=status,
            available=ready, healthy=ready, ready=ready,
            capabilities=self.CAPABILITIES, configuration=configuration,
            runtime=runtime, evidence=evidence,
            error={"error_type": error_type} if error_type else None,
        )


def validate_json_payload(payload: bytes) -> Mapping[str, Any]:
    """Strict helper for a future injected GET transport; it performs no I/O."""
    value = json.loads(payload)
    if not isinstance(value, Mapping):
        raise ValueError("OpenClaw observation must be an object")
    return value
