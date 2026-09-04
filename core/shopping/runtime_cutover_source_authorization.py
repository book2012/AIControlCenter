"""Fixed CONTROLLED_NON_PRODUCTION authority for the 01B source repair."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from core.shopping.runtime_cutover_secret_source import SOURCE_ROLE, WORDPRESS_PORT_KEY

AUTHORITATIVE_WORK_ITEM = "SHOP-SERVICE-START-01B"
ENVIRONMENT = "CONTROLLED_NON_PRODUCTION"
MUTATION_ID = "SHOP-SERVICE-START-01B:RUNTIME_CUTOVER_SOURCE_PORT_TO_58082"
DESIRED_VALUE = "58082"
MAXIMUM_USES = 1
MAXIMUM_LIFETIME = timedelta(minutes=10)


class AuthorizationError(RuntimeError):
    pass


class ConsumptionState(StrEnum):
    COMMITTED = "COMMITTED"


@dataclass(frozen=True, slots=True, init=False)
class SourceMutationAuthorization:
    authorization_id: str
    issued_at: str
    expires_at: str
    trusted_uid: int
    trusted_gid: int
    authoritative_work_item: str
    environment: str
    mutation_id: str
    source_role: str
    source_key: str
    desired_value: str
    maximum_uses: int
    production_authority: bool
    ubuntu_authority: bool

    def __new__(cls):
        raise TypeError("authorization is issued only by the fixed human issuance boundary")


@dataclass(frozen=True, slots=True, init=False)
class SourceMutationConsumptionReceipt:
    authorization_id: str
    issued_at: str
    expires_at: str
    trusted_uid: int
    trusted_gid: int
    authoritative_work_item: str
    environment: str
    mutation_id: str
    source_role: str
    source_key: str
    desired_value: str
    maximum_uses: int
    state: ConsumptionState
    production_authority: bool
    ubuntu_authority: bool

    def __new__(cls):
        raise TypeError("receipt is emitted only by durable consumption")


@dataclass(frozen=True, slots=True, init=False)
class SourceMutationConsumptionResult:
    receipt: SourceMutationConsumptionReceipt

    def __new__(cls):
        raise TypeError("result is emitted only by durable consumption")


def validate_authorization(value: object, *, now: datetime, uid: int, gid: int) -> None:
    if type(value) is not SourceMutationAuthorization:
        raise AuthorizationError("exact source authorization type required")
    expected = {
        "authoritative_work_item": AUTHORITATIVE_WORK_ITEM, "environment": ENVIRONMENT,
        "mutation_id": MUTATION_ID, "source_role": SOURCE_ROLE,
        "source_key": WORDPRESS_PORT_KEY, "desired_value": DESIRED_VALUE,
        "maximum_uses": MAXIMUM_USES, "production_authority": False,
        "ubuntu_authority": False,
    }
    if any(getattr(value, name, None) != expected_value for name, expected_value in expected.items()):
        raise AuthorizationError("authorization binding is invalid")
    if type(value.authorization_id) is not str or not value.authorization_id:
        raise AuthorizationError("authorization id is invalid")
    if type(value.trusted_uid) is not int or type(value.trusted_gid) is not int:
        raise AuthorizationError("authorization identity is invalid")
    if (value.trusted_uid, value.trusted_gid) != (uid, gid):
        raise AuthorizationError("authorization identity does not match trusted Darwin identity")
    try:
        issued = datetime.fromisoformat(value.issued_at)
        expires = datetime.fromisoformat(value.expires_at)
    except (TypeError, ValueError):
        raise AuthorizationError("authorization timestamps are invalid") from None
    if issued.tzinfo is None or expires.tzinfo is None or now.tzinfo is None:
        raise AuthorizationError("timezone-aware timestamps required")
    now = now.astimezone(timezone.utc)
    if (expires <= issued or expires - issued > MAXIMUM_LIFETIME
            or now < issued.astimezone(timezone.utc) or now >= expires.astimezone(timezone.utc)):
        raise AuthorizationError("authorization is not currently usable")


def validate_consumption_result(value: object) -> SourceMutationConsumptionReceipt:
    if type(value) is not SourceMutationConsumptionResult:
        raise AuthorizationError("exact structured consumption result required")
    receipt = value.receipt
    if type(receipt) is not SourceMutationConsumptionReceipt:
        raise AuthorizationError("exact durable consumption receipt required")
    expected = (AUTHORITATIVE_WORK_ITEM, ENVIRONMENT, MUTATION_ID, SOURCE_ROLE,
                WORDPRESS_PORT_KEY, DESIRED_VALUE, MAXIMUM_USES,
                ConsumptionState.COMMITTED, False, False)
    actual = (receipt.authoritative_work_item, receipt.environment, receipt.mutation_id,
              receipt.source_role, receipt.source_key, receipt.desired_value,
              receipt.maximum_uses, receipt.state, receipt.production_authority,
              receipt.ubuntu_authority)
    if actual != expected:
        raise AuthorizationError("consumption receipt binding is invalid")
    return receipt


__all__ = ("AuthorizationError", "ConsumptionState", "SourceMutationAuthorization",
           "SourceMutationConsumptionReceipt", "SourceMutationConsumptionResult",
           "validate_authorization", "validate_consumption_result")
