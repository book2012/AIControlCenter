from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
import json

import pytest

from core.shopping.product_drafts.deployment import (
    CommerceOperation, CommerceTransportResponse, ControlledPlanRejectedError,
    ControlledWritePlan, ReconciliationStatus, SecretSafeCredential,
    UnavailableCommerceWriteTransport, UnavailableCredentialProvider, WriteMode,
    WooCommerceControlledWriteAdapter,
)
from core.shopping.product_drafts.models import ProductDraftRevision, ProposedFields, StockStatus
from core.shopping.product_drafts.serialization import sha256_digest
from core.shopping.product_drafts.values import ActorReference, ActorType, Reference

NOW = datetime(2026, 8, 3, 0, tzinfo=timezone.utc)
DIGEST = "sha256:" + "a" * 64
SECRET = "secret-never-project"


def plan(fields=None):
    fields = fields or ProposedFields(name="Updated", regular_price=Decimal("12.50"))
    seed = dict(schema_version="1.0.0", mode=WriteMode.FAKE,
        operation=CommerceOperation.UPDATE_PRODUCT, draft_id="draft-1",
        revision_id="revision-2", revision_number=2, deployment_intent_id="intent-1",
        target_product_identifier="9", expected_source_digest=DIGEST,
        payload_digest=sha256_digest(fields), actor_reference=ActorReference("human", ActorType.HUMAN),
        authorization_reference="auth-1", authorization_policy_reference="policy-1",
        audit_reference="audit-1", correlation_id="correlation-1", idempotency_key="key-1",
        requested_at=NOW, evaluated_at=NOW)
    return ControlledWritePlan(**seed, plan_digest=sha256_digest(seed), proposed_fields=fields)


class Credentials:
    def __init__(self): self.calls = 0
    def get_credentials(self):
        self.calls += 1
        return SecretSafeCredential("consumer", SECRET)


class Intercepted:
    def __init__(self, payload=None, status=200):
        self.calls = []
        self.payload = payload or {"id": 9, "name": "Updated", "regular_price": "12.50"}
        self.status = status
    def send(self, request, credential, *, timeout_seconds):
        self.calls.append((request, credential, timeout_seconds))
        return CommerceTransportResponse(self.status, self.payload)


def adapter(transport=None, **kwargs):
    return WooCommerceControlledWriteAdapter(credential_provider=Credentials(),
        transport=transport or Intercepted(), **kwargs)


def test_shop_03b1_credential_repr_str_and_json_are_redacted():
    value = SecretSafeCredential("key", SECRET)
    assert SECRET not in repr(value) and SECRET not in str(value)
    assert SECRET not in json.dumps({"credential": repr(value)})


def test_shop_03b1_defaults_fail_closed():
    with pytest.raises(Exception, match="credential_unavailable"):
        UnavailableCredentialProvider().get_credentials()
    with pytest.raises(Exception, match="transport_unavailable"):
        UnavailableCommerceWriteTransport().send(None, SecretSafeCredential("k", "s"), timeout_seconds=1)
    result = WooCommerceControlledWriteAdapter().apply(plan(), completed_at=NOW)
    assert result.reconciliation_status is ReconciliationStatus.CREDENTIAL_UNAVAILABLE


def test_shop_03b1_credential_is_separate_and_request_has_no_secret():
    transport = Intercepted()
    result = adapter(transport).apply(plan(), completed_at=NOW)
    request, credential, timeout = transport.calls[0]
    assert credential.consumer_secret == SECRET and timeout == 10.0
    safe = request.path + repr(request.query) + request.canonical_body + repr(result.as_json_safe())
    assert SECRET not in safe and request.query == () and "consumer" not in safe


def test_shop_03b1_target_operation_allowlist_and_canonical_body():
    fields = ProposedFields(name="N", description="D", sku="S", regular_price=Decimal("10.00"),
        sale_price=Decimal("9.00"), inventory_quantity=3, stock_status=StockStatus.IN_STOCK,
        categories=(Reference("4", "ignored"),), tags=(Reference("5"),),
        image_references=(Reference("6"),))
    request = adapter().prepare(plan(fields))
    assert request.method == "PUT" and request.path.endswith("/products/9")
    assert json.loads(request.canonical_body) == {"name":"N", "description":"D", "sku":"S",
        "regular_price":"10.00", "sale_price":"9.00", "stock_quantity":3,
        "stock_status":"instock", "categories":[{"id":"4"}], "tags":[{"id":"5"}],
        "images":[{"id":"6"}]}
    assert request.canonical_body == json.dumps(json.loads(request.canonical_body), sort_keys=True,
        separators=(",", ":"), ensure_ascii=False)
    assert "ignored" not in request.canonical_body


