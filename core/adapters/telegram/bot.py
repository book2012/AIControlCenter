import os
from typing import Any, Dict

import requests


class TelegramBotAdapter:
    def __init__(
        self,
        token: str | None = None,
        chat_id: str | None = None,
    ):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def health(self) -> Dict[str, Any]:
        return {
            "adapter": "telegram",
            "configured": bool(self.token and self.chat_id),
        }

    def send_message(self, message: str) -> Dict[str, Any]:
        if not self.token or not self.chat_id:
            return {
                "adapter": "telegram",
                "ok": False,
                "error": "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not configured",
            }

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                },
                timeout=15,
            )
            response.raise_for_status()

            return {
                "adapter": "telegram",
                "ok": True,
                "result": response.json(),
            }

        except Exception as exc:
            return {
                "adapter": "telegram",
                "ok": False,
                "error": str(exc),
            }
