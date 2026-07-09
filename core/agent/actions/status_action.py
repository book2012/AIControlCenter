import json

from core.dashboard.api import DashboardAPI
from core.providers.manager import ProviderManager


class StatusAction:
    keywords = [
        "status",
        "health",
        "dashboard",
        "상태",
        "헬스",
        "서버",
        "대시보드",
        "controlcenter",
        "aicontrolcenter",
    ]

    def __init__(
        self,
        dashboard: DashboardAPI | None = None,
        providers: ProviderManager | None = None,
    ):
        self.dashboard = dashboard or DashboardAPI()
        self.providers = providers or ProviderManager()

    def matches(self, message: str) -> bool:
        text = message.lower()
        return any(keyword in text for keyword in self.keywords)

    def run(self, message: str):
        status = self.dashboard.status()

        prompt = (
            "Summarize this AIControlCenter status in Korean, briefly and clearly. "
            "Focus on Brain, integrations, storage, backup, and workers. "
            "If workers are empty, say Ubuntu worker is optional or not currently queried.\n\n"
            f"{json.dumps(status, ensure_ascii=False)}"
        )

        summary = self.providers.chat(prompt)

        return {
            "action": "status",
            "raw": status,
            "summary": summary,
        }
