from unittest.mock import patch

from fastapi.testclient import TestClient

from core.api.app import create_app


def test_datacenter_status_api() -> None:
    expected = {
        "generated_at": "2026-07-12T00:00:00+00:00",
        "overall_status": "HEALTHY",
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
    }

    with patch(
        "core.api.routes.datacenter.DatacenterSnapshotService.status",
        return_value=expected,
    ):
        client = TestClient(create_app())
        response = client.get("/datacenter/status")

    assert response.status_code == 200
    assert response.json() == expected
