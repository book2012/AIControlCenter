from typing import Dict

from core.config.settings import Settings, load_settings
from core.providers.base import AIProvider
from core.providers.registry import PROVIDER_REGISTRY


class ProviderManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.providers: Dict[str, AIProvider] = self._load_providers()

    def _load_providers(self):
        providers = {}

        for name, provider_class in PROVIDER_REGISTRY.items():
            if name == "openai":
                providers[name] = provider_class(self.settings.openai)
            elif name == "google":
                providers[name] = provider_class(self.settings.google)
            else:
                providers[name] = provider_class()

        return providers

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
