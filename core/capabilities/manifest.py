"""Narrow, fail-closed lookup of one service in the canonical manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, SchemaError


class CapabilityManifestError(ValueError):
    """Raised when canonical service metadata cannot be trusted."""


def lookup_service_metadata(
    service_id: str,
    *,
    manifest_path: Path | str,
    schema_path: Path | str,
) -> Mapping[str, Any]:
    """Return exactly one schema-validated service entry."""
    if not isinstance(service_id, str) or not service_id:
        raise CapabilityManifestError("service identity is invalid")
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        errors = tuple(Draft202012Validator(schema).iter_errors(manifest))
        if errors:
            raise CapabilityManifestError("canonical manifest is invalid")
        matches = [
            item for item in manifest["services"]
            if item.get("service_id") == service_id
        ]
        if len(matches) != 1:
            raise CapabilityManifestError("service identity is ambiguous")
        return dict(matches[0])
    except CapabilityManifestError:
        raise
    except (OSError, json.JSONDecodeError, SchemaError, KeyError, TypeError, ValueError) as exc:
        raise CapabilityManifestError("canonical manifest is unavailable") from exc


def lookup_capability_metadata(
    capability_id: str,
    *,
    manifest_path: Path | str,
    schema_path: Path | str,
) -> Mapping[str, Any]:
    """Return exactly one schema-validated capability entry."""
    if not isinstance(capability_id, str) or not capability_id:
        raise CapabilityManifestError("capability identity is invalid")
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        if tuple(Draft202012Validator(schema).iter_errors(manifest)):
            raise CapabilityManifestError("capability manifest is invalid")
        matches = [
            item for item in manifest["capabilities"]
            if item.get("capability_id") == capability_id
        ]
        if len(matches) != 1:
            raise CapabilityManifestError("capability identity is ambiguous")
        return dict(matches[0])
    except CapabilityManifestError:
        raise
    except (OSError, json.JSONDecodeError, SchemaError, KeyError, TypeError, ValueError) as exc:
        raise CapabilityManifestError("capability manifest is unavailable") from exc


__all__ = (
    "CapabilityManifestError",
    "lookup_capability_metadata",
    "lookup_service_metadata",
)
