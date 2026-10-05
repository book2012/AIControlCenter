"""SHOP_ORDER_001D zero-network WooCommerce order-create adapter foundation.

The module prepares a closed WooCommerce create-order request and depends only
on injected credential and transport ports. No HTTP/network implementation or
credential-file loader exists here.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
import json
import math
from typing import Protocol

from core.shopping.adapters.woocommerce_order_read import (
    WooCommerceOrderNormalizationError, normalize_woocommerce_order,
)
from core.shopping.order_core.catalog import ResolvedOrderCreateCommand
from core.shopping.order_core.create import (
    OrderCreateAmbiguousFailure, OrderCreateDefinitiveFailure,
)
from core.shopping.order_core.domain import OrderSnapshot


ORDER_DIGEST_META_KEY = "aicc_order_command_digest"


class OrderWriteCredentialUnavailable(RuntimeError):
    pass


class OrderWriteTransportNotSent(RuntimeError):
    """Transport proves no provider write was attempted/applied."""


class OrderWriteTransportUnknownOutcome(RuntimeError):
    """Transport cannot prove whether the provider applied the write."""


class OrderWriteCredential:
    __slots__=("_consumer_key","_consumer_secret")

    def __init__(self,consumer_key:str,consumer_secret:str)->None:
        if type(consumer_key) is not str or not consumer_key:
            raise ValueError("consumer_key is required")
        if type(consumer_secret) is not str or not consumer_secret:
            raise ValueError("consumer_secret is required")
        self._consumer_key=consumer_key;self._consumer_secret=consumer_secret

    @property
    def consumer_key(self)->str:return self._consumer_key

    @property
    def consumer_secret(self)->str:return self._consumer_secret

    def __repr__(self)->str:return "OrderWriteCredential(<redacted>)"
    __str__=__repr__


class OrderWriteCredentialProvider(Protocol):
    def get_credentials(self)->OrderWriteCredential: ...


class UnavailableOrderWriteCredentialProvider:
    def get_credentials(self)->OrderWriteCredential:
        raise OrderWriteCredentialUnavailable("order write credential unavailable")


@dataclass(frozen=True,slots=True)
class PreparedOrderWriteRequest:
    provider:str
    method:str
    path:str
    query:tuple[tuple[str,str],...]
    canonical_body:str
    correlation_id:str
    audit_reference:str


class OrderWriteDisposition(str,Enum):
    APPLIED="APPLIED"
    NOT_APPLIED="NOT_APPLIED"
    UNKNOWN="UNKNOWN"


@dataclass(frozen=True,slots=True)
class OrderWriteTransportResponse:
    status_code:int|None
    payload:Mapping[str,object]
    disposition:OrderWriteDisposition

    def __post_init__(self)->None:
        if self.status_code is not None and (
            type(self.status_code) is not int or not 100 <= self.status_code <= 599
        ):
            raise ValueError("status_code is invalid")
        if not isinstance(self.payload,Mapping):
            raise ValueError("payload must be a mapping")
        if type(self.disposition) is not OrderWriteDisposition:
            raise ValueError("disposition is invalid")


class OrderWriteTransport(Protocol):
    def send(self,request:PreparedOrderWriteRequest,credential:OrderWriteCredential,*,
             timeout_seconds:float)->OrderWriteTransportResponse: ...


class UnavailableOrderWriteTransport:
    def send(self,request:PreparedOrderWriteRequest,credential:OrderWriteCredential,*,
             timeout_seconds:float)->OrderWriteTransportResponse:
        raise OrderWriteTransportNotSent("order write transport unavailable")


class WooCommerceOrderCreateAdapter:
    """Strict request preparation + response normalization; zero network by default."""

    MAX_TIMEOUT_SECONDS=30.0

    def __init__(self,*,credential_provider:OrderWriteCredentialProvider|None=None,
                 transport:OrderWriteTransport|None=None,timeout_seconds:float=10.0)->None:
        if isinstance(timeout_seconds,bool) or not isinstance(timeout_seconds,(int,float)) \
                or not math.isfinite(timeout_seconds) or timeout_seconds<=0 \
                or timeout_seconds>self.MAX_TIMEOUT_SECONDS:
            raise ValueError("timeout_seconds must be positive and bounded")
        self._credentials=credential_provider or UnavailableOrderWriteCredentialProvider()
        self._transport=transport or UnavailableOrderWriteTransport()
        self._timeout=float(timeout_seconds)

    def prepare(self,command:ResolvedOrderCreateCommand)->PreparedOrderWriteRequest:
        if type(command) is not ResolvedOrderCreateCommand:
            raise TypeError("command must be a ResolvedOrderCreateCommand")
        line_items=[]
        for item in command.line_items:
            line={"product_id":item.provider_product_id,"quantity":item.quantity}
            if item.provider_variation_id:
                line["variation_id"]=item.provider_variation_id
            line_items.append(line)
        body={
            "status":"pending",
            "line_items":line_items,
            "meta_data":[{"key":ORDER_DIGEST_META_KEY,"value":command.command_digest}],
        }
        canonical=json.dumps(body,sort_keys=True,separators=(",",":"),
                             ensure_ascii=False,allow_nan=False)
        return PreparedOrderWriteRequest(
            provider="WOOCOMMERCE",method="POST",path="/wp-json/wc/v3/orders",
            query=(),canonical_body=canonical,correlation_id=command.correlation_id,
            audit_reference=command.audit_reference,
        )

    @staticmethod
    def _verify_digest_marker(payload:Mapping[str,object],expected:str)->None:
        raw=payload.get("meta_data")
        if type(raw) is not list:
            raise OrderCreateAmbiguousFailure("PROVIDER_METADATA_INVALID")
        markers=[]
        for item in raw:
            if isinstance(item,Mapping) and item.get("key")==ORDER_DIGEST_META_KEY:
                markers.append(item.get("value"))
        if markers != [expected]:
            raise OrderCreateAmbiguousFailure("PROVIDER_OPERATION_BINDING_MISMATCH")

    def create_order(self,command:ResolvedOrderCreateCommand)->OrderSnapshot:
        request=self.prepare(command)
        try:
            credential=self._credentials.get_credentials()
        except OrderWriteCredentialUnavailable as exc:
            raise OrderCreateDefinitiveFailure("WRITE_CREDENTIAL_UNAVAILABLE") from exc
        except Exception as exc:
            raise OrderCreateDefinitiveFailure("WRITE_CREDENTIAL_UNAVAILABLE") from exc
        if type(credential) is not OrderWriteCredential:
            raise OrderCreateDefinitiveFailure("WRITE_CREDENTIAL_INVALID")
        try:
            response=self._transport.send(request,credential,timeout_seconds=self._timeout)
        except OrderWriteTransportNotSent as exc:
            raise OrderCreateDefinitiveFailure("WRITE_TRANSPORT_NOT_SENT") from exc
        except OrderWriteTransportUnknownOutcome as exc:
            raise OrderCreateAmbiguousFailure("WRITE_TRANSPORT_UNKNOWN") from exc
        except Exception as exc:
            raise OrderCreateAmbiguousFailure("WRITE_TRANSPORT_UNKNOWN") from exc
        if type(response) is not OrderWriteTransportResponse:
            raise OrderCreateAmbiguousFailure("PROVIDER_RESPONSE_INVALID")
        if response.disposition is OrderWriteDisposition.NOT_APPLIED:
            raise OrderCreateDefinitiveFailure("PROVIDER_NOT_APPLIED")
        if response.disposition is OrderWriteDisposition.UNKNOWN:
            raise OrderCreateAmbiguousFailure("PROVIDER_OUTCOME_UNKNOWN")
        if response.status_code != 201:
            raise OrderCreateAmbiguousFailure("PROVIDER_RESPONSE_STATUS_UNEXPECTED")
        payload=response.payload
        self._verify_digest_marker(payload,command.command_digest)
        if payload.get("status")!="pending":
            raise OrderCreateAmbiguousFailure("PROVIDER_STATUS_UNEXPECTED")
        if payload.get("customer_id")!=0:
            raise OrderCreateAmbiguousFailure("PROVIDER_CUSTOMER_UNEXPECTED")
        try:
            return normalize_woocommerce_order(payload)
        except WooCommerceOrderNormalizationError as exc:
            raise OrderCreateAmbiguousFailure("PROVIDER_RESPONSE_INVALID") from exc


__all__=(
    "ORDER_DIGEST_META_KEY","OrderWriteCredential","OrderWriteCredentialProvider",
    "OrderWriteCredentialUnavailable","OrderWriteDisposition","OrderWriteTransport",
    "OrderWriteTransportNotSent","OrderWriteTransportResponse",
    "OrderWriteTransportUnknownOutcome","PreparedOrderWriteRequest",
    "UnavailableOrderWriteCredentialProvider","UnavailableOrderWriteTransport",
    "WooCommerceOrderCreateAdapter",
)
