"""Intercepted-only WooCommerce controlled product update adapter."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping

from ...models import ProductDraftRevision, ProposedFields, Reference, StockStatus
from ...serialization import sha256_digest
from ...values import require_utc
from ..models import CommerceOperation, ControlledWritePlan, WriteMode
from .credentials import CredentialProvider, UnavailableCredentialProvider
from .credentials import SecretSafeCredential
from .errors import (ControlledPlanRejectedError, CredentialUnavailableError,
                     TransportUnavailableError)
from .transport import (CommerceTransportResponse, CommerceWriteTransport,
                        PreparedCommerceWriteRequest,
                        UnavailableCommerceWriteTransport)


class ReconciliationStatus(str, Enum):
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    REMOTE_IDENTIFIER_MISMATCH = "REMOTE_IDENTIFIER_MISMATCH"
    RESPONSE_INVALID = "RESPONSE_INVALID"
    TRANSPORT_UNAVAILABLE = "TRANSPORT_UNAVAILABLE"
    CREDENTIAL_UNAVAILABLE = "CREDENTIAL_UNAVAILABLE"


FIELD_ALLOWLIST = ("name", "description", "sku", "regular_price", "sale_price",
                   "inventory_quantity", "stock_status", "categories", "tags",
                   "image_references")
REMOTE_KEYS = {"inventory_quantity": "stock_quantity", "image_references": "images"}


@dataclass(frozen=True, slots=True)
class ControlledCommerceWriteResult:
    provider: str
    operation: str
    target_product_identifier: str
    remote_product_identifier: str | None
    response_status: int | None
    response_digest: str | None
    selected_safe_product_fields: tuple[tuple[str, object], ...]
    completed_at: datetime
    reconciliation_status: ReconciliationStatus
    mismatch_fields: tuple[str, ...]
    correlation_id: str
    audit_reference: str
    mode: str = "INTERCEPTED_VALIDATION"
    live_write_performed: bool = False

    def as_json_safe(self) -> Mapping[str, object]:
        return {
            "provider": self.provider, "operation": self.operation,
            "target_product_identifier": self.target_product_identifier,
            "remote_product_identifier": self.remote_product_identifier,
            "response_status": self.response_status,
            "response_digest": self.response_digest,
            "selected_safe_product_fields": dict(self.selected_safe_product_fields),
            "completed_at": self.completed_at.isoformat().replace("+00:00", "Z"),
            "live_write_performed": False,
            "reconciliation_status": self.reconciliation_status.value,
            "mismatch_fields": list(self.mismatch_fields),
            "correlation_id": self.correlation_id,
            "audit_reference": self.audit_reference, "mode": self.mode,
        }


def _value(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, StockStatus):
        return {StockStatus.IN_STOCK: "instock", StockStatus.OUT_OF_STOCK: "outofstock",
                StockStatus.ON_BACKORDER: "onbackorder"}[value]
    if isinstance(value, tuple) and all(isinstance(item, Reference) for item in value):
        return [{"id": item.id} for item in value]
    return value


def supported_product_fields(fields: ProposedFields) -> dict[str, object]:
    if not isinstance(fields, ProposedFields):
        raise ControlledPlanRejectedError("proposed_fields_invalid")
    result: dict[str, object] = {}
    for name in FIELD_ALLOWLIST:
        value = getattr(fields, name)
        if value is not None and value != ():
            result[REMOTE_KEYS.get(name, name)] = _value(value)
    return result


class WooCommerceControlledWriteAdapter:
    MAX_TIMEOUT_SECONDS = 30.0

    def __init__(self, *, credential_provider: CredentialProvider | None = None,
                 transport: CommerceWriteTransport | None = None,
                 timeout_seconds: float = 10.0) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) \
                or not math.isfinite(timeout_seconds) or timeout_seconds <= 0 \
                or timeout_seconds > self.MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds must be positive and bounded")
        self._credentials = credential_provider or UnavailableCredentialProvider()
        self._transport = transport or UnavailableCommerceWriteTransport()
        self._timeout = float(timeout_seconds)

    def prepare(self, plan: ControlledWritePlan) -> PreparedCommerceWriteRequest:
        if isinstance(plan, ProductDraftRevision) or not isinstance(plan, ControlledWritePlan):
            raise TypeError("plan must be an immutable ControlledWritePlan")
        if plan.operation is not CommerceOperation.UPDATE_PRODUCT:
            raise ControlledPlanRejectedError("operation_unsupported")
        if not isinstance(plan.mode, WriteMode):
            raise ControlledPlanRejectedError("controlled_plan_mode_invalid")
        if not plan.target_product_identifier or not plan.target_product_identifier.isdigit() \
                or int(plan.target_product_identifier) <= 0:
            raise ControlledPlanRejectedError("target_identifier_invalid")
        if plan.proposed_fields is None:
            raise ControlledPlanRejectedError("controlled_plan_incomplete")
        seed = {
            "schema_version": plan.schema_version, "mode": plan.mode.value,
            "operation": plan.operation.value, "draft_id": plan.draft_id,
            "revision_id": plan.revision_id, "revision_number": plan.revision_number,
            "deployment_intent_id": plan.deployment_intent_id,
            "target_product_identifier": plan.target_product_identifier,
            "expected_source_digest": plan.expected_source_digest,
            "payload_digest": plan.payload_digest, "actor_reference": plan.actor_reference,
            "authorization_reference": plan.authorization_reference,
            "authorization_policy_reference": plan.authorization_policy_reference,
            "audit_reference": plan.audit_reference, "correlation_id": plan.correlation_id,
            "idempotency_key": plan.idempotency_key, "requested_at": plan.requested_at,
            "evaluated_at": plan.evaluated_at,
        }
        if sha256_digest(seed) != plan.plan_digest:
            raise ControlledPlanRejectedError("controlled_plan_digest_invalid")
        body = supported_product_fields(plan.proposed_fields)
        if not body or sha256_digest(plan.proposed_fields) != plan.payload_digest:
            raise ControlledPlanRejectedError("controlled_plan_payload_binding_invalid")
        canonical = json.dumps(body, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False)
        return PreparedCommerceWriteRequest(
            "WOOCOMMERCE", "PUT", "/wp-json/wc/v3/products/" + plan.target_product_identifier,
            (), canonical, plan.correlation_id, plan.audit_reference)

    def apply(self, plan: ControlledWritePlan, *, completed_at: datetime) -> ControlledCommerceWriteResult:
        require_utc(completed_at, "completed_at")
        request = self.prepare(plan)
        try:
            credential = self._credentials.get_credentials()
        except CredentialUnavailableError:
            return self._unavailable(plan, completed_at, ReconciliationStatus.CREDENTIAL_UNAVAILABLE)
        except Exception:
            return self._unavailable(plan, completed_at, ReconciliationStatus.CREDENTIAL_UNAVAILABLE)
        if not isinstance(credential, SecretSafeCredential):
            return self._unavailable(plan, completed_at, ReconciliationStatus.CREDENTIAL_UNAVAILABLE)
        try:
            response = self._transport.send(request, credential, timeout_seconds=self._timeout)
        except TransportUnavailableError:
            return self._unavailable(plan, completed_at, ReconciliationStatus.TRANSPORT_UNAVAILABLE)
        except Exception:
            return self._unavailable(plan, completed_at, ReconciliationStatus.TRANSPORT_UNAVAILABLE)
        return self._normalize(plan, response, completed_at)

    def _unavailable(self, plan: ControlledWritePlan, completed_at: datetime,
                     status: ReconciliationStatus) -> ControlledCommerceWriteResult:
        return ControlledCommerceWriteResult("WOOCOMMERCE", plan.operation.value,
            plan.target_product_identifier, None, None, None, (), completed_at, status, (),
            plan.correlation_id, plan.audit_reference)

    def _normalize(self, plan: ControlledWritePlan, response: CommerceTransportResponse,
                   completed_at: datetime) -> ControlledCommerceWriteResult:
        if not isinstance(response, CommerceTransportResponse) or type(response.status_code) is not int \
                or not 200 <= response.status_code < 300 or not isinstance(response.payload, Mapping):
            return self._invalid(plan, completed_at)
        payload = response.payload
        remote_id = payload.get("id")
        if isinstance(remote_id, bool) or not isinstance(remote_id, (str, int)):
            return self._invalid(plan, completed_at, response.status_code)
        remote_identifier = str(remote_id)
        expected = supported_product_fields(plan.proposed_fields)  # type: ignore[arg-type]
        selected = tuple((key, payload[key]) for key in sorted(expected) if key in payload)
        digest_payload = {"status_code": response.status_code,
                          "remote_product_identifier": remote_identifier,
                          "selected_safe_product_fields": dict(selected)}
        try:
            canonical_response = json.dumps(digest_payload, sort_keys=True,
                separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError):
            return self._invalid(plan, completed_at, response.status_code)
        digest = "sha256:" + hashlib.sha256(canonical_response.encode()).hexdigest()
        mismatches = tuple(sorted(key for key, value in expected.items()
                                  if key not in payload or payload[key] != value))
        if remote_identifier != plan.target_product_identifier:
            status = ReconciliationStatus.REMOTE_IDENTIFIER_MISMATCH
        elif mismatches:
            status = ReconciliationStatus.MISMATCH
        else:
            status = ReconciliationStatus.MATCHED
        return ControlledCommerceWriteResult("WOOCOMMERCE", plan.operation.value,
            plan.target_product_identifier, remote_identifier, response.status_code, digest,
            selected, completed_at, status, mismatches, plan.correlation_id, plan.audit_reference)

    def _invalid(self, plan: ControlledWritePlan, completed_at: datetime,
                 response_status: int | None = None) -> ControlledCommerceWriteResult:
        return ControlledCommerceWriteResult("WOOCOMMERCE", plan.operation.value,
            plan.target_product_identifier, None, response_status, None, (), completed_at,
            ReconciliationStatus.RESPONSE_INVALID, (), plan.correlation_id, plan.audit_reference)
