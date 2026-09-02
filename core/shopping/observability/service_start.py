"""Pure contracts and policy for Shopping service-start observation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping


class ServiceStartState(str, Enum):
    ABSENT = "ABSENT"
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    UNHEALTHY = "UNHEALTHY"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"


class ShoppingComponent(str, Enum):
    MARIADB = "mariadb"
    WORDPRESS = "wordpress"
    WOOCOMMERCE = "woocommerce"
    AICONTROLCENTER_SHOPPING = "aicontrolcenter_shopping"
    DASHBOARD = "dashboard"
    HOMEPAGE = "homepage"


class ComponentKind(str, Enum):
    DAEMON = "daemon"
    HOSTED_CAPABILITY = "hosted_capability"
    APPLICATION = "application"
    PROJECTION = "projection"


COMPONENT_KINDS: Mapping[ShoppingComponent, ComponentKind] = {
    ShoppingComponent.MARIADB: ComponentKind.DAEMON,
    ShoppingComponent.WORDPRESS: ComponentKind.DAEMON,
    ShoppingComponent.WOOCOMMERCE: ComponentKind.HOSTED_CAPABILITY,
    ShoppingComponent.AICONTROLCENTER_SHOPPING: ComponentKind.APPLICATION,
    ShoppingComponent.DASHBOARD: ComponentKind.PROJECTION,
    ShoppingComponent.HOMEPAGE: ComponentKind.PROJECTION,
}


class ObservationCategory(str, Enum):
    INVENTORY = "inventory"
    LIFECYCLE = "lifecycle"
    HEALTH = "health"
    BINDING = "binding"


class ObservationCompleteness(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    UNAVAILABLE = "unavailable"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"


class ObservationError(str, Enum):
    NONE = "none"
    SOURCE_UNAVAILABLE = "source_unavailable"
    MALFORMED_EVIDENCE = "malformed_evidence"
    UNSUPPORTED_EVIDENCE = "unsupported_evidence"
    AMBIGUOUS_EVIDENCE = "ambiguous_evidence"


@dataclass(frozen=True, slots=True)
class ServiceStartEvidence:
    """Value-free result supplied by a future read-only observer."""

    component: ShoppingComponent
    category: ObservationCategory
    completeness: ObservationCompleteness
    present: bool | None = None
    running: bool | None = None
    healthy: bool | None = None
    conflict: bool | None = None
    error: ObservationError = ObservationError.NONE

    def is_complete(self) -> bool:
        return (
            self.completeness is ObservationCompleteness.COMPLETE
            and self.error is ObservationError.NONE
        )


REQUIRED_CATEGORIES = frozenset(ObservationCategory)


def aggregate_service_start_state(
    component: ShoppingComponent,
    evidence: Iterable[ServiceStartEvidence],
) -> ServiceStartState:
    """Fail-closed state aggregation with deterministic conflict precedence."""
    rows = tuple(item for item in evidence if item.component is component)
    by_category: dict[ObservationCategory, ServiceStartEvidence] = {}
    for row in rows:
        if row.category in by_category:
            return ServiceStartState.CONFLICTING
        by_category[row.category] = row

    binding = by_category.get(ObservationCategory.BINDING)
    if binding is not None and binding.is_complete() and binding.conflict is True:
        return ServiceStartState.CONFLICTING

    inventory = by_category.get(ObservationCategory.INVENTORY)
    if (
        inventory is not None
        and inventory.is_complete()
        and inventory.present is False
    ):
        return ServiceStartState.ABSENT

    lifecycle = by_category.get(ObservationCategory.LIFECYCLE)
    if (
        inventory is not None
        and inventory.is_complete()
        and inventory.present is True
        and lifecycle is not None
        and lifecycle.is_complete()
        and lifecycle.running is False
    ):
        return ServiceStartState.STOPPED

    if set(by_category) != REQUIRED_CATEGORIES or any(
        not row.is_complete() for row in by_category.values()
    ):
        return ServiceStartState.UNKNOWN
    if inventory is None or inventory.present is not True:
        return ServiceStartState.UNKNOWN

    lifecycle = by_category[ObservationCategory.LIFECYCLE]
    if lifecycle.running is not True:
        return ServiceStartState.UNKNOWN

    health = by_category[ObservationCategory.HEALTH]
    if health.healthy is False:
        return ServiceStartState.UNHEALTHY
    if health.healthy is not True or binding.conflict is not False:
        return ServiceStartState.UNKNOWN
    return ServiceStartState.RUNNING


def build_service_start_projection(
    evidence: Iterable[ServiceStartEvidence],
    repository_facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a stable, JSON-safe Dashboard projection without side effects."""
    rows = tuple(evidence)
    components = [
        {
            "component": component.value,
            "kind": COMPONENT_KINDS[component].value,
            "status": aggregate_service_start_state(component, rows).value,
        }
        for component in ShoppingComponent
    ]
    statuses = [item["status"] for item in components]
    observation_complete = all(
        status != ServiceStartState.UNKNOWN.value
        for status in statuses
    )
    if ServiceStartState.CONFLICTING.value in statuses:
        overall = ServiceStartState.CONFLICTING.value
    elif not observation_complete:
        overall = ServiceStartState.UNKNOWN.value
    elif ServiceStartState.UNHEALTHY.value in statuses:
        overall = ServiceStartState.UNHEALTHY.value
    elif ServiceStartState.STOPPED.value in statuses:
        overall = ServiceStartState.STOPPED.value
    elif ServiceStartState.ABSENT.value in statuses:
        overall = ServiceStartState.ABSENT.value
    else:
        overall = ServiceStartState.RUNNING.value
    return {
        "schema_version": "1.0",
        "mode": "READ_ONLY",
        "environment": "CONTROLLED_NON_PRODUCTION",
        "overall_status": overall,
        "components": components,
        "repository_facts": dict(sorted(repository_facts.items())),
        "observation_complete": observation_complete,
        "mutation_performed": False,
        "automatic_retry": False,
        "production_access": False,
        "authorization_consumed": False,
        "ubuntu_dependency": False,
    }


__all__ = (
    "COMPONENT_KINDS",
    "ComponentKind",
    "ObservationCategory",
    "ObservationCompleteness",
    "ObservationError",
    "ServiceStartEvidence",
    "ServiceStartState",
    "ShoppingComponent",
    "aggregate_service_start_state",
    "build_service_start_projection",
)
