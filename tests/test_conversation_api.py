from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_create_conversation_api():
    response = client.post("/conversations")

    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["messages"] == []


def test_list_conversations_api():
    response = client.get("/conversations")

    assert response.status_code == 200
    assert "conversations" in response.json()


def test_missing_conversation_api():
    response = client.get("/conversations/missing")

    assert response.status_code == 404
