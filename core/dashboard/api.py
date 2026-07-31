from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from typing import Any

from core.brain.status import BrainStatus
from core.control_plane.status import ControlPlaneStatus
from core.dashboard.shopping_management import (
    unavailable_shopping_management_dashboard_payload,
)
from core.datacenter.backup_registry import BackupRegistry
from core.datacenter.snapshot import DatacenterSnapshotService
from core.datacenter.storage_registry import StorageRegistry
from core.monitoring.snapshot import MonitoringSnapshot
from core.worker.factory import WorkerFactory


ShoppingManagementProjection = Callable[
    [],
    Mapping[str, Any],
]


class DashboardAPI:
    def __init__(
        self,
        snapshot: MonitoringSnapshot | None = None,
        brain: BrainStatus | None = None,
        storage: StorageRegistry | None = None,
        backup: BackupRegistry | None = None,
        datacenter: DatacenterSnapshotService | None = None,
        control_plane: ControlPlaneStatus | None = None,
        shopping_management: (
            ShoppingManagementProjection | None
        ) = None,
    ):
        self.snapshot = snapshot or MonitoringSnapshot()
        self.brain = brain or BrainStatus()
        self.storage = storage or StorageRegistry()
        self.backup = backup or BackupRegistry()
        self.datacenter = datacenter
        self.control_plane = (
            control_plane or ControlPlaneStatus()
        )
        self.shopping_management = shopping_management

    def _datacenter_status(self) -> dict:
        if self.datacenter is not None:
            return self.datacenter.status()

        worker = WorkerFactory().create("ubuntu-main")

        return DatacenterSnapshotService(
            worker
        ).status()

    def _shopping_management_status(
        self,
    ) -> dict[str, Any] | None:
        if self.shopping_management is None:
            return None

        try:
            payload = self.shopping_management()

            if not isinstance(payload, Mapping):
                raise TypeError(
                    "shopping management projection "
                    "must return a mapping"
                )

            return deepcopy(dict(payload))
        except Exception:
            return (
                unavailable_shopping_management_dashboard_payload()
            )

    def status(
        self,
        workers: list[str] | None = None,
        *,
        include_datacenter: bool = True,
    ) -> dict:
        workers = workers or []

        result = {
            "brain": self.brain.status(),
            "control_plane": self.control_plane.status(),
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

        shopping_management = (
            self._shopping_management_status()
        )

        if shopping_management is not None:
            result["shopping_management"] = (
                shopping_management
            )

        return result
