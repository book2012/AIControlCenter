"""Read-only contracts for the immutable PROD storefront plugin runtime.

This module owns inspection and planning only.  It never creates a release,
copies a plugin, changes a runtime engine, reloads a service, or consumes
authorization.  The production compose contract supplies the validated
plugin directory through ``AICONTROLCENTER_STOREFRONT_PROD_PLUGIN_PATH``.
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
ENVIRONMENT = "prod"
SERVICE = "storefront"
PLUGIN_VERSION = "0.18.0"
PRESENTATION_IDENTIFIER = "SHOP_MEDIA_003_AGACHICHI"
ACCEPTED_GIT_COMMIT = "567cb90ee7fdec0fa82f39c3ad6ce28d46381479"
PLUGIN_DIRECTORY_NAME = "ai-shopping-storefront"
PLUGIN_MAIN_FILE = "ai-shopping-storefront.php"
CURRENT_MANIFEST_NAME = "current.json"
PROVENANCE_MARKER_NAME = ".aicontrolcenter-release.json"
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_RELEASE_ROOT = (
    Path.home() / "Library" / "Application Support" / "AIControlCenter" / "releases" / "storefront-prod"
)


class ReleaseManifestError(ValueError):
    """Raised when a PROD storefront release cannot be proven safe to serve."""


@dataclass(frozen=True)
class ReleaseManifest:
    schema_version: int
    environment: str
    service: str
    git_commit: str
    plugin_version: str
    presentation_identifier: str
    release_path: str
    created_at: str
    source_clean: bool
    source_provenance: dict[str, Any]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReleaseManifest":
        if not isinstance(value, Mapping):
            raise ReleaseManifestError("release manifest must be a JSON object")
        required = {
            "schema_version", "environment", "service", "git_commit",
            "plugin_version", "presentation_identifier", "release_path",
            "created_at", "source_clean", "source_provenance",
        }
        missing = sorted(required - set(value))
        if missing:
            raise ReleaseManifestError(
                "release manifest is missing required fields: " + ", ".join(missing)
            )
        if value["schema_version"] != SCHEMA_VERSION:
            raise ReleaseManifestError("unsupported release manifest schema")
        if value["environment"] != ENVIRONMENT or value["service"] != SERVICE:
            raise ReleaseManifestError("release manifest environment/service is invalid")

        commit = value["git_commit"]
        if not isinstance(commit, str) or not COMMIT_PATTERN.fullmatch(commit):
            raise ReleaseManifestError("release manifest git_commit is invalid")
        if commit != ACCEPTED_GIT_COMMIT:
            raise ReleaseManifestError("release manifest git_commit is not the accepted candidate")

        if value["plugin_version"] != PLUGIN_VERSION:
            raise ReleaseManifestError("release manifest plugin_version is invalid")
        if value["presentation_identifier"] != PRESENTATION_IDENTIFIER:
            raise ReleaseManifestError("release manifest presentation_identifier is invalid")

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
            raise ReleaseManifestError("only clean committed source may be a PROD release")
        provenance = value["source_provenance"]
        if not isinstance(provenance, dict):
            raise ReleaseManifestError("source_provenance must be an object")
        if provenance.get("method") != "git_archive":
            raise ReleaseManifestError("release provenance must use git_archive")
        if provenance.get("archived_revision") != commit:
            raise ReleaseManifestError("release provenance revision does not match git_commit")
        if provenance.get("working_tree_clean") is not True:
            raise ReleaseManifestError("release provenance is not clean")

        return cls(
            schema_version=SCHEMA_VERSION,
            environment=ENVIRONMENT,
            service=SERVICE,
            git_commit=commit,
            plugin_version=PLUGIN_VERSION,
            presentation_identifier=PRESENTATION_IDENTIFIER,
            release_path=release_path,
            created_at=created_at,
            source_clean=True,
            source_provenance=dict(provenance),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "environment": self.environment,
            "service": self.service,
            "git_commit": self.git_commit,
            "plugin_version": self.plugin_version,
            "presentation_identifier": self.presentation_identifier,
            "release_path": self.release_path,
            "created_at": self.created_at,
            "source_clean": self.source_clean,
            "source_provenance": self.source_provenance,
        }


def _absolute(path: Path) -> Path:
    return Path(path).expanduser().absolute()


def _read_json_file(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ReleaseManifestError(f"required manifest file is unavailable: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseManifestError(f"manifest JSON cannot be read: {path}") from exc
    if not isinstance(value, dict):
        raise ReleaseManifestError(f"manifest JSON must be an object: {path}")
    return value


def load_release_manifest(manifest_path: Path) -> ReleaseManifest:
    """Load and validate one release identity manifest without changing it."""

    return ReleaseManifest.from_mapping(_read_json_file(_absolute(manifest_path)))


def load_current_manifest(release_root: Path) -> ReleaseManifest:
    """Load the current PROD identity manifest without validating its target."""

    root = _absolute(release_root)
    if root.is_symlink() or not root.is_dir():
        raise ReleaseManifestError("PROD release root is unavailable")
    return load_release_manifest(root / CURRENT_MANIFEST_NAME)


def _expected_plugin_path(root: Path, commit: str) -> Path:
    return root / "releases" / commit / PLUGIN_DIRECTORY_NAME


def validate_release(release_root: Path) -> ReleaseManifest:
    """Validate the manifest, immutable path, marker, and plugin entrypoint."""

    root = _absolute(release_root)
    if root.is_symlink() or not root.is_dir():
        raise ReleaseManifestError("PROD release root is unavailable")

    manifest = load_current_manifest(root)
    releases_root = root / "releases"
    expected_plugin = _expected_plugin_path(root, manifest.git_commit)
    expected_commit_dir = expected_plugin.parent

    if releases_root.is_symlink() or not releases_root.is_dir():
        raise ReleaseManifestError("PROD releases directory is unavailable")
    if Path(manifest.release_path) != expected_plugin:
        raise ReleaseManifestError("release_path escapes the commit-addressed release directory")
    if expected_commit_dir.is_symlink() or not expected_commit_dir.is_dir():
        raise ReleaseManifestError("immutable PROD release directory is unavailable")
    if expected_plugin.is_symlink() or not expected_plugin.is_dir():
        raise ReleaseManifestError("immutable PROD plugin directory is unavailable")

    resolved_releases = releases_root.resolve(strict=True)
    resolved_plugin = expected_plugin.resolve(strict=True)
    try:
        resolved_plugin.relative_to(resolved_releases)
    except ValueError as exc:
        raise ReleaseManifestError("release path escapes the PROD release root") from exc
    if resolved_plugin != expected_plugin:
        raise ReleaseManifestError("PROD release path contains a symlink escape")

    marker = load_release_manifest(expected_plugin / PROVENANCE_MARKER_NAME)
    if marker != manifest:
        raise ReleaseManifestError("release provenance marker does not match current.json")

    plugin_main = expected_plugin / PLUGIN_MAIN_FILE
    if plugin_main.is_symlink() or not plugin_main.is_file():
        raise ReleaseManifestError("PROD storefront plugin is missing ai-shopping-storefront.php")
    return manifest


def status_contract(release_root: Path = DEFAULT_RELEASE_ROOT) -> dict[str, Any]:
    """Return a stable JSON status contract, including unhealthy state."""

    try:
        manifest = validate_release(release_root)
    except ReleaseManifestError as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "environment": ENVIRONMENT,
            "service": SERVICE,
            "runtime": {"managed": True, "healthy": False, "read_only": True},
            "release": None,
            "validation": {"valid": False, "error": str(exc)},
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": ENVIRONMENT,
        "service": SERVICE,
        "runtime": {"managed": True, "healthy": True, "read_only": True},
        "release": {
            "git_commit": manifest.git_commit,
            "plugin_version": manifest.plugin_version,
            "presentation_identifier": manifest.presentation_identifier,
            "path": manifest.release_path,
        },
        "validation": {"valid": True},
    }


def validate_contract(release_root: Path = DEFAULT_RELEASE_ROOT) -> dict[str, Any]:
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
        "release": manifest.as_dict(),
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


def plan_contract(
    repo: Path,
    release_root: Path = DEFAULT_RELEASE_ROOT,
    commit: str | None = None,
) -> dict[str, Any]:
    """Build a JSON-compatible plan only; never materialize or activate it."""

    repository = _absolute(repo)
    root = _absolute(release_root)
    head = _git(repository, "rev-parse", "HEAD")
    requested = commit or ACCEPTED_GIT_COMMIT
    if not COMMIT_PATTERN.fullmatch(requested):
        raise ReleaseManifestError("plan commit must be a full lowercase Git commit")
    if requested != ACCEPTED_GIT_COMMIT:
        raise ReleaseManifestError("plan commit is not the accepted candidate")
    _git(repository, "rev-parse", "--verify", f"{requested}^{{commit}}")
    source_status = _git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    source_clean = not bool(source_status)
    release_path = _expected_plugin_path(root, requested)
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": ENVIRONMENT,
        "service": SERVICE,
        "mode": "plan_only",
        "execute": False,
        "approved": source_clean and requested == head,
        "repo_path": str(repository),
        "git_commit": requested,
        "plugin_version": PLUGIN_VERSION,
        "presentation_identifier": PRESENTATION_IDENTIFIER,
        "source_clean": source_clean,
        "release_root": str(root),
        "release_path": str(release_path),
        "release": {
            "commit_addressed": True,
            "plugin_directory": PLUGIN_DIRECTORY_NAME,
            "source_provenance": {
                "method": "git_archive",
                "archived_revision": requested,
                "working_tree_clean": source_clean,
            },
        },
        "next_step": "separate explicit PROD authorization is required for any future release write",
    }


# Keep the familiar managed-runtime name available to callers while exposing
# the more explicit contract name used by this migration.
build_plan = plan_contract
