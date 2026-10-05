"""Explicit governed WooCommerce writer/reconciliation candidate; no activation.

No credential loading, implicit customer mapping, runtime defaults, retries,
payment, refund or fulfillment mutation is provided here.
"""
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from urllib.parse import urlsplit

from pydantic import SecretStr
import requests

from core.shopping.customer_identity import require_utc
from core.shopping.adapters.woocommerce_order_read import normalize_woocommerce_order
from .catalog import ResolvedOrderCreateCommand
from .create import (OrderCreateAmbiguousFailure, OrderCreateDefinitiveFailure, OrderCreateResult,
                     _customer_id, _session_id, _digest, _idempotency_key, _reference)
from .ledger import SQLiteOrderCreateLedger


@dataclass(frozen=True, slots=True)
class ProviderOrderWritePermit:
    """Internal one-operation evidence returned by an injected trusted policy.

    Construction is not authorization. The composition must provide its existing
    authority/one-shot capability boundary through authorize_once.
    """
    customer_id: str
    session_id: str
    operation_key: str
    command_digest: str
    policy_reference: str
    authorized_at: datetime
    expires_at: datetime

    def __post_init__(self):
        _customer_id(self.customer_id);_session_id(self.session_id)
        _idempotency_key(self.operation_key);_digest(self.command_digest)
        _reference(self.policy_reference,'write_policy')
        require_utc(self.authorized_at);require_utc(self.expires_at)
        if self.expires_at<=self.authorized_at:raise ValueError('permit lifetime invalid')


