"""Fail-closed WooCommerce commerce-engine capability observation."""

from __future__ import annotations

from dataclasses import dataclass
import socket
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError

from core.capabilities import CapabilityGovernanceExtensions, CapabilityObservation, CapabilityStatus


ReadonlyCatalogObserver = Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class WooCommerceConfiguration:
    deployment_status: str = "UNKNOWN"
    configuration_configured: bool | None = None
    authentication_configured: bool | None = None
    runtime_kind: str | None = None
    transport_kind: str | None = None
    manifest_entry_observed: bool = False


class WooCommerceAdapter:
    """Normalize injected, value-free evidence; intentionally exposes no actions."""

    CAPABILITIES = (
        "capability.status.read",
        "commerce.catalog.read",
        "commerce.product.read",
    )
    GOVERNANCE_EXTENSIONS = CapabilityGovernanceExtensions(
        commerce_engine_only=True, automatic_retry=False,
    )

    def __init__(self, configuration: WooCommerceConfiguration, observer: ReadonlyCatalogObserver | None = None) -> None:
        self._configuration = configuration
        self._observer = observer

    def observe(self) -> CapabilityObservation:
        config = self._configuration
        configuration = {
            "status": "UNKNOWN" if config.configuration_configured is None else (
                "CONFIGURED" if config.configuration_configured else "NOT_CONFIGURED"
            ),
            "configuration_configured": config.configuration_configured,
            "authentication_configured": config.authentication_configured,
        }
        runtime = {
            "kind": config.runtime_kind or "UNKNOWN",
            "transport": config.transport_kind or "UNKNOWN",
        }
        evidence = (
            ({"type": "canonical_capability_manifest", "deployment_status": config.deployment_status},)
            if config.manifest_entry_observed else ()
        )
        if config.deployment_status == "NOT_DEPLOYED":
            return self._result(CapabilityStatus.NOT_DEPLOYED, configuration, runtime, evidence)
        if config.deployment_status not in {"DEPLOYED", "PRODUCTION"}:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "IndeterminateDeploymentStatus")
        if config.configuration_configured is False:
            return self._result(CapabilityStatus.NOT_CONFIGURED, configuration, runtime, evidence)
        if config.configuration_configured is None:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "ConfigurationEvidenceUnknown")
        if config.authentication_configured is not True:
            error = "AuthenticationEvidenceUnknown" if config.authentication_configured is None else None
            status = CapabilityStatus.UNAVAILABLE if error else CapabilityStatus.NOT_CONFIGURED
            return self._result(status, configuration, runtime, evidence, error)
        if self._observer is None:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "ObserverNotConfigured")
        try:
            payload = self._observer()
        except (TimeoutError, socket.timeout):
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "TimeoutError")
        except (ConnectionError, HTTPError, URLError, OSError):
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "ConnectionError")
        except Exception:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "ObservationError")
        if not isinstance(payload, Mapping) or set(payload) != {"healthy", "ready", "catalog_readable"}:
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "MalformedObservation")
        if any(type(payload[key]) is not bool for key in payload):
            return self._result(CapabilityStatus.UNAVAILABLE, configuration, runtime, evidence, "MalformedObservation")
        if all(payload.values()):
            return self._result(CapabilityStatus.AVAILABLE, configuration, runtime, evidence)
        return self._result(
            CapabilityStatus.DEGRADED, configuration, runtime, evidence,
            healthy=payload["healthy"], ready=payload["ready"] and payload["catalog_readable"],
        )

    def _result(self, status, configuration, runtime, evidence, error_type=None, *, healthy=None, ready=None):
        available = status is CapabilityStatus.AVAILABLE
        return CapabilityObservation(
            provider="woocommerce", service_id="woocommerce", status=status,
            available=available, healthy=available if healthy is None else healthy,
            ready=available if ready is None else ready, capabilities=self.CAPABILITIES,
            configuration=configuration, runtime=runtime, evidence=evidence,
            error={"error_type": error_type} if error_type else None,
            governance_extensions=self.GOVERNANCE_EXTENSIONS,
        )


__all__ = ("ReadonlyCatalogObserver", "WooCommerceAdapter", "WooCommerceConfiguration")
