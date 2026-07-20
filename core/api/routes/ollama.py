"""Read-only Ollama service API route."""

from __future__ import annotations

from fastapi import APIRouter

from core.integrations.ollama import inspect_ollama


router = APIRouter(tags=["services"])


@router.get("/api/services/ollama")
def get_ollama_status() -> dict:
    """Return normalized Ollama health and model inventory."""
    return inspect_ollama()
