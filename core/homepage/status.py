from __future__ import annotations

from core.dashboard.api import DashboardAPI
from core.knowledge.search import KnowledgeSearch
from core.memory.manager import MemoryManager
from core.scheduler.status import SchedulerStatusService


class HomepageStatusService:
    def __init__(
        self,
        dashboard: DashboardAPI | None = None,
        scheduler: SchedulerStatusService | None = None,
        memory: MemoryManager | None = None,
        knowledge: KnowledgeSearch | None = None,
    ):
        self.dashboard = dashboard or DashboardAPI()
        self.scheduler = scheduler or SchedulerStatusService()
        self.memory = memory or MemoryManager()
        self.knowledge = knowledge or KnowledgeSearch()

    def status(self):
        dashboard = self.dashboard.status(
            include_datacenter=True
        )
        scheduler = self.scheduler.status()
        memory = self.memory.status()
        knowledge = self.knowledge.status()

        datacenter = dashboard.get("datacenter", {})

        return {
            "brain": dashboard["brain"],
            "storage": {
                "exists": dashboard["storage"]["exists"],
                "root": dashboard["storage"]["root"],
            },
            "backup": {
                "exists": dashboard["backup"]["exists"],
                "root": dashboard["backup"]["root"],
            },
            "scheduler": scheduler,
            "memory": memory,
            "knowledge": knowledge,
            "workers": dashboard["workers"],
            "datacenter": {
                "overall_status": datacenter.get(
                    "overall_status",
                    "UNKNOWN",
                ),
                "worker_status": datacenter.get(
                    "worker",
                    {},
                ).get("status"),
                "storage_status": datacenter.get(
                    "storage",
                    {},
                ).get("overall_status"),
                "database_schema": datacenter.get(
                    "database",
                    {},
                ).get("schema_version"),
                "backup_status": datacenter.get(
                    "backup",
                    {},
                ).get("overall_status"),
                "services_status": datacenter.get(
                    "services",
                    {},
                ).get("overall_status"),
                "unavailable_components": datacenter.get(
                    "unavailable_components",
                    [],
                ),
            },
        }
