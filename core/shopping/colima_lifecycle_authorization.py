"""Immutable one-shot authority for the dedicated 01G1F Colima runtime lifecycle reconciliation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from core.shopping.colima_lifecycle_reconciliation import (
    AuthorizationConsumptionState, AUTHORITATIVE_WORK_ITEM, MUTATION_ID, PROFILE, PROFILE_FILE,
)


MAXIMUM_USES = 1
MAXIMUM_LIFETIME = timedelta(minutes=10)


class AuthorizationError(RuntimeError):
    pass


class ConsumptionFailure(AuthorizationError):
    """Value-free durable progress evidence from the repository store."""

    def __init__(self, state: AuthorizationConsumptionState):
        super().__init__("AUTHORIZATION_CONSUMPTION_FAILED")
        self.state = state


class ConsumptionState(StrEnum):
    COMMITTED = "COMMITTED"


_STRING_BINDINGS = {
    "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
    "mutation_id": MUTATION_ID, "profile": PROFILE, "profile_file": PROFILE_FILE,
}


@dataclass(frozen=True, slots=True, init=False)
class ColimaLifecycleAuthorization:
    authorization_id: str; issued_at: str; expires_at: str
    trusted_uid: int; trusted_gid: int
    authoritative_work_item: str; mutation_id: str; profile: str; profile_file: str
    precondition_json: str
    maximum_uses: int; lifecycle_authority: bool; production_authority: bool; ubuntu_authority: bool
    def __new__(cls):
        raise TypeError("authorization is issued only by the fixed human boundary")


@dataclass(frozen=True, slots=True, init=False)
class ColimaLifecycleConsumptionReceipt:
    authorization_id: str; issued_at: str; expires_at: str
    trusted_uid: int; trusted_gid: int
    authoritative_work_item: str; mutation_id: str; profile: str; profile_file: str
    precondition_json: str
    maximum_uses: int; lifecycle_authority: bool; state: ConsumptionState
    production_authority: bool; ubuntu_authority: bool
    def __new__(cls):
        raise TypeError("receipt is emitted only by durable consumption")


@dataclass(frozen=True, slots=True, init=False)
class ColimaLifecycleConsumptionResult:
    receipt: ColimaLifecycleConsumptionReceipt
    def __new__(cls):
        raise TypeError("result is emitted only by durable consumption")


def validate_authorization(value: object, *, now: datetime, uid: int, gid: int) -> None:
    if type(value) is not ColimaLifecycleAuthorization:
        raise AuthorizationError("exact Colima lifecycle authorization type required")
    if any(
        type(getattr(value, key, None)) is not str
        or getattr(value, key) != expected
        for key, expected in _STRING_BINDINGS.items()
    ):
        raise AuthorizationError("authorization binding is invalid")
    from core.shopping.colima_lifecycle_reconciliation import parse_binding
    try:
        bound = parse_binding(value.precondition_json)
        if (bound["declared"]["owner"]["uid"], bound["declared"]["owner"]["gid"]) != (uid, gid):
            raise ValueError("source owner mismatch")
    except Exception:
        raise AuthorizationError("precondition binding invalid") from None
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
    if value.lifecycle_authority is not True:
        raise AuthorizationError("lifecycle authority required")
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


def validate_consumption_result(value: object, *, now: datetime, uid: int, gid: int) -> ColimaLifecycleConsumptionReceipt:
    if type(value) is not ColimaLifecycleConsumptionResult or type(value.receipt) is not ColimaLifecycleConsumptionReceipt:
        raise AuthorizationError("exact structured Colima lifecycle consumption receipt required")
    receipt = value.receipt
    if receipt.state is not ConsumptionState.COMMITTED:
        raise AuthorizationError("receipt is not durably committed")
    authorization = object.__new__(ColimaLifecycleAuthorization)
    for name in ColimaLifecycleAuthorization.__dataclass_fields__:
        object.__setattr__(authorization, name, getattr(receipt, name))
    validate_authorization(authorization, now=now, uid=uid, gid=gid)
    return receipt


def immutable_contract(*, uid: int, gid: int) -> dict[str, object]:
    return {
        **_STRING_BINDINGS,
        "maximum_uses": MAXIMUM_USES,
        "lifecycle_authority": True,
        "production_authority": False,
        "ubuntu_authority": False,
        "trusted_uid": uid,
        "trusted_gid": gid,
    }


__all__ = ("AuthorizationError", "ConsumptionState", "ColimaLifecycleAuthorization",
           "ColimaLifecycleConsumptionReceipt", "ColimaLifecycleConsumptionResult",
           "immutable_contract", "validate_authorization", "validate_consumption_result")
