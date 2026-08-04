from __future__ import annotations

import hashlib
import os
import shutil
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest

from core.deployment.bootstrap_evidence_recovery import TrustedBootstrapEvidenceBinding
from tests.support.operational_snapshot_factory import OperationalSnapshotFactory


_SNAPSHOT_ENVIRONMENT = (
    "AICONTROLCENTER_M3_A4B3_OPERATIONAL_SNAPSHOT",
    "AICONTROLCENTER_M3_A4B3_EVIDENCE_SNAPSHOT",
    "AICONTROLCENTER_M3_A4B3_RECOVERY_WORK",
)


@dataclass(frozen=True)
class SnapshotEntry:
    relative_path: str
    kind: str
    mode: int
    size: int
    mtime_ns: int
    digest: str | None


def snapshot_state(root: Path) -> tuple[SnapshotEntry, ...]:
    entries = []
    for path in (root, *sorted(root.rglob("*"))):
        metadata = path.lstat()
        relative = "." if path == root else str(path.relative_to(root))
        if path.is_symlink():
            kind = "symlink"
            digest = hashlib.sha256(os.readlink(path).encode()).hexdigest()
        elif path.is_file():
            kind = "file"
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            kind = "directory"
            digest = None
        entries.append(SnapshotEntry(
            relative_path=relative,
            kind=kind,
            mode=stat.S_IMODE(metadata.st_mode),
            size=metadata.st_size,
            mtime_ns=metadata.st_mtime_ns,
            digest=digest,
        ))
    return tuple(entries)


@dataclass(frozen=True)
class RetainedSQLiteSnapshot:
    operational: Path
    evidence: Path
    recovery_work: Path
    trusted_binding: TrustedBootstrapEvidenceBinding
    operational_state: tuple[SnapshotEntry, ...]
    evidence_state: tuple[SnapshotEntry, ...]

    def assert_unchanged(self) -> None:
        assert snapshot_state(self.operational) == self.operational_state
        assert snapshot_state(self.evidence) == self.evidence_state

    def working_copy(self, label: str) -> "SQLiteSnapshotWorkspace":
        root = self.recovery_work / f"pytest-snapshot-{label}-{uuid.uuid4().hex}"
        root.mkdir(mode=0o700)
        operational = root / "operational"
        evidence = root / "evidence"
        recovery = root / "recovery"
        shutil.copytree(self.operational, operational, copy_function=shutil.copy2)
        shutil.copytree(self.evidence, evidence, copy_function=shutil.copy2)
        recovery.mkdir(mode=0o700)
        return SQLiteSnapshotWorkspace(
            retained=self,
            root=root,
            operational=operational,
            evidence=evidence,
            recovery=recovery,
        )


@dataclass(frozen=True)
class SQLiteSnapshotWorkspace:
    retained: RetainedSQLiteSnapshot
    root: Path
    operational: Path
    evidence: Path
    recovery: Path

    @property
    def trusted_binding(self) -> TrustedBootstrapEvidenceBinding:
        return self.retained.trusted_binding

    @property
    def source_paths(self):
        return self.operational, self.evidence, self.recovery, self.trusted_binding

    def sqlite_sidecars(self) -> tuple[Path, ...]:
        return tuple(sorted(
            path for path in self.root.rglob("*")
            if path.name.endswith(("-wal", "-shm"))
        ))


@pytest.fixture(scope="session")
def retained_sqlite_snapshot() -> RetainedSQLiteSnapshot:
    generated = OperationalSnapshotFactory(Path(__file__).parents[2]).create()
    operational, evidence, recovery_work = (
        Path(generated.environment[name]) for name in _SNAPSHOT_ENVIRONMENT)
    retained = RetainedSQLiteSnapshot(
        operational=operational,
        evidence=evidence,
        recovery_work=recovery_work,
        trusted_binding=generated.trusted_binding,
        operational_state=snapshot_state(operational),
        evidence_state=snapshot_state(evidence),
    )
    yield retained
    retained.assert_unchanged()
    generated.cleanup()


@pytest.fixture
def sqlite_snapshot_workspace(
    retained_sqlite_snapshot: RetainedSQLiteSnapshot,
    request: pytest.FixtureRequest,
) -> SQLiteSnapshotWorkspace:
    workspace = retained_sqlite_snapshot.working_copy(request.node.name)
    yield workspace
    retained_sqlite_snapshot.assert_unchanged()
