import os
from typing import Any, Dict

from core.providers.base import AIProvider


class ClaudeProvider(AIProvider):
    def name(self) -> str:
        return "claude"

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        }

    def chat(self, prompt: str) -> Dict[str, Any]:
        if not os.getenv("ANTHROPIC_API_KEY"):
            return {
                "provider": self.name(),
                "ok": False,
                "error": "ANTHROPIC_API_KEY is not configured",
            }

        return {
            "provider": self.name(),
            "ok": False,
            "error": "Claude chat execution is not implemented yet",
        }
