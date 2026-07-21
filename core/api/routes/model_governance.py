"""Read-only model governance API route."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from core.governance.model_evaluator import (
    evaluate_model_governance,
)
from core.governance.model_registry import (
    load_model_registry,
)
from core.integrations.ollama import inspect_ollama


router = APIRouter()

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY_PATH = (
    _REPOSITORY_ROOT
    / "config"
    / "model-governance.json"
)


@router.get("/api/governance/models")
def inspect_model_governance() -> dict[str, Any]:
    """Return the approved registry versus observed Ollama inventory."""

    registry = load_model_registry(_REGISTRY_PATH)
    ollama = inspect_ollama()

    observed_models = ollama.get("models")

    if not isinstance(observed_models, list):
        observed_models = []

    evaluation = evaluate_model_governance(
        registry,
        observed_models,
    )

    payload = dict(evaluation.to_dict())

    payload["healthy"] = (
        ollama.get("healthy") is True
        and ollama.get("running") is True
    )

    payload["runtime"] = {
        "service": "ollama",
        "healthy": ollama.get("healthy") is True,
        "running": ollama.get("running") is True,
        "status": ollama.get("status"),
    }

    payload["write_operations_allowed"] = False

    return payload
