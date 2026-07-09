from typing import Any, Dict

from core.config.settings import OpenAISettings, load_settings
from core.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self, settings: OpenAISettings | None = None):
        self.settings = settings or load_settings().openai

    def name(self) -> str:
        return "openai"

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
                "error": "OPENAI_API_KEY is not configured",
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.api_key)

            response = client.chat.completions.create(
                model=self.settings.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            return {
                "provider": self.name(),
                "ok": True,
                "model": response.model,
                "content": response.choices[0].message.content,
            }

        except Exception as exc:
            return {
                "provider": self.name(),
                "ok": False,
                "error": str(exc),
            }
