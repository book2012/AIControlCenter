import json
from copy import deepcopy
from pathlib import Path

from core.deployment.manifest import (
    run_validation,
    validate_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "config/services/mac-standalone-production.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def test_production_manifest_is_valid():
    result = run_validation(MANIFEST_PATH)

    assert result["valid"] is True
    assert result["profile"] == "mac-standalone-production"
    assert result["service_count"] == 6
    assert result["errors"] == []


def test_control_plane_cannot_depend_on_ubuntu():
    manifest = load_manifest()
    invalid = deepcopy(manifest)
    invalid["control_plane"]["ubuntu_dependency"] = True

    errors = validate_manifest(invalid)

    assert "control_plane cannot depend on Ubuntu" in errors


def test_duplicate_service_ids_are_rejected():
    manifest = load_manifest()
    invalid = deepcopy(manifest)
    invalid["services"][1]["service_id"] = (
        invalid["services"][0]["service_id"]
    )

    errors = validate_manifest(invalid)

    assert "service_id values must be unique" in errors


def test_missing_manifest_returns_json_error(tmp_path: Path):
    result = run_validation(tmp_path / "missing.json")

    assert result["valid"] is False
    assert result["profile"] is None
    assert result["service_count"] == 0
    assert result["errors"]


def test_invalid_json_returns_json_error(tmp_path: Path):
    manifest_path = tmp_path / "invalid.json"
    manifest_path.write_text("{invalid")

    result = run_validation(manifest_path)

    assert result["valid"] is False
    assert result["errors"][0].startswith("JSONDecodeError:")
