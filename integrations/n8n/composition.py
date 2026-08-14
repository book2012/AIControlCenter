"""macOS-side composition for the optional n8n capability."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from core.capabilities.service import CapabilityStatusService

from .adapter import N8nAdapter, N8nConfiguration, ReadonlyObserver


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config/services/mac-standalone-production.json"
DEFAULT_SCHEMA = ROOT / "config/schemas/mac-service-manifest.schema.json"


def build_n8n_status_service(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    schema_path: Path = DEFAULT_SCHEMA,
    observer: ReadonlyObserver | None = None,
    configuration_configured: bool | None = None,
    authentication_configured: bool | None = None,
    runtime_kind: str | None = None,
    transport_kind: str | None = None,
) -> CapabilityStatusService:
    deployment_status = "UNKNOWN"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if list(Draft202012Validator(schema).iter_errors(manifest)):
            raise ValueError("invalid canonical manifest")
        matches = [item for item in manifest["services"] if item.get("service_id") == "n8n"]
        if len(matches) != 1:
            raise ValueError("ambiguous n8n identity")
        deployment_status = matches[0]["production_status"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        pass
    return CapabilityStatusService(N8nAdapter(N8nConfiguration(
        deployment_status=deployment_status,
        configuration_configured=configuration_configured,
        authentication_configured=authentication_configured,
        runtime_kind=runtime_kind,
        transport_kind=transport_kind,
    ), observer))
