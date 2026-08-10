from typing import Any, Dict

from core.config.settings import OpenAISettings, load_settings
from core.providers.base import AIProvider
from core.providers.contracts import ProviderMessage, ProviderRequest
from core.providers.errors import ProviderError
from core.providers.credentials import EnvironmentCredentialSource
from core.providers.openai_adapter import OpenAIAdapter


class OpenAIProvider(AIProvider):
    def __init__(self, settings: OpenAISettings | None = None):
        self.settings = settings or load_settings().openai

    def name(self) -> str:
        return "openai"

    def health(self) -> Dict[str, Any]:
        return {
            "provider": self.name(),
            "configured": bool(self.settings.api_key),
            "model": self.settings.model,
        }

    def chat(self, prompt: str) -> Dict[str, Any]:
        try:
            response = OpenAIAdapter(
                credential_source=EnvironmentCredentialSource(),
            ).invoke(
                ProviderRequest(
                    provider=self.name(),
                    model=self.settings.model,
                    messages=(ProviderMessage(role="user", content=prompt),),
                )
            )
            return {
                "provider": response.provider,
                "ok": True,
                "model": response.model,
                "content": response.content,
            }
        except ProviderError as exc:
            return {
                "provider": self.name(),
                "ok": False,
                **exc.to_dict(),
            }
