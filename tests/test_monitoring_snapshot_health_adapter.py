from core.monitoring.snapshot import MonitoringSnapshot


class HealthWorker:
    def __init__(self) -> None:
        self.health_calls = 0
        self.status_calls = 0

    def health_status(self) -> dict:
        self.health_calls += 1
        return {
            "schema_version": 1,
            "worker_id": "ubuntu-main",
            "role": "stateless-infrastructure-worker",
            "health": "ONLINE",
            "available": True,
        }

    def status(self) -> dict:
        self.status_calls += 1
        return {"status": "LEGACY"}


class HealthWorkerFactory:
    def __init__(self, worker: HealthWorker) -> None:
        self.worker = worker

    def create(self, worker_name: str) -> HealthWorker:
        return self.worker


def test_monitoring_snapshot_prefers_health_status() -> None:
    worker = HealthWorker()
    snapshot = MonitoringSnapshot(
        worker_factory=HealthWorkerFactory(worker),
    )

    data = snapshot.collect(["ubuntu-main"])

    result = data["ubuntu-main"]["worker"]
    assert result["schema_version"] == 1
    assert result["worker_id"] == "ubuntu-main"
    assert result["health"] == "ONLINE"
    assert worker.health_calls == 1
    assert worker.status_calls == 0


class LegacyWorker:
    def status(self) -> dict:
        return {"worker": "legacy", "status": "ONLINE"}


class LegacyWorkerFactory:
    def create(self, worker_name: str) -> LegacyWorker:
        return LegacyWorker()


def test_monitoring_snapshot_falls_back_to_status() -> None:
    snapshot = MonitoringSnapshot(
        worker_factory=LegacyWorkerFactory(),
    )

    data = snapshot.collect(["legacy-worker"])

    assert data["legacy-worker"]["worker"] == {
        "worker": "legacy",
        "status": "ONLINE",
    }
