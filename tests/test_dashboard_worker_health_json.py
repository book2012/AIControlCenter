from core.dashboard.api import DashboardAPI


class FakeSnapshot:
    def collect(self, workers: list[str]) -> dict:
        return {
            "ubuntu-main": {
                "worker": {
                    "schema_version": 1,
                    "worker_id": "ubuntu-main",
                    "role": "stateless-infrastructure-worker",
                    "health": "ONLINE",
                    "available": True,
                },
                "session": {},
                "power": {},
                "error": None,
            }
        }


class FakeStatus:
    def status(self) -> dict:
        return {}


class FakeRegistry:
    def summary(self) -> dict:
        return {}


def test_dashboard_exposes_worker_health_json() -> None:
    api = DashboardAPI(
        snapshot=FakeSnapshot(),
        brain=FakeStatus(),
        control_plane=FakeStatus(),
        storage=FakeRegistry(),
        backup=FakeRegistry(),
    )

    data = api.status(
        ["ubuntu-main"],
        include_datacenter=False,
    )

    worker = data["workers"]["ubuntu-main"]["worker"]
    assert worker["schema_version"] == 1
    assert worker["worker_id"] == "ubuntu-main"
    assert worker["health"] == "ONLINE"
    assert worker["available"] is True
