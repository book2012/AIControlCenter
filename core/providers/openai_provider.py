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
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return {
                "provider": self.name(),
                "ok": False,
                "error": "OPENAI_API_KEY is not configured",
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
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
