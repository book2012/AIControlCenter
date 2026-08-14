"""Outer composition for the optional OpenClaw capability."""

from __future__ import annotations

from pathlib import Path

from core.capabilities.manifest import CapabilityManifestError, lookup_service_metadata
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
        metadata = lookup_service_metadata(
            "openclaw", manifest_path=manifest_path, schema_path=schema_path,
        )
        deployment_status = metadata["production_status"]
    except (CapabilityManifestError, KeyError, TypeError):
        pass
    configuration = OpenClawConfiguration(
        deployment_status=deployment_status,
        endpoint_configured=endpoint_configured,
        authentication_configured=authentication_configured,
        runtime_kind=runtime_kind,
    )
    return CapabilityStatusService(OpenClawAdapter(configuration, observer))
