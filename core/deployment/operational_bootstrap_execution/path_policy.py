"""Trusted Mac home resolution and exact operational path policy."""

from __future__ import annotations

import os
import platform
import pwd
import stat
from dataclasses import dataclass
from pathlib import Path

from .models import (OperationalBootstrapExecutionError,
                     OperationalBootstrapSharedParentEvidence, canonical_digest)


class PwdMacOperationalHomeResolver:
    def resolve(self) -> Path:
        return Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()


@dataclass(frozen=True, slots=True)
class MacOperationalBootstrapPaths:
    root: Path
    audit_database: Path
    audit_backups: Path
    replay_database: Path
    replay_backups: Path
    monitoring: Path
    shared_parent_evidence: OperationalBootstrapSharedParentEvidence

    @property
    def managed_roots(self) -> tuple[Path, Path, Path]:
        return (self.audit_database.parent, self.replay_database.parent, self.monitoring)

    @property
    def managed_targets(self) -> tuple[Path, ...]:
        return (*self.managed_roots, self.audit_database, self.audit_backups,
                self.replay_database, self.replay_backups)


class MacOperationalBootstrapPathPolicy:
    def __init__(self, *, home_resolver: object, repository_root: Path,
                 test_home: Path | None = None) -> None:
        self.home_resolver = home_resolver
        self.repository_root = Path(repository_root).resolve()
        self.test_home = Path(test_home).resolve() if test_home else None

    def resolve(self, *, caller_root: Path | None = None,
                test_only: bool = False) -> MacOperationalBootstrapPaths:
        home = Path(self.home_resolver.resolve())
        if not home.is_absolute():
            raise OperationalBootstrapExecutionError("TRUSTED_HOME_INVALID")
        if caller_root is not None:
            raise OperationalBootstrapExecutionError("CALLER_SELECTED_ROOT_REJECTED")
        if test_only:
            if self.test_home is None or home != self.test_home:
                raise OperationalBootstrapExecutionError("TEST_HOME_BINDING_INVALID")
        elif platform.system() != "Darwin" or os.getuid() == 0:
            raise OperationalBootstrapExecutionError("TRUSTED_MAC_NON_ROOT_REQUIRED")
        root = home / "Library" / "Application Support" / "AIControlCenter"
        evidence = self._validate(root)
        return MacOperationalBootstrapPaths(
            root, root / "audit" / "audit-ledger.sqlite3", root / "audit" / "backups",
            root / "security" / "permit-replay.sqlite3", root / "security" / "backups",
            root / "monitoring", evidence)

    def _validate(self, root: Path) -> OperationalBootstrapSharedParentEvidence:
        if not root.is_absolute() or ".." in root.parts:
            raise OperationalBootstrapExecutionError("OPERATIONAL_PATH_INVALID")
        for candidate in reversed((root, *root.parents)):
            if candidate.is_symlink():
                raise OperationalBootstrapExecutionError("SYMLINK_PATH_REJECTED")
        try:
            root.resolve(strict=False).relative_to(self.repository_root)
            raise OperationalBootstrapExecutionError("REPOSITORY_OVERLAP_REJECTED")
        except ValueError:
            pass
        raw = str(root)
        if raw.startswith(("/Volumes/", "/Network/", "/System/", "/private/var/root/",
                           "/var/root/", "/mnt/", "/media/")):
            raise OperationalBootstrapExecutionError("UNTRUSTED_VOLUME_OR_SYSTEM_PATH")
        managed = (root / "audit", root / "security", root / "monitoring")
        preexisting = root.exists()
        mode = owner = None
        sibling_digests: tuple[str, ...] = ()
        restrictions: tuple[str, ...] = ()
        if preexisting:
            info = root.lstat()
            mode = stat.S_IMODE(info.st_mode)
            owner = info.st_uid
            if not stat.S_ISDIR(info.st_mode):
                raise OperationalBootstrapExecutionError("SHARED_PARENT_NOT_DIRECTORY")
            if owner != os.getuid():
                raise OperationalBootstrapExecutionError("SHARED_PARENT_OWNER_INVALID")
            if mode & 0o022:
                raise OperationalBootstrapExecutionError("SHARED_PARENT_GROUP_WORLD_WRITABLE")
            if any(path.exists() or path.is_symlink() for path in managed):
                raise OperationalBootstrapExecutionError("MANAGED_TARGET_ALREADY_EXISTS")
            siblings = tuple(root.iterdir())
            sibling_digests = tuple(sorted(canonical_digest({
                "name": child.name,
                "kind": "symlink" if child.is_symlink() else
                        "directory" if child.is_dir() else "file",
            }) for child in siblings))
            if mode != 0o700:
                restrictions = ("EXISTING_SHARED_PARENT_MODE_NOT_0700",)
        return OperationalBootstrapSharedParentEvidence(
            preexisting, not preexisting, mode, owner, root.is_symlink(), bool((mode or 0) & 0o022),
            len(sibling_digests), sibling_digests, True, restrictions, False)
