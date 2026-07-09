from core.config.settings import OpenAISettings
from core.providers.openai_provider import OpenAIProvider


def test_openai_provider_health_shape():
    provider = OpenAIProvider(
        settings=OpenAISettings(
            api_key=None,
            model="test-model",
            embedding_model="test-embedding",
        )
    )

    health = provider.health()

    assert health["provider"] == "openai"
    assert health["configured"] is False
    assert health["model"] == "test-model"


def test_openai_provider_chat_without_key():
    provider = OpenAIProvider(
        settings=OpenAISettings(
            api_key=None,
            model="test-model",
            embedding_model="test-embedding",
        )
    )

    result = provider.chat("hello")

    assert result["provider"] == "openai"
    assert result["ok"] is False
