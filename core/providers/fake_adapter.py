"""Deterministic network-free provider adapter for tests."""

from dataclasses import dataclass

from core.providers.contracts import ProviderRequest, ProviderResponse
from core.providers.errors import ProviderError, ProviderErrorCode


@dataclass(frozen=True)
class FakeProviderAdapter:
    fail_with: ProviderErrorCode | None = None
    content: str = "fake response"

    @property
    def provider(self) -> str:
        return "fake"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        if request.provider != self.provider:
            raise ProviderError(ProviderErrorCode.INVALID_REQUEST, self.provider, model=request.model)
        if self.fail_with is not None:
            raise ProviderError(self.fail_with, self.provider, model=request.model)
        return ProviderResponse(
            provider=self.provider,
            model=request.model,
            content=self.content,
            finish_reason="stop",
            provider_request_id="fake-request-0001",
            metadata={"adapter": "deterministic_fake"},
        )
