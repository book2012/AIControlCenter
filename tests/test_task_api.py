from fastapi.testclient import TestClient

from core.api.app import app


client = TestClient(app)


def test_list_tasks_api():
    response = client.get("/tasks")

    assert response.status_code == 200
    assert "tasks" in response.json()


def test_create_task_api():
    response = client.post(
        "/tasks",
        json={
            "worker": "missing-worker",
            "command": "status",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["worker"] == "missing-worker"
    assert data["command"] == "status"
    assert data["status"] in ["FINISHED", "FAILED"]
    assert isinstance(data["started"], str)


def test_get_missing_task_api():
    response = client.get("/tasks/not-found")

    assert response.status_code == 404
