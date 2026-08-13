from fastapi.testclient import TestClient

from core.api.app import app
from core.api.routes import scheduler as scheduler_route
from core.scheduler.heartbeat import HeartbeatStore
from core.scheduler.status import SchedulerStatusService


client = TestClient(app)


def test_scheduler_status_api():
    response = client.get("/scheduler")

    assert response.status_code == 200
    assert response.json()["status"] in {"MISSING", "STALE", "ALIVE"}
    assert response.json()["heartbeat"]["freshness_seconds"] == 90


def test_scheduler_tick_api_is_not_executable(tmp_path, monkeypatch):
    db_path = tmp_path / "scheduler.db"
    monkeypatch.setattr(
        scheduler_route,
        "service",
        SchedulerStatusService(heartbeat=HeartbeatStore(str(db_path))),
    )
    response = client.post("/scheduler/tick")

    assert response.status_code in {404, 405}
    assert not db_path.exists()
