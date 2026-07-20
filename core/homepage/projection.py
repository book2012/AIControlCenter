from copy import deepcopy
from typing import Any


def apply_standalone_contract(
    homepage_status: dict[str, Any],
    dashboard_status: dict[str, Any],
) -> dict[str, Any]:
    """Return a read-only Mac standalone projection."""

    result = deepcopy(homepage_status)
    dashboard = deepcopy(dashboard_status)

    brain = result.get("brain", {})
    brain_online = brain.get("state") == "ONLINE"

    result["workers"] = dashboard.get("workers", {})

    storage = result.get("storage")
    if not isinstance(storage, dict):
        storage = {}
    storage["required"] = False
    storage["scope"] = "external-worker"
    storage["available"] = bool(storage.get("exists", False))
    result["storage"] = storage

    backup = result.get("backup")
    if not isinstance(backup, dict):
        backup = {}
    backup["required"] = False
    backup["scope"] = "external-worker"
    backup["available"] = bool(backup.get("exists", False))
    result["backup"] = backup

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
