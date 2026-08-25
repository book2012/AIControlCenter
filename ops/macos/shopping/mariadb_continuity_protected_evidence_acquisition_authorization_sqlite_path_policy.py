"""Fail-closed path policy for the dedicated Mac acquisition database."""

from dataclasses import dataclass
from pathlib import Path
import stat


class ProtectedEvidenceAcquisitionSQLitePathPolicyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity:
    uid: int
    gid: int

    def __post_init__(self) -> None:
        if type(self.uid) is not int or self.uid < 0 or type(self.gid) is not int or self.gid < 0:
            raise ValueError("trusted uid/gid must be non-negative exact integers")


@dataclass(frozen=True, slots=True)
class ProtectedEvidenceAcquisitionSQLitePathPolicy:
    repository_root: Path
    home: Path
    ownership_identity: ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity
    test_root: Path | None = None

    @classmethod
    def production(cls, *, repository_root: Path, home: Path, ownership_identity: ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity):
        return cls(repository_root, home, ownership_identity)

    @classmethod
    def isolated_test(cls, *, repository_root: Path, test_root: Path, ownership_identity: ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity):
        root = cls._absolute(test_root, "test_root")
        return cls(repository_root, root, ownership_identity, root)

    @staticmethod
    def _absolute(value: Path, name: str) -> Path:
        value = Path(value)
        if not value.is_absolute() or ".." in value.parts:
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError(f"{name} must be absolute without traversal")
        return value

    def production_path(self) -> Path:
        if self.test_root is not None:
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("test policy has no Production path")
        return self.validate(self.home / "Library" / "Application Support" / "AIControlCenter" / "protected-evidence" / "acquisition-authorization-consumption.sqlite3")

    def validate(self, value: Path) -> Path:
        path = self._absolute(value, "database path")
        allowed = self.test_root or (self.home / "Library" / "Application Support" / "AIControlCenter" / "protected-evidence")
        try:
            path.relative_to(allowed)
        except ValueError as exc:
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("database path is outside its dedicated boundary") from exc
        try:
            path.relative_to(self.repository_root)
        except ValueError:
            pass
        else:
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("database must be outside Git")
        current = Path(path.anchor)
        for part in path.parts[1:]:
            current /= part
            if current.is_symlink():
                raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("symlink path component rejected")
            if current.exists() and current != path and not current.is_dir():
                raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("non-directory parent component")
        return path

    def _require(self, path: Path, mode: int, directory: bool) -> None:
        details = path.stat(follow_symlinks=False)
        if (stat.S_ISDIR(details.st_mode) if directory else stat.S_ISREG(details.st_mode)) is False:
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("unsafe database path kind")
        if stat.S_IMODE(details.st_mode) != mode:
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("unsafe database permissions")
        if (details.st_uid, details.st_gid) != (self.ownership_identity.uid, self.ownership_identity.gid):
            raise ProtectedEvidenceAcquisitionSQLitePathPolicyError("unsafe database ownership")

    def prepare(self, path: Path) -> None:
        self.validate(path)
        path.parent.mkdir(mode=0o700, parents=self.test_root is not None, exist_ok=True)
        path.parent.chmod(0o700)
        self._require(path.parent, 0o700, True)
        if path.exists():
            self._require(path, 0o600, False)

    def secure_database(self, path: Path) -> None:
        path.chmod(0o600)
        self._require(path, 0o600, False)


__all__ = ("ProtectedEvidenceAcquisitionSQLiteOwnershipIdentity", "ProtectedEvidenceAcquisitionSQLitePathPolicy", "ProtectedEvidenceAcquisitionSQLitePathPolicyError")
