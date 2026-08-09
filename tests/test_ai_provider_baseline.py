import json

import pytest

from core.providers import (
    ProviderError,
    ProviderErrorCode,
    ProviderMessage,
    ProviderRequest,
    ProviderResponse,
    ProviderRouter,
    ProviderUsage,
    RetryPolicy,
    TimeoutPolicy,
)
from core.providers.fake_adapter import FakeProviderAdapter
from core.providers.openai_adapter import OpenAIAdapter


def request(provider="fake"):
    return ProviderRequest(
        provider=provider,
        model="test-model",
        messages=(ProviderMessage(role="user", content="hello"),),
        metadata={"correlation_id": "test-1"},
        timeout=TimeoutPolicy(seconds=2),
        retry=RetryPolicy(max_attempts=1),
    )


def test_provider_registration_and_deterministic_lookup():
    adapter = FakeProviderAdapter()
    router = ProviderRouter()
    router.register(adapter)

    assert router.get("fake") is adapter
    assert router.registered_providers() == ("fake",)


def test_duplicate_provider_rejected_fail_closed():
    router = ProviderRouter()
    router.register(FakeProviderAdapter())

    with pytest.raises(ProviderError) as captured:
        router.register(FakeProviderAdapter())

    assert captured.value.code is ProviderErrorCode.DUPLICATE_PROVIDER


def test_unknown_provider_rejected_without_fallback():
    adapter = FakeProviderAdapter()
    router = ProviderRouter()
    router.register(adapter)

    with pytest.raises(ProviderError) as captured:
        router.invoke(request("openai"))

    assert captured.value.code is ProviderErrorCode.UNKNOWN_PROVIDER
    assert router.registered_providers() == ("fake",)


def test_fake_provider_normalized_success():
    router = ProviderRouter()
    router.register(FakeProviderAdapter(content="deterministic"))

    response = router.invoke(request())

    assert response.to_dict() == {
        "provider": "fake",
        "model": "test-model",
        "content": "deterministic",
        "status": "completed",
        "finish_reason": "stop",
        "provider_request_id": "fake-request-0001",
        "usage": None,
        "metadata": {"adapter": "deterministic_fake"},
    }


def test_fake_provider_normalized_failure():
    router = ProviderRouter()
    router.register(FakeProviderAdapter(fail_with=ProviderErrorCode.RATE_LIMIT))

    with pytest.raises(ProviderError) as captured:
        router.invoke(request())

    assert captured.value.to_dict()["error"]["code"] == "rate_limit"


@pytest.mark.parametrize("code", list(ProviderErrorCode))
def test_normalized_provider_error_shape(code):
    error = ProviderError(code, "fake", model="test-model")

    assert error.to_dict()["error"] == {
        "code": code.value,
        "message": error.args[0],
        "provider": "fake",
        "model": "test-model",
        "provider_request_id": None,
        "metadata": {},
    }


def test_request_serialization_includes_bounded_policies():
    serialized = request().to_dict()

    assert serialized["provider"] == "fake"
    assert serialized["messages"] == [{"role": "user", "content": "hello"}]
    assert serialized["timeout"] == {"seconds": 2}
    assert serialized["retry"] == {"max_attempts": 1}
    json.dumps(serialized)


def test_response_serialization_is_json_safe():
    response = ProviderResponse(
        provider="fake",
        model="test-model",
        content="ok",
        usage=ProviderUsage(input_units=1, output_units=2, total_units=3),
    )

    assert json.loads(json.dumps(response.to_dict()))["usage"]["total_units"] == 3


def test_missing_openai_credential_fails_before_invocation_boundary():
    boundary_calls = []
    adapter = OpenAIAdapter(
        credential_lookup=lambda _name: None,
        invocation_boundary=lambda provider_request, credential: boundary_calls.append(
            (provider_request, credential)
        ),
    )

    with pytest.raises(ProviderError) as captured:
        adapter.invoke(request("openai"))

    assert captured.value.code is ProviderErrorCode.CREDENTIAL_MISSING
    assert boundary_calls == []


def test_secret_sentinel_is_redacted_from_all_error_forms():
    sentinel = "test-only-secret-sentinel"
    error = ProviderError(
        ProviderErrorCode.INTERNAL_ADAPTER_ERROR,
        "openai",
        metadata={"credential": sentinel, "operation": "invoke"},
    )

    rendered = (str(error), repr(error), json.dumps(error.to_dict()))
    assert all(sentinel not in value for value in rendered)
    assert error.to_dict()["error"]["metadata"] == {"operation": "invoke"}


def test_openai_boundary_normalizes_exception_without_secret_leakage():
    sentinel = "test-only-boundary-secret"

    def fail(_provider_request, credential):
        raise RuntimeError(f"upstream rejected {credential}")

    adapter = OpenAIAdapter(
        credential_lookup=lambda _name: sentinel,
        invocation_boundary=fail,
    )

    with pytest.raises(ProviderError) as captured:
        adapter.invoke(request("openai"))

    rendered = str(captured.value) + repr(captured.value) + json.dumps(captured.value.to_dict())
    assert captured.value.code is ProviderErrorCode.INTERNAL_ADAPTER_ERROR
    assert sentinel not in rendered
