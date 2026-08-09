#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
from typing import Any


RUNTIME_ID_RE = re.compile(r"^[0-9a-f]{12}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

MARKER_NAME = ".aicontrolcenter-source-commit"
MANIFEST_NAME = ".aicontrolcenter-source-manifest.json"


class SourceArtifactError(RuntimeError):
    pass


def emit(payload: dict[str, Any]) -> None:
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )


def require_runtime_id(value: str) -> str:
    if RUNTIME_ID_RE.fullmatch(value) is None:
        raise SourceArtifactError("RUNTIME_ID_INVALID")

    return value


def require_commit(value: str) -> str:
    if COMMIT_RE.fullmatch(value) is None:
        raise SourceArtifactError("SOURCE_COMMIT_INVALID")

    return value


def git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-C",
            str(repository),
            *arguments,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )

    if completed.returncode != 0:
        raise SourceArtifactError(
            "GIT_OPERATION_FAILED:"
            + completed.stderr.strip()
        )

    return completed.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        for block in iter(
            lambda: stream.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def content_digest(root: Path) -> str:
    digest = hashlib.sha256()

    for path in sorted(
        root.rglob("*"),
        key=lambda item: item.relative_to(root).as_posix(),
    ):
        relative = path.relative_to(root).as_posix()

        if relative == MANIFEST_NAME:
            continue

        info = path.lstat()

        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")

        if stat.S_ISLNK(info.st_mode):
            digest.update(b"L\0")
            digest.update(
                os.readlink(path).encode("utf-8")
            )

        elif stat.S_ISDIR(info.st_mode):
            digest.update(b"D\0")

        elif stat.S_ISREG(info.st_mode):
            digest.update(b"F\0")

            with path.open("rb") as stream:
                for block in iter(
                    lambda: stream.read(1024 * 1024),
                    b"",
                ):
                    digest.update(block)

        else:
            raise SourceArtifactError(
                "UNSUPPORTED_SOURCE_OBJECT:"
                + relative
            )

        digest.update(b"\0")

    return digest.hexdigest()


def inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_symlinks(root: Path) -> None:
    canonical_root = root.resolve()

    for path in root.rglob("*"):
        if not path.is_symlink():
            continue

        target = path.resolve(strict=False)

        if not inside(target, canonical_root):
            raise SourceArtifactError(
                "SOURCE_SYMLINK_ESCAPES_ARTIFACT:"
                + path.relative_to(root).as_posix()
            )


def make_read_only(root: Path) -> None:
    paths = sorted(
        root.rglob("*"),
        key=lambda item: len(item.parts),
        reverse=True,
    )

    for path in paths:
        if path.is_symlink():
            continue

        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode & ~0o222)

    mode = stat.S_IMODE(root.stat().st_mode)
    root.chmod(mode & ~0o222)


def make_writable_for_cleanup(root: Path) -> None:
    if not root.exists() and not root.is_symlink():
        return

    if root.is_symlink():
        root.unlink()
        return

    for current, directories, files in os.walk(
        root,
        topdown=True,
        followlinks=False,
    ):
        current_path = Path(current)

        try:
            current_path.chmod(0o700)
        except OSError:
            pass

        for name in directories:
            path = current_path / name

            if path.is_symlink():
                continue

            try:
                path.chmod(0o700)
            except OSError:
                pass

        for name in files:
            path = current_path / name

            if path.is_symlink():
                continue

            try:
                path.chmod(0o600)
            except OSError:
                pass


def safe_extract(
    archive: Path,
    destination: Path,
) -> None:
    import tarfile

    with tarfile.open(
        archive,
        mode="r:",
    ) as bundle:
        for member in bundle.getmembers():
            relative = PurePosixPath(member.name)

            if relative.is_absolute():
                raise SourceArtifactError(
                    "ARCHIVE_ABSOLUTE_PATH_REJECTED"
                )

            if ".." in relative.parts:
                raise SourceArtifactError(
                    "ARCHIVE_PATH_TRAVERSAL_REJECTED"
                )

        bundle.extractall(
            destination,
            filter="data",
        )

    validate_symlinks(destination)


