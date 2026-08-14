import json
from pathlib import Path

import pytest

from core.notifications import NotificationPlatform, NotificationProviderRegistry
from core.notifications.contracts import (
    NotificationChannel, NotificationIntent, NotificationPriority,
    NotificationProviderStatus, NotificationRecipient, NotificationRoutingStatus,
    ProviderReadiness, ProviderReadinessEvidence,
)
from integrations.notifications import (
    TelegramNotificationAdapter, build_telegram_notification_adapter,
)


class Provider:
    def __init__(self, provider_id="provider-b", observation=None):
        self.provider_id = provider_id
        self.observation = observation or ProviderReadiness(
            provider_id, NotificationProviderStatus.AVAILABLE, True, True,
            (NotificationChannel.EMAIL,),
            evidence=(ProviderReadinessEvidence(
                "fixture", NotificationProviderStatus.AVAILABLE,
            ),),
        )

    def observe(self):
        return self.observation


def intent():
    return NotificationIntent(
        "intent-1", "operations", NotificationRecipient("recipient-1", "operator"),
        NotificationPriority.HIGH, (NotificationChannel.EMAIL,),
    )


def test_domain_contracts_are_json_compatible_and_status_types_are_separate():
    serialized = json.dumps(intent().to_dict())
    assert "recipient-1" in serialized
    assert "address" not in serialized and "message" not in serialized
    assert set(NotificationProviderStatus) != set(NotificationRoutingStatus)


def test_no_provider_configured_is_truthful():
    platform = NotificationPlatform()
    assert platform.providers()["providers"] == []
    assert platform.route(intent()).status is NotificationRoutingStatus.BLOCKED


@pytest.mark.parametrize("observation", [
    ProviderReadiness("provider-b", NotificationProviderStatus.AVAILABLE, None, True, (NotificationChannel.EMAIL,)),
    ProviderReadiness("provider-b", NotificationProviderStatus.AVAILABLE, True, False, (NotificationChannel.EMAIL,)),
    ProviderReadiness("provider-b", NotificationProviderStatus.NOT_CONFIGURED, True, False, (NotificationChannel.EMAIL,)),
    ProviderReadiness("provider-b", NotificationProviderStatus.UNKNOWN, None, True, (NotificationChannel.EMAIL,)),
    ProviderReadiness("provider-b", NotificationProviderStatus.UNAVAILABLE, True, True, (NotificationChannel.EMAIL,)),
    ProviderReadiness("provider-b", NotificationProviderStatus.AVAILABLE, True, True, (NotificationChannel.EMAIL, NotificationChannel.EMAIL)),
    ProviderReadiness("provider-b", NotificationProviderStatus.AVAILABLE, True, True, (NotificationChannel.EMAIL,), observation_only=False),
])
def test_semantically_inconsistent_provider_observation_fails_closed(observation):
    platform = NotificationPlatform(NotificationProviderRegistry((Provider(observation=observation),)))
    provider = platform.providers()["providers"][0]
    assert provider["provider_id"] == "provider-b"
    assert provider["status"] == "UNKNOWN"
    assert provider["available"] is False
    assert platform.route(intent()).status is NotificationRoutingStatus.BLOCKED


def test_malformed_and_exception_observations_preserve_safe_identity_and_values_do_not_leak():
    class Malformed:
        provider_id = "malformed"
        def observe(self):
            return {"token": "private-value"}

    class Failure:
        provider_id = "failure"
        def observe(self):
            raise RuntimeError("token=private-value")

    result = NotificationPlatform(NotificationProviderRegistry((Malformed(), Failure()))).providers()
    assert [item["provider_id"] for item in result["providers"]] == ["failure", "malformed"]
    assert all(item["status"] == "UNKNOWN" for item in result["providers"])
    assert "private-value" not in json.dumps(result)


def test_provider_evidence_values_are_bounded_and_fail_closed():
    observation = ProviderReadiness(
        "provider-b", NotificationProviderStatus.AVAILABLE, True, True,
        (NotificationChannel.EMAIL,),
        evidence=(ProviderReadinessEvidence(
            "token=private-value", NotificationProviderStatus.AVAILABLE,
        ),),
    )
    result = NotificationPlatform(NotificationProviderRegistry((
        Provider(observation=observation),
    ))).providers()
    assert result["providers"][0]["status"] == "UNKNOWN"
    assert "private-value" not in json.dumps(result)


@pytest.mark.parametrize("rejected_id", [
    "token=private-value",
    "https://secret.example/path",
    "a" * 65,
])
def test_invalid_declared_provider_identity_fails_closed_without_projection(rejected_id):
    platform = NotificationPlatform(NotificationProviderRegistry((Provider(rejected_id),)))
    serialized = json.dumps(platform.providers())
    assert platform.providers()["providers"][0]["provider_id"] == "UNKNOWN"
    assert platform.route(intent()).status is NotificationRoutingStatus.BLOCKED
    assert rejected_id not in serialized


