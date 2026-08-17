"""Value-free filesystem observations for shopping secret provisioning."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileObservation:
    regular_file: bool
    symlink_rejected: bool
    expected_ownership: bool
    safe_mode: bool
    nonempty: bool


def executable_present(path: Path) -> bool:
    """Accept a fixed path resolving to a regular executable in trusted Homebrew."""
    try:
        resolved = path.resolve(strict=True)
        metadata = resolved.stat()
    except OSError:
        return False
    trusted_root = Path("/opt/homebrew")
    try:
        resolved.relative_to(trusted_root)
    except ValueError:
        return False
    return stat.S_ISREG(metadata.st_mode) and os.access(resolved, os.X_OK)


def observe_file(path: Path, *, expected_uid: int, maximum_mode: int) -> FileObservation:
    try:
        metadata = path.lstat()
    except OSError:
        return FileObservation(False, False, False, False, False)
    symlink = stat.S_ISLNK(metadata.st_mode)
    regular = stat.S_ISREG(metadata.st_mode)
    return FileObservation(
        regular_file=regular,
        symlink_rejected=symlink,
        expected_ownership=regular and metadata.st_uid == expected_uid,
        safe_mode=regular and stat.S_IMODE(metadata.st_mode) & ~maximum_mode == 0,
        nonempty=regular and metadata.st_size > 0,
    )


def structurally_safe_identity(path: Path, *, expected_uid: int) -> bool:
    observation = observe_file(path, expected_uid=expected_uid, maximum_mode=0o600)
    return (
        observation.regular_file
        and not observation.symlink_rejected
        and observation.expected_ownership
        and observation.safe_mode
        and observation.nonempty
    )


def syntactically_valid_public_metadata(path: Path, *, expected_uid: int) -> bool:
    """Legacy structural observation; not an authority for recipient validity."""
    observation = observe_file(path, expected_uid=expected_uid, maximum_mode=0o600)
    if not (
        observation.regular_file
        and not observation.symlink_rejected
        and observation.expected_ownership
        and observation.safe_mode
        and observation.nonempty
    ):
        return False
    return True


__all__ = (
    "FileObservation",
    "executable_present",
    "observe_file",
    "structurally_safe_identity",
    "syntactically_valid_public_metadata",
)
