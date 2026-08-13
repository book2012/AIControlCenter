"""Canonical runtime-health topology loaded from the Mac service manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST_PATH = ROOT / "config/services/mac-standalone-production.json"
DEFAULT_SCHEMA_PATH = ROOT / "config/schemas/mac-service-manifest.schema.json"


class TopologyConfigurationError(ValueError):
    """Raised when the canonical topology cannot be trusted."""


@dataclass(frozen=True)
class RuntimeService:
    service_id: str
    logical_id: str
    required: bool
    lifecycle: str
    deployment_status: str
    launchd_label: str | None = None


class ServiceTopology:
    def __init__(
        self,
        manifest_path: Path | str = DEFAULT_MANIFEST_PATH,
        schema_path: Path | str = DEFAULT_SCHEMA_PATH,
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.schema_path = Path(schema_path)

    def runtime_services(self) -> tuple[RuntimeService, ...]:
        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
            errors = sorted(
                Draft202012Validator(schema).iter_errors(manifest),
                key=lambda error: tuple(str(item) for item in error.path),
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            raise TopologyConfigurationError("runtime topology is unavailable") from exc

        if errors:
            raise TopologyConfigurationError("runtime topology is invalid")

        selected = [item for item in manifest["services"] if item.get("runtime_health")]
        logical_ids = [item["logical_id"] for item in selected]
        if not selected or len(logical_ids) != len(set(logical_ids)):
            raise TopologyConfigurationError("runtime topology is ambiguous")

        return tuple(
            RuntimeService(
                service_id=item["service_id"],
                logical_id=item["logical_id"],
                required=item["required"],
                lifecycle=item["lifecycle"],
                deployment_status=item["production_status"],
                launchd_label=item.get("launchd_label"),
            )
            for item in selected
        )


__all__ = (
    "RuntimeService",
    "ServiceTopology",
    "TopologyConfigurationError",
)
