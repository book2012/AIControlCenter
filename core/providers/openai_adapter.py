"""OpenAI adapter boundary for 01A; contains no network implementation."""

from __future__ import annotations

import os
from collections.abc import Callable

from core.providers.contracts import ProviderRequest, ProviderResponse
from core.providers.credentials import OPENAI_CREDENTIAL_VARIABLE
from core.providers.errors import ProviderError, ProviderErrorCode


CredentialLookup = Callable[[str], str | None]
InvocationBoundary = Callable[[ProviderRequest, str], ProviderResponse]


class OpenAIAdapter:
    def __init__(
        self,
        *,
        credential_lookup: CredentialLookup | None = None,
        invocation_boundary: InvocationBoundary | None = None,
    ) -> None:
        self._credential_lookup = credential_lookup or os.environ.get
        self._invocation_boundary = invocation_boundary

    @property
    def provider(self) -> str:
        return "openai"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        if request.provider != self.provider:
            raise ProviderError(ProviderErrorCode.INVALID_REQUEST, self.provider, model=request.model)
        credential = self._credential_lookup(OPENAI_CREDENTIAL_VARIABLE)
        if not credential:
            raise ProviderError(ProviderErrorCode.CREDENTIAL_MISSING, self.provider, model=request.model)
        if self._invocation_boundary is None:
            raise ProviderError(ProviderErrorCode.PROVIDER_UNAVAILABLE, self.provider, model=request.model)
        try:
            return self._invocation_boundary(request, credential)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError(
                ProviderErrorCode.INTERNAL_ADAPTER_ERROR,
                self.provider,
                model=request.model,
            ) from None
