from core.providers.google_provider import GoogleProvider


def test_google_provider_health_shape():
    provider = GoogleProvider()

    health = provider.health()

    assert health["provider"] == "google"
    assert "configured" in health
    assert "model" in health
