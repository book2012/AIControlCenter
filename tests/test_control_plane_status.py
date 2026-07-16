from core.control_plane.status import ControlPlaneStatus

def test_control_plane_status_defaults() -> None:
    data = ControlPlaneStatus().status()

    assert data["service"] == "AIControlCenter"
    assert data["mode"] == "shadow"
    assert data["read_only"] is True
    assert data["health"] == "ONLINE"
    assert data["listener"] == "127.0.0.1:18100"
    assert "runtime" in data

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

class StubRuntimeMetadata:
    def status(self) -> dict:
        return {
            "available": True,
            "schema_version": 1,
            "commit": "abcdef1234567890",
            "short_commit": "abcdef123456",
            "runtime_mode": "shadow",
            "created_at": "2026-07-16T13:18:00Z",
            "metadata_path": "/tmp/metadata.json",
            "error": None,
        }

def test_control_plane_status_includes_runtime_metadata() -> None:
    status = ControlPlaneStatus(
        runtime=StubRuntimeMetadata()
    )

    data = status.status()

    assert data["runtime"]["available"] is True
    assert data["runtime"]["commit"] == "abcdef1234567890"
    assert data["runtime"]["short_commit"] == "abcdef123456"
    assert data["runtime"]["runtime_mode"] == "shadow"
