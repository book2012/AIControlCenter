from core.adapters.telegram.bot import TelegramBotAdapter


def test_telegram_adapter_health_without_config(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    adapter = TelegramBotAdapter()

    health = adapter.health()

    assert health["adapter"] == "telegram"
    assert health["configured"] is False


def test_telegram_adapter_send_without_config(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    adapter = TelegramBotAdapter()

    result = adapter.send_message("hello")

    assert result["adapter"] == "telegram"
    assert result["ok"] is False
