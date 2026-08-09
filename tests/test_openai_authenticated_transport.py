import io
import json
import socket
import urllib.error

import pytest

from core.providers import (
    ProviderError,
    ProviderErrorCode,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    ProviderUsage,
    RetryPolicy,
    TimeoutPolicy,
)
from core.providers.openai_adapter import OPENAI_RESPONSES_ENDPOINT, OpenAIAdapter
from core.providers import openai_smoke


SECRET = "test-only-openai-secret"


def provider_request(*, attempts=1):
    return ProviderRequest(
        provider="openai",
        model="gpt-test",
        messages=(ProviderMessage(role="user", content="hello"),),
        instructions="Be concise",
        timeout=TimeoutPolicy(seconds=4),
        retry=RetryPolicy(max_attempts=attempts),
    )


class Response:
    def __init__(self, payload, headers=None):
        self._body = json.dumps(payload).encode()
        self.headers = headers or {}

    def read(self):
        return self._body


def success_payload():
    return {
        "id": "resp_123",
        "model": "gpt-test-2026",
        "status": "completed",
        "output": [{"content": [{"type": "output_text", "text": "hello back"}]}],
        "usage": {"input_tokens": 7, "output_tokens": 2, "total_tokens": 9},
    }


def test_request_construction_and_authorization_is_transport_only():
    captured = []

    def transport(request, timeout):
        captured.append((request, timeout))
        return Response(success_payload())

    response = OpenAIAdapter(
        credential_lookup=lambda name: SECRET,
        http_transport=transport,
        max_output_tokens=16,
    ).invoke(provider_request())

    upstream, timeout = captured[0]
    body = json.loads(upstream.data)
    assert upstream.full_url == OPENAI_RESPONSES_ENDPOINT
    assert upstream.method == "POST"
    assert upstream.get_header("Authorization") == f"Bearer {SECRET}"
    assert upstream.get_header("Content-type") == "application/json"
    assert timeout == 4
    assert body == {
        "model": "gpt-test",
        "input": [{"role": "user", "content": "hello"}],
        "max_output_tokens": 16,
        "instructions": "Be concise",
    }
    assert SECRET not in json.dumps(response.to_dict())


def test_missing_credential_fails_before_http():
    calls = []
    adapter = OpenAIAdapter(credential_lookup=lambda name: None, http_transport=lambda *args: calls.append(args))
    with pytest.raises(ProviderError) as captured:
        adapter.invoke(provider_request())
    assert captured.value.code is ProviderErrorCode.CREDENTIAL_MISSING
    assert calls == []


@pytest.mark.parametrize(
    ("status", "code"),
    [
        (401, ProviderErrorCode.AUTHENTICATION_FAILURE),
        (403, ProviderErrorCode.AUTHENTICATION_FAILURE),
        (408, ProviderErrorCode.TIMEOUT),
        (429, ProviderErrorCode.RATE_LIMIT),
        (500, ProviderErrorCode.UPSTREAM_ERROR),
        (503, ProviderErrorCode.UPSTREAM_ERROR),
        (400, ProviderErrorCode.INVALID_REQUEST),
        (422, ProviderErrorCode.INVALID_REQUEST),
    ],
)
def test_http_failure_normalization_and_secret_redaction(status, code):
    def transport(request, timeout):
        raise urllib.error.HTTPError(
            request.full_url,
            status,
            f"rejected {SECRET}",
            {"x-request-id": "req_failure"},
            io.BytesIO(f'{{"secret":"{SECRET}"}}'.encode()),
        )

    with pytest.raises(ProviderError) as captured:
        OpenAIAdapter(credential_lookup=lambda name: SECRET, http_transport=transport).invoke(provider_request())
    error = captured.value
    rendered = str(error) + repr(error) + json.dumps(error.to_dict())
    assert error.code is code
    assert error.provider_request_id == "req_failure"
    assert SECRET not in rendered
    assert "Authorization" not in rendered


