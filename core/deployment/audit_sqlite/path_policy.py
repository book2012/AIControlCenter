"""Mac application-state path policy for the future audit ledger."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SQLiteAuditPathPolicy:
    repository_root: Path
    user_home: Path

    @property
    def canonical_future_path(self) -> Path:
        return (
            self.user_home / "Library" / "Application Support" /
            "AIControlCenter" / "audit" / "audit-ledger.sqlite3"
        )

    def identity_digest(self, configured_path: Path) -> str:
        return "sha256:" + hashlib.sha256(
            os.fsencode(configured_path)
        ).hexdigest()

    def validate(self, configured_path: Path) -> tuple[str, ...]:
        path = Path(configured_path)
        reasons: list[str] = []
        if not path.is_absolute():
            return ("RELATIVE_PATH",)
        if ".." in path.parts:
            reasons.append("PATH_TRAVERSAL")
        lowered_name = path.name.lower()
        if any(term in lowered_name for term in (
            "password", "secret", "token", "api_key", "apikey",
            "private_key", "cookie", "authorization",
        )):
            reasons.append("SECRET_BEARING_DATABASE_NAME")
        allowed_root = self.user_home / "Library" / "Application Support"
        try:
            path.relative_to(allowed_root)
        except ValueError:
            reasons.append("OUTSIDE_USER_APPLICATION_SUPPORT")
        try:
            path.relative_to(self.repository_root.resolve())
            reasons.append("REPOSITORY_PATH")
        except ValueError:
            pass
        protected = ("/System", "/Library", "/Applications", "/usr", "/bin",
                     "/sbin", "/etc", "/home", "/var", "/srv", "/mnt", "/media",
                     "/Volumes")
        raw = str(path)
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
