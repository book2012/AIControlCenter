"""Replaceable durable audit boundary; DPL-04C supplies no adapter."""

from __future__ import annotations

from typing import Protocol

from core.deployment.audit_contracts.models import (
    AuditAppendReceipt,
    AuditAppendRequest,
    AuditIntegrityReport,
    AuditQuery,
    AuditQueryResult,
)


class DurableAuditPort(Protocol):
    def append(self, request: AuditAppendRequest) -> AuditAppendReceipt: ...

    def verify_integrity(self) -> AuditIntegrityReport: ...

    def query(self, query: AuditQuery) -> AuditQueryResult: ...


__all__ = ("DurableAuditPort",)
