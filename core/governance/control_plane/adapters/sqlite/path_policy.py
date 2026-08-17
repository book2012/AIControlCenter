"""Fail-closed path policy for the Mac control-plane evidence database."""

from __future__ import annotations

from dataclasses import dataclass
import stat
from pathlib import Path


class SQLitePathPolicyError(ValueError):
    """The requested database location is not a safe durable location."""


@dataclass(frozen=True, slots=True)
class SQLiteOwnershipIdentity:
    uid: int
    gid: int

    def __post_init__(self) -> None:
        if isinstance(self.uid, bool) or not isinstance(self.uid, int) or self.uid < 0:
            raise ValueError("uid must be a non-negative integer")
        if isinstance(self.gid, bool) or not isinstance(self.gid, int) or self.gid < 0:
            raise ValueError("gid must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class SQLiteAuthorizationConsumptionPathPolicy:
    repository_root: Path
    home: Path
    ownership_identity: SQLiteOwnershipIdentity
    _test_root: Path | None = None

    @classmethod
    def production(
        cls, *, repository_root: Path, ownership_identity: SQLiteOwnershipIdentity,
        home: Path | None = None
    ) -> "SQLiteAuthorizationConsumptionPathPolicy":
        return cls(repository_root=repository_root, home=home or Path.home(), ownership_identity=ownership_identity)

    @classmethod
    def isolated_test(
        cls, *, repository_root: Path, test_root: Path,
        ownership_identity: SQLiteOwnershipIdentity
    ) -> "SQLiteAuthorizationConsumptionPathPolicy":
        root = cls._absolute_without_traversal(test_root, "test_root")
        return cls(repository_root=repository_root, home=root, ownership_identity=ownership_identity, _test_root=root)

    def _require_private_owned(self, path: Path, expected_mode: int, kind: str) -> None:
        details = path.stat(follow_symlinks=False)
        if (details.st_uid, details.st_gid) != (
            self.ownership_identity.uid, self.ownership_identity.gid
        ):
            raise SQLitePathPolicyError(f"{kind} ownership is unsafe")
        if stat.S_IMODE(details.st_mode) != expected_mode:
            raise SQLitePathPolicyError(f"{kind} permissions are unsafe")

    def _require_shared_owned(self, path: Path, kind: str) -> None:
        details = path.stat(follow_symlinks=False)
        if not stat.S_ISDIR(details.st_mode):
            raise SQLitePathPolicyError(f"{kind} is not a directory")
        if (details.st_uid, details.st_gid) != (
            self.ownership_identity.uid, self.ownership_identity.gid
        ):
            raise SQLitePathPolicyError(f"{kind} ownership is unsafe")
        if stat.S_IMODE(details.st_mode) & 0o022:
            raise SQLitePathPolicyError(f"{kind} permissions are unsafe")

    def prepare(self, path: Path) -> None:
        """Create only adapter-owned directories, then enforce private contracts."""
        if self._test_root is None:
            shared_parent = path.parent.parent
            if not shared_parent.exists():
                raise SQLitePathPolicyError("shared application-state parent is absent")
            self._require_shared_owned(shared_parent, "shared application-state parent")
            path.parent.mkdir(mode=0o700, exist_ok=True)
        self._require_private_owned(path.parent, 0o700, "governance database directory")
        if path.exists():
            if not path.is_file():
                raise SQLitePathPolicyError("database target is not a regular file")
            self._require_private_owned(path, 0o600, "governance database")

    def secure_database(self, path: Path) -> None:
        path.chmod(0o600)
        self._require_private_owned(path, 0o600, "governance database")

    @staticmethod
    def _absolute_without_traversal(value: Path, name: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            raise SQLitePathPolicyError(f"{name} must be absolute")
        if ".." in path.parts:
            raise SQLitePathPolicyError(f"{name} must not contain traversal")
        return path

    def production_path(self) -> Path:
        if self._test_root is not None:
            raise SQLitePathPolicyError("test policy cannot resolve a Production path")
        return self.validate(
            self.home
            / "Library"
            / "Application Support"
            / "AIControlCenter"
            / "governance"
            / "authorization-consumption.sqlite3"
        )

    def validate(self, value: Path) -> Path:
        path = self._absolute_without_traversal(value, "database path")
        repo = self._absolute_without_traversal(self.repository_root, "repository_root").resolve()
        allowed = (
            self._test_root.resolve()
            if self._test_root is not None
            else (
                self._absolute_without_traversal(self.home, "home").resolve()
                / "Library"
                / "Application Support"
                / "AIControlCenter"
                / "governance"
            )
        )
        if path.name in {"", ".", ".."}:
            raise SQLitePathPolicyError("database filename is required")
        try:
            path.relative_to(allowed)
        except ValueError as exc:
            raise SQLitePathPolicyError("database path is outside the allowed boundary") from exc
        try:
            path.relative_to(repo)
        except ValueError:
            pass
        else:
            raise SQLitePathPolicyError("database path must be outside the Git repository")

        # Existing components must not redirect the durable store.  The final
        # target is checked independently because a dangling symlink resolves.
        current = Path(path.anchor)
        for component in path.parts[1:]:
            current /= component
            if current.is_symlink():
                raise SQLitePathPolicyError("database path contains a symlink")
            if current.exists() and current != path and not current.is_dir():
                raise SQLitePathPolicyError("database parent chain is unsafe")
        return path


__all__ = ("SQLiteAuthorizationConsumptionPathPolicy", "SQLiteOwnershipIdentity", "SQLitePathPolicyError")
