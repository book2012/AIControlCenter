"""GET-only governance audit API routes."""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from core.api.dependencies.audit import get_audit_query_service
from core.governance.audit_query import (
    AuditQueryError,
    AuditQueryService,
    AuditSnapshotNotFoundError,
)
from core.api.services.governance_audit_operations import build_governance_audit_operations_payload


router = APIRouter(tags=["governance-audit"])

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _validate_snapshot_id(snapshot_id: str) -> str:
    if _SHA256_PATTERN.fullmatch(snapshot_id) is None:
        raise HTTPException(
            status_code=422,
            detail="snapshot_id must be lowercase SHA-256 hex",
        )

    return snapshot_id


def _service_unavailable() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail="governance audit service unavailable",
    )


@router.get("/api/governance/audit/latest")
def get_latest_audit_snapshot(
    service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
) -> dict:
    try:
        return service.get_latest().to_dict()
    except AuditQueryError as error:
        raise _service_unavailable() from error


@router.get("/api/governance/audit/snapshots")
def list_audit_snapshots(
    service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    before_captured_at: str | None = None,
    before_snapshot_id: str | None = None,
) -> dict:
    if (
        before_captured_at is None
    ) != (
        before_snapshot_id is None
    ):
        raise HTTPException(
            status_code=422,
            detail="cursor fields must be provided together",
        )

    if before_snapshot_id is not None:
        _validate_snapshot_id(before_snapshot_id)

    try:
        return service.list_snapshots(
            limit=limit,
            before_captured_at=before_captured_at,
            before_snapshot_id=before_snapshot_id,
        ).to_dict()
    except AuditQueryError as error:
        raise _service_unavailable() from error


@router.get(
    "/api/governance/audit/snapshots/{snapshot_id}"
)
def get_audit_snapshot(
    snapshot_id: str,
    service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
) -> dict:
    validated_id = _validate_snapshot_id(snapshot_id)

    try:
        return service.get_snapshot(
            validated_id
        ).to_dict()
    except AuditSnapshotNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="audit snapshot not found",
        ) from error
    except AuditQueryError as error:
        raise _service_unavailable() from error


@router.get("/api/governance/audit/comparison")
def compare_audit_snapshots(
    service: Annotated[
        AuditQueryService,
        Depends(get_audit_query_service),
    ],
    previous_snapshot_id: str | None = None,
    current_snapshot_id: str | None = None,
) -> dict:
    if (
        previous_snapshot_id is None
    ) != (
        current_snapshot_id is None
    ):
        raise HTTPException(
            status_code=422,
            detail="comparison snapshot IDs must be provided together",
        )

    try:
        if (
            previous_snapshot_id is None
            and current_snapshot_id is None
        ):
            return service.compare_latest().to_dict()

        validated_previous = _validate_snapshot_id(
            previous_snapshot_id
        )
        validated_current = _validate_snapshot_id(
            current_snapshot_id
        )

        return service.compare_explicit(
            previous_snapshot_id=validated_previous,
            current_snapshot_id=validated_current,
        ).to_dict()
    except AuditSnapshotNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="audit snapshot not found",
        ) from error
    except AuditQueryError as error:
        raise _service_unavailable() from error


@router.get("/operations")
def get_governance_audit_operations() -> dict[str, object]:
    return build_governance_audit_operations_payload()
