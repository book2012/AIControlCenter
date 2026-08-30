"""Pure SEC-02 pre-bootstrap filesystem planning and classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
import pwd
import stat
import sys
from pathlib import PurePath
from typing import Callable

GOVERNANCE_COMPONENTS = ("Library", "Application Support", "AIControlCenter", "governance")
TRUST_COMPONENT = "trust"
REQUIRED_DIRECTORY_MODE = 0o700


class FilesystemContractError(ValueError):
    """The trusted identity or fixed filesystem contract could not be proved."""


class GovernedPath(Enum):
    GOVERNANCE = "GOVERNANCE"
    TRUST = "TRUST"


class ExistingObjectKind(Enum):
    DIRECTORY = "DIRECTORY"
    SYMLINK = "SYMLINK"
    OTHER = "OTHER"


class FilesystemClassification(Enum):
    ABSENT = "ABSENT"
    SAFE_EXISTING = "SAFE_EXISTING"
    UNSAFE_EXISTING = "UNSAFE_EXISTING"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True, slots=True)
class TrustedFilesystemIdentity:
    bound_uid: int
    bound_gid: int
    passwd_home: str


@dataclass(frozen=True, slots=True)
class PreBootstrapFilesystemPlan:
    identity: TrustedFilesystemIdentity
    governance_path: str
    trust_path: str


@dataclass(frozen=True, slots=True)
class FilesystemObservation:
    path: GovernedPath
    proven_absent: bool = False
    object_kind: ExistingObjectKind | None = None
    uid: int | None = None
    gid: int | None = None
    mode: int | None = None
    descriptor_identity_proven: bool = False
    observation_complete: bool = True


def _exact_nonnegative_int(value: object) -> bool:
    return type(value) is int and value >= 0


def plan_pre_bootstrap_filesystem() -> PreBootstrapFilesystemPlan:
    """Resolve the fixed plan solely from process and Darwin passwd authority."""
    return _plan_pre_bootstrap_filesystem(
        platform_source=lambda: __import__("sys").platform,
        getuid=os.getuid,
        geteuid=os.geteuid,
        passwd_lookup=pwd.getpwuid,
    )


def observe_pre_bootstrap_filesystem() -> tuple[FilesystemObservation, FilesystemObservation]:
    """Read the two fixed Darwin directories; never create or modify them."""
    plan = plan_pre_bootstrap_filesystem()
    if sys.platform != "darwin" or not all(hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_CLOEXEC")):
        ambiguous = lambda path: FilesystemObservation(path, observation_complete=False)
        return ambiguous(GovernedPath.GOVERNANCE), ambiguous(GovernedPath.TRUST)
    return _observe_pre_bootstrap_filesystem(plan)


def _observe_pre_bootstrap_filesystem(
    plan: PreBootstrapFilesystemPlan,
) -> tuple[FilesystemObservation, FilesystemObservation]:
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    descriptors: list[int] = []

    def ambiguous(path: GovernedPath) -> FilesystemObservation:
        return FilesystemObservation(path, observation_complete=False)

    def valid_directory(metadata: object) -> bool:
        return stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)

    def open_existing(parent_fd: int, name: str) -> tuple[int, object, object]:
        """Bind a no-follow directory entry to its opened descriptor."""
        entry = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if not valid_directory(entry):
            raise FilesystemContractError("prerequisite is not a real directory")
        descriptor = os.open(name, flags, dir_fd=parent_fd)
        descriptors.append(descriptor)
        opened = os.fstat(descriptor)
        if (
            not valid_directory(opened)
            or (entry.st_dev, entry.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise FilesystemContractError("prerequisite descriptor identity is ambiguous")
        return descriptor, entry, opened

    def leaf(parent_fd: int, name: str, path: GovernedPath) -> tuple[FilesystemObservation, int | None]:
        try:
            metadata = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return FilesystemObservation(path, proven_absent=True), None
        except (OSError, TypeError, ValueError):
            return ambiguous(path), None
        if stat.S_ISLNK(metadata.st_mode):
            return FilesystemObservation(path, object_kind=ExistingObjectKind.SYMLINK, descriptor_identity_proven=True), None
        if not stat.S_ISDIR(metadata.st_mode):
            return FilesystemObservation(path, object_kind=ExistingObjectKind.OTHER, descriptor_identity_proven=True), None
        try:
            descriptor = os.open(name, flags, dir_fd=parent_fd)
            descriptors.append(descriptor)
            opened = os.fstat(descriptor)
        except (OSError, TypeError, ValueError):
            return ambiguous(path), None
        stable = (
            valid_directory(opened)
            and (metadata.st_dev, metadata.st_ino) == (opened.st_dev, opened.st_ino)
        )
        return FilesystemObservation(
            path, object_kind=ExistingObjectKind.DIRECTORY, uid=opened.st_uid, gid=opened.st_gid,
            mode=stat.S_IMODE(opened.st_mode), descriptor_identity_proven=stable,
            observation_complete=stable,
        ), descriptor

    try:
        root = os.open("/", flags)
        descriptors.append(root)
        root_metadata = os.fstat(root)
        if not valid_directory(root_metadata) or root_metadata.st_mode & 0o022:
            raise FilesystemContractError("filesystem root violates the system-ancestor policy")
        current = root
        home = PurePath(plan.identity.passwd_home)
        home_components = home.parts[1:]
        parent_components = (*home_components, *GOVERNANCE_COMPONENTS[:-1])
        home_index = len(home_components) - 1
        shared_parent_index = len(parent_components) - 1
        for index, component in enumerate(parent_components):
            current, _, opened = open_existing(current, component)
            mode = stat.S_IMODE(opened.st_mode)
            if index < home_index:  # SYSTEM_ANCESTOR: ownership is intentionally irrelevant.
                safe = opened.st_mode & 0o022 == 0
            elif index < shared_parent_index:  # passwd home, Library, Application Support
                safe = (
                    (opened.st_uid, opened.st_gid)
                    == (plan.identity.bound_uid, plan.identity.bound_gid)
                    and opened.st_mode & 0o022 == 0
                )
            else:  # exact fixed AIControlCenter shared parent
                safe = (
                    (opened.st_uid, opened.st_gid)
                    == (plan.identity.bound_uid, plan.identity.bound_gid)
                    and mode == 0o755
                )
            if not safe:
                raise FilesystemContractError("prerequisite violates its closed ancestor policy")
        governance, governance_fd = leaf(current, GOVERNANCE_COMPONENTS[-1], GovernedPath.GOVERNANCE)
        if governance_fd is None:
            return governance, ambiguous(GovernedPath.TRUST)
        trust, _ = leaf(governance_fd, TRUST_COMPONENT, GovernedPath.TRUST)
        return governance, trust
    except (OSError, TypeError, ValueError):
        return ambiguous(GovernedPath.GOVERNANCE), ambiguous(GovernedPath.TRUST)
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _plan_pre_bootstrap_filesystem(
    *,
    platform_source: Callable[[], str],
    getuid: Callable[[], int],
    geteuid: Callable[[], int],
    passwd_lookup: Callable[[int], object],
) -> PreBootstrapFilesystemPlan:
    if platform_source() != "darwin":
        raise FilesystemContractError("pre-bootstrap filesystem planning is Darwin-only")
    ruid, euid = getuid(), geteuid()
    if not _exact_nonnegative_int(ruid) or not _exact_nonnegative_int(euid) or ruid != euid or ruid == 0:
        raise FilesystemContractError("real and effective identity is invalid")
    try:
        record = passwd_lookup(ruid)
        uid, gid, home_value = record.pw_uid, record.pw_gid, record.pw_dir
    except (AttributeError, KeyError, OSError, TypeError) as error:
        raise FilesystemContractError("passwd identity is unavailable") from error
    if uid != ruid or not _exact_nonnegative_int(uid) or not _exact_nonnegative_int(gid):
        raise FilesystemContractError("passwd identity does not match the bound UID")
    if type(home_value) is not str or not home_value:
        raise FilesystemContractError("passwd home is invalid")
    home = PurePath(home_value)
    if not home.is_absolute() or any(part in {"", ".", ".."} for part in home.parts[1:]):
        raise FilesystemContractError("passwd home must be an unambiguous absolute path")
    governance = home.joinpath(*GOVERNANCE_COMPONENTS)
    identity = TrustedFilesystemIdentity(uid, gid, home_value)
    return PreBootstrapFilesystemPlan(identity, str(governance), str(governance / TRUST_COMPONENT))


def classify_governed_directory(
    observation: FilesystemObservation,
    identity: TrustedFilesystemIdentity,
) -> FilesystemClassification:
    """Classify one fixed governed directory without filesystem I/O."""
    if type(observation) is not FilesystemObservation or type(identity) is not TrustedFilesystemIdentity:
        return FilesystemClassification.AMBIGUOUS
    if not observation.observation_complete:
        return FilesystemClassification.AMBIGUOUS
    if observation.proven_absent:
        if any(value is not None for value in (observation.object_kind, observation.uid, observation.gid, observation.mode)):
            return FilesystemClassification.AMBIGUOUS
        return FilesystemClassification.ABSENT
    if not observation.descriptor_identity_proven:
        return FilesystemClassification.AMBIGUOUS
    if observation.object_kind is not ExistingObjectKind.DIRECTORY:
        return FilesystemClassification.UNSAFE_EXISTING
    if not all(_exact_nonnegative_int(value) for value in (observation.uid, observation.gid, observation.mode)):
        return FilesystemClassification.AMBIGUOUS
    if (observation.uid, observation.gid, observation.mode) != (
        identity.bound_uid,
        identity.bound_gid,
        REQUIRED_DIRECTORY_MODE,
    ):
        return FilesystemClassification.UNSAFE_EXISTING
    return FilesystemClassification.SAFE_EXISTING


__all__ = (
    "ExistingObjectKind", "FilesystemClassification", "FilesystemContractError",
    "FilesystemObservation", "GovernedPath", "PreBootstrapFilesystemPlan",
    "REQUIRED_DIRECTORY_MODE", "TrustedFilesystemIdentity",
    "classify_governed_directory", "plan_pre_bootstrap_filesystem",
    "observe_pre_bootstrap_filesystem",
)
