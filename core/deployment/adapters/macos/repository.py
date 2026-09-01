"""Repository-backed, read-only parsers for the Mac Control Plane."""

from __future__ import annotations

import json
import plistlib
import re
from pathlib import Path
from typing import Any, Protocol

import yaml

_COMMIT = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
_BRANCH = re.compile(r"^[A-Za-z0-9._/-]+$")
_LOOPBACK = re.compile(r"^(?:127\.0\.0\.1|localhost):")
_MAX_SYMBOLIC_REF_DEPTH = 16


def _single_git_line(text: str) -> str:
    """Return one Git metadata record without accepting hidden whitespace."""
    line = text.removesuffix("\n").removesuffix("\r")
    if not line or text not in {line, f"{line}\n", f"{line}\r\n"}:
        raise ValueError("malformed Git metadata record")
    return line


def _safe_ref_name(ref: str) -> bool:
    if not ref.startswith("refs/") or ref.startswith("/") or "\\" in ref:
        return False
    if any(character.isspace() for character in ref):
        return False
    components = ref.split("/")
    return all(component not in {"", ".", ".."} for component in components)


def _worktree_local_ref(ref: str) -> bool:
    return any(
        ref == namespace or ref.startswith(f"{namespace}/")
        for namespace in ("refs/bisect", "refs/rewritten", "refs/worktree")
    )


class RepositoryFileReader:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    @property
    def root(self) -> Path:
        return self._root

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


class _GitRepositoryLayout:
    """Read Git metadata from standard repositories and linked worktrees."""

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root.resolve()
        marker = self._repository_root / ".git"

        if marker.is_symlink():
            raise ValueError("Git metadata marker symlink rejected")

        if marker.is_dir():
            self._git_dir = marker.resolve()
            self._common_dir = self._git_dir
            return

        if not marker.is_file():
            raise ValueError("Git metadata marker unavailable")

        record = _single_git_line(marker.read_text(encoding="utf-8"))
        if not record.startswith("gitdir: "):
            raise ValueError("malformed Git gitdir record")

        raw_git_dir = record.removeprefix("gitdir: ")
        if not raw_git_dir:
            raise ValueError("malformed Git gitdir record")

        git_dir_candidate = Path(raw_git_dir)
        if not git_dir_candidate.is_absolute():
            git_dir_candidate = marker.parent / git_dir_candidate

        if git_dir_candidate.is_symlink() or not git_dir_candidate.is_dir():
            raise ValueError("Git worktree metadata directory unavailable")

        self._git_dir = git_dir_candidate.resolve()

        commondir_record = self._git_dir / "commondir"
        if commondir_record.is_symlink() or not commondir_record.is_file():
            raise ValueError("Git common metadata record unavailable")

        raw_common_dir = _single_git_line(
            commondir_record.read_text(encoding="utf-8")
        )
        common_dir_candidate = Path(raw_common_dir)
        if not common_dir_candidate.is_absolute():
            common_dir_candidate = self._git_dir / common_dir_candidate

        if common_dir_candidate.is_symlink() or not common_dir_candidate.is_dir():
            raise ValueError("Git common metadata directory unavailable")

        self._common_dir = common_dir_candidate.resolve()

        backlink_record = self._git_dir / "gitdir"
        if backlink_record.is_symlink() or not backlink_record.is_file():
            raise ValueError("Git worktree backlink unavailable")
        raw_backlink = _single_git_line(
            backlink_record.read_text(encoding="utf-8")
        )
        backlink_candidate = Path(raw_backlink)
        if not backlink_candidate.is_absolute():
            backlink_candidate = self._git_dir / backlink_candidate
        if backlink_candidate.is_symlink() or not backlink_candidate.is_file():
            raise ValueError("Git worktree backlink unavailable")
        if backlink_candidate.resolve() != marker.resolve():
            raise ValueError("Git worktree backlink mismatch")

    @staticmethod
    def _read_bounded(base: Path, relative_path: str) -> str:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Git metadata path traversal rejected")
        path = (base / relative).resolve()
        try:
            path.relative_to(base)
        except ValueError as error:
            raise ValueError("Git metadata path traversal rejected") from error
        return path.read_text(encoding="utf-8")

    def read_head(self) -> str:
        return self._read_bounded(self._git_dir, "HEAD")

    def is_worktree_local_ref(self, ref: str) -> bool:
        if not _safe_ref_name(ref):
            raise ValueError("unsafe Git symbolic reference")
        return _worktree_local_ref(ref)

    def read_loose_ref(self, ref: str) -> str:
        if not _safe_ref_name(ref):
            raise ValueError("unsafe Git symbolic reference")
        base = self._git_dir if _worktree_local_ref(ref) else self._common_dir
        return self._read_bounded(base, ref)

    def read_packed_refs(self) -> str:
        return self._read_bounded(self._common_dir, "packed-refs")