@pytest.mark.parametrize("timeout", [0, -1, 31, float("inf"), True, None])
def test_shop_03b1_timeout_is_positive_and_bounded(timeout):
    with pytest.raises((ValueError, TypeError)):
        WooCommerceControlledWriteAdapter(timeout_seconds=timeout)


def test_shop_03b1_rejects_raw_revision_mapping_incomplete_and_bad_target():
    live = adapter()
    with pytest.raises(TypeError): live.prepare({})
    with pytest.raises(TypeError): live.prepare(object.__new__(ProductDraftRevision))
    with pytest.raises(ControlledPlanRejectedError, match="incomplete"):
        live.prepare(replace(plan(), proposed_fields=None))
    with pytest.raises(ControlledPlanRejectedError, match="target_identifier"):
        live.prepare(replace(plan(), target_product_identifier="../9"))


def test_shop_03b1_rejects_unsupported_operation_and_unbound_payload():
    bad = plan()
    object.__setattr__(bad, "operation", "CREATE_PRODUCT")
    with pytest.raises(ControlledPlanRejectedError, match="operation_unsupported"):
        adapter().prepare(bad)
    with pytest.raises(ControlledPlanRejectedError, match="controlled_plan"):
        adapter().prepare(replace(plan(), payload_digest=DIGEST))


def test_shop_03b1_intercepted_instances_are_isolated():
    first, second = Intercepted(), Intercepted()
    adapter(first).apply(plan(), completed_at=NOW)
    assert len(first.calls) == 1 and second.calls == []


def test_shop_03b1_normalization_is_deterministic_allowlisted_and_matched():
    payload = {"regular_price":"12.50", "id":9, "name":"Updated", "cookie":SECRET,
               "consumer_secret":SECRET, "arbitrary":{"x":1}}
    one = adapter(Intercepted(payload)).apply(plan(), completed_at=NOW)
    two = adapter(Intercepted(dict(reversed(list(payload.items()))))).apply(plan(), completed_at=NOW)
    assert one == two and one.reconciliation_status is ReconciliationStatus.MATCHED
    projection = dict(one.as_json_safe())
    json.dumps(one.as_json_safe())
    assert projection["live_write_performed"] is False and projection["mode"] == "INTERCEPTED_VALIDATION"
    assert SECRET not in json.dumps(projection)
    assert dict(one.selected_safe_product_fields) == {"name":"Updated", "regular_price":"12.50"}


def test_shop_03b1_mismatch_fields_stable_and_remote_identifier_mismatch():
    result = adapter(Intercepted({"id":9, "name":"Wrong"})).apply(plan(), completed_at=NOW)
    assert result.reconciliation_status is ReconciliationStatus.MISMATCH
    assert result.mismatch_fields == ("name", "regular_price")
    result = adapter(Intercepted({"id":10, "name":"Updated", "regular_price":"12.50"})).apply(plan(), completed_at=NOW)
    assert result.reconciliation_status is ReconciliationStatus.REMOTE_IDENTIFIER_MISMATCH


@pytest.mark.parametrize("response", [CommerceTransportResponse(500, {"id":9}),
    CommerceTransportResponse(200, {}), CommerceTransportResponse(200, {"id":True})])
def test_shop_03b1_invalid_response_is_rejected(response):
    transport = Intercepted()
    transport.send = lambda *args, **kwargs: response
    result = adapter(transport).apply(plan(), completed_at=NOW)
    assert result.reconciliation_status is ReconciliationStatus.RESPONSE_INVALID
    assert result.live_write_performed is False


def test_shop_03b1_transport_unavailable_has_safe_result():
    result = adapter(UnavailableCommerceWriteTransport()).apply(plan(), completed_at=NOW)
    assert result.reconciliation_status is ReconciliationStatus.TRANSPORT_UNAVAILABLE
    assert result.live_write_performed is False and result.response_digest is None
