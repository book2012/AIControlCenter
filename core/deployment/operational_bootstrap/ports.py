"""Ports for the isolated test-only bootstrap executor."""

from typing import Protocol

from .models import OperationalBootstrapEvidenceBundle


class OperationalBootstrapPort(Protocol):
    def execute(self, **kwargs: object) -> OperationalBootstrapEvidenceBundle: ...


class OperationalBootstrapArtifactPort(Protocol):
    def digest(self, artifact: object) -> str: ...
