from datetime import datetime
from typing import Any, Dict

from core.config.settings import Settings, load_settings
from core.integrations.status import IntegrationStatus


class BrainStatus:
    def __init__(
        self,
        settings: Settings | None = None,
        integrations: IntegrationStatus | None = None,
    ):
        self.settings = settings or load_settings()
        self.integrations = integrations or IntegrationStatus(self.settings)

    def status(self) -> Dict[str, Any]:
        return {
            "name": self.settings.brain.name,
            "role": self.settings.brain.role,
            "state": "ONLINE",
            "standalone": True,
            "timestamp": datetime.utcnow().isoformat(),
            "log_level": self.settings.brain.log_level,
            "timezone": self.settings.brain.timezone,
            "capabilities": [
                "task_registry",
                "session_manager",
                "scheduler",
                "agent_framework",
                "monitoring",
                "dashboard_api",
                "backup_registry",
                "storage_registry",
                "ai_api",
                "notion",
                "github",
            ],
            "integrations": self.integrations.check(),
        }