def validate_build_root(
    runtime_root: Path,
    *,
    allow_operational_write: bool,
) -> Path:
    raw = runtime_root.expanduser()

    if raw.is_symlink():
        raise SourceArtifactError(
            "RUNTIME_ROOT_SYMLINK_REJECTED"
        )

    canonical = raw.resolve()

    operational = (
        Path.home()
        / "Library"
        / "Application Support"
        / "AIControlCenter"
        / "runtime"
    ).resolve()

    if allow_operational_write:
        if canonical != operational:
            raise SourceArtifactError(
                "OPERATIONAL_RUNTIME_ROOT_INVALID"
            )

        if os.geteuid() == 0:
            raise SourceArtifactError(
                "OPERATIONAL_ROOT_EXECUTION_REJECTED"
            )

    else:
        if not str(canonical).startswith(
            "/private/tmp/"
        ):
            raise SourceArtifactError(
                "TEST_RUNTIME_ROOT_NOT_PRIVATE_TMP"
            )

    return canonical


def validate_artifact(
    *,
    runtime_root: Path,
    artifact: Path,
    runtime_id: str,
    expected_source_commit: str | None,
    require_final_name: bool,
) -> dict[str, Any]:
    runtime_id = require_runtime_id(runtime_id)

    runtime_root = runtime_root.expanduser().resolve()

    source_parent = (
        runtime_root / "sources"
    ).resolve()

    if artifact.is_symlink():
        raise SourceArtifactError(
            "SOURCE_ARTIFACT_SYMLINK_REJECTED"
        )

    if not artifact.is_dir():
        raise SourceArtifactError(
            "SOURCE_ARTIFACT_UNAVAILABLE"
        )

    canonical = artifact.resolve()

    if canonical.parent != source_parent:
        raise SourceArtifactError(
            "SOURCE_ARTIFACT_NOT_DIRECT_CHILD"
        )

    if (
        require_final_name
        and canonical.name != runtime_id
    ):
        raise SourceArtifactError(
            "SOURCE_ARTIFACT_RUNTIME_ID_MISMATCH"
        )

    marker_path = canonical / MARKER_NAME
    manifest_path = canonical / MANIFEST_NAME

    required_files = (
        canonical / "core" / "api" / "shadow.py",
        canonical / "core" / "runtime" / "data_paths.py",
        canonical / "config" / "workers.yaml",
    )

    if not marker_path.is_file():
        raise SourceArtifactError(
            "SOURCE_MARKER_UNAVAILABLE"
        )

    marker_bytes = marker_path.read_bytes()

    try:
        marker_text = marker_bytes.decode("ascii")
    except UnicodeDecodeError as error:
        raise SourceArtifactError(
            "SOURCE_MARKER_INVALID"
        ) from error

    if (
        not marker_text.endswith("\n")
        or marker_text.count("\n") != 1
    ):
        raise SourceArtifactError(
            "SOURCE_MARKER_INVALID"
        )

    source_commit = marker_text[:-1]
    require_commit(source_commit)

    if expected_source_commit is not None:
        if source_commit != require_commit(
            expected_source_commit
        ):
            raise SourceArtifactError(
                "SOURCE_COMMIT_MISMATCH"
            )

    if not manifest_path.is_file():
        raise SourceArtifactError(
            "SOURCE_MANIFEST_UNAVAILABLE"
        )

    try:
        manifest = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        raise SourceArtifactError(
            "SOURCE_MANIFEST_INVALID"
        ) from error

    required_manifest_fields = {
        "schema_version",
        "runtime_id",
        "source_commit",
        "git_tree",
        "archive_sha256",
        "content_sha256",
        "artifact_root",
        "build_status",
        "production_authorized",
    }

    if set(manifest) != required_manifest_fields:
        raise SourceArtifactError(
            "SOURCE_MANIFEST_FIELDS_INVALID"
        )

    if manifest["schema_version"] != 1:
        raise SourceArtifactError(
            "SOURCE_MANIFEST_SCHEMA_INVALID"
        )

    if manifest["runtime_id"] != runtime_id:
        raise SourceArtifactError(
            "SOURCE_MANIFEST_RUNTIME_ID_MISMATCH"
        )

    if manifest["source_commit"] != source_commit:
        raise SourceArtifactError(
            "SOURCE_MANIFEST_COMMIT_MISMATCH"
        )

    git_tree = manifest["git_tree"]

    if (
        not isinstance(git_tree, str)
        or COMMIT_RE.fullmatch(git_tree) is None
    ):
        raise SourceArtifactError(
            "SOURCE_MANIFEST_GIT_TREE_INVALID"
        )

    for field in (
        "archive_sha256",
        "content_sha256",
    ):
        value = manifest[field]

        if (
            not isinstance(value, str)
            or SHA256_RE.fullmatch(value) is None
        ):
            raise SourceArtifactError(
                "SOURCE_MANIFEST_"
                + field.upper()
                + "_INVALID"
            )

    expected_artifact_root = (
        runtime_root
        / "sources"
        / runtime_id
    ).resolve()

    if (
        manifest["artifact_root"]
        != str(expected_artifact_root)
    ):
        raise SourceArtifactError(
            "SOURCE_MANIFEST_ARTIFACT_ROOT_MISMATCH"
        )

    if manifest["build_status"] != "COMPLETE":
        raise SourceArtifactError(
            "SOURCE_MANIFEST_BUILD_STATUS_INVALID"
        )

    if manifest["production_authorized"] is not False:
        raise SourceArtifactError(
            "SOURCE_MANIFEST_PRODUCTION_FLAG_INVALID"
        )

    for required_file in required_files:
        if not required_file.is_file():
            raise SourceArtifactError(
                "REQUIRED_RUNTIME_SOURCE_ASSET_UNAVAILABLE:"
                + required_file.relative_to(
                    canonical
                ).as_posix()
            )

    if (canonical / ".git").exists():
        raise SourceArtifactError(
            "SOURCE_ARTIFACT_GIT_METADATA_REJECTED"
        )

    validate_symlinks(canonical)

    for path in [
        canonical,
        *canonical.rglob("*"),
    ]:
        if path.is_symlink():
            continue

        mode = stat.S_IMODE(
            path.stat().st_mode
        )

        if mode & 0o222:
            relative = (
                "."
                if path == canonical
                else path.relative_to(
                    canonical
                ).as_posix()
            )

            raise SourceArtifactError(
                "SOURCE_ARTIFACT_WRITABLE:"
                + relative
            )

    calculated = content_digest(canonical)

    if calculated != manifest["content_sha256"]:
        raise SourceArtifactError(
            "SOURCE_CONTENT_DIGEST_MISMATCH"
        )

    return {
        "status": "PASS",
        "schema_version": 1,
        "runtime_id": runtime_id,
        "source_commit": source_commit,
        "git_tree": git_tree,
        "archive_sha256": manifest[
            "archive_sha256"
        ],
        "content_sha256": calculated,
        "artifact_root": str(canonical),
        "application_entrypoint": str(
            canonical
            / "core"
            / "api"
            / "shadow.py"
        ),
        "data_path_contract": str(
            canonical
            / "core"
            / "runtime"
            / "data_paths.py"
        ),
        "worker_config": str(
            canonical
            / "config"
            / "workers.yaml"
        ),
        "immutable": True,
        "production_authorized": False,
    }


