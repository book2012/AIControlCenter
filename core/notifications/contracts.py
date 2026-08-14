"""Provider-neutral Notification Platform v1 contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Protocol


class NotificationChannel(str, Enum):
    EMAIL = "EMAIL"
    PUSH = "PUSH"
    SMS = "SMS"
    TELEGRAM = "TELEGRAM"
    WEBHOOK = "WEBHOOK"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationProviderStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_DEPLOYED = "NOT_DEPLOYED"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class NotificationRoutingStatus(str, Enum):
    PLANNED = "PLANNED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class NotificationRecipient:
    """Opaque AIControlCenter recipient reference; never a transport address."""

    recipient_id: str
    recipient_kind: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class NotificationIntent:
    intent_id: str
    category: str
    recipient: NotificationRecipient
    priority: NotificationPriority = NotificationPriority.NORMAL
    requested_channels: tuple[NotificationChannel, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "category": self.category,
            "recipient": self.recipient.to_dict(),
            "priority": self.priority.value,
            "requested_channels": [item.value for item in self.requested_channels],
        }


@dataclass(frozen=True)
class ProviderReadinessEvidence:
    evidence_type: str
    status: NotificationProviderStatus
    error_type: str | None = None
    reason_code: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "evidence_type": self.evidence_type,
            "status": self.status.value,
            "error_type": self.error_type,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class ProviderReadiness:
    provider_id: str
    status: NotificationProviderStatus
    configured: bool | None
    available: bool
    channels: tuple[NotificationChannel, ...]
    observation_only: bool = True
    evidence: tuple[ProviderReadinessEvidence, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "status": self.status.value,
            "configured": self.configured,
            "available": self.available,
            "channels": [item.value for item in self.channels],
            "observation_only": self.observation_only,
            "evidence": [item.to_dict() for item in self.evidence],
        }


@dataclass(frozen=True)
class RoutingDecision:
    intent_id: str
    status: NotificationRoutingStatus
    channel: NotificationChannel | None
    provider_id: str | None
    reason_code: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "intent_id": self.intent_id,
            "status": self.status.value,
            "channel": self.channel.value if self.channel else None,
            "provider_id": self.provider_id,
            "reason_code": self.reason_code,
        }


class NotificationProvider(Protocol):
    """Readiness-only provider port. V1 deliberately has no send method."""

    @property
    def provider_id(self) -> str: ...

    def observe(self) -> ProviderReadiness: ...


__all__ = (
    "NotificationChannel", "NotificationIntent", "NotificationPriority",
    "NotificationProvider", "NotificationProviderStatus",
    "NotificationRecipient", "NotificationRoutingStatus",
    "ProviderReadiness", "ProviderReadinessEvidence", "RoutingDecision",
)
