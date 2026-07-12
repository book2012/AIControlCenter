from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    PROJECT_ROOT
    / "deploy"
    / "macos"
    / "remote-smoke-test.sh"
)


def test_remote_smoke_script_exists_and_is_executable() -> None:
    assert SCRIPT.exists()
    assert SCRIPT.stat().st_mode & 0o111


def test_remote_smoke_uses_ssh_runner() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    assert "SSHRunner" in content
    assert "UbuntuWorkerClient" in content
    assert "DatacenterSnapshotService" in content


def test_remote_smoke_requires_datacenter_connection_settings() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    assert "DATACENTER_HOST" in content
    assert "DATACENTER_SSH_USER" in content
    assert "DATACENTER_SSH_PORT" in content


def test_remote_smoke_never_executes_real_shutdown() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    assert "shutdown_plan()" in content
    assert "systemctl poweroff" not in content
    assert "shutdown(" not in content


def test_remote_smoke_validates_schema_and_integrity() -> None:
    content = SCRIPT.read_text(encoding="utf-8")

    assert "storage_schema_v3" in content
    assert "storage_integrity" in content
    assert '"3"' in content
    assert '"ok"' in content
