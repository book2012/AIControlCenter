"""Core port for safe secret-backend metadata inspection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field


_IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,126}[A-Za-z0-9]$|^[A-Za-z0-9]$"


class SecretReference(BaseModel):
    """Value-free metadata identifying a secret without resolving it.

    A reference is deliberately not a credential source.  It carries only
    bounded names that an explicitly authorized outer boundary may interpret.
    """

    model_config = ConfigDict(
        extra="forbid", frozen=True, validate_default=True,
        revalidate_instances="always", hide_input_in_errors=True,
    )

    backend: str = Field(
        strict=True, min_length=1, max_length=128, pattern=_IDENTIFIER,
    )
    key_name: str = Field(
        strict=True, min_length=1, max_length=128, pattern=_IDENTIFIER,
    )

    def to_dict(self) -> dict[str, str]:
        """Return metadata only; never a secret value."""

        return {"backend": self.backend, "key_name": self.key_name}


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


__all__ = ("SecretBackendInspection", "SecretBackendInspectionPort", "SecretReference")
