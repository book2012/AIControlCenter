from pathlib import Path
from unittest.mock import patch

from importlib.util import module_from_spec, spec_from_file_location


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ops/macos/ollama/generate-rollback-backup.py"

SPEC = spec_from_file_location("ollama_rollback_backup", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


@patch.object(MODULE, "inspect_launchd")
def test_dry_run_performs_no_copy(inspect_launchd, tmp_path: Path):
    inspect_launchd.return_value = {
        "service": "system/com.aicontrolcenter.ollama",
        "present": False,
        "running": False,
        "pid": None,
    }

    result = MODULE.build_backup(tmp_path, write_backup=False)

    assert result["mode"] == "dry-run"
    assert result["write_performed"] is False
    assert result["manifest_path"] is None
    assert result["copies"] == []
    assert list(tmp_path.iterdir()) == []


@patch.object(MODULE, "inspect_launchd")
def test_write_backup_creates_manifest(inspect_launchd, tmp_path: Path):
    inspect_launchd.return_value = {
        "service": "system/com.aicontrolcenter.ollama",
        "present": False,
        "running": False,
        "pid": None,
    }

    result = MODULE.build_backup(tmp_path, write_backup=True)

    assert result["mode"] == "write-backup"
    assert result["write_performed"] is True
    assert result["manifest_path"] is not None
    assert Path(result["manifest_path"]).is_file()


def test_models_are_metadata_only(tmp_path: Path):
    result = MODULE.build_backup(tmp_path, write_backup=False)

    assert result["models_policy"]["copy_models"] is False
    assert result["models_policy"]["preserve_models"] is True
    assert result["models_policy"]["metadata_only"] is True


def test_restore_plan_is_declared(tmp_path: Path):
    result = MODULE.build_backup(tmp_path, write_backup=False)

    assert "restore-plist-if-backed-up" in result["restore_plan"]
    assert "restore-environment-if-backed-up" in result["restore_plan"]
    assert "restore-binary-if-backed-up" in result["restore_plan"]
