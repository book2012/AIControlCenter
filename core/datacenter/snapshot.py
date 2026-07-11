from __future__ import annotations

from datetime import datetime, timezone

from core.worker.worker_client import WorkerClient


class DatacenterSnapshotService:

    def __init__(self, worker: WorkerClient):
        self.worker = worker

    def status(self) -> dict:

        worker = self.worker.status()
        storage = self.worker.storage_status()
        database = self.worker.storage_db_status()
        backup = self.worker.backup_status()
        services = self.worker.services_status()

        overall = "HEALTHY"

        if worker["status"] not in {"READY", "ONLINE"}:
            overall = "WARNING"

        if storage.get("overall_status") != "HEALTHY":
            overall = "WARNING"

        if backup.get("overall_status") not in {"HEALTHY", "WARNING"}:
            overall = "WARNING"

        return {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),

            "overall_status": overall,

            "worker": worker,

            "storage": storage,

            "database": database,

            "backup": backup,

            "services": services,
        }
