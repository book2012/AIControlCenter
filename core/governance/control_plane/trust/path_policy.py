"""Read-only Darwin trust-registry path and descriptor policy."""

from __future__ import annotations

import os
import pwd
import stat
import sys
from pathlib import PurePath
from typing import Callable

from .models import PathPolicyError

REGISTRY_COMPONENTS = (
    "Library",
    "Application Support",
    "AIControlCenter",
    "governance",
    "trust",
)
REGISTRY_FILENAME = "sec02-human-issuers.v1.json"
REGISTRY_SUFFIX = PurePath(*REGISTRY_COMPONENTS, REGISTRY_FILENAME)
MAX_REGISTRY_BYTES = 1_048_576


def read_trust_registry() -> bytes:
    """Read the registry using only process and passwd identity authority."""
    return _read_trust_registry(
        platform_source=lambda: sys.platform,
        getuid=os.getuid,
        geteuid=os.geteuid,
        passwd_lookup=pwd.getpwuid,
    )


def _read_trust_registry(
    *,
    platform_source: Callable[[], str],
    getuid: Callable[[], int],
    geteuid: Callable[[], int],
    passwd_lookup: Callable[[int], pwd.struct_passwd],
) -> bytes:
    """Test seam for runtime sources; never a Production authority surface."""
    if platform_source() != "darwin":
        raise PathPolicyError("trust registry is Darwin-only")
    if not all(
        hasattr(os, name)
        for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC", "supports_dir_fd")
    ) or os.open not in os.supports_dir_fd:
        raise PathPolicyError("descriptor-relative no-follow traversal is unsupported")

    ruid, euid = getuid(), geteuid()
    if isinstance(ruid, bool) or isinstance(euid, bool) or ruid != euid:
        raise PathPolicyError("real and effective UID differ or are invalid")
    if ruid <= 0:
        raise PathPolicyError("root or invalid UID is prohibited")
    try:
        record = passwd_lookup(ruid)
    except (KeyError, OSError) as error:
        raise PathPolicyError("passwd identity is unavailable") from error
    if (
        isinstance(record.pw_uid, bool)
        or record.pw_uid != ruid
        or isinstance(record.pw_gid, bool)
        or record.pw_gid < 0
        or not isinstance(record.pw_dir, str)
        or not record.pw_dir
    ):
        raise PathPolicyError("passwd identity does not match the bound UID")
    expected_uid, expected_gid = record.pw_uid, record.pw_gid
    home = PurePath(record.pw_dir)
    if not home.is_absolute() or any(part in {"", ".", ".."} for part in home.parts[1:]):
        raise PathPolicyError("passwd home must be an unambiguous absolute path")

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    file_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []
    try:
        descriptor = os.open("/", directory_flags)
        descriptors.append(descriptor)
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise PathPolicyError("filesystem root is not a directory")
        components = (*home.parts[1:], *REGISTRY_COMPONENTS)
        for index, component in enumerate(components):
            descriptor = os.open(component, directory_flags, dir_fd=descriptor)
            descriptors.append(descriptor)
            opened_directory = os.fstat(descriptor)
            if not stat.S_ISDIR(opened_directory.st_mode):
                raise PathPolicyError("trust path component is not a directory")
            if index == len(components) - 1:
                if stat.S_IMODE(opened_directory.st_mode) != 0o700:
                    raise PathPolicyError("trust directory must have exact mode 0700")
                if (opened_directory.st_uid, opened_directory.st_gid) != (
                    expected_uid,
                    expected_gid,
                ):
                    raise PathPolicyError("trust directory ownership mismatch")

        file_descriptor = os.open(REGISTRY_FILENAME, file_flags, dir_fd=descriptor)
        descriptors.append(file_descriptor)
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise PathPolicyError("registry must be a regular file")
        if stat.S_IMODE(before.st_mode) != 0o600 or (
            before.st_uid,
            before.st_gid,
        ) != (expected_uid, expected_gid):
            raise PathPolicyError("registry mode or ownership mismatch")
        if before.st_size < 0 or before.st_size > MAX_REGISTRY_BYTES or before.st_nlink != 1:
            raise PathPolicyError("registry size or link policy mismatch")

        chunks: list[bytes] = []
        remaining = MAX_REGISTRY_BYTES + 1
        while remaining:
            chunk = os.read(file_descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(file_descriptor)
        stable = (
            before.st_dev,
            before.st_ino,
            before.st_mode,
            before.st_uid,
            before.st_gid,
            before.st_size,
            before.st_nlink,
        ) == (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_uid,
            after.st_gid,
            after.st_size,
            after.st_nlink,
        )
        if len(data) > MAX_REGISTRY_BYTES or len(data) != before.st_size or not stable:
            raise PathPolicyError("registry changed while being read")
        return data
    except PathPolicyError:
        raise
    except (OSError, TypeError, ValueError) as error:
        raise PathPolicyError("descriptor-bound registry read failed closed") from error
    finally:
        for opened_descriptor in reversed(descriptors):
            try:
                os.close(opened_descriptor)
            except OSError:
                pass
