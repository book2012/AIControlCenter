"""Pure service-level contracts for reusable macOS platform inspection.

Aggregate runtime health remains owned by :mod:`core.runtime.service_health`.
Host observation, including launchd classification, is injected by outer
composition so this module cannot become a second runtime-health framework.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
import re
from typing import Any, Callable, Mapping


SERVICE_STATES = frozenset({"RUNNING", "STOPPED", "UNAVAILABLE", "NOT_DEPLOYED"})
PLATFORM_KEYS = frozenset({
    "application_entrypoint", "immutable_runtime", "log_parent", "logs",
    "health_observation", "lifecycle_capabilities", "lifecycle_planning",
})
FILE_KEYS = frozenset({"path", "type", "mode", "owner", "group"})


class ServiceDefinitionError(ValueError):
    """Raised when a service definition cannot be trusted."""


def _absolute_path(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and PurePath(value).is_absolute()


def _validate_file(value: Any, expected_type: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != FILE_KEYS:
        raise ServiceDefinitionError("filesystem contract has unexpected fields")
    if value["type"] != expected_type or not _absolute_path(value["path"]):
        raise ServiceDefinitionError("filesystem type or path is invalid")
    if type(value["mode"]) is not int or not 0 <= value["mode"] <= 0o7777:
        raise ServiceDefinitionError("filesystem mode is invalid")
    if any(not isinstance(value[key], str) or not value[key] for key in ("owner", "group")):
        raise ServiceDefinitionError("filesystem identity is invalid")
    return dict(value)


@dataclass(frozen=True)
class ServiceDefinition:
    service_id: str
    launchd_label: str
    required: bool
    runtime_type: str
    application_entrypoint: str | None
    log_parent: Mapping[str, Any]
    logs: tuple[Mapping[str, Any], ...]
    health_observation: str
    lifecycle_capabilities: tuple[str, ...]
    lifecycle_bounded_action: str | None
    lifecycle_eligible_statuses: tuple[str, ...]
    immutable_runtime: Mapping[str, Any] | None

    @classmethod
    def from_mapping(cls, service: Mapping[str, Any]) -> "ServiceDefinition":
        """Build from one canonical manifest service, deriving all identity fields."""
        if not isinstance(service, Mapping):
            raise ServiceDefinitionError("service definition is invalid")
        platform = service.get("service_platform")
        if not isinstance(platform, Mapping) or set(platform) != PLATFORM_KEYS:
            raise ServiceDefinitionError("service platform definition has unexpected fields")
        service_id = service.get("service_id")
        launchd_label = service.get("launchd_label")
        runtime_type = service.get("runtime")
        if not isinstance(service_id, str) or re.fullmatch(r"[a-z0-9][a-z0-9-]*", service_id) is None:
            raise ServiceDefinitionError("service_id is invalid")
        if service.get("lifecycle") != "launchd" or not isinstance(launchd_label, str) or not launchd_label:
            raise ServiceDefinitionError("launchd identity is invalid")
        if type(service.get("required")) is not bool:
            raise ServiceDefinitionError("required is invalid")
        if not isinstance(runtime_type, str) or not runtime_type:
            raise ServiceDefinitionError("runtime is invalid")
        if platform["health_observation"] not in {"launchd", "heartbeat"}:
            raise ServiceDefinitionError("health observation is invalid")
        capabilities = platform["lifecycle_capabilities"]
        if capabilities != ["inspect"]:
            raise ServiceDefinitionError("PA-01 lifecycle is inspect-only")
        planning = platform["lifecycle_planning"]
        if (
            not isinstance(planning, Mapping)
            or set(planning) != {"bounded_action", "eligible_statuses"}
            or planning["bounded_action"] != "bootstrap"
            or planning["eligible_statuses"] != ["NOT_DEPLOYED"]
        ):
            raise ServiceDefinitionError("lifecycle planning is invalid")
        parent = _validate_file(platform["log_parent"], "directory")
        logs_value = platform["logs"]
        if not isinstance(logs_value, list) or not logs_value:
            raise ServiceDefinitionError("log contract is invalid")
        logs = tuple(_validate_file(item, "file") for item in logs_value)
        paths = [parent["path"], *(item["path"] for item in logs)]
        if len(paths) != len(set(paths)):
            raise ServiceDefinitionError("filesystem paths must be unique")
        runtime = platform["immutable_runtime"]
        if not isinstance(runtime, Mapping) or set(runtime) != {"runtime_root"}:
            raise ServiceDefinitionError("immutable runtime contract is invalid")
        if not _absolute_path(runtime["runtime_root"]):
            raise ServiceDefinitionError("immutable runtime root is invalid")
        entrypoint = platform["application_entrypoint"]
        if not isinstance(entrypoint, str) or not entrypoint:
            raise ServiceDefinitionError("application entrypoint is invalid")
        return cls(
            service_id=service_id, launchd_label=launchd_label,
            required=service["required"], runtime_type=runtime_type,
            application_entrypoint=entrypoint, log_parent=parent, logs=logs,
            health_observation=platform["health_observation"],
            lifecycle_capabilities=("inspect",),
            lifecycle_bounded_action="bootstrap",
            lifecycle_eligible_statuses=tuple(planning["eligible_statuses"]),
            immutable_runtime=dict(runtime),
        )


def inspect_service(
    definition: ServiceDefinition, *, launchd_observer: Callable[[str], str],
    filesystem_observer: Callable[[tuple[Mapping[str, Any], ...]], Mapping[str, Any]],
    runtime_observer: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    freshness_observer: Callable[[ServiceDefinition], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate one service; aggregate policy remains a caller responsibility."""
    try:
        state = launchd_observer(definition.launchd_label)
        if state not in SERVICE_STATES:
            raise ValueError
        launchd = {"status": state}
    except Exception as exc:
        state = "UNAVAILABLE"
        launchd = {"status": state, "inspection_error": {"error_type": type(exc).__name__}}
    try:
        filesystem = dict(filesystem_observer((definition.log_parent, *definition.logs)))
    except Exception as exc:
        filesystem = {"ready": False, "inspection_error": {"error_type": type(exc).__name__}}
    try:
        runtime = dict(runtime_observer(definition.immutable_runtime or {}))
    except Exception as exc:
        runtime = {"ready": False, "inspection_error": {"error_type": type(exc).__name__}}
    freshness = {"required": definition.health_observation == "heartbeat", "fresh": True}
    if freshness["required"]:
        try:
            freshness = dict(freshness_observer(definition) if freshness_observer else {"fresh": False})
            freshness["required"] = True
        except Exception as exc:
            freshness = {"required": True, "fresh": False, "inspection_error": {"error_type": type(exc).__name__}}
    ready = bool(
        state == "RUNNING" and filesystem.get("ready") is True
        and runtime.get("ready") is True and freshness.get("fresh") is True
    )
    status = "STALE" if state == "RUNNING" and freshness.get("fresh") is not True else state
    return {
        "schema_version": "1.0", "service_id": definition.service_id,
        "required": definition.required, "status": status, "ready": ready,
        "healthy": ready, "fails_platform_health": definition.required and not ready,
        "launchd": launchd, "filesystem": filesystem,
        "immutable_runtime": runtime, "freshness": freshness,
    }


