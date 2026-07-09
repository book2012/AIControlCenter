from core.providers.manager import ProviderManager


def test_provider_manager_chat_shape():
    manager = ProviderManager()

    result = manager.chat(
        prompt="hello",
        provider="missing",
    )

    assert "ok" in result
    assert "attempts" in result
    assert result["attempts"][0]["reason"] == "unknown_provider"
