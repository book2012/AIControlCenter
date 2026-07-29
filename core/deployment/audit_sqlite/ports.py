"""Read-only inspection capability; deliberately not an append port."""

from __future__ import annotations

from typing import Protocol

from core.deployment.audit_sqlite.models import SQLiteAuditInspectionReport


class SQLiteAuditReadOnlyPort(Protocol):
    def inspect(self, *, inspected_at: str) -> SQLiteAuditInspectionReport: ...


__all__ = ("SQLiteAuditReadOnlyPort",)
