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
    assert response.json()["worker"] == "missing-worker"
    assert response.json()["command"] == "status"
    assert response.json()["status"] in ["FINISHED", "FAILED"]
