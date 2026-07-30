"""Ports owned by the controlled operational composition boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Protocol


class ControlledOperationalClockPort(Protocol):
    def now(self) -> str: ...


class ControlledOperationalApprovalArtifactReaderPort(Protocol):
    def read(self, path: Path) -> Mapping[str, object]: ...


class ControlledOperationalPreflightArtifactReaderPort(Protocol):
    def read(self, path: Path) -> Mapping[str, object]: ...


class ControlledOperationalArtifactWriterPort(Protocol):
    def write(self, path: Path, value: Mapping[str, object]) -> None: ...


class ControlledOperationalGitEvidencePort(Protocol):
    def collect(self) -> Mapping[str, object]: ...


class ControlledOperationalHostEvidencePort(Protocol):
    def collect(self) -> Mapping[str, object]: ...
