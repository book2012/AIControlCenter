"""Outer composition for the optional OpenClaw capability."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from core.capabilities.service import CapabilityStatusService

from .adapter import OpenClawAdapter, OpenClawConfiguration, ReadonlyObserver


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config/services/mac-standalone-production.json"
DEFAULT_SCHEMA = ROOT / "config/schemas/mac-service-manifest.schema.json"


def build_openclaw_status_service(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    schema_path: Path = DEFAULT_SCHEMA,
    observer: ReadonlyObserver | None = None,
    endpoint_configured: bool | None = None,
    authentication_configured: bool | None = None,
    runtime_kind: str | None = None,
) -> CapabilityStatusService:
    deployment_status = "UNKNOWN"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if list(Draft202012Validator(schema).iter_errors(manifest)):
            raise ValueError("invalid canonical manifest")
        matches = [item for item in manifest["services"] if item.get("service_id") == "openclaw"]
        if len(matches) != 1:
            raise ValueError("ambiguous OpenClaw identity")
        deployment_status = matches[0]["production_status"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    configuration = OpenClawConfiguration(
        deployment_status=deployment_status,
        endpoint_configured=endpoint_configured,
        authentication_configured=authentication_configured,
        runtime_kind=runtime_kind,
    )
    return CapabilityStatusService(OpenClawAdapter(configuration, observer))
