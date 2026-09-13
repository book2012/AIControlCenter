"""Dashboard projection of AIControlCenter's completed catalog observations."""
from typing import Any

from core.shopping.observability.read_telemetry import CatalogReadTelemetrySnapshot


def unavailable_shopping_read_telemetry_dashboard_payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0", "mode": "READ_ONLY", "status": "UNAVAILABLE",
        "telemetry": None, "error": {"code": "SHOPPING_READ_TELEMETRY_UNAVAILABLE"},
    }


def build_shopping_read_telemetry_dashboard_payload(
    snapshot: CatalogReadTelemetrySnapshot,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0", "mode": "READ_ONLY",
        "status": snapshot.health.overall_state.value,
        "telemetry": snapshot.to_json(), "error": None,
    }
