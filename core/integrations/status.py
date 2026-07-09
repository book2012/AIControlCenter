import os
from typing import Any, Dict


class IntegrationStatus:
    def __init__(self):
        self.required = {
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "notion": "NOTION_API_KEY",
            "github": "GITHUB_TOKEN",
        }

    def check(self) -> Dict[str, Any]:
        integrations = {}

        for name, env_key in self.required.items():
            value = os.getenv(env_key)

            integrations[name] = {
                "env": env_key,
                "configured": bool(value),
            }

        return {
            "integrations": integrations,
            "ready": any(item["configured"] for item in integrations.values()),
        }
