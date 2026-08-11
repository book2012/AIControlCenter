"""Non-bypassable Control Plane path policy for Shopping durability."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Protocol

from core.runtime.data_paths import DATA_ROOT_ENV, resolve_data_path


class DatabasePathPolicy(Protocol):
    def validate(self, path: str | Path) -> Path: ...


@dataclass(frozen=True, slots=True)
class DurableDatabasePathPolicy:
    repository_root: Path | None = None

    def validate(self, path: str | Path) -> Path:
        supplied = Path(path).expanduser()
        if not supplied.is_absolute():
            raise ValueError("shopping durable database path must be absolute")
        # Reject symlinks in every existing component; resolving first would hide them.
        cursor = Path(supplied.anchor)
        for part in supplied.parts[1:]:
            cursor /= part
            if cursor.exists() and cursor.is_symlink():
                raise ValueError("shopping durable database path cannot traverse symlinks")
        candidate = supplied.resolve(strict=False)
        blocked = (Path("/private/tmp"), Path("/tmp"), Path("/var/tmp"), Path("/home"))
        if any(candidate == root or root in candidate.parents for root in blocked):
            raise ValueError("shopping durable database path is outside the Mac Control Plane policy")
        source = (self.repository_root or Path(__file__).resolve().parents[4]).resolve(strict=False)
        if candidate == source or source in candidate.parents:
            raise ValueError("shopping durable database cannot be stored in the repository tree")
        return candidate


@dataclass(frozen=True, slots=True)
class IsolatedTestDatabasePathPolicy:
    """Explicit test-only policy whose authority is confined to one temporary root."""
    root: Path

    def __post_init__(self) -> None:
        root = Path(self.root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("test database root must be an existing directory")
        object.__setattr__(self, "root", root)

    def validate(self, path: str | Path) -> Path:
        supplied = Path(path)
        if not supplied.is_absolute():
            raise ValueError("test database path must be absolute")
        candidate = supplied.resolve(strict=False)
        if candidate == self.root or self.root not in candidate.parents:
            raise ValueError("test database path is outside its isolated root")
        return candidate


DEFAULT_DURABLE_PATH_POLICY = DurableDatabasePathPolicy()


def validate_durable_database_path(path: str | Path, *, repository_root: str | Path | None = None) -> Path:
    return DurableDatabasePathPolicy(None if repository_root is None else Path(repository_root)).validate(path)


def resolve_product_draft_database_path(*, repository_root: str | Path | None = None) -> Path:
    """Resolve the configured external Mac data-root target, failing closed."""
    raw = os.environ.get(DATA_ROOT_ENV)
    if raw is None or not raw.strip():
        raise ValueError(f"{DATA_ROOT_ENV} must configure an absolute external Mac data root")
    return DurableDatabasePathPolicy(None if repository_root is None else Path(repository_root)).validate(
        resolve_data_path("shopping/product-drafts.sqlite3"))
