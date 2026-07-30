"""Trusted Mac home resolution and exact operational path policy."""

from __future__ import annotations

import os
import platform
import pwd
from dataclasses import dataclass
from pathlib import Path

from .models import OperationalBootstrapExecutionError


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


class MacOperationalBootstrapPathPolicy:
    def __init__(self, *, home_resolver: object, repository_root: Path,
                 test_home: Path | None = None) -> None:
        self.home_resolver = home_resolver
        self.repository_root = Path(repository_root).resolve()
        self.test_home = Path(test_home).resolve() if test_home else None

    def resolve(self, *, caller_root: Path | None = None,
                test_only: bool = False) -> MacOperationalBootstrapPaths:
        home = Path(self.home_resolver.resolve()).resolve()
        if caller_root is not None:
            raise OperationalBootstrapExecutionError("CALLER_SELECTED_ROOT_REJECTED")
        if test_only:
            if self.test_home is None or home != self.test_home:
                raise OperationalBootstrapExecutionError("TEST_HOME_BINDING_INVALID")
        elif platform.system() != "Darwin" or os.getuid() == 0:
            raise OperationalBootstrapExecutionError("TRUSTED_MAC_NON_ROOT_REQUIRED")
        root = home / "Library" / "Application Support" / "AIControlCenter"
        self._validate(root)
        return MacOperationalBootstrapPaths(
            root, root / "audit" / "audit-ledger.sqlite3", root / "audit" / "backups",
            root / "security" / "permit-replay.sqlite3", root / "security" / "backups",
            root / "monitoring")

    def _validate(self, root: Path) -> None:
        if not root.is_absolute() or ".." in root.parts:
            raise OperationalBootstrapExecutionError("OPERATIONAL_PATH_INVALID")
        for candidate in (root, *root.parents):
            if candidate.exists() and candidate.is_symlink():
                raise OperationalBootstrapExecutionError("SYMLINK_PATH_REJECTED")
        try:
            root.relative_to(self.repository_root)
            raise OperationalBootstrapExecutionError("REPOSITORY_OVERLAP_REJECTED")
        except ValueError:
            pass
        raw = str(root)
        if raw.startswith(("/Volumes/", "/Network/", "/System/", "/private/var/root/",
                           "/var/root/", "/mnt/", "/media/")):
            raise OperationalBootstrapExecutionError("UNTRUSTED_VOLUME_OR_SYSTEM_PATH")
