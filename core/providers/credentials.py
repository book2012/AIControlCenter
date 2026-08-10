"""Environment-backed provider credential consumption contracts."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from typing import Protocol


OPENAI_CREDENTIAL_VARIABLE = "OPENAI_API_KEY"
ANTHROPIC_CREDENTIAL_VARIABLE = "ANTHROPIC_API_KEY"
PROVIDER_CREDENTIAL_VARIABLES = frozenset(
    (OPENAI_CREDENTIAL_VARIABLE, ANTHROPIC_CREDENTIAL_VARIABLE)
)


class CredentialSource(Protocol):
    def get(self, variable_name: str) -> str | None:
        ...


@dataclass(frozen=True, repr=False)
class EnvironmentCredentialSource:
    """Read canonical credential variables from an injected environment."""

    environment: Mapping[str, str] = field(default_factory=lambda: os.environ)

    def get(self, variable_name: str) -> str | None:
        if variable_name not in PROVIDER_CREDENTIAL_VARIABLES:
            return None
        return self.environment.get(variable_name)

    def __repr__(self) -> str:
        return "EnvironmentCredentialSource(redacted=True)"
