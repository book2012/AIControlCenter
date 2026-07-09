from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_providers_api():
    response = client.get("/providers")

    assert response.status_code == 200
    assert "providers" in response.json()


def test_provider_detail_api():
    response = client.get("/providers/openai")

    assert response.status_code == 200
    assert response.json()["provider"] == "openai"


def test_provider_missing_api():
    response = client.get("/providers/missing")

    assert response.status_code == 404


def test_provider_chat_api():
    response = client.post(
        "/providers/openai/chat",
        json={"prompt": "hello"},
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "openai"
