from core.integrations.status import IntegrationStatus


def test_integration_status_shape():
    status = IntegrationStatus().check()

    assert "integrations" in status
    assert "openai" in status["integrations"]
    assert "notion" in status["integrations"]
    assert "github" in status["integrations"]


def test_notion_uses_notion_api_key():
    status = IntegrationStatus().check()

    assert status["integrations"]["notion"]["env"] == "NOTION_API_KEY"
