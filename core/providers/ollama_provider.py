from typing import Any, Dict

from core.providers.base import AIProvider


class OllamaProvider(AIProvider):
    def name(self) -> str:
        return "ollama"

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "configured": False,
            "local": True,
        }

    def chat(self, prompt: str) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "ok": False,
            "error": "Ollama chat execution is not implemented yet",
        }
