from core.dashboard.api import DashboardAPI
from core.monitoring.snapshot import MonitoringSnapshot


class TimeoutWorker:
    def health_status(self) -> dict:
        raise TimeoutError("ssh_command_timeout")


class TimeoutWorkerFactory:
    def create(self, worker_name: str) -> TimeoutWorker:
        return TimeoutWorker()


class FakeStatus:
    def status(self) -> dict:
        return {}


class FakeRegistry:
    def summary(self) -> dict:
        return {}


def test_dashboard_survives_worker_timeout() -> None:
    snapshot = MonitoringSnapshot(
        worker_factory=TimeoutWorkerFactory(),
    )
    api = DashboardAPI(
        snapshot=snapshot,
        brain=FakeStatus(),
        control_plane=FakeStatus(),
        storage=FakeRegistry(),
        backup=FakeRegistry(),
    )

    data = api.status(
        ["ubuntu-main"],
        include_datacenter=False,
    )

    worker = data["workers"]["ubuntu-main"]
    assert worker["worker"] == {
        "worker": "ubuntu-main",
        "status": "OPTIONAL_UNAVAILABLE",
        "optional": True,
    }
    assert worker["error"] == {
        "type": "TimeoutError",
        "message": "ssh_command_timeout",
    }


class InvalidJsonWorker:
    def health_status(self) -> dict:
        raise ValueError("invalid_worker_health_json")


class InvalidJsonWorkerFactory:
    def create(self, worker_name: str) -> InvalidJsonWorker:
        return InvalidJsonWorker()


def test_dashboard_survives_invalid_worker_json() -> None:
    snapshot = MonitoringSnapshot(
        worker_factory=InvalidJsonWorkerFactory(),
    )
    api = DashboardAPI(
        snapshot=snapshot,
        brain=FakeStatus(),
        control_plane=FakeStatus(),
        storage=FakeRegistry(),
        backup=FakeRegistry(),
    )

    data = api.status(
        ["ubuntu-main"],
        include_datacenter=False,
    )

    worker = data["workers"]["ubuntu-main"]
    assert worker["worker"]["status"] == "OPTIONAL_UNAVAILABLE"
    assert worker["error"] == {
        "type": "ValueError",
        "message": "invalid_worker_health_json",
    }
