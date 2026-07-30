"""Ports for operational bootstrap execution."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .models import *


class OperationalPermitArtifactReaderPort(Protocol):
    def read(self, path: Path) -> tuple[str, dict]: ...


class OperationalPermitAtomicClaimPort(Protocol):
    def claim(self, permit_path: Path,
              request: OperationalBootstrapClaimRequest) -> OperationalBootstrapClaimReceipt: ...


class MacOperationalHomeResolverPort(Protocol):
    def resolve(self) -> Path: ...


class OperationalBootstrapRuntimeArtifactPort(Protocol):
    def execute(self, *, request: OperationalBootstrapRuntimeRequest,
                paths: object, claim: OperationalBootstrapClaimReceipt,
                plan: OperationalBootstrapRuntimePlan) -> OperationalBootstrapRuntimeReceipt: ...
