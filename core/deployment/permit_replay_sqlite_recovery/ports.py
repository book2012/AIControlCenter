"""Replaceable recovery ports."""

from __future__ import annotations

from typing import Protocol

from core.deployment.permit_replay_sqlite_recovery.models import (
    PermitReplayBackupReceipt,
    PermitReplayBackupRequest,
    PermitReplayRestoreReceipt,
    PermitReplayRestoreRequest,
)


class PermitReplayBackupPort(Protocol):
    def backup(self, request: PermitReplayBackupRequest) -> PermitReplayBackupReceipt: ...


class PermitReplayRestorePort(Protocol):
    def restore(self, request: PermitReplayRestoreRequest) -> PermitReplayRestoreReceipt: ...
