from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_brain_agent_api():
    response = client.post(
        "/agents/brain/ask",
        json={
            "prompt": "hello",
            "provider": "missing",
        },
    )

    assert response.status_code == 200
    assert "ok" in response.json()
    assert "attempts" in response.json()
