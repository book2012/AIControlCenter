"""Read-only macOS filesystem and immutable-runtime adapters."""

from __future__ import annotations

import errno
import grp
from pathlib import Path
import pwd
import stat
from typing import Any, Callable, Mapping, Sequence

from core.runtime.service_health import ServiceHealth
from core.runtime.service_platform import ServiceDefinition, inspect_service
from core.runtime.service_topology import ServiceTopology


def inspect_path(path: Path, *, expected_type: str, expected_uid: int, expected_gid: int, expected_mode: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path), "exists": False, "regular_file": False, "directory": False,
        "symlink": False, "owner_matches": False, "group_matches": False,
        "mode_matches": False, "inspection_error": None, "valid": False,
    }
    try:
        metadata = path.lstat()
    except OSError as error:
        if error.errno != errno.ENOENT:
            result["inspection_error"] = {"error_type": type(error).__name__, "errno": errno.errorcode.get(error.errno, "UNKNOWN")}
        return result
    result.update({
        "exists": True, "regular_file": stat.S_ISREG(metadata.st_mode),
        "directory": stat.S_ISDIR(metadata.st_mode), "symlink": stat.S_ISLNK(metadata.st_mode),
        "owner_matches": metadata.st_uid == expected_uid, "group_matches": metadata.st_gid == expected_gid,
        "mode_matches": stat.S_IMODE(metadata.st_mode) == expected_mode,
    })
    type_matches = result["regular_file"] if expected_type == "file" else result["directory"]
    result["valid"] = bool(type_matches and not result["symlink"] and result["owner_matches"] and result["group_matches"] and result["mode_matches"])
    return result


def inspect_filesystem(specifications: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Resolve stable identity names at the macOS boundary and validate exactly."""
    paths = []
    for item in specifications:
        try:
            uid = pwd.getpwnam(str(item["owner"])).pw_uid
            gid = grp.getgrnam(str(item["group"])).gr_gid
        except Exception as exc:
            paths.append({"path": str(item["path"]), "valid": False, "inspection_error": {"error_type": type(exc).__name__}})
            continue
        paths.append(inspect_path(
            Path(item["path"]), expected_type=str(item["type"]), expected_uid=uid,
            expected_gid=gid, expected_mode=int(item["mode"]),
        ))
    return {"ready": bool(paths) and all(item["valid"] for item in paths), "paths": paths}


def inspect_immutable_runtime(contract: Mapping[str, Any], *, source_validator: Callable[[Path], Mapping[str, Any]]) -> dict[str, Any]:
    """Validate the canonical runtime/current release and its matching source."""
    runtime_root = Path(str(contract["runtime_root"]))
    current = runtime_root / "current"
    result: dict[str, Any] = {"ready": False, "runtime_root": str(runtime_root), "current": str(current)}
    try:
        metadata = current.lstat()
        if not stat.S_ISLNK(metadata.st_mode):
            return result
        release = current.resolve(strict=True)
        if release.parent.resolve(strict=True) != (runtime_root / "venvs").resolve(strict=True):
            return result
        source = runtime_root / "sources" / release.name
        validation = dict(source_validator(source))
    except Exception as exc:
        result["inspection_error"] = {"error_type": type(exc).__name__}
        return result
    result.update({"runtime_id": release.name, "source_root": str(source), "validation": validation, "ready": validation.get("immutable_source_context_valid") is True})
    return result


def inspect_canonical_immutable_runtime(contract: Mapping[str, Any]) -> dict[str, Any]:
    from ops.macos.launchd.canonical_api_daemon_refresh import validate_immutable_source_context
    return inspect_immutable_runtime(contract, source_validator=validate_immutable_source_context)


def inspect_platform_services(
    *, topology: ServiceTopology, service_health: ServiceHealth,
    filesystem_observer: Callable[[Sequence[Mapping[str, Any]]], Mapping[str, Any]] = inspect_filesystem,
    runtime_observer: Callable[[Mapping[str, Any]], Mapping[str, Any]] = inspect_canonical_immutable_runtime,
) -> dict[str, Any]:
    """Compose existing health observations with PA-01 per-service inspection."""
    try:
        definitions = topology.platform_services()
    except Exception as exc:
        return {
            "schema_version": "1.0", "services": {},
            "inspection_error": {"error_type": type(exc).__name__},
        }

    def freshness(definition: ServiceDefinition) -> Mapping[str, Any]:
        if definition.health_observation != "heartbeat":
            return {"fresh": True}
        return service_health.heartbeat_status()

    services = {
        definition.service_id: inspect_service(
            definition,
            launchd_observer=service_health.launchd_inspector,
            filesystem_observer=filesystem_observer,
            runtime_observer=runtime_observer,
            freshness_observer=freshness,
        )
        for definition in definitions
    }
    return {
        "schema_version": "1.0", "services": services,
    }


__all__ = ("inspect_canonical_immutable_runtime", "inspect_filesystem", "inspect_immutable_runtime", "inspect_path", "inspect_platform_services")
