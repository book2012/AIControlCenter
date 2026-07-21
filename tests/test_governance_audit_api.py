from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from core.api.app import create_app
from core.api.dependencies.audit import get_audit_query_service
from core.governance.audit_query import (
    AuditQueryError,
    AuditSnapshotNotFoundError,
)


SNAPSHOT_ID = "a" * 64
PREVIOUS_ID = "b" * 64
CURRENT_ID = "c" * 64


@dataclass
class Result:
    payload: dict

    def to_dict(self) -> dict:
        return self.payload


class FakeAuditQueryService:
    def get_latest(self) -> Result:
        return Result(
            {
                "service": "model-governance-audit",
                "mode": "read-only",
                "snapshot": None,
                "empty": True,
            }
        )

    def list_snapshots(
        self,
        *,
        limit: int = 100,
        before_captured_at: str | None = None,
        before_snapshot_id: str | None = None,
    ) -> Result:
        return Result(
            {
                "service": "model-governance-audit",
                "mode": "read-only",
                "items": [],
                "count": 0,
                "next_cursor": None,
                "received_limit": limit,
                "received_before_captured_at":
                    before_captured_at,
                "received_before_snapshot_id":
                    before_snapshot_id,
            }
        )

    def get_snapshot(
        self,
        snapshot_id: str,
    ) -> Result:
        if snapshot_id == SNAPSHOT_ID:
            return Result(
                {
                    "service": "model-governance-audit",
                    "mode": "read-only",
                    "snapshot": {
                        "snapshot_id": snapshot_id,
                    },
                }
            )

        raise AuditSnapshotNotFoundError(
            "hidden snapshot lookup detail"
        )

    def compare_latest(self) -> Result:
        return Result(
            {
                "service": "model-governance-audit",
                "mode": "read-only",
                "status": "NO_DATA",
                "previous_snapshot": None,
                "current_snapshot": None,
                "comparison": None,
            }
        )

    def compare_explicit(
        self,
        *,
        previous_snapshot_id: str,
        current_snapshot_id: str,
    ) -> Result:
        return Result(
            {
                "service": "model-governance-audit",
                "mode": "read-only",
                "status": "UNCHANGED",
                "previous_snapshot": {
                    "snapshot_id": previous_snapshot_id,
                },
                "current_snapshot": {
                    "snapshot_id": current_snapshot_id,
                },
                "comparison": {
                    "status": "UNCHANGED",
                },
            }
        )


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    service = FakeAuditQueryService()

    app.dependency_overrides[
        get_audit_query_service
    ] = lambda: service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_latest_empty_state(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/latest"
    )

    assert response.status_code == 200
    assert response.json()["empty"] is True
    assert response.json()["mode"] == "read-only"


def test_list_snapshots(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/snapshots",
        params={"limit": 10},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
    assert response.json()["received_limit"] == 10


@pytest.mark.parametrize(
    "limit",
    [0, 1001],
)
def test_list_limit_is_bounded(
    client: TestClient,
    limit: int,
) -> None:
    response = client.get(
        "/api/governance/audit/snapshots",
        params={"limit": limit},
    )

    assert response.status_code == 422


def test_cursor_fields_must_be_complete(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/snapshots",
        params={
            "before_snapshot_id": SNAPSHOT_ID,
        },
    )

    assert response.status_code == 422


def test_get_snapshot(
    client: TestClient,
) -> None:
    response = client.get(
        f"/api/governance/audit/snapshots/{SNAPSHOT_ID}"
    )

    assert response.status_code == 200
    assert (
        response.json()["snapshot"]["snapshot_id"]
        == SNAPSHOT_ID
    )


def test_snapshot_not_found(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/snapshots/"
        + ("d" * 64)
    )

    assert response.status_code == 404
    assert "hidden" not in response.text


def test_invalid_snapshot_id(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/snapshots/INVALID"
    )

    assert response.status_code == 422


def test_compare_latest(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/comparison"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "NO_DATA"


def test_compare_explicit(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/comparison",
        params={
            "previous_snapshot_id": PREVIOUS_ID,
            "current_snapshot_id": CURRENT_ID,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "UNCHANGED"


def test_comparison_ids_must_be_complete(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/governance/audit/comparison",
        params={
            "previous_snapshot_id": PREVIOUS_ID,
        },
    )

    assert response.status_code == 422


def test_openapi_exposes_get_only_routes() -> None:
    schema = create_app().openapi()

    expected_paths = {
        "/api/governance/audit/latest",
        "/api/governance/audit/snapshots",
        "/api/governance/audit/snapshots/{snapshot_id}",
        "/api/governance/audit/comparison",
    }

    assert expected_paths.issubset(
        schema["paths"]
    )

    for path in expected_paths:
        methods = {
            method.upper()
            for method in schema["paths"][path]
            if method.lower()
            in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
            }
        }

        assert methods == {"GET"}


class FailingAuditQueryService(
    FakeAuditQueryService
):
    def get_latest(self) -> Result:
        raise AuditQueryError(
            "/private/database/path.sqlite3"
        )


def test_internal_error_is_hidden() -> None:
    app = create_app()

    app.dependency_overrides[
        get_audit_query_service
    ] = lambda: FailingAuditQueryService()

    with TestClient(app) as client:
        response = client.get(
            "/api/governance/audit/latest"
        )

    assert response.status_code == 503
    assert "database" not in response.text
    assert "private" not in response.text
