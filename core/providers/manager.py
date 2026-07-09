from typing import Dict

from core.config.settings import Settings, load_settings
from core.providers.base import AIProvider
from core.providers.claude_provider import ClaudeProvider
from core.providers.google_provider import GoogleProvider
from core.providers.ollama_provider import OllamaProvider
from core.providers.openai_provider import OpenAIProvider


class ProviderManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()

        self.providers: Dict[str, AIProvider] = {
            "openai": OpenAIProvider(self.settings.openai),
            "google": GoogleProvider(self.settings.google),
            "claude": ClaudeProvider(),
            "ollama": OllamaProvider(),
        }

    def list(self):
        return {
            name: provider.health()
            for name, provider in self.providers.items()
        }

    def get(self, name: str) -> AIProvider:
        if name not in self.providers:
            raise KeyError(f"Unknown provider: {name}")

        return self.providers[name]

    def health(self):
        providers = self.list()

        return {
            "providers": providers,
            "ready": any(
                item.get("configured")
                for item in providers.values()
            ),
        }
