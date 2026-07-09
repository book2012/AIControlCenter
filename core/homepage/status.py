from core.dashboard.api import DashboardAPI
from core.scheduler.status import SchedulerStatusService
from core.memory.manager import MemoryManager
from core.knowledge.search import KnowledgeSearch


class HomepageStatusService:
    def __init__(self):
        self.dashboard = DashboardAPI()
        self.scheduler = SchedulerStatusService()
        self.memory = MemoryManager()
        self.knowledge = KnowledgeSearch()

    def status(self):
        dashboard = self.dashboard.status()
        scheduler = self.scheduler.status()
        memory = self.memory.status()
        knowledge = self.knowledge.status()

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
        }
