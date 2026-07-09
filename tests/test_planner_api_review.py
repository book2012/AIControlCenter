from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_planner_review_api():
    response = client.post(
        "/planner/plan",
        json={"goal": "Check system status"},
    )

    plan_id = response.json()["id"]

    response = client.post(f"/planner/plans/{plan_id}/review")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_planner_review_missing_api():
    response = client.post("/planner/plans/missing/review")

    assert response.status_code == 404
