from pathlib import Path

from scripts import platform_readiness


def test_project_roots_are_defined() -> None:
    assert platform_readiness.PROJECT_ROOT.is_dir()
    assert isinstance(
        platform_readiness.DATACENTER_ROOT,
        Path,
    )


def test_command_ok_accepts_successful_command() -> None:
    assert platform_readiness.command_ok(
        ["python3", "-c", "raise SystemExit(0)"]
    ) is True


def test_command_ok_rejects_failed_command() -> None:
    assert platform_readiness.command_ok(
        ["python3", "-c", "raise SystemExit(1)"]
    ) is False
