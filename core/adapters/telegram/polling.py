import time
from typing import Any, Dict

import requests

from core.adapters.telegram.brain_chat import TelegramBrainChat
from core.adapters.telegram.bot import TelegramBotAdapter
from core.config.loader import ConfigLoader


class TelegramPollingBot:
    def __init__(
        self,
        bot: TelegramBotAdapter | None = None,
        chat: TelegramBrainChat | None = None,
        interval: int = 3,
    ):
        ConfigLoader().load()
        self.bot = bot or TelegramBotAdapter()
        self.chat = chat or TelegramBrainChat(bot=self.bot)
        self.interval = interval
        self.offset = None

    def get_updates(self) -> Dict[str, Any]:
        if not self.bot.token:
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN is not configured"}

        params = {}
        if self.offset is not None:
            params["offset"] = self.offset

        response = requests.get(
            f"https://api.telegram.org/bot{self.bot.token}/getUpdates",
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def handle_update(self, update: Dict[str, Any]):
        self.offset = update["update_id"] + 1

        message = update.get("message", {})
        text = message.get("text")
        chat = message.get("chat", {})
        chat_id = chat.get("id")

        if not text or not chat_id:
            return None

        self.bot.chat_id = str(chat_id)

        if text.startswith("/start"):
            return self.bot.send_message("AIControlCenter Telegram Brain is online.")

        if text.startswith("/ask "):
            prompt = text.replace("/ask ", "", 1).strip()
            return self.chat.handle_message(prompt, provider="openai")

        return self.bot.send_message("Use /ask <message>")

    def run_once(self):
        updates = self.get_updates()

        if not updates.get("ok"):
            return updates

        results = []

        for update in updates.get("result", []):
            result = self.handle_update(update)
            if result is not None:
                results.append(result)

        return {
            "ok": True,
            "processed": len(results),
            "results": results,
        }

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(self.interval)
