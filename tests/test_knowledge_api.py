from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_knowledge_status_api():
    response = client.get("/knowledge")

    assert response.status_code == 200
    assert response.json()["ready"] is True


def test_knowledge_search_api():
    response = client.get("/knowledge/search?q=AIControlCenter")

    assert response.status_code == 200
    assert "results" in response.json()
