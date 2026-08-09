"""Strict provider registration and explicit routing."""

from __future__ import annotations

from core.providers.contracts import ProviderAdapter, ProviderIdentity, ProviderRequest, ProviderResponse
from core.providers.errors import ProviderError, ProviderErrorCode


class ProviderRouter:
    def __init__(self) -> None:
        self._adapters: dict[str, ProviderAdapter] = {}

    def register(self, adapter: ProviderAdapter) -> None:
        identity = ProviderIdentity.normalize(adapter.provider)
        if identity in self._adapters:
            raise ProviderError(ProviderErrorCode.DUPLICATE_PROVIDER, identity)
        self._adapters[identity] = adapter

    def get(self, provider: ProviderIdentity | str) -> ProviderAdapter:
        identity = ProviderIdentity.normalize(provider)
        try:
            return self._adapters[identity]
        except KeyError:
            raise ProviderError(ProviderErrorCode.UNKNOWN_PROVIDER, identity) from None

    def registered_providers(self) -> tuple[str, ...]:
        return tuple(sorted(self._adapters))

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        return self.get(request.provider).invoke(request)
