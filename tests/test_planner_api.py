from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_planner_api():
    response = client.post(
        "/planner/plan",
        json={"goal": "Check system status"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "draft"
