import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "ops/macos/ollama/install-managed-ollama.sh"


def make_command(path: Path, body: str) -> Path:
    path.write_text("#!/bin/bash\n" + body + "\n")
    path.chmod(0o755)
    return path


def test_apply_requires_execution_token(tmp_path: Path):
    approval = tmp_path / "approval.json"
    plan = tmp_path / "plan.json"
    snapshot = tmp_path / "snapshot.json"

    approval.write_text("{}")
    plan.write_text("{}")
    snapshot.write_text("{}")

    result = subprocess.run(
        [
            str(INSTALLER),
            "--approval",
            str(approval),
            "--plan",
            str(plan),
            "--snapshot",
            str(snapshot),
            "--backup-root",
            str(tmp_path / "backup"),
            "--apply",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 4
    assert "execution token is required" in result.stdout


def test_apply_requires_backup_root(tmp_path: Path):
    approval = tmp_path / "approval.json"
    plan = tmp_path / "plan.json"
    snapshot = tmp_path / "snapshot.json"

    approval.write_text("{}")
    plan.write_text("{}")
    snapshot.write_text("{}")

    result = subprocess.run(
        [
            str(INSTALLER),
            "--approval",
            str(approval),
            "--plan",
            str(plan),
            "--snapshot",
            str(snapshot),
            "--execution-token",
            "0" * 64,
            "--apply",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 4
    assert "backup root is required" in result.stdout


def test_health_failure_triggers_rollback_contract():
    text = INSTALLER.read_text()

    assert "rollback \"$BACKUP_DIRECTORY\"" in text
    assert "Automatic rollback completed" in text
    assert "HEALTH_CODE" in text
    assert "Execution gate blocked apply mode" in text


def test_default_mode_remains_dry_run():
    text = INSTALLER.read_text()

    assert 'MODE="dry-run"' in text
    assert "Dry-run completed; no system changes performed" in text