def lifecycle_dry_run(definition: ServiceDefinition, inspection: Mapping[str, Any]) -> dict[str, Any]:
    """Plan one future action from trusted observations; never authorize or execute it."""
    try:
        launchd = inspection["launchd"]
        filesystem = inspection["filesystem"]
        runtime = inspection["immutable_runtime"]
        status = inspection["status"]
        eligible = bool(
            status in definition.lifecycle_eligible_statuses
            and inspection["ready"] is False
            and isinstance(launchd, Mapping) and launchd.get("status") == status
            and set(launchd) == {"status"}
            and isinstance(filesystem, Mapping) and filesystem.get("ready") is True
            and "inspection_error" not in filesystem
            and isinstance(runtime, Mapping) and runtime.get("ready") is True
            and "inspection_error" not in runtime
        )
    except (KeyError, TypeError, ValueError):
        eligible = False
    return {
        "schema_version": "1.0", "plan_type": "service_lifecycle_dry_run",
        "service_id": definition.service_id, "capabilities": ["inspect"],
        "eligible": eligible,
        "bounded_action": definition.lifecycle_bounded_action if eligible else None,
        "authorization_included": False,
        "mutation_performed": False, "write_operations_executed": 0,
        "launchctl_mutations_executed": 0, "retry_operations_executed": 0,
        "rollback_operations_executed": 0, "kickstart_operations_executed": 0,
    }


__all__ = ("ServiceDefinition", "ServiceDefinitionError", "inspect_service", "lifecycle_dry_run")
