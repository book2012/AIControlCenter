from core.dashboard.api import DashboardAPI


def test_dashboard_status():
    api = DashboardAPI()

    data = api.status(["ubuntu-main"])

    assert "brain" in data
    assert "storage" in data
    assert "backup" in data
    assert "workers" in data
    assert "ubuntu-main" in data["workers"]
    assert "worker" in data["workers"]["ubuntu-main"]
    assert "session" in data["workers"]["ubuntu-main"]
    assert "power" in data["workers"]["ubuntu-main"]


class FakeDatacenterSnapshot:
    def status(self):
        return {
            "overall_status": "HEALTHY",
            "database": {
                "schema_version": "3",
            },
            "services": {
                "overall_status": "HEALTHY",
            },
        }


def test_dashboard_includes_datacenter_snapshot() -> None:
    api = DashboardAPI(
        datacenter=FakeDatacenterSnapshot()
    )

    data = api.status(
        include_datacenter=True
    )

    assert "datacenter" in data
    assert data["datacenter"]["overall_status"] == "HEALTHY"
    assert data["datacenter"]["database"]["schema_version"] == "3"


def test_dashboard_can_skip_datacenter_snapshot() -> None:
    api = DashboardAPI(
        datacenter=FakeDatacenterSnapshot()
    )

    data = api.status(
        include_datacenter=False
    )

    assert "datacenter" not in data
    assert "brain" in data
    assert "storage" in data
    assert "backup" in data
    assert "workers" in data
