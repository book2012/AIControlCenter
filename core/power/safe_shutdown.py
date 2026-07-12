from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ShutdownContext:
    confirmed: bool = False
    running_tasks: int = 0
    active_storage_operations: int = 0
    active_backup_operations: int = 0


class SafeShutdownService:
    ONLINE_STATES = {
        "READY",
        "ONLINE",
        "WARNING",
        "RECOVERY",
    }

    def evaluate(
        self,
        *,
        worker: dict[str, Any],
        storage: dict[str, Any],
        backup: dict[str, Any],
        context: ShutdownContext,
    ) -> dict[str, Any]:
        reasons: list[str] = []

        worker_status = str(
            worker.get("status", "UNKNOWN")
        ).upper()

        storage_status = str(
            storage.get("overall_status", "UNKNOWN")
        ).upper()

        backup_status = str(
            backup.get("overall_status", "UNKNOWN")
        ).upper()

        if worker_status not in self.ONLINE_STATES:
            reasons.append("worker_not_available")

        if context.running_tasks > 0:
            reasons.append("running_tasks")

        if context.active_storage_operations > 0:
            reasons.append("active_storage_operations")

        if context.active_backup_operations > 0:
            reasons.append("active_backup_operations")

        if storage_status not in {"HEALTHY", "WARNING"}:
            reasons.append("storage_not_safe")

        if backup_status not in {"HEALTHY", "WARNING"}:
            reasons.append("backup_not_safe")

        if not context.confirmed:
            reasons.append("confirmation_required")

        approved = len(reasons) == 0

        return {
            "approved": approved,
            "decision": (
                "APPROVED"
                if approved
                else "BLOCKED"
            ),
            "worker_status": worker_status,
            "storage_status": storage_status,
            "backup_status": backup_status,
            "running_tasks": context.running_tasks,
            "active_storage_operations": (
                context.active_storage_operations
            ),
            "active_backup_operations": (
                context.active_backup_operations
            ),
            "confirmed": context.confirmed,
            "blocking_reasons": reasons,
            "command_executed": False,
        }
