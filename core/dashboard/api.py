from __future__ import annotations

from core.brain.status import BrainStatus
from core.datacenter.backup_registry import BackupRegistry
from core.datacenter.snapshot import DatacenterSnapshotService
from core.datacenter.storage_registry import StorageRegistry
from core.monitoring.snapshot import MonitoringSnapshot
from core.worker.factory import WorkerFactory


class DashboardAPI:
    def __init__(
        self,
        snapshot: MonitoringSnapshot | None = None,
        brain: BrainStatus | None = None,
        storage: StorageRegistry | None = None,
        backup: BackupRegistry | None = None,
        datacenter: DatacenterSnapshotService | None = None,
    ):
        self.snapshot = snapshot or MonitoringSnapshot()
        self.brain = brain or BrainStatus()
        self.storage = storage or StorageRegistry()
        self.backup = backup or BackupRegistry()
        self.datacenter = datacenter

    def _datacenter_status(self) -> dict:
        if self.datacenter is not None:
            return self.datacenter.status()

        worker = WorkerFactory().create("ubuntu-main")

        return DatacenterSnapshotService(
            worker
        ).status()

    def status(
        self,
        workers: list[str] | None = None,
        *,
        include_datacenter: bool = True,
    ) -> dict:
        workers = workers or []

        result = {
            "brain": self.brain.status(),
            "storage": self.storage.summary(),
            "backup": self.backup.summary(),
            "workers": (
                self.snapshot.collect(workers)
                if workers
                else {}
            ),
        }

        if include_datacenter:
            result["datacenter"] = self._datacenter_status()

        return result
