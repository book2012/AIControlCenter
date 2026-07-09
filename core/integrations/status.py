from typing import Any, Dict

from core.config.settings import Settings, load_settings


class IntegrationStatus:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()

    def check(self) -> Dict[str, Any]:
        integrations = {
            "openai": {
                "env": "OPENAI_API_KEY",
                "configured": bool(self.settings.openai.api_key),
            },
            "google": {
                "env": "GOOGLE_API_KEY",
                "configured": bool(self.settings.google.api_key),
            },
            "notion": {
                "env": "NOTION_API_KEY",
                "configured": bool(self.settings.notion.api_key),
            },
            "github": {
                "env": "GITHUB_TOKEN",
                "configured": bool(self.settings.github.token),
            },
        }

        return {
            "integrations": integrations,
            "ready": any(item["configured"] for item in integrations.values()),
        }
