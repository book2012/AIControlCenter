from core.monitoring.snapshot import MonitoringSnapshot


class FailingWorker:
    def status(self) -> dict:
        raise TimeoutError("ssh_command_timeout")


class FakeWorkerFactory:
    def create(self, worker_name: str) -> FailingWorker:
        return FailingWorker()


def test_monitoring_snapshot_normalizes_worker_error() -> None:
    snapshot = MonitoringSnapshot(
        worker_factory=FakeWorkerFactory(),
    )

    data = snapshot.collect(["ubuntu-main"])
    worker = data["ubuntu-main"]

    assert worker["worker"] == {
        "worker": "ubuntu-main",
        "status": "OPTIONAL_UNAVAILABLE",
        "optional": True,
    }
    assert worker["error"] == {
        "type": "TimeoutError",
        "message": "ssh_command_timeout",
    }