class WooCommerceOrderWriter:
    def __init__(self, *, base_url: str, consumer_key: SecretStr, consumer_secret: SecretStr,
                 ledger: SQLiteOrderCreateLedger, clock, authorize_once, resolve_customer, session=None):
        parsed=urlsplit(base_url)
        if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ('','/') or parsed.port not in (None,443)):
            raise ValueError('explicit canonical HTTPS WooCommerce origin required')
        if any(not isinstance(v,SecretStr) or not v.get_secret_value() for v in (consumer_key,consumer_secret)):
            raise ValueError('explicit scoped WooCommerce credentials required')
        if type(ledger) is not SQLiteOrderCreateLedger or not all(callable(v) for v in (clock,authorize_once,resolve_customer)):
            raise ValueError('explicit durable policy/customer composition required')
        self._base=base_url.rstrip('/')+'/wp-json/wc/v3/orders'
        self._credentials=(consumer_key,consumer_secret)
        self._ledger=ledger;self._clock=clock;self._authorize=authorize_once;self._customer=resolve_customer
        self._session=session if session is not None else requests.Session()

    def __repr__(self):return 'WooCommerceOrderWriter(explicit_composition=True)'

    def _auth(self):return tuple(v.get_secret_value() for v in self._credentials)

    @staticmethod
    def _document(response):
        body=bytearray()
        try:
            for chunk in response.iter_content(chunk_size=8192):
                if len(body)+len(chunk)>1048576:raise ValueError('provider response exceeds bounds')
                body.extend(chunk)
            return json.loads(body.decode('utf-8'))
        finally:response.close()

    @staticmethod
    def _tag(key):return hashlib.sha256(('aicc-order:'+key).encode()).hexdigest()

    @staticmethod
    def _verify_metadata(raw, key, digest, customer):
        if type(raw) is not dict or raw.get('customer_id')!=customer or type(raw.get('customer_id')) is not int:
            raise ValueError('provider customer binding invalid')
        meta=raw.get('meta_data')
        if type(meta) is not list or len(meta)>100:raise ValueError('provider metadata invalid')
        for name,value in [('_aicc_order_operation',WooCommerceOrderWriter._tag(key)),('_aicc_command_digest',digest)]:
            matches=[m.get('value') for m in meta if type(m) is dict and m.get('key')==name]
            if matches!=[value]:raise ValueError('provider operation binding invalid')

    def create_order(self, command):
        # All failures before dispatch can prove no write was attempted.
        try:
            if type(command) is not ResolvedOrderCreateCommand:raise ValueError()
            key=_idempotency_key(command.idempotency_key);digest=_digest(command.command_digest)
            now=require_utc(self._clock())
            permit=self._authorize(command,now)
            if (type(permit) is not ProviderOrderWritePermit or permit.customer_id!=command.customer_id
                or permit.operation_key!=key or permit.command_digest!=digest
                or not permit.authorized_at<=now<permit.expires_at):raise ValueError()
            customer=self._customer(command.customer_id)
            if type(customer) is not int or customer<=0:raise ValueError()
            if not 1 <= len(command.line_items) <= 100 or any(v.quantity>1000 for v in command.line_items):raise ValueError()
            lines=[{'product_id':v.provider_product_id,'variation_id':v.provider_variation_id,'quantity':v.quantity}
                   for v in command.line_items]
            if not permit.authorized_at<=require_utc(self._clock())<permit.expires_at:raise ValueError()
        except Exception:
            raise OrderCreateDefinitiveFailure('PROVIDER_PREWRITE_DENIED') from None
        # A second invocation cannot consume the already committed dispatch.
        self._ledger.claim_provider_dispatch(key,digest,command.customer_id,permit.session_id,customer,lines)
        payload={'customer_id':customer,'status':'pending','set_paid':False,'line_items':lines,
                 'meta_data':[{'key':'_aicc_order_operation','value':self._tag(key)},
                              {'key':'_aicc_command_digest','value':digest}]}
        try:
            response=self._session.post(self._base,json=payload,auth=self._auth(),timeout=15,
                                        allow_redirects=False,stream=True)
            if response.status_code!=201:
                response.close()
                raise ValueError('provider outcome unknown')
            raw=self._document(response)
            self._verify_metadata(raw,key,digest,customer)
            snapshot=normalize_woocommerce_order(raw)
            if snapshot.status!='pending' or raw.get('date_paid') is not None or raw.get('date_paid_gmt') is not None:
                raise ValueError('provider unexpectedly paid or changed status')
            return snapshot
        except Exception:
            # Even HTTP failures may follow a provider-side write; never infer no order.
            raise OrderCreateAmbiguousFailure('WOOCOMMERCE_OUTCOME_UNKNOWN') from None

    def reconcile_completed(self, operation_key, provider_order_id):
        """Explicit exact-order GET evidence only. Never retries POST or certifies absence."""
        key=_idempotency_key(operation_key)
        if type(provider_order_id) is not int or provider_order_id<=0:raise ValueError('provider order id invalid')
        operation=self._ledger.inspect_operation(key)
        dispatch=self._ledger.inspect_provider_dispatch(key)
        if operation is None or dispatch is None or operation['state'] not in ('CLAIMED','UNKNOWN_OUTCOME'):
            raise ValueError('unresolved dispatched operation required')
        try:
            response=self._session.get(self._base+'/'+str(provider_order_id),auth=self._auth(),timeout=15,
                                       allow_redirects=False,stream=True)
            if response.status_code!=200:
                response.close();raise ValueError()
            raw=self._document(response)
            self._verify_metadata(raw,key,operation['command_digest'],dispatch['provider_customer_id'])
            snapshot=normalize_woocommerce_order(raw)
            if snapshot.provider_order_id!=provider_order_id:raise ValueError()
            actual=[{'product_id':v.product_id,'variation_id':v.variation_id,'quantity':v.quantity}
                    for v in snapshot.line_items]
            if sorted(actual,key=lambda v:(v['product_id'],v['variation_id'])) != sorted(json.loads(dispatch['expected_lines_json']),key=lambda v:(v['product_id'],v['variation_id'])):
                raise ValueError()
        except Exception:
            raise OrderCreateAmbiguousFailure('RECONCILIATION_UNPROVEN') from None
        result=OrderCreateResult(customer_id=operation['customer_id'],snapshot=snapshot,idempotency_key=key,
            command_digest=operation['command_digest'],correlation_id=operation['correlation_reference'],
            audit_reference=operation['audit_reference'])
        if operation['state']=='CLAIMED':self._ledger.unknown(key,result.command_digest,'EXPLICIT_CRASH_RECONCILIATION')
        self._ledger.reconcile_completed(key,result.command_digest,result)
        return result
