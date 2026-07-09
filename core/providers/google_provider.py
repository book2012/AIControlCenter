from typing import Any, Dict

import requests

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

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.model}:generateContent"
        )

        try:
            response = requests.post(
                url,
                params={"key": self.settings.api_key},
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                timeout=30,
            )

            response.raise_for_status()
            data = response.json()

            content = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text")
            )

            return {
                "provider": self.name(),
                "ok": True,
                "model": self.settings.model,
                "content": content,
                "raw": data,
            }

        except Exception as exc:
            return {
                "provider": self.name(),
                "ok": False,
                "error": str(exc),
            }
