from core.dashboard.api import DashboardAPI

def test_dashboard_includes_control_plane_status() -> None:
    data = DashboardAPI().status(
        include_datacenter=False
    )

    assert "control_plane" in data
    assert data["control_plane"]["service"] == "AIControlCenter"
    assert data["control_plane"]["mode"] == "shadow"
    assert data["control_plane"]["read_only"] is True
    assert data["control_plane"]["health"] == "ONLINE"

def test_dashboard_control_plane_listener_is_local() -> None:
    data = DashboardAPI().status(
        include_datacenter=False
    )

    assert data["control_plane"]["listener"] == "127.0.0.1:18100"

from fastapi.testclient import TestClient
from core.api.app import app
from core.api.dependencies.audit import DATA_ROOT_ENV, reset_audit_dependencies

def test_dashboard_route_exposes_control_plane_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(DATA_ROOT_ENV, str(tmp_path / "audit-state"))
    reset_audit_dependencies()
    client = TestClient(app)
    try:
        response = client.get("/dashboard")
    finally:
        reset_audit_dependencies()

    assert response.status_code == 200
    data = response.json()
    assert data["control_plane"]["service"] == "AIControlCenter"
    assert data["control_plane"]["mode"] == "shadow"
    assert data["control_plane"]["read_only"] is True
    assert data["control_plane"]["listener"] == "127.0.0.1:18100"

def test_dashboard_control_plane_includes_runtime_status() -> None:
    data = DashboardAPI().status(
        include_datacenter=False
    )

    assert "runtime" in data["control_plane"]
    assert "available" in data["control_plane"]["runtime"]
    assert "commit" in data["control_plane"]["runtime"]
    assert "short_commit" in data["control_plane"]["runtime"]
    assert "error" in data["control_plane"]["runtime"]
