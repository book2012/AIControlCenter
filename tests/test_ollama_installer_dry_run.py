import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "ops/macos/ollama/install-managed-ollama.sh"


def test_installer_is_executable():
    assert INSTALLER.exists()
    assert INSTALLER.stat().st_mode & 0o111


def test_installer_requires_all_artifacts():
    result = subprocess.run(
        [str(INSTALLER)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "approval, plan and snapshot are required" in result.stdout


def test_apply_mode_is_explicitly_disabled(tmp_path: Path):
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
            "--apply",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "brew install ollama" not in result.stderr
