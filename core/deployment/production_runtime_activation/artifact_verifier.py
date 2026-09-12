"""Read-only verification of the bootstrap runtime and its source artifact."""
from __future__ import annotations

import hmac
from importlib import import_module
import os
from pathlib import Path
import re
import stat

from core.runtime.metadata import RuntimeMetadata

from .models import ProductionRuntimeActivationError
from .plan import ProductionRuntimeActivationPlan

# Import the Control Plane's existing producer/validator, never candidate code.
# Its content_sha256 is a source-tree contract, not a canonical JSON digest.
_source_contract = import_module("ops.macos.runtime.runtime-source-artifact")


def _directory(path: Path, code: str) -> None:
    try:
        if (
            not path.is_absolute()
            or ".." in path.parts
            or path.resolve(strict=True) != path
            or not path.is_dir()
        ):
            raise ProductionRuntimeActivationError(code)
    except (OSError, RuntimeError) as exc:
        raise ProductionRuntimeActivationError(code) from exc


def _regular_file(path: Path, code: str) -> None:
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ProductionRuntimeActivationError(code)
    except OSError as exc:
        raise ProductionRuntimeActivationError(code) from exc


def _verify_marker(directory: Path, commit: str) -> None:
    path = directory / _source_contract.MARKER_NAME
    code = "CANDIDATE_SOURCE_MARKER_INVALID"
    _regular_file(path, code)
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ProductionRuntimeActivationError(code)
            marker = stream.read(42)
    except OSError as exc:
        raise ProductionRuntimeActivationError(code) from exc
    if re.fullmatch(rb"[0-9a-f]{40}\n", marker) is None:
        raise ProductionRuntimeActivationError(code)
    if marker != (commit + "\n").encode("ascii"):
        raise ProductionRuntimeActivationError("CANDIDATE_SOURCE_COMMIT_MISMATCH")


class FilesystemProductionRuntimeActivationArtifactVerifier:
    """Verify an explicit canonical runtime root without executing candidate code.

    Read venvs/<id> identity and sources/<id> using the existing source manifest
    validator. The plan binds sha256:<recomputed content_sha256>, not metadata
    JSON, archive bytes, or a venv tree. No current pointer is read or written.
    The caller must keep finalized candidates immutable through execution.
    """

    def __init__(self, runtime_root: Path) -> None:
        self.runtime_root = Path(runtime_root)

    def verify(self, plan: ProductionRuntimeActivationPlan) -> None:
        root = self.runtime_root
        _directory(root, "CANDIDATE_RUNTIME_ROOT_PATH_INVALID")
        runtime = root / "venvs" / plan.candidate_runtime_id
        source = root / "sources" / plan.candidate_runtime_id
        for parent, candidate, code in (
            (runtime.parent, runtime, "CANDIDATE_RUNTIME_PATH_INVALID"),
            (source.parent, source, "CANDIDATE_SOURCE_PATH_INVALID"),
        ):
            _directory(parent, code)
            _directory(candidate, code)

        _verify_marker(runtime, plan.candidate_source_commit)
        metadata_path = runtime / "metadata.json"
        metadata_code = "CANDIDATE_RUNTIME_METADATA_INVALID"
        _regular_file(metadata_path, metadata_code)
        try:
            metadata = RuntimeMetadata(metadata_path).status()
        except (OSError, ValueError, TypeError) as exc:
            raise ProductionRuntimeActivationError(metadata_code) from exc
        if metadata["available"] is not True:
            raise ProductionRuntimeActivationError(metadata_code)
        if (
            metadata["commit"] != plan.candidate_source_commit
            or metadata["short_commit"] != plan.candidate_runtime_id
        ):
            raise ProductionRuntimeActivationError("CANDIDATE_RUNTIME_METADATA_MISMATCH")

        _verify_marker(source, plan.candidate_source_commit)
        artifact_code = "CANDIDATE_SOURCE_ARTIFACT_INVALID"
        _regular_file(source / _source_contract.MANIFEST_NAME, artifact_code)
        try:
            # Check containment before the existing validator reads source files.
            _source_contract.validate_symlinks(source)
            evidence = _source_contract.validate_artifact(
                runtime_root=root,
                artifact=source,
                runtime_id=plan.candidate_runtime_id,
                expected_source_commit=plan.candidate_source_commit,
                require_final_name=True,
            )
        except (OSError, RuntimeError, ValueError, TypeError) as exc:
            raise ProductionRuntimeActivationError(artifact_code) from exc
        if not hmac.compare_digest(
            "sha256:" + evidence["content_sha256"],
            plan.source_artifact_content_digest,
        ):
            raise ProductionRuntimeActivationError("SOURCE_ARTIFACT_CONTENT_DIGEST_MISMATCH")
