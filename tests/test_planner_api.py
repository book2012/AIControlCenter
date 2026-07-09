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
    assert "id" in response.json()


def test_planner_list_api():
    response = client.get("/planner/plans")

    assert response.status_code == 200
    assert "plans" in response.json()


def test_planner_missing_plan_api():
    response = client.get("/planner/plans/missing")

    assert response.status_code == 404