def test_missing_declared_identity_cannot_project_invalid_observed_identity():
    class MissingIdentity:
        def observe(self):
            return ProviderReadiness(
                "secret=value", NotificationProviderStatus.AVAILABLE, True, True,
                (NotificationChannel.EMAIL,),
            )

    platform = NotificationPlatform(NotificationProviderRegistry((MissingIdentity(),)))
    serialized = json.dumps(platform.providers())
    assert platform.providers()["providers"][0]["provider_id"] == "UNKNOWN"
    assert platform.route(intent()).status is NotificationRoutingStatus.BLOCKED
    assert "secret=value" not in serialized


def test_valid_declared_identity_with_mismatched_observed_identity_fails_closed():
    provider = Provider(
        "provider-a",
        ProviderReadiness(
            "provider-b", NotificationProviderStatus.AVAILABLE, True, True,
            (NotificationChannel.EMAIL,),
        ),
    )
    platform = NotificationPlatform(NotificationProviderRegistry((provider,)))
    serialized = json.dumps(platform.providers())
    assert platform.providers()["providers"][0]["provider_id"] == "provider-a"
    assert platform.route(intent()).status is NotificationRoutingStatus.BLOCKED
    assert "provider-b" not in serialized


@pytest.mark.parametrize("provider_id", [
    "telegram", "provider-a", "provider_b", "provider.example",
])
def test_bounded_provider_identity_grammar_accepts_valid_values(provider_id):
    platform = NotificationPlatform(NotificationProviderRegistry((Provider(provider_id),)))
    assert platform.providers()["providers"][0]["provider_id"] == provider_id
    assert platform.route(intent()).status is NotificationRoutingStatus.PLANNED


def test_duplicate_provider_identity_is_deterministically_non_routable():
    platform = NotificationPlatform(NotificationProviderRegistry((Provider("duplicate"), Provider("duplicate"))))
    assert all(item["status"] == "UNKNOWN" for item in platform.providers()["providers"])
    assert platform.route(intent()).status is NotificationRoutingStatus.BLOCKED


def test_routing_is_deterministic_available_only_and_observation_only():
    registry = NotificationProviderRegistry((Provider("provider-b"), Provider("provider-a")))
    platform = NotificationPlatform(registry)
    decision = platform.route(intent())
    assert decision.provider_id == "provider-a"
    assert decision.status is NotificationRoutingStatus.PLANNED
    assert platform.platform()["governance"]["automatic_retry"] is False


@pytest.mark.parametrize(("deployment", "configured", "available", "expected"), [
    ("NOT_DEPLOYED", None, None, NotificationProviderStatus.NOT_DEPLOYED),
    ("DEPLOYED", None, None, NotificationProviderStatus.UNKNOWN),
    ("PRODUCTION", None, None, NotificationProviderStatus.UNKNOWN),
    ("DEPLOYED", False, None, NotificationProviderStatus.NOT_CONFIGURED),
    ("PRODUCTION", True, True, NotificationProviderStatus.AVAILABLE),
    ("PRODUCTION", True, False, NotificationProviderStatus.UNAVAILABLE),
])
def test_telegram_truth_semantics(deployment, configured, available, expected):
    result = TelegramNotificationAdapter(deployment, configured, available).observe()
    assert result.status is expected
    assert result.available is (expected is NotificationProviderStatus.AVAILABLE)


def test_canonical_telegram_provider_truth_is_optional_not_deployed():
    provider = NotificationPlatform(NotificationProviderRegistry((
        build_telegram_notification_adapter(),
    ))).providers()["providers"][0]
    assert provider["provider_id"] == "telegram"
    assert provider["status"] == "NOT_DEPLOYED"
    assert provider["configured"] is None
    assert provider["available"] is False
    assert provider["observation_only"] is True


def test_optional_provider_absence_has_no_external_discovery(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "private-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "private-recipient")
    result = NotificationPlatform().providers()
    assert result["providers"] == []
    assert "private" not in json.dumps(result)


def test_core_has_no_outer_imports():
    imports = []
    for path in Path("core").rglob("*.py"):
        for line in path.read_text().splitlines():
            if line.startswith(("import ops", "from ops", "import integrations", "from integrations")):
                imports.append((path, line))
    assert imports == []


def test_notification_surface_has_no_send_or_retry_or_transport_execution():
    assert not hasattr(NotificationPlatform(), "send")
    assert not hasattr(NotificationPlatform(), "retry")
    source = Path("integrations/notifications/telegram.py").read_text()
    assert "def send" not in source
    assert all(word not in source for word in ("requests", "httpx", "urllib", "socket", "subprocess"))
