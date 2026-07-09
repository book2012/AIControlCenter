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

    def chat(self, prompt: str, provider: str | None = None):
        preferred = provider or self.settings.ai.provider

        attempts = []

        if preferred not in self.providers:
            attempts.append({
                "provider": preferred,
                "skipped": True,
                "reason": "unknown_provider",
            })
            order = list(self.providers.keys())
        else:
            order = [preferred] + [
                name for name in self.providers
                if name != preferred
            ]

        for name in order:
            current = self.providers[name]
            health = current.health()

            if not health.get("configured"):
                attempts.append({
                    "provider": name,
                    "skipped": True,
                    "reason": "not_configured",
                })
                continue

            result = current.chat(prompt)
            attempts.append(result)

            if result.get("ok"):
                return {
                    "ok": True,
                    "provider": name,
                    "result": result,
                    "attempts": attempts,
                }

        return {
            "ok": False,
            "provider": None,
            "result": None,
            "attempts": attempts,
        }