class _GitObjectResolver:
    """Resolve Git object IDs using bounded Git metadata only."""

    def __init__(self, layout: _GitRepositoryLayout) -> None:
        self._layout = layout

    def resolve(self, ref: str) -> str:
        return self._resolve(ref, seen=set(), depth=0)

    def _resolve(self, ref: str, *, seen: set[str], depth: int) -> str:
        if not _safe_ref_name(ref):
            raise ValueError("unsafe Git symbolic reference")
        if depth >= _MAX_SYMBOLIC_REF_DEPTH:
            raise ValueError("Git symbolic reference depth exceeded")
        if ref in seen:
            raise ValueError("Git symbolic reference cycle")
        seen.add(ref)

        try:
            loose = _single_git_line(self._layout.read_loose_ref(ref))
        except FileNotFoundError as error:
            if self._layout.is_worktree_local_ref(ref):
                raise ValueError(
                    "unresolved worktree-local Git reference"
                ) from error
            return self._resolve_packed(ref)

        if _COMMIT.fullmatch(loose):
            return loose
        if loose.startswith("ref: "):
            target = loose.removeprefix("ref: ")
            return self._resolve(target, seen=seen, depth=depth + 1)
        raise ValueError("malformed loose Git reference")

    def _resolve_packed(self, ref: str) -> str:
        try:
            packed = self._layout.read_packed_refs()
        except FileNotFoundError as error:
            raise ValueError("unresolved Git reference") from error

        matches: list[str] = []
        for line in packed.splitlines():
            if not line or line.startswith("#") or line.startswith("^"):
                continue
            fields = line.split()
            if len(fields) >= 2 and fields[1] == ref:
                if len(fields) != 2 or line != f"{fields[0]} {fields[1]}":
                    raise ValueError("malformed matching packed Git reference")
                if not _COMMIT.fullmatch(fields[0]):
                    raise ValueError("malformed matching packed Git object ID")
                matches.append(fields[0])

        if len(matches) != 1:
            raise ValueError("ambiguous or unresolved packed Git reference")
        return matches[0]


class GitRepositoryAdapter:
    def __init__(
        self,
        files: RepositoryFileReader,
        repository_id: str = "AIControlCenter",
    ) -> None:
        self._files = files
        self._repository_id = repository_id

    def observe_git_identity(self) -> dict[str, Any]:
        layout = _GitRepositoryLayout(self._files.root)
        head = _single_git_line(layout.read_head())

        if _COMMIT.fullmatch(head):
            branch, commit = "HEAD", head
        elif head.startswith("ref: "):
            ref = head.removeprefix("ref: ")
            if not _safe_ref_name(ref):
                raise ValueError("unsafe Git HEAD reference")
            branch = (
                ref.removeprefix("refs/heads/")
                if ref.startswith("refs/heads/")
                else ref
            )
            if not _BRANCH.fullmatch(branch):
                raise ValueError("malformed Git branch")
            commit = _GitObjectResolver(layout).resolve(ref)
        else:
            raise ValueError("malformed Git HEAD")

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
