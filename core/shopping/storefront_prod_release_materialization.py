"""Authorized, commit-addressed materialization of the PROD storefront release.

This module is deliberately separate from ``storefront_prod_runtime``.  The
runtime module remains read-only; this module is the only release writer and
does not import or invoke any runtime lifecycle implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess
import tarfile
import tempfile
from typing import Any, Mapping

from core.shopping.storefront_prod_runtime import (
    ACCEPTED_GIT_COMMIT,
    CURRENT_MANIFEST_NAME,
    DEFAULT_RELEASE_ROOT,
    ENVIRONMENT,
    PLUGIN_DIRECTORY_NAME,
    PLUGIN_MAIN_FILE,
    PLUGIN_VERSION,
    PRESENTATION_IDENTIFIER,
    PROVENANCE_MARKER_NAME,
    SCHEMA_VERSION,
    SERVICE,
    ReleaseManifestError,
    validate_release,
)


ARCHIVE_SUBTREE = "deploy/shopping/wordpress/plugins/ai-shopping-storefront"
EXPECTED_FILE_COUNT = 299
AUTHORIZATION_SCHEMA_VERSION = 1
_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
_VERSION_PATTERN = re.compile(
    r"^\s*\*\s+Version:\s+" + re.escape(PLUGIN_VERSION) + r"\s*$", re.MULTILINE
)
_PRESENTATION_PATTERN = re.compile(
    r"AI_SHOPPING_STOREFRONT_PRESENTATION['\"]\s*,\s*['\"]"
    + re.escape(PRESENTATION_IDENTIFIER)
    + r"['\"]"
)


class ReleaseMaterializationError(RuntimeError):
    """Raised when an immutable release cannot be materialized safely."""


class AuthorizationRequiredError(ReleaseMaterializationError):
    """Raised when a release write has no explicit authorization."""


class AuthorizationConsumedError(ReleaseMaterializationError):
    """Raised when a one-shot authorization is reused."""


@dataclass
class ReleaseMaterializationAuthorization:
    """An in-process one-shot authorization bound to one exact destination."""

    authorization_id: str
    git_commit: str
    release_root: str
    consumed: bool = False

    def consume(self, *, git_commit: str, release_root: Path) -> None:
        if self.consumed:
            raise AuthorizationConsumedError("release materialization authorization was consumed")
        if self.git_commit != git_commit:
            raise AuthorizationRequiredError("authorization commit binding is invalid")
        if Path(self.release_root) != release_root:
            raise AuthorizationRequiredError("authorization release-root binding is invalid")
        self.consumed = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": AUTHORIZATION_SCHEMA_VERSION,
            "authorization_id": self.authorization_id,
            "git_commit": self.git_commit,
            "release_root": self.release_root,
            "consumed": self.consumed,
        }


def _absolute(path: Path) -> Path:
    return Path(path).expanduser().absolute()


def issue_authorization(
    release_root: Path = DEFAULT_RELEASE_ROOT,
    *,
    git_commit: str = ACCEPTED_GIT_COMMIT,
) -> ReleaseMaterializationAuthorization:
    """Issue one explicit, destination-bound authorization in memory."""

    root = _absolute(release_root)
    if git_commit != ACCEPTED_GIT_COMMIT or not _COMMIT_PATTERN.fullmatch(git_commit):
        raise AuthorizationRequiredError("only the accepted commit may be authorized")
    return ReleaseMaterializationAuthorization(
        authorization_id=secrets.token_hex(16),
        git_commit=git_commit,
        release_root=str(root),
    )


def _authorization_path(path: Path, release_root: Path) -> Path:
    value = _absolute(path)
    if value == release_root or release_root in value.parents:
        raise AuthorizationRequiredError("authorization state must be outside the release root")
    if value.exists() and value.is_symlink():
        raise AuthorizationRequiredError("authorization state symlink is rejected")
    return value


def save_authorization(path: Path, authorization: ReleaseMaterializationAuthorization) -> None:
    """Persist an authorization receipt outside the release root."""

    target = _absolute(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and (target.is_symlink() or not target.is_file()):
        raise AuthorizationRequiredError("authorization state path is unsafe")
    payload = json.dumps(authorization.as_dict(), sort_keys=True, indent=2) + "\n"
    fd, temporary_name = tempfile.mkstemp(prefix=".authorization-", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def load_authorization(path: Path, release_root: Path) -> ReleaseMaterializationAuthorization:
    """Load one untrusted receipt without granting it any authority."""

    target = _authorization_path(path, _absolute(release_root))
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuthorizationRequiredError("authorization state is unavailable") from exc
    if not isinstance(value, Mapping):
        raise AuthorizationRequiredError("authorization state is invalid")
    if value.get("schema_version") != AUTHORIZATION_SCHEMA_VERSION:
        raise AuthorizationRequiredError("authorization schema is invalid")
    authorization_id = value.get("authorization_id")
    commit = value.get("git_commit")
    bound_root = value.get("release_root")
    consumed = value.get("consumed")
    if (
        not isinstance(authorization_id, str)
        or not authorization_id
        or commit != ACCEPTED_GIT_COMMIT
        or not isinstance(bound_root, str)
        or not isinstance(consumed, bool)
    ):
        raise AuthorizationRequiredError("authorization state is invalid")
    if Path(bound_root) != _absolute(release_root):
        raise AuthorizationRequiredError("authorization release-root binding is invalid")
    return ReleaseMaterializationAuthorization(
        authorization_id=authorization_id,
        git_commit=commit,
        release_root=bound_root,
        consumed=consumed,
    )


@dataclass(frozen=True)
class _ArchivedFile:
    relative_path: str
    content: bytes
    mode: int


def _git(repo: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseMaterializationError("Git source inspection failed") from exc
    return result.stdout.strip()


def _assert_clean_control_plane(repo: Path) -> None:
    status = _git(
        repo,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if status:
        raise ReleaseMaterializationError(
            "control-plane worktree must be clean before materialization"
        )


def _git_archive(repo: Path, commit: str) -> bytes:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "archive",
                "--format=tar",
                commit,
                "--",
                ARCHIVE_SUBTREE,
            ],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseMaterializationError("accepted Git archive could not be produced") from exc
    if not result.stdout:
        raise ReleaseMaterializationError("accepted Git archive is empty")
    return result.stdout


def _relative_archive_path(name: str) -> str | None:
    if "\\" in name or "\x00" in name or name.startswith("/"):
        raise ReleaseMaterializationError("archive contains an unsafe path")
    normalized = name.rstrip("/")
    components = normalized.split("/")
    if any(component in {"", ".", ".."} for component in components):
        raise ReleaseMaterializationError("archive contains a traversal path")
    subtree = ARCHIVE_SUBTREE
    prefix = subtree + "/"
    if normalized == subtree:
        return ""
    if normalized.startswith(prefix):
        relative = normalized[len(prefix):]
        if not relative:
            raise ReleaseMaterializationError("archive contains an empty payload path")
        PurePosixPath(relative)
        return relative
    if subtree.startswith(normalized + "/"):
        return None
    raise ReleaseMaterializationError("archive contains content outside the exact plugin subtree")


def _read_archive(archive: bytes) -> tuple[_ArchivedFile, ...]:
    files: list[_ArchivedFile] = []
    seen: set[str] = set()
    try:
        tar = tarfile.open(fileobj=BytesIO(archive), mode="r:")
    except (OSError, tarfile.TarError) as exc:
        raise ReleaseMaterializationError("accepted Git archive is not a valid tar stream") from exc
    with tar:
        for member in tar:
            if member.issym() or member.islnk():
                raise ReleaseMaterializationError("symlinks are not allowed in the release payload")
            if not (member.isdir() or member.isfile()):
                raise ReleaseMaterializationError("special archive members are not allowed")
            relative = _relative_archive_path(member.name)
            if relative is None or member.isdir():
                continue
            if relative == "":
                raise ReleaseMaterializationError("plugin subtree root must be a directory")
            if relative in seen:
                raise ReleaseMaterializationError("archive contains a duplicate payload path")
            source = tar.extractfile(member)
            if source is None:
                raise ReleaseMaterializationError("archive file content is unavailable")
            files.append(
                _ArchivedFile(
                    relative_path=relative,
                    content=source.read(),
                    mode=stat.S_IMODE(member.mode) or 0o644,
                )
            )
            seen.add(relative)
    files.sort(key=lambda item: item.relative_path)
    if len(files) != EXPECTED_FILE_COUNT:
        raise ReleaseMaterializationError(
            f"accepted plugin payload file count is {len(files)}, expected {EXPECTED_FILE_COUNT}"
        )
    return tuple(files)


def _validate_identity(files: tuple[_ArchivedFile, ...]) -> None:
    by_path = {item.relative_path: item.content for item in files}
    main = by_path.get(PLUGIN_MAIN_FILE)
    if main is None:
        raise ReleaseMaterializationError("accepted plugin entrypoint is missing")
    try:
        text = main.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReleaseMaterializationError("accepted plugin entrypoint is not UTF-8") from exc
    if not _VERSION_PATTERN.search(text):
        raise ReleaseMaterializationError(f"accepted plugin version is not {PLUGIN_VERSION}")
    if not _PRESENTATION_PATTERN.search(text):
        raise ReleaseMaterializationError(
            "accepted presentation identifier is not SHOP_MEDIA_003_AGACHICHI"
        )


def _commit_created_at(repo: Path, commit: str) -> str:
    raw = _git(repo, "show", "-s", "--format=%cI", commit)
    try:
        value = datetime.fromisoformat(raw).astimezone(timezone.utc)
    except ValueError as exc:
        raise ReleaseMaterializationError("accepted commit timestamp is invalid") from exc
    return value.isoformat().replace("+00:00", "Z")


def _manifest(repo: Path, release_path: Path, files: tuple[_ArchivedFile, ...], commit: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "environment": ENVIRONMENT,
        "service": SERVICE,
        "git_commit": commit,
        "plugin_version": PLUGIN_VERSION,
        "presentation_identifier": PRESENTATION_IDENTIFIER,
        "release_path": str(release_path),
        "created_at": _commit_created_at(repo, commit),
        "source_clean": True,
        "source_provenance": {
            "method": "git_archive",
            "archived_revision": commit,
            "archived_subtree": ARCHIVE_SUBTREE,
            "archive_format": "tar",
            "working_tree_clean": True,
        },
        "files": [
            {
                "path": item.relative_path,
                "sha256": hashlib.sha256(item.content).hexdigest(),
            }
            for item in files
        ],
        "relative_file_paths": [item.relative_path for item in files],
        "file_count": len(files),
    }


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")


def _read_existing_current(root: Path) -> str | None:
    current = root / CURRENT_MANIFEST_NAME
    if current.is_symlink():
        raise ReleaseMaterializationError("current release marker symlink is rejected")
    if not current.exists():
        return None
    if not current.is_file():
        raise ReleaseMaterializationError("current release marker is not a regular file")
    try:
        raw = current.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseMaterializationError("current release marker is invalid") from exc
    if not isinstance(value, dict):
        raise ReleaseMaterializationError("current release marker is invalid")
    commit = value.get("git_commit")
    release_path = value.get("release_path")
    if not isinstance(commit, str) or not _COMMIT_PATTERN.fullmatch(commit):
        raise ReleaseMaterializationError("current release marker commit is invalid")
    expected = root / "releases" / commit / PLUGIN_DIRECTORY_NAME
    if release_path != str(expected):
        raise ReleaseMaterializationError("current release marker path is invalid")
    if expected.is_symlink() or not expected.is_dir():
        raise ReleaseMaterializationError("current immutable release is unavailable")
    marker = expected / PROVENANCE_MARKER_NAME
    if marker.is_symlink() or not marker.is_file():
        raise ReleaseMaterializationError("current release provenance marker is unavailable")
    try:
        marker_value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReleaseMaterializationError("current release provenance marker is invalid") from exc
    if marker_value != value:
        raise ReleaseMaterializationError("current release marker and provenance marker differ")
    entrypoint = expected / PLUGIN_MAIN_FILE
    if entrypoint.is_symlink() or not entrypoint.is_file():
        raise ReleaseMaterializationError("current release plugin entrypoint is unavailable")
    return raw


def _check_existing_components(root: Path, target: Path) -> None:
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ReleaseMaterializationError("release root is not a real directory")
    releases = root / "releases"
    commit_dir = target.parent
    if releases.exists() and (releases.is_symlink() or not releases.is_dir()):
        raise ReleaseMaterializationError("release directory is not a real directory")
    if commit_dir.exists():
        raise ReleaseMaterializationError("accepted commit release destination already exists")
    _read_existing_current(root)
    if target.exists():
        raise ReleaseMaterializationError("release destination already exists")
    for path in (root, releases, commit_dir, target):
        if path.exists() and path.is_symlink():
            raise ReleaseMaterializationError("release destination symlink is rejected")


def _write_staged_payload(stage: Path, files: tuple[_ArchivedFile, ...]) -> None:
    plugin = stage / PLUGIN_DIRECTORY_NAME
    plugin.mkdir(parents=True)
    for item in files:
        destination = plugin / Path(*PurePosixPath(item.relative_path).parts)
        if destination.is_symlink():
            raise ReleaseMaterializationError("staged payload path is a symlink")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(item.content)
            stream.flush()
            os.fsync(stream.fileno())
        destination.chmod(item.mode)


def _verify_staged_payload(stage: Path, files: tuple[_ArchivedFile, ...]) -> None:
    plugin = stage / PLUGIN_DIRECTORY_NAME
    actual = sorted(
        path.relative_to(plugin).as_posix()
        for path in plugin.rglob("*")
        if path.is_file() and path.name != PROVENANCE_MARKER_NAME
    )
    expected = [item.relative_path for item in files]
    if actual != expected:
        raise ReleaseMaterializationError("staged payload file identity differs from the archive")
    if any(path.is_symlink() for path in plugin.rglob("*")):
        raise ReleaseMaterializationError("staged payload contains a symlink")
    for item in files:
        path = plugin / Path(*PurePosixPath(item.relative_path).parts)
        if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(item.content).digest():
            raise ReleaseMaterializationError("staged payload digest differs from the archive")


def _write_atomic_text(path: Path, value: str) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=".current-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_release(
    repo: Path,
    release_root: Path = DEFAULT_RELEASE_ROOT,
    *,
    authorization: ReleaseMaterializationAuthorization | None = None,
    authorization_file: Path | None = None,
    commit: str = ACCEPTED_GIT_COMMIT,
) -> dict[str, Any]:
    """Materialize one immutable release after consuming explicit authority.

    All Git and destination checks happen before the one-shot authorization is
    consumed.  The first release-root write happens only after consumption and
    durable authorization-state update (when an authorization file is used).
    """

    if authorization is None:
        raise AuthorizationRequiredError("explicit one-shot authorization is required")
    if commit != ACCEPTED_GIT_COMMIT:
        raise ReleaseMaterializationError("only the accepted commit may be materialized")
    repository = _absolute(repo)
    root = _absolute(release_root)
    target = root / "releases" / commit / PLUGIN_DIRECTORY_NAME
    if repository == root or repository in root.parents:
        raise ReleaseMaterializationError("source repository and release root must be distinct")
    _git(repository, "rev-parse", "--verify", f"{commit}^{{commit}}")
    _assert_clean_control_plane(repository)
    archive = _git_archive(repository, commit)
    files = _read_archive(archive)
    _validate_identity(files)
    manifest = _manifest(repository, target, files, commit)
    _check_existing_components(root, target)
    previous_current = _read_existing_current(root)

    authorization.consume(git_commit=commit, release_root=root)
    if authorization_file is not None:
        state_path = _authorization_path(authorization_file, root)
        save_authorization(state_path, authorization)

    stage: Path | None = None
    moved = False
    current_swapped = False
    root_created = False
    try:
        root.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=".storefront-prod-materialization-", dir=root.parent))
        _write_staged_payload(stage, files)
        marker = stage / PLUGIN_DIRECTORY_NAME / PROVENANCE_MARKER_NAME
        _write_text(marker, _canonical_json(manifest))
        _verify_staged_payload(stage, files)

        if not root.exists():
            root.mkdir()
            root_created = True
        _check_existing_components(root, target)
        releases = root / "releases"
        releases.mkdir(exist_ok=True)
        commit_dir = releases / commit
        commit_dir.mkdir()
        os.replace(stage / PLUGIN_DIRECTORY_NAME, target)
        moved = True
        _write_atomic_text(root / CURRENT_MANIFEST_NAME, _canonical_json(manifest))
        current_swapped = True
        try:
            validate_release(root)
        except ReleaseManifestError as exc:
            raise ReleaseMaterializationError("materialized release failed runtime validation") from exc
        return manifest
    except Exception:
        if current_swapped and root.exists() and not root.is_symlink():
            current = root / CURRENT_MANIFEST_NAME
            if previous_current is None:
                if current.exists() and not current.is_symlink():
                    current.unlink()
            else:
                _write_atomic_text(current, previous_current)
        if moved and target.exists() and not target.is_symlink():
            shutil.rmtree(target)
        commit_dir = target.parent
        if commit_dir.exists() and not commit_dir.is_symlink():
            try:
                commit_dir.rmdir()
            except OSError:
                pass
        if root_created and root.exists() and not root.is_symlink():
            shutil.rmtree(root)
        raise
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage)


__all__ = [
    "ARCHIVE_SUBTREE",
    "AuthorizationConsumedError",
    "AuthorizationRequiredError",
    "EXPECTED_FILE_COUNT",
    "ReleaseMaterializationAuthorization",
    "ReleaseMaterializationError",
    "issue_authorization",
    "load_authorization",
    "materialize_release",
    "save_authorization",
]
