from core.homepage.status import HomepageStatusService


class FakeDashboard:
    def status(self, workers=None, *, include_datacenter=True):
        assert include_datacenter is True

        return {
            "brain": {
                "state": "ONLINE",
            },
            "storage": {
                "exists": True,
                "root": "/mnt/storage",
            },
            "backup": {
                "exists": True,
                "root": "/mnt/storage/Backup",
            },
            "workers": {},
            "datacenter": {
                "overall_status": "HEALTHY",
                "unavailable_components": [],
                "worker": {
                    "status": "READY",
                },
                "storage": {
                    "overall_status": "HEALTHY",
                },
                "database": {
                    "schema_version": "3",
                },
                "backup": {
                    "overall_status": "HEALTHY",
                },
                "services": {
                    "overall_status": "HEALTHY",
                },
            },
        }


class FakeStatusService:
    def status(self):
        return {
            "status": "OK",
        }


def test_homepage_includes_datacenter_summary() -> None:
    service = HomepageStatusService(
        dashboard=FakeDashboard(),
        scheduler=FakeStatusService(),
        memory=FakeStatusService(),
        knowledge=FakeStatusService(),
    )

    result = service.status()

    assert result["datacenter"] == {
        "overall_status": "HEALTHY",
        "worker_status": "READY",
        "storage_status": "HEALTHY",
        "database_schema": "3",
        "backup_status": "HEALTHY",
        "services_status": "HEALTHY",
        "unavailable_components": [],
    }
