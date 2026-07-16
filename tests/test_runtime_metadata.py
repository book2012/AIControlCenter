import json
from pathlib import Path

from core.runtime.metadata import RuntimeMetadata

def test_runtime_metadata_loads_valid_file(tmp_path: Path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps({
            "schema_version": 1,
            "commit": "67e617ebc469e36daa82e060c547bed78aec441c",
            "short_commit": "67e617ebc469",
            "runtime_mode": "shadow",
            "created_at": "2026-07-16T13:18:00Z",
        }),
        encoding="utf-8",
    )

    data = RuntimeMetadata(metadata_path).status()

    assert data["available"] is True
    assert data["schema_version"] == 1
    assert data["commit"] == "67e617ebc469e36daa82e060c547bed78aec441c"
    assert data["short_commit"] == "67e617ebc469"
    assert data["runtime_mode"] == "shadow"
    assert data["error"] is None

def test_runtime_metadata_handles_missing_file(tmp_path: Path) -> None:
    data = RuntimeMetadata(tmp_path / "missing.json").status()

    assert data["available"] is False
    assert data["commit"] is None
    assert data["error"]["type"] == "metadata_not_found"

def test_runtime_metadata_handles_invalid_json(tmp_path: Path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text("{invalid-json", encoding="utf-8")

    data = RuntimeMetadata(metadata_path).status()

    assert data["available"] is False
    assert data["commit"] is None
    assert data["error"]["type"] == "invalid_metadata_json"

def test_runtime_metadata_rejects_non_object_json(tmp_path: Path) -> None:
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    data = RuntimeMetadata(metadata_path).status()

    assert data["available"] is False
    assert data["error"]["type"] == "invalid_metadata_shape"
