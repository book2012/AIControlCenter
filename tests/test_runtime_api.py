from fastapi.testclient import TestClient

from core.api.app import create_app
from core.runtime.service_health import ServiceHealth
from ops.macos.runtime import application
from ops.macos.launchd.application_scheduler_logs import inspect_contract


def test_runtime_health_composition_injects_scheduler_log_inspector():
    service_health = ServiceHealth(scheduler_log_inspector=inspect_contract)
    app = create_app(service_health=service_health)

    assert app.state.service_health is service_health
    assert app.state.service_health.scheduler_log_inspector is inspect_contract


def test_macos_production_app_composes_scheduler_log_inspector():
    assert application.app.state.service_health is application.service_health
    assert (
        application.app.state.service_health.scheduler_log_inspector
        is inspect_contract
    )


def test_runtime_health_api():
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

    client = TestClient(create_app(service_health=FakeRuntimeHealth()))
    response = client.get("/runtime/health")

    assert response.status_code == 200
    assert "healthy" in response.json()
    assert "services" in response.json()
    assert "scheduler_heartbeat" in response.json()
    assert response.json()["services"]["api"]["launchd_label"] == (
        "com.aicontrolcenter.api"
    )
    assert response.json()["healthy"] is False
