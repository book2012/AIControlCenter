"""Read-only loader for the AIControlCenter model governance registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence


SUPPORTED_SCHEMA_VERSION = "1.0"
SUPPORTED_APPROVAL_STATUSES = frozenset(
    {"PROPOSED", "APPROVED", "SUSPENDED", "REVOKED"}
)


class ModelRegistryError(ValueError):
    """Raised when the model governance registry is invalid."""


@dataclass(frozen=True)
class ResourcePolicy:
    maximum_disk_bytes: int
    maximum_memory_bytes: int
    maximum_context_tokens: int


@dataclass(frozen=True)
class ApprovedModel:
    model_id: str
    runtime: str
    runtime_name: str
    approval_status: str
    expected_digest: str | None
    resource_policy: ResourcePolicy


@dataclass(frozen=True)
class ModelRegistry:
    schema_version: str
    service: str
    mode: str
    control_plane: str
    default_policy: str
    models: tuple[ApprovedModel, ...]
    source_path: Path

    @property
    def approved_models(self) -> tuple[ApprovedModel, ...]:
        return tuple(
            model
            for model in self.models
            if model.approval_status == "APPROVED"
        )

    def to_dict(self) -> Mapping[str, Any]:
        models: Sequence[Mapping[str, Any]] = tuple(
            MappingProxyType(
                {
                    "id": model.model_id,
                    "runtime": model.runtime,
                    "runtime_name": model.runtime_name,
                    "approval_status": model.approval_status,
                    "expected_digest": model.expected_digest,
                    "resource_policy": {
                        "maximum_disk_bytes":
                            model.resource_policy.maximum_disk_bytes,
                        "maximum_memory_bytes":
                            model.resource_policy.maximum_memory_bytes,
                        "maximum_context_tokens":
                            model.resource_policy.maximum_context_tokens,
                    },
                }
            )
            for model in self.models
        )

        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "service": self.service,
                "mode": self.mode,
                "control_plane": self.control_plane,
                "default_policy": self.default_policy,
                "model_count": len(self.models),
                "approved_count": len(self.approved_models),
                "models": models,
                "source_path": str(self.source_path),
            }
        )


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ModelRegistryError(f"{field} must be an object")
    return value


def _require_non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelRegistryError(f"{field} must be a non-empty string")
    return value.strip()


def _require_positive_integer(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ModelRegistryError(f"{field} must be a positive integer")
    return value


def _parse_resource_policy(
    payload: Any,
    model_id: str,
) -> ResourcePolicy:
    policy = _require_mapping(
        payload,
        f"model {model_id} resource_policy",
    )

    return ResourcePolicy(
        maximum_disk_bytes=_require_positive_integer(
            policy.get("maximum_disk_bytes"),
            f"model {model_id} maximum_disk_bytes",
        ),
        maximum_memory_bytes=_require_positive_integer(
            policy.get("maximum_memory_bytes"),
            f"model {model_id} maximum_memory_bytes",
        ),
        maximum_context_tokens=_require_positive_integer(
            policy.get("maximum_context_tokens"),
            f"model {model_id} maximum_context_tokens",
        ),
    )


def _parse_model(payload: Any) -> ApprovedModel:
    model = _require_mapping(payload, "registry model")

    model_id = _require_non_empty_string(model.get("id"), "model id")
    runtime = _require_non_empty_string(
        model.get("runtime"),
        f"model {model_id} runtime",
    )
    runtime_name = _require_non_empty_string(
        model.get("runtime_name"),
        f"model {model_id} runtime_name",
    )
    approval_status = _require_non_empty_string(
        model.get("approval_status"),
        f"model {model_id} approval_status",
    )

    if runtime != "ollama":
        raise ModelRegistryError(
            f"model {model_id} runtime must be ollama"
        )

    if approval_status not in SUPPORTED_APPROVAL_STATUSES:
        raise ModelRegistryError(
            f"model {model_id} has unsupported approval status"
        )

    expected_digest = model.get("expected_digest")

    if expected_digest is not None:
        expected_digest = _require_non_empty_string(
            expected_digest,
            f"model {model_id} expected_digest",
        )

    return ApprovedModel(
        model_id=model_id,
        runtime=runtime,
        runtime_name=runtime_name,
        approval_status=approval_status,
        expected_digest=expected_digest,
        resource_policy=_parse_resource_policy(
            model.get("resource_policy"),
            model_id,
        ),
    )


def load_model_registry(path: str | Path) -> ModelRegistry:
    """Load and validate a model registry without modifying it."""

    source_path = Path(path).expanduser().resolve()

    try:
        payload = json.loads(
            source_path.read_text(encoding="utf-8")
        )
    except FileNotFoundError as error:
        raise ModelRegistryError(
            f"registry not found: {source_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ModelRegistryError(
            f"registry contains invalid JSON: {error}"
        ) from error

    root = _require_mapping(payload, "registry root")

    if root.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        raise ModelRegistryError("unsupported schema_version")

    if root.get("service") != "model-governance":
        raise ModelRegistryError("service must be model-governance")

    if root.get("mode") != "read-only":
        raise ModelRegistryError("mode must be read-only")

    if root.get("control_plane") != "AIControlCenter":
        raise ModelRegistryError(
            "control_plane must be AIControlCenter"
        )

    registry = _require_mapping(root.get("registry"), "registry")

    if registry.get("source_of_truth") != "AIControlCenter":
        raise ModelRegistryError(
            "registry source_of_truth must be AIControlCenter"
        )

    if registry.get("default_policy") != "DENY":
        raise ModelRegistryError(
            "registry default_policy must be DENY"
        )

    raw_models = registry.get("models")

    if not isinstance(raw_models, list):
        raise ModelRegistryError("registry models must be an array")

    models = tuple(_parse_model(model) for model in raw_models)

    model_ids = [model.model_id for model in models]
    runtime_names = [model.runtime_name for model in models]

    if len(model_ids) != len(set(model_ids)):
        raise ModelRegistryError("duplicate model id")

    if len(runtime_names) != len(set(runtime_names)):
        raise ModelRegistryError("duplicate runtime_name")

    return ModelRegistry(
        schema_version=SUPPORTED_SCHEMA_VERSION,
        service="model-governance",
        mode="read-only",
        control_plane="AIControlCenter",
        default_policy="DENY",
        models=models,
        source_path=source_path,
    )