@pytest.mark.parametrize("failure", [TimeoutError(), socket.timeout()])
def test_client_timeout_normalization(failure):
    def transport(request, timeout):
        raise failure
    with pytest.raises(ProviderError) as captured:
        OpenAIAdapter(credential_lookup=lambda name: SECRET, http_transport=transport).invoke(provider_request())
    assert captured.value.code is ProviderErrorCode.TIMEOUT


@pytest.mark.parametrize("body", [b"not-json", b"[]", json.dumps({"id": "x"}).encode()])
def test_invalid_response_normalization(body):
    class InvalidResponse:
        headers = {}
        def read(self):
            return body
    with pytest.raises(ProviderError) as captured:
        OpenAIAdapter(
            credential_lookup=lambda name: SECRET,
            http_transport=lambda request, timeout: InvalidResponse(),
        ).invoke(provider_request())
    assert captured.value.code is ProviderErrorCode.INTERNAL_ADAPTER_ERROR


def test_success_response_id_usage_and_output_text_normalization():
    response = OpenAIAdapter(
        credential_lookup=lambda name: SECRET,
        http_transport=lambda request, timeout: Response(success_payload()),
    ).invoke(provider_request())
    assert response.content == "hello back"
    assert response.model == "gpt-test-2026"
    assert response.provider_request_id == "resp_123"
    assert response.finish_reason == "stop"
    assert response.usage == ProviderUsage(input_units=7, output_units=2, total_units=9)


def test_header_request_id_is_used_when_payload_id_absent():
    payload = success_payload()
    del payload["id"]
    response = OpenAIAdapter(
        credential_lookup=lambda name: SECRET,
        http_transport=lambda request, timeout: Response(payload, {"x-request-id": "req_header"}),
    ).invoke(provider_request())
    assert response.provider_request_id == "req_header"


def test_exactly_one_call_no_retry_and_non_single_attempt_is_rejected():
    calls = []
    def failing_transport(request, timeout):
        calls.append(request)
        raise urllib.error.HTTPError(request.full_url, 500, "failure", {}, None)
    adapter = OpenAIAdapter(credential_lookup=lambda name: SECRET, http_transport=failing_transport)
    with pytest.raises(ProviderError):
        adapter.invoke(provider_request())
    assert len(calls) == 1
    with pytest.raises(ProviderError) as captured:
        adapter.invoke(provider_request(attempts=2))
    assert captured.value.code is ProviderErrorCode.INVALID_REQUEST
    assert len(calls) == 1


def test_smoke_json_is_sanitized_and_omits_generated_text(capsys, monkeypatch):
    class SmokeAdapter:
        def invoke(self, request):
            assert request.retry.max_attempts == 1
            return ProviderResponse(
                provider="openai",
                model=request.model,
                content=f"{openai_smoke.MARKER} generated-private-text {SECRET}",
                provider_request_id="resp_smoke",
                usage=ProviderUsage(input_units=11, output_units=3, total_units=14),
            )
    monkeypatch.setattr(openai_smoke, "OpenAIAdapter", lambda **kwargs: SmokeAdapter())
    assert openai_smoke.main(["--model", "gpt-test", "--json"]) == 0
    output = capsys.readouterr().out
    report = json.loads(output)
    assert report["final_status"] == "VALIDATED"
    assert report["network_calls"] == 1
    assert report["usage"] == {"input_tokens": 11, "output_tokens": 3, "total_tokens": 14}
    assert SECRET not in output
    assert "generated-private-text" not in output
    assert "content" not in report


def test_smoke_missing_credential_report_is_json_safe(capsys, monkeypatch):
    monkeypatch.setattr(
        openai_smoke,
        "OpenAIAdapter",
        lambda **kwargs: OpenAIAdapter(credential_lookup=lambda name: None),
    )
    assert openai_smoke.main(["--model", "gpt-test", "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["network_calls"] == 0
    assert report["error_code"] == "credential_missing"
    assert report["final_status"] == "BLOCKED"
