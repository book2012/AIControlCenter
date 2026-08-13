from fastapi.testclient import TestClient

from core.api.app import app
from core.api.routes import runtime


client = TestClient(app)


def test_runtime_health_api(monkeypatch):
    class FakeRuntimeHealth:
        def status(self):
            return {
                "healthy": False,
                "services": {
                    "api": {
                        "status": "RUNNING",
                        "launchd_label": "com.aicontrolcenter.api",
                    },
                    "telegram": {"status": "NOT_DEPLOYED", "required": False},
                    "scheduler": {"status": "NOT_DEPLOYED", "required": True},
                },
                "scheduler_heartbeat": {"status": "STALE", "fresh": False},
            }

    monkeypatch.setattr(runtime, "service_health", FakeRuntimeHealth())
    response = client.get("/runtime/health")

    assert response.status_code == 200
    assert "healthy" in response.json()
    assert "services" in response.json()
    assert "scheduler_heartbeat" in response.json()
    assert response.json()["services"]["api"]["launchd_label"] == (
        "com.aicontrolcenter.api"
    )
    assert response.json()["healthy"] is False
