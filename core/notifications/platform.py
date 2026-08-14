"""AIControlCenter-owned notification registry, routing policy, and facade."""

from __future__ import annotations

import re
from typing import Iterable

from .contracts import (
    NotificationChannel, NotificationIntent, NotificationProvider,
    NotificationProviderStatus, NotificationRoutingStatus, ProviderReadiness,
    ProviderReadinessEvidence, RoutingDecision,
)


GOVERNANCE = {
    "authority": "AICONTROLCENTER",
    "read_only": True,
    "production_authorization": False,
    "provider_transport_only": True,
    "external_business_policy_ownership": False,
    "action_execution": False,
    "automatic_retry": False,
}

_PROVIDER_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class NotificationProviderRegistry:
    def __init__(self, providers: Iterable[NotificationProvider] = ()) -> None:
        self._providers = tuple(providers)

    def providers(self) -> tuple[ProviderReadiness, ...]:
        observations: list[ProviderReadiness] = []
        for provider in self._providers:
            provider_id = _provider_identity(provider)
            if provider_id == "UNKNOWN":
                observations.append(_failed_observation("UNKNOWN", "InvalidProviderIdentity"))
                continue
            try:
                observations.append(_normalize_observation(provider.observe(), provider_id))
            except Exception as exc:
                observations.append(_failed_observation(provider_id, type(exc).__name__))

        duplicate_ids = {
            item.provider_id for item in observations
            if sum(candidate.provider_id == item.provider_id for candidate in observations) > 1
        }
        observations = [
            _failed_observation(item.provider_id, "DuplicateProviderIdentity")
            if item.provider_id in duplicate_ids else item
            for item in observations
        ]
        return tuple(sorted(observations, key=lambda item: item.provider_id))


def _provider_identity(provider: object) -> str:
    value = getattr(provider, "provider_id", None)
    return value if _valid_provider_identity(value) else "UNKNOWN"


def _valid_provider_identity(value: object) -> bool:
    return isinstance(value, str) and _PROVIDER_ID_PATTERN.fullmatch(value) is not None


def _failed_observation(provider_id: str, error_type: str) -> ProviderReadiness:
    safe_error_type = error_type if error_type.isidentifier() and len(error_type) <= 64 else "ObservationError"
    return ProviderReadiness(
        provider_id=provider_id,
        status=NotificationProviderStatus.UNKNOWN,
        configured=None,
        available=False,
        channels=(),
        evidence=(ProviderReadinessEvidence(
            evidence_type="provider_observation",
            status=NotificationProviderStatus.UNKNOWN,
            error_type=safe_error_type,
            reason_code="OBSERVATION_REJECTED",
        ),),
    )


def _normalize_observation(item: object, expected_provider_id: str) -> ProviderReadiness:
    if not isinstance(item, ProviderReadiness):
        raise TypeError
    if not _valid_provider_identity(item.provider_id):
        raise ValueError
    if item.provider_id != expected_provider_id:
        raise ValueError
    if item.configured is not None and type(item.configured) is not bool:
        raise TypeError
    if type(item.available) is not bool or type(item.observation_only) is not bool:
        raise TypeError
    if item.observation_only is not True:
        raise ValueError
    if not isinstance(item.status, NotificationProviderStatus):
        raise TypeError
    if not isinstance(item.channels, tuple):
        raise TypeError
    if any(not isinstance(channel, NotificationChannel) for channel in item.channels):
        raise TypeError
    if len(set(item.channels)) != len(item.channels):
        raise ValueError
    if not isinstance(item.evidence, tuple) or any(
        not isinstance(evidence, ProviderReadinessEvidence) for evidence in item.evidence
    ):
        raise TypeError
    for evidence in item.evidence:
        if not isinstance(evidence.status, NotificationProviderStatus):
            raise TypeError
        for value in (evidence.evidence_type, evidence.error_type, evidence.reason_code):
            if value is not None and (
                not isinstance(value, str) or not value.isidentifier() or len(value) > 64
            ):
                raise ValueError

    required = {
        NotificationProviderStatus.AVAILABLE: (True, True),
        NotificationProviderStatus.NOT_CONFIGURED: (False, False),
    }
    if item.status in required and (item.configured, item.available) != required[item.status]:
        raise ValueError
    if item.status in {
        NotificationProviderStatus.NOT_DEPLOYED,
        NotificationProviderStatus.UNKNOWN,
        NotificationProviderStatus.UNAVAILABLE,
        NotificationProviderStatus.DEGRADED,
    } and item.available is not False:
        raise ValueError
    return item


class DeterministicRoutingPolicy:
    """Choose the first requested channel, then provider id; never deliver."""

    def decide(
        self, intent: NotificationIntent, providers: tuple[ProviderReadiness, ...],
    ) -> RoutingDecision:
        for channel in intent.requested_channels:
            candidates = sorted(
                (item for item in providers if channel in item.channels
                 and item.status is NotificationProviderStatus.AVAILABLE
                 and item.available is True and item.configured is True),
                key=lambda item: item.provider_id,
            )
            if candidates:
                return RoutingDecision(
                    intent.intent_id, NotificationRoutingStatus.PLANNED,
                    channel, candidates[0].provider_id, "OBSERVATION_ONLY_ROUTE",
                )
        return RoutingDecision(
            intent.intent_id, NotificationRoutingStatus.BLOCKED,
            None, None, "NO_AVAILABLE_PROVIDER",
        )


class NotificationPlatform:
    def __init__(
        self,
        registry: NotificationProviderRegistry | None = None,
        routing_policy: DeterministicRoutingPolicy | None = None,
    ) -> None:
        self._registry = registry or NotificationProviderRegistry()
        self._routing_policy = routing_policy or DeterministicRoutingPolicy()

    def platform(self) -> dict[str, object]:
        providers = self._registry.providers()
        return {
            "schema_version": "notification-platform/v1",
            "status": "READ_ONLY_VALIDATION",
            "known_provider_count": len(providers),
            "known_channels": sorted({c.value for p in providers for c in p.channels}),
            "governance": dict(GOVERNANCE),
        }

    def providers(self) -> dict[str, object]:
        return {
            "schema_version": "notification-platform/v1",
            "providers": [item.to_dict() for item in self._registry.providers()],
            "governance": dict(GOVERNANCE),
        }

    def route(self, intent: NotificationIntent) -> RoutingDecision:
        """Evaluate deterministic policy only; this cannot execute delivery."""
        return self._routing_policy.decide(intent, self._registry.providers())


__all__ = (
    "DeterministicRoutingPolicy", "GOVERNANCE", "NotificationPlatform",
    "NotificationProviderRegistry",
)
