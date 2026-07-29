"""Immutable contracts for durable permit reservation and terminal writes."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from core.deployment.contracts import sha256_digest


class PermitReplayWriteStatus(StrEnum):
    COMMITTED = "COMMITTED"
    IDEMPOTENT = "IDEMPOTENT"
    DENIED = "DENIED"
    UNAVAILABLE = "UNAVAILABLE"
    BLOCKED = "BLOCKED"
    INVALID = "INVALID"


class PermitTerminalState(StrEnum):
    CONSUMED = "CONSUMED"
    FAILED_CLOSED = "FAILED_CLOSED"


@dataclass(frozen=True, slots=True)
class PermitReplayWriterConfig:
    database_path: Path
    busy_timeout_seconds: float = 2.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "database_path", Path(self.database_path))
        if not 0 < self.busy_timeout_seconds <= 5:
            raise ValueError("busy_timeout_seconds must be bounded")


@dataclass(frozen=True, slots=True)
class PermitReservationRequest:
    permit_id: str
    permit_digest: str
    activation_id: str
    activation_request_digest: str
    package_digest: str
    plan_digest: str
    readiness_report_id: str
    readiness_report_digest: str
    target_identity: str
    environment: str
    sandbox_root_identity_digest: str
    requester_identity: str
    operator_identity: str
    approver_identity: str
    reserved_at: str
    expires_at: str
    production_authorized: bool = False


@dataclass(frozen=True, slots=True)
class PermitTerminalRequest:
    permit_id: str
    permit_digest: str
    activation_id: str
    activation_request_digest: str
    target_identity: str
    environment: str
    terminal_state: PermitTerminalState
    event_at: str
    actor_identity: str
    production_authorized: bool = False


@dataclass(frozen=True, slots=True, order=True)
class PermitReplayWriteFinding:
    code: str
    severity: str = "ERROR"
    detail: str = "request denied"


@dataclass(frozen=True, slots=True)
class PermitReplayWriteValidationReport:
    status: PermitReplayWriteStatus
    findings: tuple[PermitReplayWriteFinding, ...]
    database_path_identity_digest: str
    transaction_committed: bool = False

    @property
    def allowed(self) -> bool:
        return self.status in (
            PermitReplayWriteStatus.COMMITTED, PermitReplayWriteStatus.IDEMPOTENT
        )


@dataclass(frozen=True, slots=True)
class _Receipt:
    receipt_id: str
    event_id: str
    ledger_sequence: int
    permit_id: str
    permit_digest: str
    activation_id: str
    activation_request_digest: str
    event_type: str
    payload_digest: str
    previous_event_hash: str
    event_hash: str
    database_path_identity_digest: str
    transaction_committed: bool
    idempotent_retry: bool
    event_at: str
    production_authorized: bool
    receipt_digest: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PermitReservationReceipt(_Receipt):
    pass


@dataclass(frozen=True, slots=True)
class PermitTerminalReceipt(_Receipt):
    pass


def build_receipt(receipt_type: type[_Receipt], **values: Any) -> _Receipt:
    semantic = dict(values)
    digest = sha256_digest(semantic)
    return receipt_type(
        **semantic,
        receipt_id="permit-replay-receipt-" + digest[7:39],
        receipt_digest=digest,
    )
