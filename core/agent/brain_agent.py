from core.providers.manager import ProviderManager


class BrainAgent:
    def __init__(self, providers: ProviderManager | None = None):
        self.providers = providers or ProviderManager()

    def ask(self, prompt: str, provider: str | None = None):
        return self.providers.chat(
            prompt=prompt,
            provider=provider,
        )
