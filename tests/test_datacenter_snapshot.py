from core.datacenter.snapshot import DatacenterSnapshotService


class FakeWorker:
    def status(self):
        return {
            "worker": "ubuntu-storage-worker",
            "status": "READY",
        }

    def storage_status(self):
        return {
            "overall_status": "HEALTHY",
        }

    def storage_db_status(self):
        return {
            "exists": True,
            "schema_version": "3",
        }

    def backup_status(self):
        return {
            "overall_status": "HEALTHY",
        }

    def services_status(self):
        return {
            "overall_status": "HEALTHY",
            "services": {
                "immich": {"status": "HEALTHY"},
                "nextcloud": {"status": "HEALTHY"},
            },
        }


def test_datacenter_snapshot_is_healthy() -> None:
    result = DatacenterSnapshotService(
        FakeWorker()
    ).status()

    assert result["overall_status"] == "HEALTHY"
    assert result["worker"]["status"] == "READY"
    assert result["database"]["schema_version"] == "3"
    assert result["storage"]["overall_status"] == "HEALTHY"
    assert result["backup"]["overall_status"] == "HEALTHY"
    assert result["services"]["overall_status"] == "HEALTHY"
    assert result["generated_at"]


class WarningWorker(FakeWorker):
    def status(self):
        return {
            "worker": "ubuntu-storage-worker",
            "status": "OFFLINE",
        }


def test_datacenter_snapshot_warns_when_worker_is_not_ready() -> None:
    result = DatacenterSnapshotService(
        WarningWorker()
    ).status()

    assert result["overall_status"] == "WARNING"


class StorageWarningWorker(FakeWorker):
    def storage_status(self):
        return {
            "overall_status": "WARNING",
        }


def test_datacenter_snapshot_warns_when_storage_is_not_healthy() -> None:
    result = DatacenterSnapshotService(
        StorageWarningWorker()
    ).status()

    assert result["overall_status"] == "WARNING"
