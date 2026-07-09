from core.adapters.telegram.brain_chat import TelegramBrainChat


class FakeBot:
    def send_message(self, message: str):
        return {
            "ok": True,
            "message": message,
        }


class FakeAgent:
    def ask(self, message: str, provider=None):
        return {
            "ok": True,
            "result": {
                "content": "hello from brain"
            },
        }


def test_telegram_brain_chat():
    chat = TelegramBrainChat(
        bot=FakeBot(),
        agent=FakeAgent(),
    )

    result = chat.handle_message("hello")

    assert result["reply"] == "hello from brain"
    assert result["delivery"]["ok"] is True
