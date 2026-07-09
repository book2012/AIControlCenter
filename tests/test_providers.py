from core.providers.manager import ProviderManager


def test_provider_manager_health():
    manager = ProviderManager()

    health = manager.health()

    assert "providers" in health
    assert "openai" in health["providers"]
    assert "claude" in health["providers"]
    assert "ollama" in health["providers"]


def test_get_unknown_provider():
    manager = ProviderManager()

    try:
        manager.get("missing")
        assert False
    except KeyError:
        assert True
