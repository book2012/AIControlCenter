from pathlib import Path
from typing import Any

import yaml

from core.dashboard.api import DashboardAPI
from core.datacenter.backup_registry import BackupRegistry
from core.datacenter.storage_registry import StorageRegistry


class StubMonitoringSnapshot:
    def collect(
        self,
        workers: list[str],
    ) -> dict[str, dict[str, Any]]:
        return {
            worker: {
                "state": "UNKNOWN",
                "source": "test",
            }
            for worker in workers
        }


def build_registries(
    tmp_path: Path,
) -> tuple[StorageRegistry, BackupRegistry]:
    storage_root = tmp_path / "Storage"
    backup_root = storage_root / "Backup"

    storage_root.mkdir()
    backup_root.mkdir()

    storage_config = {
        "storage": {
            "root": str(storage_root),
            "categories": {
                "ai": "AI",
                "backup": "Backup",
                "plex": "Plex",
                "inventory": "Inventory",
            },
        }
    }

    backup_config = {
        "backup": {
            "root": str(backup_root),
            "categories": {
                "ubuntu": "Ubuntu",
                "macmini": "MacMini",
                "databases": "Databases",
            },
        }
    }

    storage_config_path = (
        tmp_path / "storage.yaml"
    )
    backup_config_path = (
        tmp_path / "backup.yaml"
    )

    storage_config_path.write_text(
        yaml.safe_dump(storage_config),
        encoding="utf-8",
    )

    backup_config_path.write_text(
        yaml.safe_dump(backup_config),
        encoding="utf-8",
    )

    return (
        StorageRegistry(
            config_path=str(storage_config_path)
        ),
        BackupRegistry(
            config_path=str(backup_config_path)
        ),
    )


def test_dashboard_integrated_status_without_workers(
    tmp_path: Path,
) -> None:
    storage, backup = build_registries(tmp_path)

    api = DashboardAPI(
        snapshot=StubMonitoringSnapshot(),
        storage=storage,
        backup=backup,
    )

    data = api.status(
        include_datacenter=False
    )

    assert data["brain"]["state"] == "ONLINE"
    assert data["brain"]["standalone"] is True
    assert data["storage"]["exists"] is True
    assert data["backup"]["exists"] is True
    assert data["workers"] == {}


def test_dashboard_integrated_status_with_worker(
    tmp_path: Path,
) -> None:
    storage, backup = build_registries(tmp_path)

    api = DashboardAPI(
        snapshot=StubMonitoringSnapshot(),
        storage=storage,
        backup=backup,
    )

    data = api.status(
        ["ubuntu-main"],
        include_datacenter=False,
    )

    assert data["brain"]["state"] == "ONLINE"
    assert "ubuntu-main" in data["workers"]
