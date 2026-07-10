from datetime import datetime

from core.runtime.service_health import ServiceHealth


class FakeHeartbeat:
    def latest(self):
        return {
            "status": "ALIVE",
            "created": datetime.utcnow().isoformat(),
        }


class FakeServiceHealth(ServiceHealth):
    def systemd_status(self, unit: str) -> str:
        return "active"


def test_service_health():
    service = FakeServiceHealth(heartbeat=FakeHeartbeat())

    result = service.status()

    assert result["healthy"] is True
    assert result["scheduler_heartbeat"]["fresh"] is True


def test_service_health_format():
    service = FakeServiceHealth(heartbeat=FakeHeartbeat())

    text = service.format_text()

    assert "Service Health" in text
    assert "Overall: HEALTHY" in text
