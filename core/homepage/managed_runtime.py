"""Read-only contracts for the managed Homepage DEV release runtime.

This module deliberately stops at status, validation, and planning.  It does
not materialize releases, install launchd assets, or execute a lifecycle
operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping


SCHEMA_VERSION = 1
ENVIRONMENT = "dev"
SERVICE = "homepage"
HOST = "127.0.0.1"
PORT = 18080
LAUNCHD_LABEL = "com.aicontrolcenter.homepage-dev"
PRESENTATION_IDENTIFIER = "SHOP_MEDIA_003_AGACHICHI"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class ReleaseManifestError(ValueError):
    """Raised when a DEV release cannot be proven safe to serve."""


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    environment: str
    service: str
    git_commit: str
    release_path: str
    created_at: str
    source_clean: bool
    source_provenance: dict[str, Any]
    presentation_identifier: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReleaseManifest":
        if not isinstance(value, Mapping):
            raise ReleaseManifestError("release manifest must be a JSON object")
        required = {
            "schema_version", "environment", "service", "git_commit",
            "release_path", "created_at", "source_clean", "source_provenance",
            "presentation_identifier",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ReleaseManifestError("release manifest is missing required fields: " + ", ".join(missing))
        if value["schema_version"] != SCHEMA_VERSION:
            raise ReleaseManifestError("unsupported release manifest schema")
        if value["environment"] != ENVIRONMENT or value["service"] != SERVICE:
            raise ReleaseManifestError("release manifest environment/service is invalid")
        commit = value["git_commit"]
        if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
            raise ReleaseManifestError("release manifest git_commit is invalid")
        release_path = value["release_path"]
        if not isinstance(release_path, str) or not Path(release_path).is_absolute():
            raise ReleaseManifestError("release_path must be absolute")
        created_at = value["created_at"]
        if not isinstance(created_at, str):
            raise ReleaseManifestError("created_at must be an ISO-8601 string")
        try:
            datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ReleaseManifestError("created_at must be an ISO-8601 string") from exc
        if value["source_clean"] is not True:
            raise ReleaseManifestError("only clean committed source may be a DEV release")
        provenance = value["source_provenance"]
        if not isinstance(provenance, dict):
            raise ReleaseManifestError("source_provenance must be an object")
        if provenance.get("method") != "git_archive":
            raise ReleaseManifestError("release provenance must use git_archive")
        if provenance.get("archived_revision") != commit:
            raise ReleaseManifestError("release provenance revision does not match git_commit")
        if provenance.get("working_tree_clean") is not True:
            raise ReleaseManifestError("release provenance is not clean")
        presentation = value["presentation_identifier"]
        if not isinstance(presentation, str) or not presentation:
            raise ReleaseManifestError("presentation_identifier must be non-empty")
        return cls(
            schema_version=SCHEMA_VERSION,
            environment=ENVIRONMENT,
            service=SERVICE,
            git_commit=commit,
            release_path=release_path,
            created_at=created_at,
            source_clean=True,
            source_provenance=dict(provenance),
            presentation_identifier=presentation,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "environment": self.environment,
            "service": self.service,
            "git_commit": self.git_commit,
            "release_path": self.release_path,
            "created_at": self.created_at,
            "source_clean": self.source_clean,
            "source_provenance": self.source_provenance,
            "presentation_identifier": self.presentation_identifier,
        }


def _read_json_file(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ReleaseManifestError(f"required manifest file is unavailable: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseManifestError(f"manifest JSON cannot be read: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseManifestError(f"manifest JSON must be an object: {path}")
    return value


def load_current_manifest(release_root: Path) -> ReleaseManifest:
    """Load and parse the current DEV manifest without changing anything."""

    root = Path(release_root)
    if root.is_symlink() or not root.is_dir():
        raise ReleaseManifestError("DEV release root is unavailable")
    return ReleaseManifest.from_mapping(_read_json_file(root / "current.json"))


def validate_release(release_root: Path) -> ReleaseManifest:
    """Validate the manifest, release path, and materialized provenance marker."""

    root = Path(release_root)
    manifest = load_current_manifest(root)
    expected_path = (root / "releases" / manifest.git_commit).absolute()
    declared_path = Path(manifest.release_path)
    if declared_path != expected_path:
        raise ReleaseManifestError("release_path does not match the expected commit directory")
    if not expected_path.is_dir() or expected_path.is_symlink():
        raise ReleaseManifestError("immutable DEV release directory is unavailable")
    if expected_path.resolve() != expected_path:
        raise ReleaseManifestError("DEV release directory contains a symlink escape")
    marker = _read_json_file(expected_path / ".aicontrolcenter-release.json")
    marker_manifest = ReleaseManifest.from_mapping(marker)
    if marker_manifest != manifest:
        raise ReleaseManifestError("release provenance marker does not match current.json")
    for required in (expected_path / "core/homepage/preview.py", expected_path / "core/homepage/__init__.py"):
        if not required.is_file() or required.is_symlink():
            raise ReleaseManifestError("materialized DEV runtime is incomplete")
    return manifest


def status_contract(release_root: Path) -> dict[str, Any]:
    """Return the stable JSON status contract, including unhealthy state."""

    try:
        manifest = validate_release(release_root)
    except ReleaseManifestError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "environment": ENVIRONMENT,
            "service": SERVICE,
            "host": HOST,
            "port": PORT,
            "release": None,
            "runtime": {"managed": True, "healthy": False},
            "validation": {"valid": False, "error": str(exc)},
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": ENVIRONMENT,
        "service": SERVICE,
        "host": HOST,
        "port": PORT,
        "release": {
            "git_commit": manifest.git_commit,
            "path": manifest.release_path,
            "presentation_identifier": manifest.presentation_identifier,
        },
        "runtime": {"managed": True, "healthy": True},
        "validation": {"valid": True},
    }


def validate_contract(release_root: Path) -> dict[str, Any]:
    """Return a deterministic JSON validation result."""

    try:
        manifest = validate_release(release_root)
    except ReleaseManifestError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "environment": ENVIRONMENT,
            "service": SERVICE,
            "valid": False,
            "error": str(exc),
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": ENVIRONMENT,
        "service": SERVICE,
        "valid": True,
        "release": {
            "git_commit": manifest.git_commit,
            "path": manifest.release_path,
            "source_clean": manifest.source_clean,
            "source_provenance": manifest.source_provenance,
            "presentation_identifier": manifest.presentation_identifier,
        },
    }


def _git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseManifestError("Git inspection failed") from exc
    return result.stdout.strip()


def build_plan(repo: Path, release_root: Path, commit: str | None = None) -> dict[str, Any]:
    """Build a plan only; this function never creates or changes a file."""

    repo = Path(repo).absolute()
    root = Path(release_root).absolute()
    head = _git(repo, "rev-parse", "HEAD")
    requested = commit or head
    if not COMMIT_PATTERN.fullmatch(requested):
        raise ReleaseManifestError("plan commit must be a full lowercase Git commit")
    _git(repo, "rev-parse", "--verify", f"{requested}^{{commit}}")
    source_status = _git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    source_clean = not bool(source_status)
    release_path = root / "releases" / requested
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": ENVIRONMENT,
        "service": SERVICE,
        "mode": "plan_only",
        "execute": False,
        "approved": source_clean and requested == head,
        "repo_path": str(repo),
        "git_commit": requested,
        "source_clean": source_clean,
        "release_root": str(root),
        "release_path": str(release_path),
        "materialization": {
            "method": "git_archive",
            "archive_revision": requested,
            "archive_prefix": f"{requested}/",
            "exclude_runtime_secrets": True,
            "working_tree_source": False,
        },
        "next_step": "materialize only after explicit DEV deployment authorization",
    }
