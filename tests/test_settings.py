from core.config.settings import load_settings


def test_load_settings():
    settings = load_settings()

    assert settings.brain.name
    assert settings.brain.role == "brain"
    assert settings.ai.provider
    assert settings.openai.model
    assert settings.google.model
    assert settings.storage.root
