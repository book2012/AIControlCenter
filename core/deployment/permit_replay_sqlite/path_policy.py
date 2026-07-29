"""Explicit Mac application-state path policy for future permit/replay state."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class PermitReplayPathPolicy:
    repository_root: Path
    user_home: Path

    @property
    def canonical_future_path(self) -> Path:
        return (
            self.user_home / "Library" / "Application Support" /
            "AIControlCenter" / "security" / "permit-replay.sqlite3"
        )

    def identity_digest(self, configured_path: Path) -> str:
        return "sha256:" + hashlib.sha256(os.fsencode(configured_path)).hexdigest()

    def validate(self, configured_path: Path) -> tuple[str, ...]:
        path = Path(configured_path)
        if not path.is_absolute():
            return ("RELATIVE_PATH",)
        reasons: list[str] = []
        if ".." in path.parts:
            reasons.append("PATH_TRAVERSAL")
        normalized = path.name.lower().replace("-", "_")
        if any(marker in normalized for marker in (
            "password", "secret", "token", "api_key", "apikey", "private_key",
            "cookie", "authorization", "credential", "nonce",
        )):
            reasons.append("SECRET_BEARING_DATABASE_NAME")
        allowed_root = self.user_home / "Library" / "Application Support"
        try:
            path.relative_to(allowed_root)
        except ValueError:
            reasons.append("OUTSIDE_USER_APPLICATION_STATE")
        try:
            path.relative_to(self.repository_root.resolve())
            reasons.append("REPOSITORY_PATH")
        except ValueError:
            pass
        raw = str(path)
        protected = (
            "/System", "/Library", "/Applications", "/usr", "/bin", "/sbin",
            "/etc", "/home", "/var", "/srv", "/mnt", "/media", "/Volumes",
        )
        if any(raw == prefix or raw.startswith(prefix + "/") for prefix in protected):
            reasons.append("PROTECTED_OR_NON_MAC_OWNERSHIP_PATH")
        current = Path(path.anchor)
        for component in path.parts[1:]:
            current /= component
            if current.is_symlink():
                reasons.append("SYMLINK_PATH_COMPONENT")
                break
            if not current.exists():
                break
        return tuple(sorted(set(reasons)))
