from core.adapters.telegram.polling import TelegramPollingBot


class FakeBot:
    token = "test"
    chat_id = None

    def send_message(self, message: str):
        return {"ok": True, "message": message}


class FakeChat:
    def handle_message(self, message: str, provider=None):
        return {"reply": "brain reply", "message": message}


def test_telegram_polling_start():
    bot = TelegramPollingBot(
        bot=FakeBot(),
        chat=FakeChat(),
    )

    result = bot.handle_update({
        "update_id": 1,
        "message": {
            "text": "/start",
            "chat": {"id": 123},
        },
    })

    assert result["ok"] is True


def test_telegram_polling_ask():
    bot = TelegramPollingBot(
        bot=FakeBot(),
        chat=FakeChat(),
    )

    result = bot.handle_update({
        "update_id": 2,
        "message": {
            "text": "/ask hello",
            "chat": {"id": 123},
        },
    })

    assert result["reply"] == "brain reply"
