"""Collision-free replaceable ports for separately composed SQLite recovery."""

from typing import Protocol

from .models import (
    SQLiteAuditBackupReceipt,
    SQLiteAuditBackupRequest,
    SQLiteAuditRestoreReceipt,
    SQLiteAuditRestoreRequest,
)


class SQLiteAuditBackupPort(Protocol):
    def backup(self, request: SQLiteAuditBackupRequest) -> SQLiteAuditBackupReceipt: ...


class SQLiteAuditRestorePort(Protocol):
    def restore(self, request: SQLiteAuditRestoreRequest) -> SQLiteAuditRestoreReceipt: ...
