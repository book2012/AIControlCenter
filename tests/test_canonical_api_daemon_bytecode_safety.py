from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "ops" / "macos" / "launchd"

MODULES = (
    "canonical_api_daemon.py",
    "canonical_api_daemon_refresh.py",
    "canonical_api_daemon_bootstrap.py",
)


def _copy_launchd_modules(tmp_path: Path) -> Path:
    destination = tmp_path / "launchd"
    destination.mkdir()

    for name in MODULES:
        shutil.copy2(SOURCE_DIR / name, destination / name)

    return destination


def _environment_without_bytecode_protection() -> dict[str, str]:
    environment = os.environ.copy()
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    environment.pop("PYTHONPYCACHEPREFIX", None)
    return environment


def _assert_cli_creates_no_local_bytecode(
    tmp_path: Path,
    script_name: str,
) -> None:
    launchd_dir = _copy_launchd_modules(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(launchd_dir / script_name),
            "--help",
        ],
        cwd=launchd_dir,
        env=_environment_without_bytecode_protection(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert not (launchd_dir / "__pycache__").exists()
    assert list(launchd_dir.rglob("*.pyc")) == []


def test_refresh_executor_disables_bytecode_before_local_imports(
    tmp_path: Path,
) -> None:
    _assert_cli_creates_no_local_bytecode(
        tmp_path,
        "canonical_api_daemon_refresh.py",
    )


def test_bootstrap_executor_disables_bytecode_before_local_imports(
    tmp_path: Path,
) -> None:
    _assert_cli_creates_no_local_bytecode(
        tmp_path,
        "canonical_api_daemon_bootstrap.py",
    )
