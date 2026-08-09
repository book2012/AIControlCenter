"""Credential lookup contract; credential installation is outside 01A."""

from typing import Protocol


OPENAI_CREDENTIAL_VARIABLE = "OPENAI_API_KEY"


class CredentialSource(Protocol):
    def get(self, variable_name: str) -> str | None:
        ...
