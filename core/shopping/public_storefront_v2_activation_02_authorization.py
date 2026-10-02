"""Immutable, bounded authorization values for Activation-02."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from enum import StrEnum

from core.shopping.public_storefront_v2_activation_02_reconciliation import (
    AUTHORITY_ID, AUTHORITATIVE_WORK_ITEM, MAXIMUM_LIFETIME_SECONDS, MAXIMUM_USES,
    MUTATION_ID, PROFILE, PROFILE_FILE, parse_preconditions,
)


class AuthorizationError(RuntimeError):
    pass


class ConsumptionFailure(AuthorizationError):
    def __init__(self, state: str):
        super().__init__("AUTHORIZATION_CONSUMPTION_FAILED")
        self.state = state


class ConsumptionState(StrEnum):
    COMMITTED = "COMMITTED"


_FIELDS = (
    "authorization_id", "issued_at", "expires_at", "trusted_uid", "trusted_gid",
    "authority_id", "authoritative_work_item", "mutation_id", "profile", "profile_file",
    "source_head", "activation_bundle_sha256", "precondition_json", "artifact_identities_json",
    "expected_ports_json", "maximum_uses", "activation_authority", "caddy_reload_authority",
    "colima_restart_authority", "wordpress_runtime_mutation_authority", "database_recreation_allowed",
    "volume_recreation_allowed", "ubuntu_authority", "woo_write_authority", "dns_change_allowed",
)


@dataclass(frozen=True, slots=True, init=False)
class PublicStorefrontV2ActivationAuthorization:
    authorization_id: str
    issued_at: str
    expires_at: str
    trusted_uid: int
    trusted_gid: int
    authority_id: str
    authoritative_work_item: str
    mutation_id: str
    profile: str
    profile_file: str
    source_head: str
    activation_bundle_sha256: str
    precondition_json: str
    artifact_identities_json: str
    expected_ports_json: str
    maximum_uses: int
    activation_authority: bool
    caddy_reload_authority: bool
    colima_restart_authority: bool
    wordpress_runtime_mutation_authority: bool
    database_recreation_allowed: bool
    volume_recreation_allowed: bool
    ubuntu_authority: bool
    woo_write_authority: bool
    dns_change_allowed: bool

    def __new__(cls):
        raise TypeError("authorization is issued only by the fixed human boundary")


@dataclass(frozen=True, slots=True, init=False)
class PublicStorefrontV2ActivationConsumptionReceipt:
    authorization_id: str
    issued_at: str
    expires_at: str
    trusted_uid: int
    trusted_gid: int
    authority_id: str
    authoritative_work_item: str
    mutation_id: str
    profile: str
    profile_file: str
    source_head: str
    activation_bundle_sha256: str
    precondition_json: str
    artifact_identities_json: str
    expected_ports_json: str
    maximum_uses: int
    state: ConsumptionState
    activation_authority: bool
    caddy_reload_authority: bool
    colima_restart_authority: bool
    wordpress_runtime_mutation_authority: bool
    database_recreation_allowed: bool
    volume_recreation_allowed: bool
    ubuntu_authority: bool
    woo_write_authority: bool
    dns_change_allowed: bool

    def __new__(cls):
        raise TypeError("receipt is emitted only by durable consumption")


@dataclass(frozen=True, slots=True, init=False)
class PublicStorefrontV2ActivationConsumptionResult:
    receipt: PublicStorefrontV2ActivationConsumptionReceipt

    def __new__(cls):
        raise TypeError("result is emitted only by durable consumption")


def _parse_time(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError
    return result.astimezone(timezone.utc)


def validate_authorization(value: object, *, now: datetime, uid: int, gid: int) -> None:
    if type(value) is not PublicStorefrontV2ActivationAuthorization:
        raise AuthorizationError("exact Activation-02 authorization required")
    if (value.authority_id, value.authoritative_work_item, value.mutation_id,
            value.profile, value.profile_file) != (AUTHORITY_ID, AUTHORITATIVE_WORK_ITEM,
                                                    MUTATION_ID, PROFILE, PROFILE_FILE):
        raise AuthorizationError("authority identity binding invalid")
    if (type(value.authorization_id) is not str or not re.fullmatch(r"[0-9a-f-]{36}", value.authorization_id)
            or type(value.source_head) is not str or not re.fullmatch(r"[0-9a-f]{40}", value.source_head)
            or type(value.activation_bundle_sha256) is not str or not re.fullmatch(r"[0-9a-f]{64}", value.activation_bundle_sha256)):
        raise AuthorizationError("source identity binding invalid")
    try:
        preconditions = parse_preconditions(value.precondition_json)
        if (preconditions["source"]["head"] != value.source_head or
                preconditions["source"]["activation_bundle_sha256"] != value.activation_bundle_sha256 or
                json.loads(value.artifact_identities_json) != preconditions["source"]["artifacts"]):
            raise ValueError
    except Exception:
        raise AuthorizationError("precondition binding invalid") from None
    if (type(value.trusted_uid) is not int or type(value.trusted_gid) is not int or
            (value.trusted_uid, value.trusted_gid) != (uid, gid) or value.maximum_uses != MAXIMUM_USES):
        raise AuthorizationError("trusted identity or maximum uses invalid")
    required_true = ("activation_authority", "caddy_reload_authority")
    required_false = ("colima_restart_authority", "wordpress_runtime_mutation_authority",
                      "database_recreation_allowed", "volume_recreation_allowed", "ubuntu_authority",
                      "woo_write_authority", "dns_change_allowed")
    if any(type(getattr(value, name)) is not bool or getattr(value, name) is not True for name in required_true):
        raise AuthorizationError("activation capability missing")
    if any(type(getattr(value, name)) is not bool or getattr(value, name) is not False for name in required_false):
        raise AuthorizationError("forbidden capability present")
    try:
        issued, expires, current = _parse_time(value.issued_at), _parse_time(value.expires_at), _parse_time(now.isoformat())
    except (TypeError, ValueError):
        raise AuthorizationError("authorization timestamps invalid") from None
    if expires <= issued or (expires - issued).total_seconds() > MAXIMUM_LIFETIME_SECONDS or current < issued or current >= expires:
        raise AuthorizationError("authorization is not currently usable")


def validate_consumption_result(value: object, *, now: datetime, uid: int, gid: int):
    if (type(value) is not PublicStorefrontV2ActivationConsumptionResult or
            type(value.receipt) is not PublicStorefrontV2ActivationConsumptionReceipt or
            value.receipt.state is not ConsumptionState.COMMITTED):
        raise AuthorizationError("receipt is not durably committed")
    auth = object.__new__(PublicStorefrontV2ActivationAuthorization)
    for field in _FIELDS:
        object.__setattr__(auth, field, getattr(value.receipt, field))
    validate_authorization(auth, now=now, uid=uid, gid=gid)
    return value.receipt


def immutable_contract(*, uid: int, gid: int) -> dict[str, object]:
    return {"authority_id": AUTHORITY_ID, "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
            "mutation_id": MUTATION_ID, "profile": PROFILE, "profile_file": PROFILE_FILE,
            "trusted_uid": uid, "trusted_gid": gid, "maximum_uses": MAXIMUM_USES,
            "activation_authority": True, "caddy_reload_authority": True,
            "colima_restart_authority": False, "wordpress_runtime_mutation_authority": False,
            "database_recreation_allowed": False, "volume_recreation_allowed": False,
            "ubuntu_authority": False, "woo_write_authority": False, "dns_change_allowed": False}


__all__ = ["AuthorizationError", "ConsumptionFailure", "ConsumptionState", "PublicStorefrontV2ActivationAuthorization",
           "PublicStorefrontV2ActivationConsumptionReceipt", "PublicStorefrontV2ActivationConsumptionResult",
           "immutable_contract", "validate_authorization", "validate_consumption_result", "_FIELDS"]
