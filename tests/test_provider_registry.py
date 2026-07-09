from core.providers.registry import available_providers, get_provider_class


def test_available_providers():
    providers = available_providers()

    assert "openai" in providers
    assert "google" in providers
    assert "claude" in providers
    assert "ollama" in providers


def test_get_provider_class():
    provider_class = get_provider_class("openai")

    assert provider_class is not None


def test_get_missing_provider_class():
    try:
        get_provider_class("missing")
        assert False
    except KeyError:
        assert True
