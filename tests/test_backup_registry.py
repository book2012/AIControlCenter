from pathlib import Path

import yaml

from core.datacenter.backup_registry import BackupRegistry


def build_backup_registry(
    tmp_path: Path,
) -> BackupRegistry:
    root = tmp_path / "Backup"
    root.mkdir()

    config = {
        "backup": {
            "root": str(root),
            "categories": {
                "ubuntu": "Ubuntu",
                "macmini": "MacMini",
                "databases": "Databases",
            },
        }
    }

    config_path = tmp_path / "backup.yaml"

    config_path.write_text(
        yaml.safe_dump(config),
        encoding="utf-8",
    )

    return BackupRegistry(
        config_path=str(config_path)
    )


def test_backup_registry_root_exists(
    tmp_path: Path,
) -> None:
    registry = build_backup_registry(tmp_path)

    assert registry.exists() is True


def test_backup_registry_summary(
    tmp_path: Path,
) -> None:
    registry = build_backup_registry(tmp_path)
    summary = registry.summary()

    assert summary["exists"] is True
    assert "ubuntu" in summary["categories"]
    assert "macmini" in summary["categories"]
    assert "databases" in summary["categories"]