def build(
    args: argparse.Namespace,
) -> dict[str, Any]:
    runtime_id = require_runtime_id(
        args.runtime_id
    )

    source_commit = require_commit(
        args.source_commit
    )

    repository = Path(
        args.repository_root
    ).expanduser().resolve()

    if not repository.is_dir():
        raise SourceArtifactError(
            "REPOSITORY_ROOT_INVALID"
        )

    runtime_root = validate_build_root(
        Path(args.runtime_root),
        allow_operational_write=(
            args.allow_operational_write
        ),
    )

    if (
        inside(runtime_root, repository)
        or inside(repository, runtime_root)
    ):
        raise SourceArtifactError(
            "REPOSITORY_RUNTIME_OVERLAP_REJECTED"
        )

    resolved_commit = git(
        repository,
        "rev-parse",
        "--verify",
        source_commit + "^{commit}",
    )

    if resolved_commit != source_commit:
        raise SourceArtifactError(
            "SOURCE_COMMIT_RESOLUTION_MISMATCH"
        )

    git_tree = git(
        repository,
        "rev-parse",
        source_commit + "^{tree}",
    )

    if COMMIT_RE.fullmatch(git_tree) is None:
        raise SourceArtifactError(
            "GIT_TREE_INVALID"
        )

    source_parent = runtime_root / "sources"

    if source_parent.is_symlink():
        raise SourceArtifactError(
            "SOURCE_PARENT_SYMLINK_REJECTED"
        )

    source_parent.mkdir(
        parents=True,
        exist_ok=True,
        mode=0o700,
    )

    source_parent.chmod(0o700)

    final = source_parent / runtime_id

    if final.exists() or final.is_symlink():
        raise SourceArtifactError(
            "SOURCE_DESTINATION_ALREADY_EXISTS"
        )

    staging = source_parent / (
        "."
        + runtime_id
        + "."
        + str(os.getpid())
        + ".staging"
    )

    if staging.exists() or staging.is_symlink():
        raise SourceArtifactError(
            "SOURCE_STAGING_ALREADY_EXISTS"
        )

    archive_fd, archive_name = tempfile.mkstemp(
        prefix="." + runtime_id + ".",
        suffix=".tar",
        dir=str(source_parent),
    )

    os.close(archive_fd)

    archive = Path(archive_name)
    staging_created = False

    try:
        completed = subprocess.run(
            [
                "/usr/bin/git",
                "-C",
                str(repository),
                "archive",
                "--format=tar",
                "-o",
                str(archive),
                source_commit,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )

        if completed.returncode != 0:
            raise SourceArtifactError(
                "GIT_ARCHIVE_FAILED:"
                + completed.stderr.strip()
            )

        archive_sha256 = sha256_file(archive)

        staging.mkdir(mode=0o700)
        staging_created = True

        safe_extract(
            archive,
            staging,
        )

        (
            staging
            / MARKER_NAME
        ).write_text(
            source_commit + "\n",
            encoding="ascii",
        )

        calculated = content_digest(staging)

        manifest = {
            "schema_version": 1,
            "runtime_id": runtime_id,
            "source_commit": source_commit,
            "git_tree": git_tree,
            "archive_sha256": archive_sha256,
            "content_sha256": calculated,
            "artifact_root": str(
                final.resolve()
            ),
            "build_status": "COMPLETE",
            "production_authorized": False,
        }

        (
            staging
            / MANIFEST_NAME
        ).write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        make_read_only(staging)

        validate_artifact(
            runtime_root=runtime_root,
            artifact=staging,
            runtime_id=runtime_id,
            expected_source_commit=source_commit,
            require_final_name=False,
        )

        if final.exists() or final.is_symlink():
            raise SourceArtifactError(
                "SOURCE_DESTINATION_ALREADY_EXISTS"
            )

        os.rename(
            staging,
            final,
        )

        staging_created = False

        result = validate_artifact(
            runtime_root=runtime_root,
            artifact=final,
            runtime_id=runtime_id,
            expected_source_commit=source_commit,
            require_final_name=True,
        )

        result["operation"] = "BUILD"

        result[
            "operational_write_authorized"
        ] = bool(
            args.allow_operational_write
        )

        return result

    finally:
        try:
            archive.unlink()
        except FileNotFoundError:
            pass

        if staging_created:
            make_writable_for_cleanup(
                staging
            )

            shutil.rmtree(
                staging,
                ignore_errors=True,
            )


def validate(
    args: argparse.Namespace,
) -> dict[str, Any]:
    runtime_root = Path(
        args.runtime_root
    ).expanduser().resolve()

    runtime_id = require_runtime_id(
        args.runtime_id
    )

    artifact = (
        runtime_root
        / "sources"
        / runtime_id
    )

    result = validate_artifact(
        runtime_root=runtime_root,
        artifact=artifact,
        runtime_id=runtime_id,
        expected_source_commit=(
            args.expected_source_commit
        ),
        require_final_name=True,
    )

    result["operation"] = "VALIDATE"

    return result


def make_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()

    commands = root.add_subparsers(
        dest="command",
        required=True,
    )

    build_parser = commands.add_parser(
        "build"
    )

    build_parser.add_argument(
        "--repository-root",
        required=True,
    )

    build_parser.add_argument(
        "--runtime-root",
        required=True,
    )

    build_parser.add_argument(
        "--runtime-id",
        required=True,
    )

    build_parser.add_argument(
        "--source-commit",
        required=True,
    )

    build_parser.add_argument(
        "--allow-operational-write",
        action="store_true",
    )

    validate_parser = commands.add_parser(
        "validate"
    )

    validate_parser.add_argument(
        "--runtime-root",
        required=True,
    )

    validate_parser.add_argument(
        "--runtime-id",
        required=True,
    )

    validate_parser.add_argument(
        "--expected-source-commit",
    )

    return root


def main() -> int:
    args = make_parser().parse_args()

    try:
        if args.command == "build":
            result = build(args)
        else:
            result = validate(args)

    except SourceArtifactError as error:
        emit(
            {
                "status": "ERROR",
                "error": str(error),
                "production_authorized": False,
            }
        )

        return 3

    except Exception as error:
        emit(
            {
                "status": "ERROR",
                "error": (
                    "INTERNAL_ERROR:"
                    + type(error).__name__
                ),
                "production_authorized": False,
            }
        )

        return 4

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
