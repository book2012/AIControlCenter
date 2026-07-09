from core.adapters.telegram.bot import TelegramBotAdapter
from core.agent.brain_agent import BrainAgent


class TelegramBrainChat:
    def __init__(
        self,
        bot: TelegramBotAdapter | None = None,
        agent: BrainAgent | None = None,
    ):
        self.bot = bot or TelegramBotAdapter()
        self.agent = agent or BrainAgent()

    def handle_message(self, message: str, provider: str | None = None):
        result = self.agent.ask(message, provider=provider)

        reply = ""
        if result.get("ok") and result.get("result"):
            reply = result["result"].get("content", "")
        else:
            reply = "AI response failed."

        delivery = self.bot.send_message(reply)

        return {
            "message": message,
            "reply": reply,
            "ai": result,
            "delivery": delivery,
        }
