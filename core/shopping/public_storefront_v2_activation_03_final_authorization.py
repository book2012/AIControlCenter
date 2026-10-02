"""One-shot, non-reusable authority for public storefront V2 activation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re

from core.shopping.public_storefront_v2_activation_03_final_reconciliation import (
    AUTHORITY_ID, AUTHORITATIVE_WORK_ITEM, MAXIMUM_LIFETIME_SECONDS, MAXIMUM_USES,
    MUTATION_ID, PROFILE, PROFILE_FILE, parse_preconditions,
)


class AuthorizationError(RuntimeError):
    pass


class ConsumptionFailure(AuthorizationError):
    def __init__(self, state: str):
        super().__init__("AUTHORIZATION_CONSUMPTION_FAILED")
        self.state = state


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
    lifecycle_authority: bool
    caddy_reload_authority: bool
    production_write_authority: bool
    ubuntu_authority: bool
    business_mutation_authority: bool
    database_recreation_allowed: bool
    volume_recreation_allowed: bool
    dns_change_allowed: bool
    woo_write_authority: bool

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
    state: str
    activation_authority: bool
    lifecycle_authority: bool
    caddy_reload_authority: bool
    production_write_authority: bool
    ubuntu_authority: bool
    business_mutation_authority: bool
    database_recreation_allowed: bool
    volume_recreation_allowed: bool
    dns_change_allowed: bool
    woo_write_authority: bool

    def __new__(cls):
        raise TypeError("receipt is emitted only by durable consumption")


@dataclass(frozen=True, slots=True, init=False)
class PublicStorefrontV2ActivationConsumptionResult:
    receipt: PublicStorefrontV2ActivationConsumptionReceipt

    def __new__(cls):
        raise TypeError("result is emitted only by durable consumption")


def validate_authorization(value: object, *, now: datetime, uid: int, gid: int) -> None:
    if type(value) is not PublicStorefrontV2ActivationAuthorization:
        raise AuthorizationError("exact public storefront V2 authorization required")
    if (value.authority_id != AUTHORITY_ID or
            value.authoritative_work_item != AUTHORITATIVE_WORK_ITEM or
            value.mutation_id != MUTATION_ID or value.profile != PROFILE or
            value.profile_file != PROFILE_FILE):
        raise AuthorizationError("authority identity binding invalid")
    if (type(value.source_head) is not str or re.fullmatch(r"[0-9a-f]{40}", value.source_head) is None or
            type(value.activation_bundle_sha256) is not str or
            re.fullmatch(r"[0-9a-f]{64}", value.activation_bundle_sha256) is None):
        raise AuthorizationError("source identity binding invalid")
    try:
        preconditions = parse_preconditions(value.precondition_json)
        if (preconditions["source"]["head"] != value.source_head or
                preconditions["source"]["activation_bundle_sha256"] != value.activation_bundle_sha256 or
                json.loads(value.artifact_identities_json) != preconditions["source"]["artifacts"]):
            raise ValueError
    except Exception:
        raise AuthorizationError("precondition binding invalid") from None
    if type(value.authorization_id) is not str or not value.authorization_id:
        raise AuthorizationError("authorization id invalid")
    if (type(value.trusted_uid) is not int or type(value.trusted_gid) is not int or
            (value.trusted_uid, value.trusted_gid) != (uid, gid)):
        raise AuthorizationError("trusted identity mismatch")
    if type(value.maximum_uses) is not int or value.maximum_uses != MAXIMUM_USES:
        raise AuthorizationError("maximum uses invalid")
    required_true = ("activation_authority", "lifecycle_authority", "caddy_reload_authority")
    required_false = ("production_write_authority", "ubuntu_authority",
                      "business_mutation_authority", "database_recreation_allowed",
                      "volume_recreation_allowed", "dns_change_allowed", "woo_write_authority")
    if any(type(getattr(value, name)) is not bool or getattr(value, name) is not True for name in required_true):
        raise AuthorizationError("activation capability missing")
    if any(type(getattr(value, name)) is not bool or getattr(value, name) is not False for name in required_false):
        raise AuthorizationError("forbidden capability present")
    try:
        issued = datetime.fromisoformat(value.issued_at)
        expires = datetime.fromisoformat(value.expires_at)
    except (TypeError, ValueError):
        raise AuthorizationError("authorization timestamps invalid") from None
    if (issued.tzinfo is None or expires.tzinfo is None or now.tzinfo is None or
            expires <= issued or
            (expires - issued).total_seconds() > MAXIMUM_LIFETIME_SECONDS or
            now.astimezone(timezone.utc) < issued.astimezone(timezone.utc) or
            now.astimezone(timezone.utc) >= expires.astimezone(timezone.utc)):
        raise AuthorizationError("authorization is not currently usable")


def validate_consumption_result(value: object, *, now: datetime, uid: int, gid: int):
    if (type(value) is not PublicStorefrontV2ActivationConsumptionResult or
            type(value.receipt) is not PublicStorefrontV2ActivationConsumptionReceipt or
            value.receipt.state != "COMMITTED"):
        raise AuthorizationError("receipt is not durably committed")
    receipt = value.receipt
    authorization = object.__new__(PublicStorefrontV2ActivationAuthorization)
    for name in PublicStorefrontV2ActivationAuthorization.__dataclass_fields__:
        object.__setattr__(authorization, name, getattr(receipt, name))
    validate_authorization(authorization, now=now, uid=uid, gid=gid)
    return receipt


def immutable_contract(*, uid: int, gid: int) -> dict[str, object]:
    return {
        "authority_id": AUTHORITY_ID,
        "authoritative_work_item": AUTHORITATIVE_WORK_ITEM,
        "mutation_id": MUTATION_ID,
        "profile": PROFILE,
        "profile_file": PROFILE_FILE,
        "trusted_uid": uid,
        "trusted_gid": gid,
        "maximum_uses": MAXIMUM_USES,
        "activation_authority": True,
        "lifecycle_authority": True,
        "caddy_reload_authority": True,
        "production_write_authority": False,
        "ubuntu_authority": False,
        "business_mutation_authority": False,
        "database_recreation_allowed": False,
        "volume_recreation_allowed": False,
        "dns_change_allowed": False,
        "woo_write_authority": False,
    }


__all__ = [
    "AuthorizationError", "ConsumptionFailure", "PublicStorefrontV2ActivationAuthorization",
    "PublicStorefrontV2ActivationConsumptionReceipt", "PublicStorefrontV2ActivationConsumptionResult",
    "immutable_contract", "validate_authorization", "validate_consumption_result",
]
