import os
from typing import Any, Dict

from core.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    def name(self) -> str:
        return "openai"

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "configured": bool(os.getenv("OPENAI_API_KEY")),
        }

    def chat(self, prompt: str) -> Dict[str, Any]:
        if not os.getenv("OPENAI_API_KEY"):
            return {
                "provider": self.name(),
                "ok": False,
                "error": "OPENAI_API_KEY is not configured",
            }

        return {
            "provider": self.name(),
            "ok": False,
            "error": "OpenAI chat execution is not implemented yet",
        }
