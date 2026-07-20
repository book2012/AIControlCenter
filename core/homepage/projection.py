from copy import deepcopy
from typing import Any


def apply_standalone_contract(
    homepage_status: dict[str, Any],
    dashboard_status: dict[str, Any],
) -> dict[str, Any]:
    """Apply the Mac standalone status contract without mutating inputs."""

    result = deepcopy(homepage_status)
    dashboard = deepcopy(dashboard_status)

    brain = result.get("brain", {})
    brain_online = brain.get("state") == "ONLINE"

    result["workers"] = dashboard.get("workers", {})

    for component_name in ("storage", "backup"):
        component = result.get(component_name)
        if not isinstance(component, dict):
            component = {}
        component["required"] = False
        component["scope"] = "external-worker"
        component["available"] = bool(component.get("exists", False))
        result[component_name] = component

    datacenter = dashboard.get("datacenter", {})
    optional_available = (
        datacenter.get("overall_status") not in (None, "UNAVAILABLE")
    )

    result["platform"] = {
        "status": "ONLINE" if brain_online else "DEGRADED",
        "standalone": True,
        "ubuntu_required": False,
        "optional_infrastructure_available": optional_available,
    }

    return result
