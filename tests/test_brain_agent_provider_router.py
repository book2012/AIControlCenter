import json

import pytest

from core.agent.brain_agent import BrainAgent
from core.config.settings import load_settings
from core.providers import ProviderErrorCode, ProviderRouter
from core.providers.fake_adapter import FakeProviderAdapter
from core.providers.openai_adapter import OpenAIAdapter


def agent_with(adapter, *, configured_provider="fake"):
    settings = load_settings()
    settings.ai.provider = configured_provider
    router = ProviderRouter()
    router.register(adapter)
    return BrainAgent(provider_router=router, settings=settings)


def test_canonical_brain_workflow_routes_to_fake_adapter_with_json_safe_metadata():
    agent = agent_with(FakeProviderAdapter(content="normalized answer"))

    result = agent.ask("hello", provider="fake")

    assert result["ok"] is True
    assert result["provider"] == "fake"
    assert result["result"]["content"] == "normalized answer"
    assert result["metadata"] == {
        "provider": "fake",
        "model": "provider-managed",
        "result_class": "provider_response",
        "request_id": "fake-request-0001",
    }
    assert json.loads(json.dumps(result)) == result


def test_configured_provider_selection_is_explicit_and_deterministic():
    agent = agent_with(FakeProviderAdapter(), configured_provider="fake")

    assert agent.ask("hello")["provider"] == "fake"


def test_unknown_provider_fails_closed_without_invoking_registered_adapter():
    calls = []

    class RecordingAdapter:
        provider = "fake"

        def invoke(self, request):
            calls.append(request)
            raise AssertionError("registered adapter must not be used as fallback")

    result = agent_with(RecordingAdapter()).ask("hello", provider="missing")

    assert result["ok"] is False
    assert result["error"]["code"] == "unknown_provider"
    assert calls == []


@pytest.mark.parametrize(
    "failure",
    [ProviderErrorCode.PROVIDER_UNAVAILABLE, ProviderErrorCode.UPSTREAM_ERROR],
)
def test_normalized_provider_failure_propagates_without_fallback(failure):
    result = agent_with(FakeProviderAdapter(fail_with=failure)).ask(
        "hello", provider="fake"
    )

    assert result["ok"] is False
    assert result["error"]["code"] == failure.value
    assert result["metadata"]["result_class"] == failure.value
    assert len(result["attempts"]) == 1


def test_missing_credential_is_normalized_before_any_transport_call():
    transport_calls = []
    adapter = OpenAIAdapter(
        credential_lookup=lambda _name: None,
        http_transport=lambda *args: transport_calls.append(args),
    )

    result = agent_with(adapter, configured_provider="openai").ask(
        "hello", provider="openai"
    )

    assert result["ok"] is False
    assert result["error"]["code"] == "credential_missing"
    assert transport_calls == []


def test_vendor_response_object_cannot_escape_adapter_boundary():
    class VendorObject:
        pass

    class InvalidAdapter:
        provider = "fake"

        def invoke(self, request):
            return VendorObject()

    result = agent_with(InvalidAdapter()).ask("hello", provider="fake")

    assert result["ok"] is False
    assert result["error"]["code"] == "internal_adapter_error"


def test_legacy_provider_manager_injection_remains_compatible():
    class LegacyProviders:
        def chat(self, prompt, provider=None):
            return {"ok": True, "provider": provider, "result": {"content": prompt}}

    result = BrainAgent(providers=LegacyProviders()).ask("hello", provider="legacy")

    assert result["result"]["content"] == "hello"
