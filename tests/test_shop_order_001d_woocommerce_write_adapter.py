from __future__ import annotations

from datetime import datetime,timezone
from decimal import Decimal
import json

import pytest

from core.shopping.adapters.woocommerce_order_write import (
    ORDER_DIGEST_META_KEY,OrderWriteCredential,OrderWriteDisposition,
    OrderWriteTransportNotSent,OrderWriteTransportResponse,
    OrderWriteTransportUnknownOutcome,UnavailableOrderWriteCredentialProvider,
    UnavailableOrderWriteTransport,WooCommerceOrderCreateAdapter,
)
from core.shopping.order_core import (
    OrderCreateAmbiguousFailure,OrderCreateDefinitiveFailure,
    ResolvedOrderCreateCommand,ResolvedOrderCreateLine,
)

NOW=datetime(2026,10,5,13,0,tzinfo=timezone.utc)
DIGEST="a"*64
SECRET="secret-never-project"

def command(*,variation=0):
    return ResolvedOrderCreateCommand(
        customer_id="AG-CUS-"+"1"*12+"4"+"1"*3+"8"+"1"*15,
        line_items=(ResolvedOrderCreateLine("123","456" if variation else None,123,variation,2),),
        command_digest=DIGEST,correlation_id="corr-001",audit_reference="audit-001")

def response_payload(*,digest=DIGEST,status="pending",customer_id=0,product_id=123,
                     variation_id=0,quantity=2):
    return {
        "id":501,"number":"501","status":status,"currency":"KRW","customer_id":customer_id,
        "line_items":[{"id":7001,"product_id":product_id,"variation_id":variation_id,
                       "sku":None,"name":"Product","quantity":quantity,"subtotal":"20000",
                       "total":"20000","total_tax":"0"}],
        "total":"20000","total_tax":"0",
        "date_created_gmt":"2026-10-05T13:00:00Z",
        "date_modified_gmt":"2026-10-05T13:00:00Z","version":"10.0.0",
        "meta_data":[{"id":1,"key":ORDER_DIGEST_META_KEY,"value":digest}],
    }

class Credentials:
    def __init__(self):self.calls=0
    def get_credentials(self):
        self.calls+=1;return OrderWriteCredential("consumer",SECRET)

class Intercepted:
    def __init__(self,response=None,error=None):
        self.response=response or OrderWriteTransportResponse(
            201,response_payload(),OrderWriteDisposition.APPLIED)
        self.error=error;self.calls=[]
    def send(self,request,credential,*,timeout_seconds):
        self.calls.append((request,credential,timeout_seconds))
        if self.error:raise self.error
        return self.response

def adapter(transport=None,credentials=None,**kwargs):
    return WooCommerceOrderCreateAdapter(
        credential_provider=credentials or Credentials(),
        transport=transport or Intercepted(),**kwargs)

def test_defaults_are_zero_network_fail_closed():
    with pytest.raises(Exception):UnavailableOrderWriteCredentialProvider().get_credentials()
    with pytest.raises(OrderWriteTransportNotSent):
        UnavailableOrderWriteTransport().send(None,OrderWriteCredential("k","s"),timeout_seconds=1)
    with pytest.raises(OrderCreateDefinitiveFailure,match="WRITE_CREDENTIAL_UNAVAILABLE"):
        WooCommerceOrderCreateAdapter().create_order(command())

def test_credential_repr_is_redacted_and_request_contains_no_secret():
    credential=OrderWriteCredential("consumer",SECRET)
    assert SECRET not in repr(credential) and SECRET not in str(credential)
    transport=Intercepted();result=adapter(transport).create_order(command())
    request,used,timeout=transport.calls[0]
    safe=request.path+repr(request.query)+request.canonical_body+repr(result)
    assert used.consumer_secret==SECRET and timeout==10.0
    assert SECRET not in safe and "consumer" not in safe

def test_prepared_request_is_closed_canonical_and_unpaid_pending():
    request=adapter().prepare(command(variation=456))
    assert request.method=="POST" and request.path=="/wp-json/wc/v3/orders" and request.query==()
    body=json.loads(request.canonical_body)
    assert body=={
        "status":"pending",
        "line_items":[{"product_id":123,"variation_id":456,"quantity":2}],
        "meta_data":[{"key":ORDER_DIGEST_META_KEY,"value":DIGEST}],
    }
    forbidden={"price","subtotal","total","tax","billing","shipping","payment_method",
               "payment_method_title","transaction_id","set_paid","coupon_lines","customer_id"}
    assert forbidden.isdisjoint(body)
    assert request.canonical_body==json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False)

