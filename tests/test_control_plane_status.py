from core.control_plane.status import ControlPlaneStatus

def test_control_plane_status_defaults() -> None:
    data = ControlPlaneStatus().status()

    assert data == {
        "service": "AIControlCenter",
        "mode": "shadow",
        "read_only": True,
        "health": "ONLINE",
        "listener": "127.0.0.1:18100",
    }

def test_control_plane_status_supports_injection() -> None:
    status = ControlPlaneStatus(
        service="test-control-plane",
        mode="test",
        listener="127.0.0.1:9999",
        read_only=False,
    )

    data = status.status()

    assert data["service"] == "test-control-plane"
    assert data["mode"] == "test"
    assert data["listener"] == "127.0.0.1:9999"
    assert data["read_only"] is False
