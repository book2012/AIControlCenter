import json
from pathlib import Path

import pytest

from core.governance.model_registry import (
    ModelRegistryError,
    load_model_registry,
)


def write_registry(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "model-governance.json"
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return path


def base_registry() -> dict:
    return {
        "schema_version": "1.0",
        "service": "model-governance",
        "mode": "read-only",
        "control_plane": "AIControlCenter",
        "registry": {
            "source_of_truth": "AIControlCenter",
            "default_policy": "DENY",
            "models": [],
        },
    }


def approved_model() -> dict:
    return {
        "id": "example-model",
        "runtime": "ollama",
        "runtime_name": "example:latest",
        "approval_status": "APPROVED",
        "expected_digest": None,
        "resource_policy": {
            "maximum_disk_bytes": 1,
            "maximum_memory_bytes": 1,
            "maximum_context_tokens": 1,
        },
    }


def test_loads_empty_default_deny_registry(
    tmp_path: Path,
) -> None:
    path = write_registry(tmp_path, base_registry())

    registry = load_model_registry(path)

    assert registry.mode == "read-only"
    assert registry.default_policy == "DENY"
    assert registry.models == ()
    assert registry.approved_models == ()
    assert registry.to_dict()["model_count"] == 0


def test_load_does_not_modify_registry(
    tmp_path: Path,
) -> None:
    path = write_registry(tmp_path, base_registry())
    before = path.read_bytes()

    load_model_registry(path)

    assert path.read_bytes() == before


def test_rejects_non_read_only_mode(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    payload["mode"] = "write"

    with pytest.raises(ModelRegistryError):
        load_model_registry(write_registry(tmp_path, payload))


def test_rejects_non_default_deny_policy(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    payload["registry"]["default_policy"] = "ALLOW"

    with pytest.raises(ModelRegistryError):
        load_model_registry(write_registry(tmp_path, payload))


def test_rejects_duplicate_model_ids(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    model = approved_model()
    second = {**model, "runtime_name": "example:second"}
    payload["registry"]["models"] = [model, second]

    with pytest.raises(ModelRegistryError):
        load_model_registry(write_registry(tmp_path, payload))


def test_rejects_duplicate_runtime_names(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    model = approved_model()
    second = {**model, "id": "second-model"}
    payload["registry"]["models"] = [model, second]

    with pytest.raises(ModelRegistryError):
        load_model_registry(write_registry(tmp_path, payload))


def test_rejects_unknown_approval_status(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    model = approved_model()
    model["approval_status"] = "UNKNOWN"
    payload["registry"]["models"] = [model]

    with pytest.raises(ModelRegistryError):
        load_model_registry(write_registry(tmp_path, payload))


def test_rejects_invalid_resource_budget(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    model = approved_model()
    model["resource_policy"]["maximum_disk_bytes"] = 0
    payload["registry"]["models"] = [model]

    with pytest.raises(ModelRegistryError):
        load_model_registry(write_registry(tmp_path, payload))


def test_loads_valid_approved_model(
    tmp_path: Path,
) -> None:
    payload = base_registry()
    payload["registry"]["models"] = [approved_model()]

    registry = load_model_registry(
        write_registry(tmp_path, payload)
    )

    assert len(registry.models) == 1
    assert len(registry.approved_models) == 1
    assert registry.models[0].runtime == "ollama"
