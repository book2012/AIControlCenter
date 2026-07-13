from pathlib import Path

import yaml

from core.datacenter.storage_registry import StorageRegistry


def build_storage_registry(
    tmp_path: Path,
) -> StorageRegistry:
    root = tmp_path / "Storage"
    root.mkdir()

    config = {
        "storage": {
            "root": str(root),
            "categories": {
                "ai": "AI",
                "backup": "Backup",
                "plex": "Plex",
                "inventory": "Inventory",
            },
        }
    }

    config_path = tmp_path / "storage.yaml"

    config_path.write_text(
        yaml.safe_dump(config),
        encoding="utf-8",
    )

    return StorageRegistry(
        config_path=str(config_path)
    )


def test_storage_registry_root_exists(
    tmp_path: Path,
) -> None:
    registry = build_storage_registry(tmp_path)

    assert registry.exists() is True


def test_storage_registry_summary(
    tmp_path: Path,
) -> None:
    registry = build_storage_registry(tmp_path)
    summary = registry.summary()

    assert summary["exists"] is True
    assert "ai" in summary["categories"]
    assert "backup" in summary["categories"]
    assert "plex" in summary["categories"]
    assert "inventory" in summary["categories"]
