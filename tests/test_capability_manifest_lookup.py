import json
from pathlib import Path

import pytest

from core.capabilities.manifest import CapabilityManifestError, lookup_service_metadata
from integrations.n8n.composition import build_n8n_status_service
from integrations.openclaw.composition import build_openclaw_status_service


MANIFEST = Path("config/services/mac-standalone-production.json")
SCHEMA = Path("config/schemas/mac-service-manifest.schema.json")


def lookup(service_id, manifest=MANIFEST, schema=SCHEMA):
    return lookup_service_metadata(service_id, manifest_path=manifest, schema_path=schema)


def test_valid_unique_identity_returns_only_service_metadata():
    result = lookup("openclaw")
    assert result["service_id"] == "openclaw"
    assert "services" not in result and "control_plane" not in result


def test_missing_identity_fails_closed():
    with pytest.raises(CapabilityManifestError):
        lookup("missing")


def test_duplicate_identity_fails_closed(tmp_path):
    value = json.loads(MANIFEST.read_text())
    value["services"].append(next(x for x in value["services"] if x["service_id"] == "n8n"))
    path = tmp_path / "manifest.json"; path.write_text(json.dumps(value))
    with pytest.raises(CapabilityManifestError):
        lookup("n8n", path)


@pytest.mark.parametrize("contents", ["not-json", "{}"])
def test_malformed_or_schema_invalid_manifest_fails_closed(tmp_path, contents):
    path = tmp_path / "manifest.json"; path.write_text(contents)
    with pytest.raises(CapabilityManifestError):
        lookup("n8n", path)


def test_unreadable_paths_fail_closed(tmp_path):
    with pytest.raises(CapabilityManifestError):
        lookup("n8n", tmp_path / "missing.json")
    with pytest.raises(CapabilityManifestError):
        lookup("n8n", MANIFEST, tmp_path / "missing-schema.json")


def test_malformed_schema_json_fails_closed(tmp_path):
    path = tmp_path / "schema.json"; path.write_text("not-json")
    with pytest.raises(CapabilityManifestError):
        lookup("n8n", MANIFEST, path)


def test_invalid_draft_2020_12_schema_fails_closed(tmp_path):
    path = tmp_path / "schema.json"
    path.write_text(json.dumps({"type": 7}))
    with pytest.raises(CapabilityManifestError):
        lookup("n8n", MANIFEST, path)


def test_openclaw_and_n8n_composition_compatibility():
    assert build_openclaw_status_service().status()["status"] == "NOT_DEPLOYED"
    assert build_n8n_status_service().status()["status"] == "NOT_DEPLOYED"
