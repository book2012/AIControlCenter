from typing import Dict, Type

from core.providers.base import AIProvider
from core.providers.claude_provider import ClaudeProvider
from core.providers.google_provider import GoogleProvider
from core.providers.ollama_provider import OllamaProvider
from core.providers.openai_provider import OpenAIProvider


PROVIDER_REGISTRY: Dict[str, Type[AIProvider]] = {
    "openai": OpenAIProvider,
    "google": GoogleProvider,
    "claude": ClaudeProvider,
    "ollama": OllamaProvider,
}


def available_providers():
    return sorted(PROVIDER_REGISTRY.keys())


def get_provider_class(name: str):
    if name not in PROVIDER_REGISTRY:
        raise KeyError(f"Unknown provider: {name}")

    return PROVIDER_REGISTRY[name]
