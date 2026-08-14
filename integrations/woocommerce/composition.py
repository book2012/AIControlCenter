"""Outer composition for the optional WooCommerce commerce engine."""

from __future__ import annotations

from pathlib import Path

from core.capabilities.manifest import CapabilityManifestError, lookup_capability_metadata
from core.capabilities.service import CapabilityStatusService

from .adapter import ReadonlyCatalogObserver, WooCommerceAdapter, WooCommerceConfiguration


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config/capabilities/mac-standalone-production.json"
DEFAULT_SCHEMA = ROOT / "config/schemas/capability-manifest.schema.json"


def build_woocommerce_status_service(
    *, manifest_path: Path = DEFAULT_MANIFEST, schema_path: Path = DEFAULT_SCHEMA,
    observer: ReadonlyCatalogObserver | None = None,
    configuration_configured: bool | None = None,
    authentication_configured: bool | None = None,
    runtime_kind: str | None = None, transport_kind: str | None = None,
) -> CapabilityStatusService:
    deployment_status = "UNKNOWN"
    manifest_entry_observed = False
    try:
        metadata = lookup_capability_metadata("woocommerce", manifest_path=manifest_path, schema_path=schema_path)
        deployment_status = metadata["production_status"]
        manifest_entry_observed = True
    except (CapabilityManifestError, KeyError, TypeError):
        pass
    return CapabilityStatusService(WooCommerceAdapter(WooCommerceConfiguration(
        deployment_status=deployment_status,
        configuration_configured=configuration_configured,
        authentication_configured=authentication_configured,
        runtime_kind=runtime_kind, transport_kind=transport_kind,
        manifest_entry_observed=manifest_entry_observed,
    ), observer))


__all__ = ("build_woocommerce_status_service",)
