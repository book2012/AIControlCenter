import json
from pathlib import Path

import pytest

from core.governance.model_evaluator import (
    COMPLIANT,
    DIGEST_MISMATCH,
    MISSING,
    RESOURCE_POLICY_VIOLATION,
    UNAPPROVED,
    evaluate_model_governance,
)
from core.governance.model_registry import load_model_registry


def registry_payload(models: list[dict]) -> dict:
    return {
        "schema_version": "1.0",
        "service": "model-governance",
        "mode": "read-only",
        "control_plane": "AIControlCenter",
        "registry": {
            "source_of_truth": "AIControlCenter",
            "default_policy": "DENY",
            "models": models,
        },
    }


def approved_model(
    *,
    digest: str | None = None,
    maximum_disk_bytes: int = 100,
    approval_status: str = "APPROVED",
) -> dict:
    return {
        "id": "approved-model",
        "runtime": "ollama",
        "runtime_name": "example:latest",
        "approval_status": approval_status,
        "expected_digest": digest,
        "resource_policy": {
            "maximum_disk_bytes": maximum_disk_bytes,
            "maximum_memory_bytes": 100,
            "maximum_context_tokens": 4096,
        },
    }


def load_registry(
    tmp_path: Path,
    models: list[dict],
):
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(registry_payload(models)),
        encoding="utf-8",
    )
    return load_model_registry(path)


def test_empty_registry_and_inventory(tmp_path: Path) -> None:
    registry = load_registry(tmp_path, [])

    result = evaluate_model_governance(registry, [])

    assert result.approved_count == 0
    assert result.observed_count == 0
    assert result.compliant_count == 0
    assert result.violation_count == 0
    assert result.models == ()


def test_approved_observed_model_is_compliant(
    tmp_path: Path,
) -> None:
    registry = load_registry(
        tmp_path,
        [approved_model(digest="sha256:approved")],
    )

    result = evaluate_model_governance(
        registry,
        [
            {
                "name": "example:latest",
                "digest": "sha256:approved",
                "size": 50,
            }
        ],
    )

    model = result.models[0]

    assert model.compliance_status == COMPLIANT
    assert model.available is True
    assert model.observed is True
    assert result.compliant_count == 1
    assert result.violation_count == 0


def test_approved_missing_model(tmp_path: Path) -> None:
    registry = load_registry(
        tmp_path,
        [approved_model()],
    )

    result = evaluate_model_governance(registry, [])

    model = result.models[0]

    assert model.compliance_status == MISSING
    assert model.observed is False
    assert model.available is False


def test_observed_unapproved_model(tmp_path: Path) -> None:
    registry = load_registry(tmp_path, [])

    result = evaluate_model_governance(
        registry,
        [{"name": "unknown:latest", "size": 10}],
    )

    model = result.models[0]

    assert model.compliance_status == UNAPPROVED
    assert model.model_id is None
    assert model.observed is True
    assert model.available is False


def test_digest_mismatch(tmp_path: Path) -> None:
    registry = load_registry(
        tmp_path,
        [approved_model(digest="sha256:approved")],
    )

    result = evaluate_model_governance(
        registry,
        [
            {
                "name": "example:latest",
                "digest": "sha256:unexpected",
                "size": 50,
            }
        ],
    )

    model = result.models[0]

    assert model.compliance_status == DIGEST_MISMATCH
    assert model.available is False
    assert model.expected_digest == "sha256:approved"
    assert model.observed_digest == "sha256:unexpected"


def test_resource_policy_violation(tmp_path: Path) -> None:
    registry = load_registry(
        tmp_path,
        [approved_model(maximum_disk_bytes=100)],
    )

    result = evaluate_model_governance(
        registry,
        [{"name": "example:latest", "size": 101}],
    )

    model = result.models[0]

    assert model.compliance_status == RESOURCE_POLICY_VIOLATION
    assert model.available is False
    assert model.maximum_disk_bytes == 100
    assert model.observed_size_bytes == 101


def test_suspended_model_is_not_available(
    tmp_path: Path,
) -> None:
    registry = load_registry(
        tmp_path,
        [approved_model(approval_status="SUSPENDED")],
    )

    result = evaluate_model_governance(
        registry,
        [{"name": "example:latest", "size": 50}],
    )

    model = result.models[0]

    assert model.compliance_status == COMPLIANT
    assert model.approval_status == "SUSPENDED"
    assert model.available is False


def test_accepts_ollama_model_field(tmp_path: Path) -> None:
    registry = load_registry(tmp_path, [])

    result = evaluate_model_governance(
        registry,
        [{"model": "observed:latest", "size": 1}],
    )

    assert result.models[0].runtime_name == "observed:latest"


def test_rejects_missing_observed_name(
    tmp_path: Path,
) -> None:
    registry = load_registry(tmp_path, [])

    with pytest.raises(ValueError):
        evaluate_model_governance(
            registry,
            [{"size": 1}],
        )


def test_rejects_duplicate_observed_runtime_names(
    tmp_path: Path,
) -> None:
    registry = load_registry(tmp_path, [])

    with pytest.raises(ValueError):
        evaluate_model_governance(
            registry,
            [
                {"name": "duplicate:latest"},
                {"model": "duplicate:latest"},
            ],
        )


def test_evaluation_does_not_modify_registry_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "registry.json"
    path.write_text(
        json.dumps(registry_payload([])),
        encoding="utf-8",
    )

    before = path.read_bytes()
    registry = load_model_registry(path)

    evaluate_model_governance(registry, [])

    assert path.read_bytes() == before


def test_to_dict_returns_expected_empty_contract(
    tmp_path: Path,
) -> None:
    registry = load_registry(tmp_path, [])

    payload = dict(
        evaluate_model_governance(
            registry,
            [],
        ).to_dict()
    )

    assert payload["service"] == "model-governance"
    assert payload["mode"] == "read-only"
    assert payload["default_policy"] == "DENY"
    assert payload["approved_count"] == 0
    assert payload["observed_count"] == 0
    assert payload["compliant_count"] == 0
    assert payload["violation_count"] == 0
    assert payload["models"] == []
