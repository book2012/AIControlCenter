"""Read-only Telegram transport readiness adapter for PA-04 v1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.capabilities.manifest import CapabilityManifestError, lookup_service_metadata
from core.notifications.contracts import (
    NotificationChannel, NotificationProviderStatus, ProviderReadiness,
    ProviderReadinessEvidence,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "config/services/mac-standalone-production.json"
DEFAULT_SCHEMA = ROOT / "config/schemas/mac-service-manifest.schema.json"


@dataclass(frozen=True)
class TelegramNotificationAdapter:
    provider_id = "telegram"
    deployment_status: str = "UNKNOWN"
    configured: bool | None = None
    available: bool | None = None

    def observe(self) -> ProviderReadiness:
        evidence_status = _deployment_status(self.deployment_status)
        evidence = (ProviderReadinessEvidence("canonical_manifest", evidence_status),)
        if evidence_status is NotificationProviderStatus.NOT_DEPLOYED:
            return ProviderReadiness(
                "telegram", evidence_status, self.configured, False,
                (NotificationChannel.TELEGRAM,), evidence=evidence,
            )
        if evidence_status is not NotificationProviderStatus.UNKNOWN:
            return ProviderReadiness(
                "telegram", NotificationProviderStatus.UNKNOWN, None, False,
                (NotificationChannel.TELEGRAM,), evidence=evidence,
            )
        if self.configured is False:
            status = NotificationProviderStatus.NOT_CONFIGURED
        elif self.configured is None or self.available is None:
            status = NotificationProviderStatus.UNKNOWN
        elif self.available:
            status = NotificationProviderStatus.AVAILABLE
        else:
            status = NotificationProviderStatus.UNAVAILABLE
        return ProviderReadiness(
            "telegram", status, self.configured,
            status is NotificationProviderStatus.AVAILABLE,
            (NotificationChannel.TELEGRAM,), evidence=evidence,
        )


def _deployment_status(value: str) -> NotificationProviderStatus:
    if value == "NOT_DEPLOYED":
        return NotificationProviderStatus.NOT_DEPLOYED
    if value in {"DEPLOYED", "PRODUCTION"}:
        return NotificationProviderStatus.UNKNOWN
    return NotificationProviderStatus.UNKNOWN


def build_telegram_notification_adapter(
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
    schema_path: Path = DEFAULT_SCHEMA,
    configured: bool | None = None,
    available: bool | None = None,
) -> TelegramNotificationAdapter:
    deployment_status = "UNKNOWN"
    try:
        metadata = lookup_service_metadata(
            "telegram", manifest_path=manifest_path, schema_path=schema_path,
        )
        deployment_status = metadata["production_status"]
    except (CapabilityManifestError, KeyError, TypeError):
        pass
    return TelegramNotificationAdapter(deployment_status, configured, available)


__all__ = ("TelegramNotificationAdapter", "build_telegram_notification_adapter")
