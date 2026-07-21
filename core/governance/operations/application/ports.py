"""Replaceable application execution ports."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from .models import (
    BackupExecutionResult,
    SnapshotExecutionResult,
)


class SnapshotExecutor(Protocol):
    def execute(
        self,
        *,
        run_id: UUID,
        scheduled_for: datetime,
    ) -> SnapshotExecutionResult:
        """Perform one read-only audit snapshot."""


class BackupVerifier(Protocol):
    def verify(
        self,
        *,
        run_id: UUID,
        scheduled_for: datetime,
    ) -> BackupExecutionResult:
        """Perform one verified online backup."""
