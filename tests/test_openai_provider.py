from core.providers.openai_provider import OpenAIProvider


def test_openai_provider_health_shape():
    provider = OpenAIProvider()

    health = provider.health()

    assert health["provider"] == "openai"
    assert "configured" in health


def test_openai_provider_chat_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    provider = OpenAIProvider()

    result = provider.chat("hello")

    assert result["provider"] == "openai"
    assert result["ok"] is False
