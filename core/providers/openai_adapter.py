"""Authenticated OpenAI Responses API transport behind ProviderAdapter."""

from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from typing import Any

from core.providers.contracts import ProviderRequest, ProviderResponse, ProviderUsage
from core.providers.credentials import OPENAI_CREDENTIAL_VARIABLE
from core.providers.errors import ProviderError, ProviderErrorCode


OPENAI_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
DEFAULT_MAX_OUTPUT_TOKENS = 128

CredentialLookup = Callable[[str], str | None]
InvocationBoundary = Callable[[ProviderRequest, str], ProviderResponse]
HttpTransport = Callable[[urllib.request.Request, float], Any]


def _stdlib_transport(request: urllib.request.Request, timeout: float) -> Any:
    return urllib.request.urlopen(request, timeout=timeout)


class OpenAIAdapter:
    def __init__(
        self,
        *,
        credential_lookup: CredentialLookup | None = None,
        invocation_boundary: InvocationBoundary | None = None,
        http_transport: HttpTransport | None = None,
        endpoint: str = OPENAI_RESPONSES_ENDPOINT,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> None:
        if max_output_tokens < 1 or max_output_tokens > DEFAULT_MAX_OUTPUT_TOKENS:
            raise ValueError(f"max_output_tokens must be between 1 and {DEFAULT_MAX_OUTPUT_TOKENS}")
        self._credential_lookup = credential_lookup or os.environ.get
        self._invocation_boundary = invocation_boundary
        self._http_transport = http_transport or _stdlib_transport
        self._endpoint = endpoint
        self._max_output_tokens = max_output_tokens

    @property
    def provider(self) -> str:
        return "openai"

    def invoke(self, request: ProviderRequest) -> ProviderResponse:
        if request.provider != self.provider or request.retry.max_attempts != 1:
            raise ProviderError(ProviderErrorCode.INVALID_REQUEST, self.provider, model=request.model)
        credential = self._credential_lookup(OPENAI_CREDENTIAL_VARIABLE)
        if not credential:
            raise ProviderError(ProviderErrorCode.CREDENTIAL_MISSING, self.provider, model=request.model)
        try:
            boundary = self._invocation_boundary or self._invoke_responses_api
            return boundary(request, credential)
        except ProviderError:
            raise
        except Exception:
            raise ProviderError(
                ProviderErrorCode.INTERNAL_ADAPTER_ERROR,
                self.provider,
                model=request.model,
            ) from None

    def _invoke_responses_api(self, request: ProviderRequest, credential: str) -> ProviderResponse:
        body: dict[str, Any] = {
            "model": request.model,
            "input": [message.to_dict() for message in request.messages],
            "max_output_tokens": self._max_output_tokens,
        }
        if request.instructions is not None:
            body["instructions"] = request.instructions
        encoded = json.dumps(body, separators=(",", ":")).encode("utf-8")
        upstream_request = urllib.request.Request(
            self._endpoint,
            data=encoded,
            headers={
                "Authorization": f"Bearer {credential}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            response = self._http_transport(upstream_request, request.timeout.seconds)
            raw_body = response.read()
            headers = getattr(response, "headers", {})
        except urllib.error.HTTPError as exc:
            self._raise_http_error(exc, request.model)
        except (TimeoutError, socket.timeout):
            raise ProviderError(ProviderErrorCode.TIMEOUT, self.provider, model=request.model) from None
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise ProviderError(ProviderErrorCode.TIMEOUT, self.provider, model=request.model) from None
            raise ProviderError(ProviderErrorCode.INTERNAL_ADAPTER_ERROR, self.provider, model=request.model) from None

        try:
            payload = json.loads(raw_body)
            if not isinstance(payload, dict):
                raise ValueError
            content = self._extract_content(payload)
            usage = self._extract_usage(payload.get("usage"))
        except (TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError(
                ProviderErrorCode.INTERNAL_ADAPTER_ERROR,
                self.provider,
                model=request.model,
            ) from None

        response_id = self._safe_identifier(payload.get("id")) or self._header_request_id(headers)
        response_model = payload.get("model") if isinstance(payload.get("model"), str) else request.model
        status = payload.get("status") if isinstance(payload.get("status"), str) else "completed"
        return ProviderResponse(
            provider=self.provider,
            model=response_model,
            content=content,
            status=status,
            finish_reason=self._finish_reason(payload),
            provider_request_id=response_id,
            usage=usage,
        )

    def _raise_http_error(self, exc: urllib.error.HTTPError, model: str) -> None:
        status = exc.code
        request_id = self._header_request_id(exc.headers or {})
        if status in (401, 403):
            code = ProviderErrorCode.AUTHENTICATION_FAILURE
        elif status == 408:
            code = ProviderErrorCode.TIMEOUT
        elif status == 429:
            code = ProviderErrorCode.RATE_LIMIT
        elif 500 <= status <= 599:
            code = ProviderErrorCode.UPSTREAM_ERROR
        elif 400 <= status <= 499:
            code = ProviderErrorCode.INVALID_REQUEST
        else:
            code = ProviderErrorCode.INTERNAL_ADAPTER_ERROR
        raise ProviderError(code, self.provider, model=model, provider_request_id=request_id) from None

    @staticmethod
    def _extract_content(payload: Mapping[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str):
            return output_text
        chunks: list[str] = []
        output = payload.get("output")
        if not isinstance(output, list):
            raise ValueError("missing output")
        for item in output:
            if not isinstance(item, dict) or not isinstance(item.get("content"), list):
                continue
            for part in item["content"]:
                if isinstance(part, dict) and part.get("type") in ("output_text", "text"):
                    text = part.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
        if not chunks:
            raise ValueError("missing output text")
        return "".join(chunks)

    @staticmethod
    def _extract_usage(value: Any) -> ProviderUsage | None:
        if not isinstance(value, dict):
            return None
        def token(name: str) -> int | None:
            item = value.get(name)
            return item if isinstance(item, int) and item >= 0 else None
        return ProviderUsage(
            input_units=token("input_tokens"),
            output_units=token("output_tokens"),
            total_units=token("total_tokens"),
        )

    @staticmethod
    def _finish_reason(payload: Mapping[str, Any]) -> str | None:
        incomplete = payload.get("incomplete_details")
        if isinstance(incomplete, dict) and isinstance(incomplete.get("reason"), str):
            return incomplete["reason"]
        return "stop" if payload.get("status") == "completed" else None

    @staticmethod
    def _safe_identifier(value: Any) -> str | None:
        return value if isinstance(value, str) and value else None

    @classmethod
    def _header_request_id(cls, headers: Any) -> str | None:
        try:
            return cls._safe_identifier(headers.get("x-request-id"))
        except (AttributeError, TypeError):
            return None
