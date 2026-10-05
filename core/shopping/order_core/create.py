"""SHOP_ORDER_001A provider-neutral order-create contract foundation.

This module defines only AIControlCenter-owned application contracts. It does
not compose a WooCommerce writer, credential loader, HTTP transport, API route,
or production activation path.
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

from .domain import OrderContractError, OrderSnapshot


_CUSTOMER_ID = TypeAdapter(CustomerId)
_IDEMPOTENCY_RE = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
_REFERENCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_MAX_LINES = 100
_MAX_QUANTITY = 1000


class OrderCreateContractError(OrderContractError):
    """A create command or result violated the closed Order contract."""


class OrderCreateOperationConflict(ValueError):
    """An idempotency key was rebound to a different immutable command."""


class OrderCreateOperationInFlight(RuntimeError):
    """The exact operation is already consumed and has no replayable result."""


class OrderCreateOperationTerminalFailure(RuntimeError):
    """The exact operation failed and must not be retried automatically."""


def _reference(value: object, field: str) -> str:
    if type(value) is not str:
        raise OrderCreateContractError(f"{field}:TYPE")
    normalized = value.strip()
    if _REFERENCE_RE.fullmatch(normalized) is None:
        raise OrderCreateContractError(f"{field}:FORMAT")
    return normalized


def _idempotency_key(value: object) -> str:
    if type(value) is not str:
        raise OrderCreateContractError("idempotency_key:TYPE")
    normalized = value.strip()
    if _IDEMPOTENCY_RE.fullmatch(normalized) is None:
        raise OrderCreateContractError("idempotency_key:FORMAT")
    return normalized


def _customer_id(value: object) -> str:
    try:
        return _CUSTOMER_ID.validate_python(value)
    except (ValidationError, TypeError, ValueError) as exc:
        raise OrderCreateContractError("customer_id:INVALID") from exc


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
        if (
            type(self.quantity) is not int
            or not 1 <= self.quantity <= _MAX_QUANTITY
        ):
            raise OrderCreateContractError("quantity:INVALID")


@dataclass(frozen=True, slots=True)
class OrderCreateCommand:
    """Closed create intent owned by AIControlCenter.

    Price, currency, discounts, taxes, billing/shipping contact data, payment
    material, and provider metadata are deliberately absent. Those facts must
    come from trusted server-side authorities in later milestones.
    """

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
        payload = {
            "customer_id": self.customer_id,
            "line_items": [
                {
                    "product_id": item.product_id,
                    "variation_id": item.variation_id,
                    "quantity": item.quantity,
                }
                for item in self.line_items
            ],
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "audit_reference": self.audit_reference,
            "requested_at": self.requested_at.isoformat(),
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


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
        object.__setattr__(self, "correlation_id", _reference(self.correlation_id, "correlation_id"))
        object.__setattr__(self, "audit_reference", _reference(self.audit_reference, "audit_reference"))
        if type(self.snapshot) is not OrderSnapshot:
            raise OrderCreateContractError("snapshot:TYPE")
        if not re.fullmatch(r"[0-9a-f]{64}", self.command_digest):
            raise OrderCreateContractError("command_digest:FORMAT")
        if type(self.idempotent_replay) is not bool:
            raise OrderCreateContractError("idempotent_replay:TYPE")

    def as_replay(self) -> "OrderCreateResult":
        return replace(self, idempotent_replay=True)


class OrderCreatePort(Protocol):
    """Provider-neutral write port. No concrete provider writer exists in 001A."""

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
    """Consumes an operation key before any future provider write invocation."""

    production_safe: bool

    def claim(self, key: str, command_digest: str) -> OrderCreateClaim:
        ...

    def complete(
        self,
        key: str,
        command_digest: str,
        result: OrderCreateResult,
    ) -> None:
        ...

    def fail(self, key: str, command_digest: str) -> None:
        ...


@dataclass(slots=True)
class _OperationRecord:
    command_digest: str
    state: str = "IN_FLIGHT"
    result: OrderCreateResult | None = None


class InMemoryOrderCreateOperationCoordinator:
    """Thread-safe test coordinator; explicitly forbidden for Production."""

    production_safe = False

    def __init__(self) -> None:
        self._lock = Lock()
        self._operations: dict[str, _OperationRecord] = {}

    def claim(self, key: str, command_digest: str) -> OrderCreateClaim:
        key = _idempotency_key(key)
        if not re.fullmatch(r"[0-9a-f]{64}", command_digest):
            raise OrderCreateContractError("command_digest:FORMAT")
        with self._lock:
            record = self._operations.get(key)
            if record is None:
                self._operations[key] = _OperationRecord(command_digest)
                return OrderCreateClaim(OrderCreateClaimStatus.CLAIMED)
            if record.command_digest != command_digest:
                raise OrderCreateOperationConflict(
                    "idempotency key conflicts with another command"
                )
            if record.state == "COMPLETED":
                if record.result is None:
                    raise RuntimeError("completed operation has no result")
                return OrderCreateClaim(OrderCreateClaimStatus.COMPLETED, record.result)
            if record.state == "TERMINAL_FAILED":
                raise OrderCreateOperationTerminalFailure(
                    "operation previously failed terminally"
                )
            raise OrderCreateOperationInFlight("operation is already in flight")

    def complete(
        self,
        key: str,
        command_digest: str,
        result: OrderCreateResult,
    ) -> None:
        if type(result) is not OrderCreateResult:
            raise OrderCreateContractError("result:TYPE")
        with self._lock:
            record = self._operations.get(key)
            if (
                record is None
                or record.command_digest != command_digest
                or record.state != "IN_FLIGHT"
            ):
                raise RuntimeError("only the claimed operation can be completed")
            record.state = "COMPLETED"
            record.result = result

    def fail(self, key: str, command_digest: str) -> None:
        with self._lock:
            record = self._operations.get(key)
            if (
                record is None
                or record.command_digest != command_digest
                or record.state != "IN_FLIGHT"
            ):
                raise RuntimeError("only the claimed operation can be failed")
            record.state = "TERMINAL_FAILED"


def _line_quantities_from_command(
    command: OrderCreateCommand,
) -> dict[tuple[int, int], int]:
    return {
        (item.product_id, item.variation_id): item.quantity
        for item in command.line_items
    }


def _line_quantities_from_snapshot(
    snapshot: OrderSnapshot,
) -> dict[tuple[int, int], int]:
    result: dict[tuple[int, int], int] = {}
    for item in snapshot.line_items:
        identity = (item.product_id, item.variation_id)
        result[identity] = result.get(identity, 0) + item.quantity
    return result


def _validate_created_snapshot(
    command: OrderCreateCommand,
    snapshot: OrderSnapshot,
) -> None:
    if _line_quantities_from_snapshot(snapshot) != _line_quantities_from_command(command):
        raise OrderCreateContractError("order_creator:LINE_ITEMS_MISMATCH")


class OrderCreateService:
    """Application orchestration with claim-before-write semantics.

    001A intentionally has no default composition. A future milestone must
    inject both a durable production-safe coordinator and a separately reviewed
    provider writer before this service can be reachable from any runtime.
    """

    def __init__(
        self,
        *,
        order_creator: OrderCreatePort,
        coordinator: OrderCreateOperationCoordinator,
    ) -> None:
        self._order_creator = order_creator
        self._coordinator = coordinator

    def execute(self, command: OrderCreateCommand) -> OrderCreateResult:
        if type(command) is not OrderCreateCommand:
            raise OrderCreateContractError("command:TYPE")
        digest = command.command_digest
        claim = self._coordinator.claim(command.idempotency_key, digest)
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
                customer_id=command.customer_id,
                snapshot=snapshot,
                idempotency_key=command.idempotency_key,
                command_digest=digest,
                correlation_id=command.correlation_id,
                audit_reference=command.audit_reference,
            )
        except Exception:
            self._coordinator.fail(command.idempotency_key, digest)
            raise
        self._coordinator.complete(command.idempotency_key, digest, result)
        return result


__all__ = (
    "InMemoryOrderCreateOperationCoordinator",
    "OrderCreateClaim",
    "OrderCreateClaimStatus",
    "OrderCreateCommand",
    "OrderCreateContractError",
    "OrderCreateLine",
    "OrderCreateOperationConflict",
    "OrderCreateOperationCoordinator",
    "OrderCreateOperationInFlight",
    "OrderCreateOperationTerminalFailure",
    "OrderCreatePort",
    "OrderCreateResult",
    "OrderCreateService",
)
