"""Mac-only, credential-blind Shopping service-start observation adapter."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from core.shopping.observability.service_start import (
    ObservationCategory,
    ObservationCompleteness,
    ObservationError,
    ObservationReason,
    ObservationSource,
    ServiceStartEvidence,
    ShoppingComponent,
    build_service_start_projection,
)
from ops.macos.shopping.repository_service_start import (
    ShoppingRepositoryPaths,
    load_shopping_repository_facts,
)
from ops.macos.shopping.runtime_inspector import inspect_runtime


ROOT = Path(__file__).resolve().parents[3]
CONTROL_PLANE_BASE = "http://127.0.0.1:58081"


@dataclass(frozen=True, slots=True)
class HttpObservation:
    status: int
    payload: object


RuntimeObserver = Callable[[], Mapping[str, Any]]
HttpObserver = Callable[[str], HttpObservation]


def _shopping_health(value: Mapping[str, object]) -> bool | None:
    required_strings = (
        "service", "status", "environment", "runtime", "deployment_target",
        "control_plane", "write_mode",
    )
    if any(not isinstance(value.get(key), str) for key in required_strings):
        return None
    if value["service"] != "AIShoppingPlatform":
        return None
    if value["status"] == "ONLINE":
        return True
    if value["status"] == "DISABLED":
        return False
    return None


def _dashboard_health(value: Mapping[str, object]) -> bool | None:
    required_mappings = ("brain", "control_plane", "storage", "backup", "workers")
    if any(not isinstance(value.get(key), Mapping) for key in required_mappings):
        return None
    brain = value["brain"]
    control_plane = value["control_plane"]
    if brain.get("state") != "ONLINE" or control_plane.get("health") != "ONLINE":
        return None
    return True


def _homepage_health(value: Mapping[str, object]) -> bool | None:
    required_mappings = ("brain", "scheduler", "memory", "knowledge", "platform")
    if any(not isinstance(value.get(key), Mapping) for key in required_mappings):
        return None
    status = value["platform"].get("status")
    if status == "ONLINE":
        return True
    if status == "DEGRADED":
        return False
    return None


def _get_json(url: str) -> HttpObservation:
    if not url.startswith("http://127.0.0.1:"):
        raise ValueError("only loopback HTTP observation is supported")
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=3) as response:
        return HttpObservation(response.status, json.load(response))


def _row(
    component: ShoppingComponent,
    category: ObservationCategory,
    *,
    completeness: ObservationCompleteness = ObservationCompleteness.COMPLETE,
    error: ObservationError = ObservationError.NONE,
    source: ObservationSource | None = None,
    reason: ObservationReason | None = None,
    **values: bool | None,
) -> ServiceStartEvidence:
    return ServiceStartEvidence(
        component=component,
        category=category,
        completeness=completeness,
        error=error,
        source=source,
        reason=reason,
        **values,
    )


def _unknown(
    component: ShoppingComponent,
    error: ObservationError,
    source: ObservationSource,
    *,
    completeness: ObservationCompleteness = ObservationCompleteness.UNAVAILABLE,
    reason: ObservationReason | None = None,
) -> tuple[ServiceStartEvidence, ...]:
    return tuple(
        _row(
            component,
            category,
            completeness=completeness,
            error=error,
            source=source,
            reason=reason,
        )
        for category in ObservationCategory
    )


def _container_evidence(
    component: ShoppingComponent,
    service: object,
    publishers: object,
    *,
    expected_port: int,
) -> tuple[ServiceStartEvidence, ...]:
    if not isinstance(service, Mapping) or set(service) != {"present", "running", "healthy"}:
        return _unknown(component, ObservationError.MALFORMED_EVIDENCE,
                        ObservationSource.CONTAINER_RUNTIME,
                        completeness=ObservationCompleteness.MALFORMED)
    if any(type(service[key]) is not bool for key in service):
        return _unknown(component, ObservationError.MALFORMED_EVIDENCE,
                        ObservationSource.CONTAINER_RUNTIME,
                        completeness=ObservationCompleteness.MALFORMED)
    present = service["present"]
    running = service["running"]
    healthy = service["healthy"]
    if not present:
        return (_row(component, ObservationCategory.INVENTORY, present=False,
                     source=ObservationSource.CONTAINER_RUNTIME),)

    binding_complete = isinstance(publishers, list)
    conflict: bool | None = None
    if binding_complete:
        if component is ShoppingComponent.MARIADB:
            conflict = bool(publishers)
        else:
            expected = {
                "URL": "127.0.0.1", "TargetPort": 80,
                "PublishedPort": expected_port, "Protocol": "tcp",
            }
            conflict = len(publishers) != 1 or publishers[0] != expected
    return (
        _row(component, ObservationCategory.INVENTORY, present=True,
             source=ObservationSource.CONTAINER_RUNTIME),
        _row(component, ObservationCategory.LIFECYCLE, running=running,
             source=ObservationSource.CONTAINER_RUNTIME),
        _row(component, ObservationCategory.HEALTH, healthy=healthy,
             source=ObservationSource.CONTAINER_RUNTIME),
        _row(
            component,
            ObservationCategory.BINDING,
            completeness=(
                ObservationCompleteness.COMPLETE
                if binding_complete else ObservationCompleteness.INCOMPLETE
            ),
            error=(
                ObservationError.NONE
                if binding_complete else ObservationError.AMBIGUOUS_EVIDENCE
            ),
            conflict=conflict,
            source=ObservationSource.CONTAINER_RUNTIME,
        ),
    )


def _http_component(
    component: ShoppingComponent,
    url: str,
    observer: HttpObserver,
    validator: Callable[[Mapping[str, object]], bool | None],
) -> tuple[ServiceStartEvidence, ...]:
    try:
        observed = observer(url)
        if type(observed.status) is not int:
            raise TypeError
        if observed.status != 200:
            return _unknown(component, ObservationError.SOURCE_UNAVAILABLE,
                            ObservationSource.LOOPBACK_HTTP,
                            reason=ObservationReason.HTTP_NON_SUCCESS)
        if not isinstance(observed.payload, Mapping):
            raise ValueError
        healthy = validator(observed.payload)
        if healthy is None:
            raise ValueError
    except (TypeError, ValueError):
        return _unknown(component, ObservationError.MALFORMED_EVIDENCE,
                        ObservationSource.LOOPBACK_HTTP,
                        completeness=ObservationCompleteness.MALFORMED,
                        reason=ObservationReason.MALFORMED_HTTP_EVIDENCE)
    except Exception:
        return _unknown(component, ObservationError.SOURCE_UNAVAILABLE,
                        ObservationSource.LOOPBACK_HTTP,
                        reason=ObservationReason.LOOPBACK_HTTP_UNAVAILABLE)
    return (
        _row(component, ObservationCategory.INVENTORY, present=True, source=ObservationSource.LOOPBACK_HTTP),
        _row(component, ObservationCategory.LIFECYCLE, running=True, source=ObservationSource.LOOPBACK_HTTP),
        _row(component, ObservationCategory.HEALTH, healthy=healthy, source=ObservationSource.LOOPBACK_HTTP),
        _row(component, ObservationCategory.BINDING, conflict=False, source=ObservationSource.LOOPBACK_HTTP),
    )


def _woocommerce_evidence(
    url: str,
    observer: HttpObserver,
) -> tuple[ServiceStartEvidence, ...]:
    component = ShoppingComponent.WOOCOMMERCE
    try:
        observed = observer(url)
        if type(observed.status) is not int:
            raise TypeError
        if observed.status != 200:
            return _unknown(component, ObservationError.SOURCE_UNAVAILABLE,
                            ObservationSource.LOOPBACK_HTTP,
                            reason=ObservationReason.HTTP_NON_SUCCESS)
        if not isinstance(observed.payload, Mapping):
            raise ValueError
        namespaces = observed.payload.get("namespaces")
        if not isinstance(namespaces, list) or any(not isinstance(item, str) for item in namespaces):
            raise ValueError
        if "wc/v3" not in namespaces:
            return (_row(component, ObservationCategory.INVENTORY, present=False,
                         source=ObservationSource.LOOPBACK_HTTP),)
    except (TypeError, ValueError):
        return _unknown(component, ObservationError.MALFORMED_EVIDENCE,
                        ObservationSource.LOOPBACK_HTTP,
                        completeness=ObservationCompleteness.MALFORMED,
                        reason=ObservationReason.MALFORMED_HTTP_EVIDENCE)
    except Exception:
        return _unknown(component, ObservationError.SOURCE_UNAVAILABLE,
                        ObservationSource.LOOPBACK_HTTP,
                        reason=ObservationReason.LOOPBACK_HTTP_UNAVAILABLE)
    return (
        _row(component, ObservationCategory.INVENTORY, present=True, source=ObservationSource.LOOPBACK_HTTP),
        _row(component, ObservationCategory.LIFECYCLE, running=True, source=ObservationSource.LOOPBACK_HTTP),
        _row(component, ObservationCategory.HEALTH, healthy=True, source=ObservationSource.LOOPBACK_HTTP),
        _row(component, ObservationCategory.BINDING, conflict=False, source=ObservationSource.LOOPBACK_HTTP),
    )


class MacShoppingServiceStartObserver:
    """One-shot adapter implementing ShoppingServiceStartObservationPort."""

    def __init__(
        self,
        *,
        repository_facts: Mapping[str, Any],
        runtime_observer: RuntimeObserver = inspect_runtime,
        http_observer: HttpObserver = _get_json,
        platform: str = sys.platform,
    ) -> None:
        self._facts = dict(repository_facts)
        self._runtime_observer = runtime_observer
        self._http_observer = http_observer
        self._platform = platform

    async def observe(self) -> tuple[ServiceStartEvidence, ...]:
        if self._platform != "darwin":
            return tuple(
                row
                for component in ShoppingComponent
                for row in _unknown(component, ObservationError.UNSUPPORTED_EVIDENCE,
                                    ObservationSource.CONTAINER_RUNTIME,
                                    completeness=ObservationCompleteness.UNSUPPORTED)
            )
        runtime: Mapping[str, Any] = {}
        rows: list[ServiceStartEvidence]
        try:
            runtime = self._runtime_observer()
            if not isinstance(runtime, Mapping):
                raise ValueError
            if runtime.get("available") is not True:
                error_type = runtime.get("error_type")
                unavailable_reasons = {
                    "RuntimeUnavailable": ObservationReason.RUNTIME_UNAVAILABLE,
                    "DockerInspectionUnavailable": ObservationReason.DOCKER_INSPECTION_UNAVAILABLE,
                }
                reason = unavailable_reasons.get(error_type)
                error = (ObservationError.MALFORMED_EVIDENCE
                         if error_type == "MalformedDockerInspection" or reason is None
                         else ObservationError.SOURCE_UNAVAILABLE)
                if error is ObservationError.MALFORMED_EVIDENCE:
                    reason = ObservationReason.MALFORMED_DOCKER_INSPECTION
                completeness = (ObservationCompleteness.MALFORMED
                                if error is ObservationError.MALFORMED_EVIDENCE
                                else ObservationCompleteness.UNAVAILABLE)
                rows = list(_unknown(ShoppingComponent.MARIADB, error,
                                     ObservationSource.CONTAINER_RUNTIME,
                                     completeness=completeness, reason=reason))
                rows.extend(_unknown(ShoppingComponent.WORDPRESS, error,
                                     ObservationSource.CONTAINER_RUNTIME,
                                     completeness=completeness, reason=reason))
                runtime = {}
            else:
                publishers = runtime.get("publishers")
                if not isinstance(publishers, Mapping):
                    publishers = {}
                port = self._facts.get("wordpress_port")
                if type(port) is not int:
                    raise ValueError
                rows = list(_container_evidence(
                    ShoppingComponent.MARIADB,
                    runtime.get("database"), publishers.get("database"),
                    expected_port=port,
                ))
                rows.extend(_container_evidence(
                    ShoppingComponent.WORDPRESS,
                    runtime.get("wordpress"), publishers.get("wordpress"),
                    expected_port=port,
                ))
                runtime_reason = {
                    "RuntimeNotDeployed": ObservationReason.RUNTIME_NOT_DEPLOYED,
                    "RuntimeNotHealthy": ObservationReason.RUNTIME_NOT_HEALTHY,
                    "PortCollision": ObservationReason.PORT_COLLISION,
                }.get(runtime.get("error_type"))
                if runtime_reason is not None:
                    rows = [
                        ServiceStartEvidence(
                            component=row.component, category=row.category,
                            completeness=row.completeness, present=row.present,
                            running=row.running, healthy=row.healthy,
                            conflict=row.conflict, error=row.error, source=row.source,
                            reason=runtime_reason,
                        )
                        for row in rows
                    ]
        except ValueError:
            rows = list(_unknown(ShoppingComponent.MARIADB, ObservationError.MALFORMED_EVIDENCE,
                                 ObservationSource.CONTAINER_RUNTIME,
                                 completeness=ObservationCompleteness.MALFORMED))
            rows.extend(_unknown(ShoppingComponent.WORDPRESS, ObservationError.MALFORMED_EVIDENCE,
                                 ObservationSource.CONTAINER_RUNTIME,
                                 completeness=ObservationCompleteness.MALFORMED))
            runtime = {}
        except Exception:
            rows = list(_unknown(ShoppingComponent.MARIADB, ObservationError.SOURCE_UNAVAILABLE,
                                 ObservationSource.CONTAINER_RUNTIME))
            rows.extend(_unknown(ShoppingComponent.WORDPRESS, ObservationError.SOURCE_UNAVAILABLE,
                                 ObservationSource.CONTAINER_RUNTIME))
            runtime = {}

        wordpress = runtime.get("wordpress") if isinstance(runtime, Mapping) else None
        if isinstance(wordpress, Mapping) and wordpress.get("running") is True:
            woo_url = f"http://127.0.0.1:{self._facts['wordpress_port']}/wp-json/"
            rows.extend(_woocommerce_evidence(woo_url, self._http_observer))
        else:
            rows.extend(_unknown(ShoppingComponent.WOOCOMMERCE, ObservationError.SOURCE_UNAVAILABLE,
                                 ObservationSource.LOOPBACK_HTTP,
                                 reason=ObservationReason.LOOPBACK_HTTP_UNAVAILABLE))

        probes = (
            (ShoppingComponent.AICONTROLCENTER_SHOPPING, "/shopping/health",
             _shopping_health),
            (ShoppingComponent.DASHBOARD, "/dashboard", _dashboard_health),
            (ShoppingComponent.HOMEPAGE, "/homepage/status",
             _homepage_health),
        )
        for component, path, validator in probes:
            rows.extend(_http_component(
                component, CONTROL_PLANE_BASE + path, self._http_observer, validator,
            ))
        return tuple(rows)


async def observe_once(root: Path = ROOT) -> dict[str, Any]:
    facts = load_shopping_repository_facts(ShoppingRepositoryPaths.canonical(root))
    evidence = await MacShoppingServiceStartObserver(repository_facts=facts).observe()
    return build_service_start_projection(evidence, facts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    payload = asyncio.run(observe_once())
    print(json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = ("HttpObservation", "MacShoppingServiceStartObserver", "observe_once")