def test_success_response_normalizes_to_existing_order_snapshot():
    result=adapter().create_order(command())
    assert result.provider=="woocommerce" and result.provider_order_id==501
    assert result.status=="pending" and result.customer_reference is None
    assert result.line_items[0].product_id==123 and result.line_items[0].quantity==2

@pytest.mark.parametrize("timeout",[0,-1,31,float("inf"),True,None])
def test_timeout_is_positive_bounded_and_not_boolean(timeout):
    with pytest.raises((ValueError,TypeError)):WooCommerceOrderCreateAdapter(timeout_seconds=timeout)

def test_transport_not_sent_is_definitive_but_unknown_transport_is_ambiguous():
    with pytest.raises(OrderCreateDefinitiveFailure,match="WRITE_TRANSPORT_NOT_SENT"):
        adapter(Intercepted(error=OrderWriteTransportNotSent())).create_order(command())
    with pytest.raises(OrderCreateAmbiguousFailure,match="WRITE_TRANSPORT_UNKNOWN"):
        adapter(Intercepted(error=OrderWriteTransportUnknownOutcome())).create_order(command())

def test_explicit_transport_disposition_controls_no_write_vs_unknown():
    not_applied=OrderWriteTransportResponse(400,{},OrderWriteDisposition.NOT_APPLIED)
    with pytest.raises(OrderCreateDefinitiveFailure,match="PROVIDER_NOT_APPLIED"):
        adapter(Intercepted(not_applied)).create_order(command())
    unknown=OrderWriteTransportResponse(None,{},OrderWriteDisposition.UNKNOWN)
    with pytest.raises(OrderCreateAmbiguousFailure,match="PROVIDER_OUTCOME_UNKNOWN"):
        adapter(Intercepted(unknown)).create_order(command())

@pytest.mark.parametrize("payload,code",[
    (response_payload(digest="b"*64),"PROVIDER_OPERATION_BINDING_MISMATCH"),
    ({**response_payload(),"meta_data":[]},"PROVIDER_OPERATION_BINDING_MISMATCH"),
    ({**response_payload(),"status":"processing"},"PROVIDER_STATUS_UNEXPECTED"),
    ({**response_payload(),"customer_id":9},"PROVIDER_CUSTOMER_UNEXPECTED"),
])
def test_applied_response_must_match_operation_and_safe_order_state(payload,code):
    response=OrderWriteTransportResponse(201,payload,OrderWriteDisposition.APPLIED)
    with pytest.raises(OrderCreateAmbiguousFailure,match=code):
        adapter(Intercepted(response)).create_order(command())

def test_malformed_or_non_201_applied_response_is_ambiguous():
    with pytest.raises(OrderCreateAmbiguousFailure,match="STATUS_UNEXPECTED"):
        adapter(Intercepted(OrderWriteTransportResponse(
            200,response_payload(),OrderWriteDisposition.APPLIED))).create_order(command())
    bad={**response_payload()};bad.pop("number")
    with pytest.raises(OrderCreateAmbiguousFailure,match="RESPONSE_INVALID"):
        adapter(Intercepted(OrderWriteTransportResponse(
            201,bad,OrderWriteDisposition.APPLIED))).create_order(command())

def test_response_arbitrary_fields_and_secrets_do_not_cross_order_projection():
    payload={**response_payload(),"consumer_secret":SECRET,"cookie":SECRET,
             "billing":{"email":"secret@example.test"},"arbitrary":{"x":1}}
    result=adapter(Intercepted(OrderWriteTransportResponse(
        201,payload,OrderWriteDisposition.APPLIED))).create_order(command())
    assert SECRET not in repr(result) and "secret@example.test" not in repr(result)

def test_adapter_source_has_no_http_client_or_network_implementation():
    from pathlib import Path
    source=Path("core/shopping/adapters/woocommerce_order_write.py").read_text()
    for token in ("requests.","httpx.","HTTPSConnection","urllib.request","socket.","Session("):
        assert token not in source
