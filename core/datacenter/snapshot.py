from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from core.worker.worker_client import WorkerClient


class DatacenterSnapshotService:
    def __init__(self, worker: WorkerClient):
        self.worker = worker

    @staticmethod
    def _safe_call(
        component: str,
        operation: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        try:
            return operation()
        except Exception as error:
            return {
                "component": component,
                "overall_status": "UNAVAILABLE",
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                },
            }

    def status(self) -> dict[str, Any]:
        worker = self._safe_call(
            "worker",
            self.worker.status,
        )
        storage = self._safe_call(
            "storage",
            self.worker.storage_status,
        )
        database = self._safe_call(
            "database",
            self.worker.storage_db_status,
        )
        backup = self._safe_call(
            "backup",
            self.worker.backup_status,
        )
        services = self._safe_call(
            "services",
            self.worker.services_status,
        )

        unavailable = [
            name
            for name, data in {
                "worker": worker,
                "storage": storage,
                "database": database,
                "backup": backup,
                "services": services,
            }.items()
            if data.get("overall_status") == "UNAVAILABLE"
        ]

        warning = False

        if worker.get("status") not in {"READY", "ONLINE"}:
            warning = True

        if storage.get("overall_status") != "HEALTHY":
            warning = True

        if not database.get("exists", False):
            warning = True

        if database.get("schema_version") != "3":
            warning = True

        if backup.get("overall_status") not in {
            "HEALTHY",
            "WARNING",
        }:
            warning = True

        if services.get("overall_status") not in {
            "HEALTHY",
            "WARNING",
        }:
            warning = True

        if len(unavailable) == 5:
            overall_status = "UNAVAILABLE"
        elif unavailable or warning:
            overall_status = "WARNING"
        else:
            overall_status = "HEALTHY"

        return {
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "overall_status": overall_status,
            "unavailable_components": unavailable,
            "worker": worker,
            "storage": storage,
            "database": database,
            "backup": backup,
            "services": services,
        }
