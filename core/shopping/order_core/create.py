"""SHOP_ORDER_001A/001B provider-neutral order-create application contracts.

No WooCommerce writer, credential loader, HTTP route, or production activation
is composed here. 001B adds trusted-authority binding and ambiguous-write
quarantine semantics required before any future provider write can be safe.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
import hashlib
import json
import re
from threading import Lock
from typing import Protocol

from pydantic import TypeAdapter, ValidationError

from core.shopping.customer_identity import CustomerId, require_utc
from core.shopping.customer_sessions import SessionId

from .domain import OrderContractError, OrderSnapshot


_CUSTOMER_ID = TypeAdapter(CustomerId)
_SESSION_ID = TypeAdapter(SessionId)
_IDEMPOTENCY_RE = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_REFERENCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_REASON_RE = re.compile(r"[A-Z][A-Z0-9_]{0,63}\Z")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}\Z")
_MAX_LINES = 100
_MAX_QUANTITY = 1000


class OrderCreateContractError(OrderContractError):
    """A create command, authority, or result violated the closed contract."""


class OrderCreateOperationConflict(ValueError):
    """An idempotency key was rebound to another command or authority."""


class OrderCreateOperationInFlight(RuntimeError):
    """The exact operation is claimed and cannot be invoked again."""


class OrderCreateOperationTerminalFailure(RuntimeError):
    """The exact operation definitively failed and cannot auto-retry."""


class OrderCreateOperationUnknownOutcome(RuntimeError):
    """A provider write may have happened; automatic retry is prohibited."""


class OrderCreateDefinitiveFailure(RuntimeError):
    """Writer certifies that no provider order was created."""

    def __init__(self, reason_code: str):
        self.reason_code = _reason_code(reason_code)
        super().__init__(self.reason_code)


class OrderCreateAmbiguousFailure(RuntimeError):
    """Writer cannot prove whether the provider order was created."""

    def __init__(self, reason_code: str = "UNKNOWN_OUTCOME"):
        self.reason_code = _reason_code(reason_code)
        super().__init__(self.reason_code)


def _reference(value: object, field: str) -> str:
    if type(value) is not str:
        raise OrderCreateContractError(f"{field}:TYPE")
    normalized = value.strip()
    if _REFERENCE_RE.fullmatch(normalized) is None:
        raise OrderCreateContractError(f"{field}:FORMAT")
    return normalized


def _reason_code(value: object) -> str:
    if type(value) is not str or _REASON_RE.fullmatch(value) is None:
        raise OrderCreateContractError("reason_code:FORMAT")
    return value


def _idempotency_key(value: object) -> str:
    if type(value) is not str:
        raise OrderCreateContractError("idempotency_key:TYPE")
    normalized = value.strip()
    if _IDEMPOTENCY_RE.fullmatch(normalized) is None:
        raise OrderCreateContractError("idempotency_key:FORMAT")
    return normalized


def _digest(value: object) -> str:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise OrderCreateContractError("command_digest:FORMAT")
    return value


def _customer_id(value: object) -> str:
    try:
        return _CUSTOMER_ID.validate_python(value)
    except (ValidationError, TypeError, ValueError) as exc:
        raise OrderCreateContractError("customer_id:INVALID") from exc


def _session_id(value: object) -> str:
    try:
        return _SESSION_ID.validate_python(value)
    except (ValidationError, TypeError, ValueError) as exc:
        raise OrderCreateContractError("session_id:INVALID") from exc


@dataclass(frozen=True, slots=True)
class OrderCreateLine:
    """Customer intent for one canonical catalog item; no client price authority."""

    product_id: int
    variation_id: int = 0
    quantity: int = 1

    def __post_init__(self) -> None:
        if type(self.product_id) is not int or self.product_id <= 0:
            raise OrderCreateContractError("product_id:INVALID")
        if type(self.variation_id) is not int or self.variation_id < 0:
            raise OrderCreateContractError("variation_id:INVALID")
        if type(self.quantity) is not int or not 1 <= self.quantity <= _MAX_QUANTITY:
            raise OrderCreateContractError("quantity:INVALID")


@dataclass(frozen=True, slots=True)
class OrderCreateCommand:
    """Closed customer intent with no client authority over commerce truth."""

    customer_id: str
    line_items: tuple[OrderCreateLine, ...]
    idempotency_key: str
    correlation_id: str
    audit_reference: str
    requested_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "customer_id", _customer_id(self.customer_id))
        object.__setattr__(self, "idempotency_key", _idempotency_key(self.idempotency_key))
        object.__setattr__(self, "correlation_id", _reference(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "audit_reference", _reference(self.audit_reference, "audit_reference"))
        if type(self.line_items) is not tuple:
            raise OrderCreateContractError("line_items:TYPE")
        if not 1 <= len(self.line_items) <= _MAX_LINES:
            raise OrderCreateContractError("line_items:BOUNDS")
        identities: set[tuple[int, int]] = set()
        for item in self.line_items:
            if type(item) is not OrderCreateLine:
                raise OrderCreateContractError("line_items:MEMBER_TYPE")
            identity = (item.product_id, item.variation_id)
            if identity in identities:
                raise OrderCreateContractError("line_items:DUPLICATE_PRODUCT")
            identities.add(identity)
        try:
            require_utc(self.requested_at)
        except (TypeError, ValueError) as exc:
            raise OrderCreateContractError("requested_at:UTC_REQUIRED") from exc

    @property
    def command_digest(self) -> str:
        encoded = json.dumps(
            {
                "customer_id": self.customer_id,
                "line_items": [
                    {"product_id": item.product_id, "variation_id": item.variation_id,
                     "quantity": item.quantity}
                    for item in self.line_items
                ],
                "idempotency_key": self.idempotency_key,
                "correlation_id": self.correlation_id,
                "audit_reference": self.audit_reference,
                "requested_at": self.requested_at.isoformat(),
            },
            sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class OrderCreateAuthority:
    """Server-owned authorization evidence from a trusted session boundary.

    Constructing this type does not authenticate a browser by itself. A future
    API composition must create it only after existing session credential,
    revocation, expiry, origin and CSRF validation have succeeded.
    """

    customer_id: str
    session_id: str
    authorization_reference: str
    authorized_at: datetime
    expires_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "customer_id", _customer_id(self.customer_id))
        object.__setattr__(self, "session_id", _session_id(self.session_id))
        object.__setattr__(
            self, "authorization_reference",
            _reference(self.authorization_reference, "authorization_reference"),
        )
        try:
            require_utc(self.authorized_at)
            require_utc(self.expires_at)
        except (TypeError, ValueError) as exc:
            raise OrderCreateContractError("authority:UTC_REQUIRED") from exc
        if self.expires_at <= self.authorized_at:
            raise OrderCreateContractError("authority:EXPIRED")


@dataclass(frozen=True, slots=True)
class OrderCreateResult:
    customer_id: str
    snapshot: OrderSnapshot
    idempotency_key: str
    command_digest: str
    correlation_id: str
    audit_reference: str
    idempotent_replay: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "customer_id", _customer_id(self.customer_id))
        object.__setattr__(self, "idempotency_key", _idempotency_key(self.idempotency_key))
        object.__setattr__(self, "command_digest", _digest(self.command_digest))
        object.__setattr__(self, "correlation_id", _reference(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "audit_reference", _reference(self.audit_reference, "audit_reference"))
        if type(self.snapshot) is not OrderSnapshot:
            raise OrderCreateContractError("snapshot:TYPE")
        if type(self.idempotent_replay) is not bool:
            raise OrderCreateContractError("idempotent_replay:TYPE")

    def as_replay(self) -> "OrderCreateResult":
        return replace(self, idempotent_replay=True)


class OrderCreatePort(Protocol):
    def create_order(self, command: OrderCreateCommand) -> OrderSnapshot:
        ...


class OrderCreateClaimStatus(str, Enum):
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True, slots=True)
class OrderCreateClaim:
    status: OrderCreateClaimStatus
    result: OrderCreateResult | None = None


class OrderCreateOperationCoordinator(Protocol):
    """Durably consumes authority-bound operation identity before a write."""

    production_safe: bool

    def claim(
        self, command: OrderCreateCommand, authority: OrderCreateAuthority
    ) -> OrderCreateClaim:
        ...

    def complete(self, key: str, command_digest: str, result: OrderCreateResult) -> None:
        ...

    def fail(self, key: str, command_digest: str, reason_code: str) -> None:
        ...

    def unknown(self, key: str, command_digest: str, reason_code: str) -> None:
        ...


@dataclass(slots=True)
class _OperationRecord:
    command_digest: str
    customer_id: str
    session_id: str
    authorization_reference: str
    authorized_at: datetime
    expires_at: datetime
    state: str = "CLAIMED"
    result: OrderCreateResult | None = None


def _validate_authority(command: OrderCreateCommand, authority: OrderCreateAuthority) -> None:
    if type(authority) is not OrderCreateAuthority:
        raise OrderCreateContractError("authority:TYPE")
    if authority.customer_id != command.customer_id:
        raise OrderCreateContractError("authority:CUSTOMER_MISMATCH")
    if not authority.authorized_at <= command.requested_at < authority.expires_at:
        raise OrderCreateContractError("authority:TIME_MISMATCH")


class InMemoryOrderCreateOperationCoordinator:
    """Thread-safe test coordinator; explicitly forbidden for Production."""

    production_safe = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._operations: dict[str, _OperationRecord] = {}

    def claim(
        self, command: OrderCreateCommand, authority: OrderCreateAuthority
    ) -> OrderCreateClaim:
        if type(command) is not OrderCreateCommand:
            raise OrderCreateContractError("command:TYPE")
        _validate_authority(command, authority)
        key = command.idempotency_key
        digest = command.command_digest
        binding = (
            digest, authority.customer_id, authority.session_id, authority.authorization_reference,
            authority.authorized_at, authority.expires_at,
        )
        identity = (digest, authority.customer_id, authority.session_id)
        with self._lock:
            record = self._operations.get(key)
            if record is None:
                self._operations[key] = _OperationRecord(*binding)
                return OrderCreateClaim(OrderCreateClaimStatus.CLAIMED)
            existing_identity = (
                record.command_digest, record.customer_id, record.session_id,
            )
            if existing_identity != identity:
                raise OrderCreateOperationConflict("idempotency key conflicts with another command or session")
            if record.state == "COMPLETED":
                if record.result is None:
                    raise RuntimeError("completed operation has no result")
                return OrderCreateClaim(OrderCreateClaimStatus.COMPLETED, record.result)
            if record.state == "TERMINAL_FAILED":
                raise OrderCreateOperationTerminalFailure("operation previously failed terminally")
            if record.state == "UNKNOWN_OUTCOME":
                raise OrderCreateOperationUnknownOutcome("operation is quarantined with unknown outcome")
            raise OrderCreateOperationInFlight("operation is already in flight")

    def complete(self, key: str, command_digest: str, result: OrderCreateResult) -> None:
        key = _idempotency_key(key); digest = _digest(command_digest)
        if type(result) is not OrderCreateResult:
            raise OrderCreateContractError("result:TYPE")
        with self._lock:
            record = self._operations.get(key)
            if record is None or record.command_digest != digest or record.state != "CLAIMED":
                raise RuntimeError("only the exact claimed operation can be completed")
            record.state = "COMPLETED"; record.result = result

    def fail(self, key: str, command_digest: str, reason_code: str) -> None:
        key = _idempotency_key(key); digest = _digest(command_digest); _reason_code(reason_code)
        with self._lock:
            record = self._operations.get(key)
            if record is None or record.command_digest != digest or record.state != "CLAIMED":
                raise RuntimeError("only the exact claimed operation can fail")
            record.state = "TERMINAL_FAILED"

    def unknown(self, key: str, command_digest: str, reason_code: str) -> None:
        key = _idempotency_key(key); digest = _digest(command_digest); _reason_code(reason_code)
        with self._lock:
            record = self._operations.get(key)
            if record is None or record.command_digest != digest or record.state != "CLAIMED":
                raise RuntimeError("only the exact claimed operation can be quarantined")
            record.state = "UNKNOWN_OUTCOME"


def _line_quantities_from_command(command: OrderCreateCommand) -> dict[tuple[int, int], int]:
    return {(item.product_id, item.variation_id): item.quantity for item in command.line_items}


def _line_quantities_from_snapshot(snapshot: OrderSnapshot) -> dict[tuple[int, int], int]:
    result: dict[tuple[int, int], int] = {}
    for item in snapshot.line_items:
        identity = (item.product_id, item.variation_id)
        result[identity] = result.get(identity, 0) + item.quantity
    return result


def _validate_created_snapshot(command: OrderCreateCommand, snapshot: OrderSnapshot) -> None:
    if _line_quantities_from_snapshot(snapshot) != _line_quantities_from_command(command):
        raise OrderCreateContractError("order_creator:LINE_ITEMS_MISMATCH")


class OrderCreateService:
    """Authority-bound orchestration with claim-before-write semantics."""

    def __init__(self, *, order_creator: OrderCreatePort,
                 coordinator: OrderCreateOperationCoordinator) -> None:
        self._order_creator = order_creator
        self._coordinator = coordinator

    def execute(self, command: OrderCreateCommand, authority: OrderCreateAuthority) -> OrderCreateResult:
        if type(command) is not OrderCreateCommand:
            raise OrderCreateContractError("command:TYPE")
        _validate_authority(command, authority)
        digest = command.command_digest
        claim = self._coordinator.claim(command, authority)
        if claim.status is OrderCreateClaimStatus.COMPLETED:
            if claim.result is None:
                raise RuntimeError("completed operation has no result")
            return claim.result.as_replay()
        try:
            snapshot = self._order_creator.create_order(command)
            if type(snapshot) is not OrderSnapshot:
                raise OrderCreateContractError("order_creator:INVALID_RESULT")
            _validate_created_snapshot(command, snapshot)
            result = OrderCreateResult(
                customer_id=command.customer_id, snapshot=snapshot,
                idempotency_key=command.idempotency_key, command_digest=digest,
                correlation_id=command.correlation_id, audit_reference=command.audit_reference,
            )
        except OrderCreateDefinitiveFailure as exc:
            self._coordinator.fail(command.idempotency_key, digest, exc.reason_code)
            raise
        except OrderCreateAmbiguousFailure as exc:
            self._coordinator.unknown(command.idempotency_key, digest, exc.reason_code)
            raise
        except Exception:
            self._coordinator.unknown(command.idempotency_key, digest, "PROVIDER_OR_POSTWRITE_UNKNOWN")
            raise
        self._coordinator.complete(command.idempotency_key, digest, result)
        return result


__all__ = (
    "InMemoryOrderCreateOperationCoordinator", "OrderCreateAmbiguousFailure",
    "OrderCreateAuthority", "OrderCreateClaim", "OrderCreateClaimStatus",
    "OrderCreateCommand", "OrderCreateContractError", "OrderCreateDefinitiveFailure",
    "OrderCreateLine", "OrderCreateOperationConflict", "OrderCreateOperationCoordinator",
    "OrderCreateOperationInFlight", "OrderCreateOperationTerminalFailure",
    "OrderCreateOperationUnknownOutcome", "OrderCreatePort", "OrderCreateResult",
    "OrderCreateService",
)
