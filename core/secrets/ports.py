"""Core port for safe secret-backend metadata inspection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class SecretBackendInspection:
    """Value-free backend readiness metadata returned by an outer adapter."""

    backend_kind: str
    production_status: str
    configuration_valid: bool
    ready: bool
    checks: tuple[tuple[str, bool], ...]
    error_code: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "backend_kind": self.backend_kind,
            "production_status": self.production_status,
            "configuration_valid": self.configuration_valid,
            "ready": self.ready,
            "checks": [
                {"name": name, "passed": passed}
                for name, passed in self.checks
            ],
            "error_code": self.error_code,
            "value_free": True,
            "secret_values_read": False,
        }


class SecretBackendInspectionPort(Protocol):
    def inspect(self) -> SecretBackendInspection:
        """Inspect backend readiness without reading secret material."""
        ...


__all__ = ("SecretBackendInspection", "SecretBackendInspectionPort")
