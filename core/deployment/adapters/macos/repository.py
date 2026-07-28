"""Repository-backed, read-only parsers for the Mac Control Plane."""

from __future__ import annotations

import json
import plistlib
import re
from pathlib import Path
from typing import Any, Protocol

import yaml

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")
_LOOPBACK = re.compile(r"^(?:127\.0\.0\.1|localhost):")


class RepositoryFileReader:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def read_text(self, relative_path: str) -> str:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("repository path traversal rejected")
        path = (self._root / relative).resolve()
        try:
            path.relative_to(self._root)
        except ValueError as error:
            raise ValueError("repository path traversal rejected") from error
        return path.read_text(encoding="utf-8")


class GitRepositoryAdapter:
    def __init__(self, files: RepositoryFileReader, repository_id: str = "AIControlCenter") -> None:
        self._files = files
        self._repository_id = repository_id

    def observe_git_identity(self) -> dict[str, Any]:
        head = self._files.read_text(".git/HEAD").strip()
        if not head.startswith("ref: refs/heads/"):
            raise ValueError("detached Git HEAD is unavailable")
        ref = head.removeprefix("ref: ")
        branch = ref.removeprefix("refs/heads/")
        commit = self._files.read_text(f".git/{ref}").strip()
        if not _BRANCH.fullmatch(branch) or not _COMMIT.fullmatch(commit):
            raise ValueError("malformed Git identity")
        return {
            "repository_id": self._repository_id,
            "branch": branch,
            "commit": commit,
            "evidence": [{"kind": "git-reference", "reference": ".git/HEAD"}],
        }


class RuntimeMetadataFileAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe_runtime_metadata(self) -> dict[str, Any]:
        data = json.loads(self._files.read_text(self._path))
        if not isinstance(data, dict):
            raise ValueError("runtime metadata must be an object")
        required = {"schema_version", "commit", "short_commit", "runtime_mode", "created_at"}
        if not required.issubset(data) or not _COMMIT.fullmatch(str(data["commit"])):
            raise ValueError("malformed runtime metadata")
        return {
            "metadata_schema_version": data["schema_version"],
            "commit": data["commit"],
            "short_commit": data["short_commit"],
            "runtime_mode": data["runtime_mode"],
            "created_at": data["created_at"],
            "evidence": [{"kind": "runtime-metadata", "reference": self._path}],
        }


class LaunchdSnapshotSource(Protocol):
    def snapshot(self, label: str) -> str | None: ...


class LaunchdDesiredStateAdapter:
    def __init__(
        self,
        files: RepositoryFileReader,
        plist_paths: tuple[str, ...],
        snapshots: LaunchdSnapshotSource,
    ) -> None:
        self._files, self._paths, self._snapshots = files, plist_paths, snapshots

    def observe_launchd(self) -> dict[str, Any]:
        services = []
        unavailable = False
        for path in sorted(self._paths):
            parsed = plistlib.loads(self._files.read_text(path).encode("utf-8"))
            label = parsed.get("Label")
            arguments = parsed.get("ProgramArguments")
            if not isinstance(label, str) or not isinstance(arguments, list):
                raise ValueError("malformed launchd desired state")
            snapshot = self._snapshots.snapshot(label)
            if snapshot is None:
                current = "unavailable"
                unavailable = True
            elif "state = running" in snapshot:
                current = "running"
            else:
                current = "loaded"
            services.append({
                "label": label,
                "desired": "loaded",
                "current": current,
                "run_at_load": parsed.get("RunAtLoad") is True,
            })
        return {
            "state": "degraded" if unavailable else "present",
            "services": services,
            "errors": ([{"code": "launchd-observation-unavailable", "message": "One or more launchd observations were unavailable."}] if unavailable else []),
            "evidence": [{"kind": "launchd-plist", "reference": path} for path in sorted(self._paths)],
        }


class CaddyFileAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe_caddy_desired_state(self) -> dict[str, Any]:
        text = self._files.read_text(self._path)
        upstreams = re.findall(r"\breverse_proxy\s+([^\s{]+)", text)
        if not upstreams:
            raise ValueError("Caddy upstream missing")
        loopback = all(_LOOPBACK.match(value) for value in upstreams)
        return {
            "owner": "host-caddy",
            "sole_public_edge": loopback,
            "upstreams": sorted(upstreams),
            "application_exposure": "loopback-only" if loopback else "public-prohibited",
            "evidence": [{"kind": "caddy-desired-state", "reference": self._path}],
        }


class ColimaContractAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe_colima_contract(self) -> dict[str, Any]:
        data = json.loads(self._files.read_text(self._path))
        if not isinstance(data, dict) or data.get("schema_version") != 1:
            raise ValueError("malformed Colima contract")
        if data.get("ubuntu_runtime_allowed") is not False or data.get("ai_workloads_allowed") is not False:
            raise ValueError("Colima ownership policy invalid")
        binding = data.get("wordpress_host_binding")
        if not isinstance(binding, str) or not binding.startswith("127.0.0.1:"):
            raise ValueError("Colima binding must be loopback-only")
        return {
            "profile": data.get("profile"),
            "runtime": data.get("runtime"),
            "architecture": data.get("architecture"),
            "auto_activate": data.get("auto_activate"),
            "allowed_workloads": data.get("allowed_workloads"),
            "ai_workloads_allowed": False,
            "ubuntu_runtime_allowed": False,
            "public_ingress_owner": data.get("public_ingress_owner"),
            "wordpress_host_binding": binding,
            "evidence": [{"kind": "colima-contract", "reference": self._path}],
        }


class ComposeFileAdapter:
    def __init__(self, files: RepositoryFileReader, path: str) -> None:
        self._files, self._path = files, path

    def observe_compose_desired_state(self) -> dict[str, Any]:
        data = yaml.safe_load(self._files.read_text(self._path))
        if not isinstance(data, dict) or not isinstance(data.get("services"), dict):
            raise ValueError("malformed Compose desired state")
        services = data["services"]
        wordpress = services.get("wordpress")
        if not isinstance(wordpress, dict):
            raise ValueError("WordPress service missing")
        ports = wordpress.get("ports", [])
        if not isinstance(ports, list):
            raise ValueError("WordPress ports malformed")
        bindings = [str(value) for value in ports]
        loopback = all(value.startswith("127.0.0.1:") for value in bindings)
        environment_text = json.dumps(services, sort_keys=True)
        return {
            "project": data.get("name"),
            "services": sorted(services),
            "wordpress": True,
            "woocommerce": "WORDPRESS_" in environment_text,
            "wordpress_exposure": "loopback-only" if loopback else "public-prohibited",
            "direct_public_ports": not loopback,
            "internal_networks": sorted(
                name for name, value in (data.get("networks") or {}).items()
                if isinstance(value, dict) and value.get("internal") is True
            ),
            "evidence": [{"kind": "compose-desired-state", "reference": self._path}],
        }


__all__ = (
    "CaddyFileAdapter",
    "ColimaContractAdapter",
    "ComposeFileAdapter",
    "GitRepositoryAdapter",
    "LaunchdDesiredStateAdapter",
    "LaunchdSnapshotSource",
    "RepositoryFileReader",
    "RuntimeMetadataFileAdapter",
)
