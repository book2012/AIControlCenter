from typing import Any, Dict

from core.config.settings import GoogleSettings, load_settings
from core.providers.base import AIProvider


class GoogleProvider(AIProvider):
    def __init__(self, settings: GoogleSettings | None = None):
        self.settings = settings or load_settings().google

    def name(self) -> str:
        return "google"

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "configured": bool(self.settings.api_key),
            "model": self.settings.model,
        }

    def chat(self, prompt: str) -> Dict[str, Any]:
        if not self.settings.api_key:
            return {
                "provider": self.name(),
                "ok": False,
                "error": "GOOGLE_API_KEY is not configured",
            }

        return {
            "provider": self.name(),
            "ok": False,
            "error": "Google Gemini execution is not implemented yet",
        }
