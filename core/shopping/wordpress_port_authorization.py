"""Immutable one-shot authority for the fixed WordPress port reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from core.shopping.wordpress_port_reconciliation import (
    AUTHORITATIVE_WORK_ITEM, COMPOSE_FILE, COMPOSE_PROJECT, COMPOSE_SERVICE,
    DATABASE_CONTAINER, ENVIRONMENT, EXPECTED_AFTER_BINDING,
    EXPECTED_BEFORE_BINDING, MUTATION_ID, TARGET_CONTEXT, WORDPRESS_CONTAINER,
)

MAXIMUM_USES = 1
MAXIMUM_LIFETIME = timedelta(minutes=10)


class AuthorizationError(RuntimeError):
    pass


class ConsumptionState(StrEnum):
    COMMITTED = "COMMITTED"


_STRING_BINDINGS = {
    "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
    "environment": ENVIRONMENT, "mutation_id": MUTATION_ID,
    "target_context": TARGET_CONTEXT, "compose_project": COMPOSE_PROJECT,
    "compose_file": COMPOSE_FILE, "compose_service": COMPOSE_SERVICE,
    "database_container": DATABASE_CONTAINER,
    "wordpress_container": WORDPRESS_CONTAINER,
    "expected_before_binding": EXPECTED_BEFORE_BINDING,
    "expected_after_binding": EXPECTED_AFTER_BINDING,
}


@dataclass(frozen=True, slots=True, init=False)
class WordPressMutationAuthorization:
    authorization_id: str; issued_at: str; expires_at: str
    trusted_uid: int; trusted_gid: int
    authoritative_work_item: str; environment: str; mutation_id: str
    target_context: str; compose_project: str; compose_file: str
    compose_service: str; database_container: str; wordpress_container: str
    expected_before_binding: str; expected_after_binding: str
    maximum_uses: int; production_authority: bool; ubuntu_authority: bool
    def __new__(cls):
        raise TypeError("authorization is issued only by the fixed human boundary")


@dataclass(frozen=True, slots=True, init=False)
class WordPressMutationConsumptionReceipt:
    authorization_id: str; issued_at: str; expires_at: str
    trusted_uid: int; trusted_gid: int
    authoritative_work_item: str; environment: str; mutation_id: str
    target_context: str; compose_project: str; compose_file: str
    compose_service: str; database_container: str; wordpress_container: str
    expected_before_binding: str; expected_after_binding: str
    maximum_uses: int; state: ConsumptionState
    production_authority: bool; ubuntu_authority: bool
    def __new__(cls):
        raise TypeError("receipt is emitted only by durable consumption")


@dataclass(frozen=True, slots=True, init=False)
class WordPressMutationConsumptionResult:
    receipt: WordPressMutationConsumptionReceipt
    def __new__(cls):
        raise TypeError("result is emitted only by durable consumption")


def validate_authorization(value: object, *, now: datetime, uid: int, gid: int) -> None:
    if type(value) is not WordPressMutationAuthorization:
        raise AuthorizationError("exact WordPress authorization type required")
    if any(
        type(getattr(value, key, None)) is not str
        or getattr(value, key) != expected
        for key, expected in _STRING_BINDINGS.items()
    ):
        raise AuthorizationError("authorization binding is invalid")
    if type(value.authorization_id) is not str or not value.authorization_id:
        raise AuthorizationError("authorization id is invalid")
    if type(value.issued_at) is not str or type(value.expires_at) is not str:
        raise AuthorizationError("authorization timestamps are invalid")
    if (
        type(value.trusted_uid) is not int
        or type(value.trusted_gid) is not int
        or type(uid) is not int
        or type(gid) is not int
        or (value.trusted_uid, value.trusted_gid) != (uid, gid)
    ):
        raise AuthorizationError("authorization identity does not match trusted Darwin identity")
    if type(value.maximum_uses) is not int or value.maximum_uses != MAXIMUM_USES:
        raise AuthorizationError("authorization maximum uses is invalid")
    if type(value.production_authority) is not bool or value.production_authority is not False:
        raise AuthorizationError("production authority is invalid")
    if type(value.ubuntu_authority) is not bool or value.ubuntu_authority is not False:
        raise AuthorizationError("Ubuntu authority is invalid")
    try:
        issued, expires = datetime.fromisoformat(value.issued_at), datetime.fromisoformat(value.expires_at)
    except (TypeError, ValueError):
        raise AuthorizationError("authorization timestamps are invalid") from None
    if issued.tzinfo is None or expires.tzinfo is None or now.tzinfo is None:
        raise AuthorizationError("timezone-aware timestamps required")
    now = now.astimezone(timezone.utc)
    if expires <= issued or expires - issued > MAXIMUM_LIFETIME or now < issued.astimezone(timezone.utc) or now >= expires.astimezone(timezone.utc):
        raise AuthorizationError("authorization is not currently usable")


def validate_consumption_result(value: object, *, now: datetime, uid: int, gid: int) -> WordPressMutationConsumptionReceipt:
    if type(value) is not WordPressMutationConsumptionResult or type(value.receipt) is not WordPressMutationConsumptionReceipt:
        raise AuthorizationError("exact structured WordPress consumption receipt required")
    receipt = value.receipt
    if receipt.state is not ConsumptionState.COMMITTED:
        raise AuthorizationError("receipt is not durably committed")
    authorization = object.__new__(WordPressMutationAuthorization)
    for name in WordPressMutationAuthorization.__dataclass_fields__:
        object.__setattr__(authorization, name, getattr(receipt, name))
    validate_authorization(authorization, now=now, uid=uid, gid=gid)
    return receipt


def immutable_contract(*, uid: int, gid: int) -> dict[str, object]:
    return {
        **_STRING_BINDINGS,
        "maximum_uses": MAXIMUM_USES,
        "production_authority": False,
        "ubuntu_authority": False,
        "trusted_uid": uid,
        "trusted_gid": gid,
    }


__all__ = ("AuthorizationError", "ConsumptionState", "WordPressMutationAuthorization",
           "WordPressMutationConsumptionReceipt", "WordPressMutationConsumptionResult",
           "immutable_contract", "validate_authorization", "validate_consumption_result")
