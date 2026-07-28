"""GET-only DPL v1 API composition."""

from __future__ import annotations

import json
import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse

from core.api.dependencies.deployment import (
    get_deployment_api_composer,
    get_ingress_readiness_service,
    get_mac_inventory_service,
)
from core.deployment.application import (
    DeploymentApiComposer,
    IngressReadinessService,
    MacInventoryService,
)
from core.deployment.contracts import (
    DeploymentContractValidationError,
    load_schema_registry,
    sha256_digest,
    validate_contract_payload,
)

router = APIRouter(prefix="/api/deployment/v1", tags=["deployment"])
_IDENTITY = re.compile(r"^[A-Za-z0-9._:/-]{1,128}$")


def _identity(value: str | None, fallback: str) -> str:
    return value if value and _IDENTITY.fullmatch(value) else fallback


def _context(request: Request) -> tuple[str, str, str]:
    return (
        _identity(request.headers.get("x-actor-id"), "anonymous"),
        _identity(request.headers.get("x-context-id"), "api"),
        _identity(request.headers.get("x-request-id"), "unassigned"),
    )


def _error(code: str, message: str, path: str, status_code: int) -> JSONResponse:
    payload = {
        "schema_version": "dpl/v1",
        "read_only": True,
        "error": {"code": code, "message": message, "path": path},
    }
    validate_contract_payload(
        registry=load_schema_registry(), contract_name="ErrorEnvelope", payload=payload
    )
    return JSONResponse(status_code=status_code, content=payload)


@router.get("/schemas")
def discover_schemas(
    request: Request,
    composer: Annotated[DeploymentApiComposer, Depends(get_deployment_api_composer)],
) -> dict[str, Any]:
    actor, context, request_id = _context(request)
    return composer.compose(
        operation="schema-discovery",
        result=composer.discover(),
        actor_identity=actor,
        context_identity=context,
        request_identity=request_id,
    )


@router.get("/packages/inspect")
def inspect_package(
    request: Request,
    package: Annotated[str, Query(min_length=2, max_length=100000)],
    composer: Annotated[DeploymentApiComposer, Depends(get_deployment_api_composer)],
) -> Any:
    actor, context, request_id = _context(request)
    try:
        decoded = json.loads(package)
        if not isinstance(decoded, dict):
            raise ValueError
        result = composer.inspect_package(decoded)
    except (json.JSONDecodeError, ValueError, DeploymentContractValidationError):
        composer.compose(
            operation="package-inspection",
            result={"valid": False},
            actor_identity=actor,
            context_identity=context,
            request_identity=request_id,
            classification="INVALID",
            error_code="invalid-package",
        )
        return _error(
            "invalid-package",
            "Deployment package is malformed or invalid.",
            "package",
            422,
        )
    return composer.compose(
        operation="package-inspection",
        result=result,
        actor_identity=actor,
        context_identity=context,
        request_identity=request_id,
        subject_digest=result["package_digest"],
    )


@router.get("/inventory/mac")
def get_mac_inventory(
    request: Request,
    service: Annotated[MacInventoryService, Depends(get_mac_inventory_service)],
    composer: Annotated[DeploymentApiComposer, Depends(get_deployment_api_composer)],
) -> dict[str, Any]:
    actor, context, request_id = _context(request)
    result = service.collect()
    classification = (
        "UNAVAILABLE"
        if all(item["state"] == "unavailable" for item in result["items"])
        else "DEGRADED"
        if any(item["state"] in {"degraded", "unavailable"} for item in result["items"])
        else "SUCCESS"
    )
    return composer.compose(
        operation="mac-inventory",
        result=result,
        actor_identity=actor,
        context_identity=context,
        request_identity=request_id,
        classification=classification,
        subject_digest=sha256_digest(result),
    )


@router.get("/readiness/ingress")
def get_ingress_readiness(
    request: Request,
    service: Annotated[
        IngressReadinessService, Depends(get_ingress_readiness_service)
    ],
    composer: Annotated[DeploymentApiComposer, Depends(get_deployment_api_composer)],
) -> dict[str, Any]:
    actor, context, request_id = _context(request)
    result = service.evaluate()
    status = result["overall_status"]
    classification = {
        "READY": "SUCCESS",
        "NOT_READY": "NOT_READY",
        "DEGRADED": "DEGRADED",
        "UNAVAILABLE": "UNAVAILABLE",
        "INVALID": "INVALID",
    }[status]
    return composer.compose(
        operation="ingress-readiness",
        result=result,
        actor_identity=actor,
        context_identity=context,
        request_identity=request_id,
        classification=classification,
        subject_digest=sha256_digest(result),
    )


__all__ = ("router",)
