import os
from typing import Any, Dict

from core.providers.base import AIProvider


class GoogleProvider(AIProvider):
    def name(self) -> str:
        return "google"

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "configured": bool(os.getenv("GOOGLE_API_KEY")),
        }

    def chat(self, prompt: str) -> Dict[str, Any]:
        if not os.getenv("GOOGLE_API_KEY"):
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
