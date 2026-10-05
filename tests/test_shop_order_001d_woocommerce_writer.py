"""No network: governed Woo write and exact GET reconciliation are mocked."""
from datetime import timedelta
from dataclasses import replace
import json
from types import SimpleNamespace
from unittest.mock import Mock

from pydantic import SecretStr
import pytest

from test_shop_order_001c_session_composition import api, clients, composed, deny_network, intent, authenticated_request
from test_shop_order_001c_catalog_resolution import Catalog, product
from test_shop_ai_order_core_v1 import _raw_order
from core.shopping.order_core import OrderCreateService, ShoppingServiceOrderCatalogResolver, OrderCreateAmbiguousFailure, OrderCreateDefinitiveFailure
from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter, ProviderOrderWritePermit


class Response:
    def __init__(self,body,status=201):self.status_code=status;self.body=body;self.closed=False
    def iter_content(self,chunk_size):yield json.dumps(self.body).encode()
    def close(self):self.closed=True


@pytest.fixture
def writer_setup(api,composed):
    application,store,_=composed
    req=authenticated_request(api)
    projection=api.boundary.authenticate('s'*43,now=api.time.now)
    policy=Mock(side_effect=lambda command,now:ProviderOrderWritePermit(command.customer_id,projection.id,
        command.idempotency_key,command.command_digest,'dev-policy-001',now,now+timedelta(seconds=30)))
    customer=Mock(return_value=55)
    session=Mock()
    def post(url,**kwargs):
        body=_raw_order(order_id=101,status='pending')
        body['line_items'][0].update(product_id=123,variation_id=0,quantity=1)
        body['meta_data']=kwargs['json']['meta_data']
        return Response(body)
    session.post.side_effect=post
    writer=WooCommerceOrderWriter(base_url='https://woo.dev.example.test',consumer_key=SecretStr('synthetic-key'),
        consumer_secret=SecretStr('synthetic-secret'),ledger=store,clock=lambda:api.time.now,
        authorize_once=policy,resolve_customer=customer,session=session)
    service=OrderCreateService(catalog_resolver=ShoppingServiceOrderCatalogResolver(Catalog(product())),
                               order_creator=writer,coordinator=store)
    application._orders=service
    return SimpleNamespace(app=application,store=store,req=req,writer=writer,session=session,policy=policy,customer=customer)


def test_governed_write_claims_before_post_and_replay_does_not_call_policy_or_provider(writer_setup):
    value=writer_setup
    original=value.session.post.side_effect
    def observed(url,**kwargs):
        assert value.store.inspect_provider_dispatch('order-session-001') is not None
        assert value.store.inspect_operation('order-session-001')['state']=='CLAIMED'
        payload=kwargs['json']
        assert set(payload)=={'customer_id','status','set_paid','line_items','meta_data'}
        assert payload['status']=='pending' and payload['set_paid'] is False
        assert kwargs['allow_redirects'] is False and kwargs['stream'] is True
        return original(url,**kwargs)
    value.session.post.side_effect=observed
    first=value.app.execute(value.req,intent())
    replay=value.app.execute(value.req,intent())
    assert first.snapshot.provider_order_id==101 and replay.idempotent_replay
    assert value.policy.call_count==1 and value.session.post.call_count==1
    assert len(value.store.notification_statuses())==1


@pytest.mark.parametrize('denial',['policy','customer','expired','session'])
def test_prewrite_denial_never_calls_http(writer_setup,denial):
    value=writer_setup
    if denial=='policy':value.policy.side_effect=RuntimeError('credential-marker')
    if denial=='customer':value.customer.return_value=0
    if denial in ('expired','session'):
        original=value.policy.side_effect
        def bad(command,now):
            permit=original(command,now)
            return replace(permit,expires_at=now) if denial=='expired' else replace(permit,session_id='AG-SES-'+'9'*12+'4'+'9'*3+'8'+'9'*15)
        value.policy.side_effect=bad
    with pytest.raises(Exception):value.app.execute(value.req,intent())
    assert value.session.post.call_count==0


@pytest.mark.parametrize('status',[200,302,400,401,403,422,429,500])
def test_any_unproven_http_outcome_is_quarantined_and_cannot_retry(writer_setup,status):
    value=writer_setup;value.session.post.side_effect=lambda *args,**kwargs:Response({},status)
    with pytest.raises(OrderCreateAmbiguousFailure):value.app.execute(value.req,intent())
    assert value.store.inspect_operation('order-session-001')['state']=='UNKNOWN_OUTCOME'
    with pytest.raises(Exception):value.app.execute(value.req,intent())
    assert value.session.post.call_count==1 and value.store.notification_statuses()==[]


def test_timeout_reconciliation_uses_exact_provider_evidence_and_never_posts_again(writer_setup):
    value=writer_setup
    response=value.session.post.side_effect('url',json={'meta_data':[{'key':'_aicc_order_operation','value':value.writer._tag('order-session-001')},
        {'key':'_aicc_command_digest','value':'placeholder'}]})
    value.session.post.side_effect=RuntimeError('credential-marker-url')
    with pytest.raises(OrderCreateAmbiguousFailure):value.app.execute(value.req,intent())
    response.body['meta_data'][1]['value']=value.store.inspect_operation('order-session-001')['command_digest']
    response.status_code=200;value.session.get.return_value=response
    recovered=value.writer.reconcile_completed('order-session-001',101)
    assert recovered.snapshot.provider_order_id==101
    assert value.app.execute(value.req,intent()).idempotent_replay
    assert value.session.post.call_count==1 and value.session.get.call_count==1
    assert len(value.store.notification_statuses())==1


@pytest.mark.parametrize('change',['customer','operation','digest','quantity','order_id'])
def test_reconciliation_rejects_wrong_evidence(writer_setup,change):
    value=writer_setup;original=value.session.post.side_effect
    value.session.post.side_effect=RuntimeError('timeout')
    with pytest.raises(OrderCreateAmbiguousFailure):value.app.execute(value.req,intent())
    digest=value.store.inspect_operation('order-session-001')['command_digest']
    response=original('url',json={'meta_data':[{'key':'_aicc_order_operation','value':value.writer._tag('order-session-001')},
        {'key':'_aicc_command_digest','value':digest}]});response.status_code=200
    if change=='customer':response.body['customer_id']=56
    if change=='operation':response.body['meta_data'][0]['value']='0'*64
    if change=='digest':response.body['meta_data'][1]['value']='0'*64
    if change=='quantity':response.body['line_items'][0]['quantity']=2
    if change=='order_id':response.body['id']=102
    value.session.get.return_value=response
    with pytest.raises(OrderCreateAmbiguousFailure):value.writer.reconcile_completed('order-session-001',101)
    assert value.store.inspect_operation('order-session-001')['state']=='UNKNOWN_OUTCOME'
    assert value.session.post.call_count==1


def test_not_found_is_not_proof_of_no_order(writer_setup):
    value=writer_setup;value.session.post.side_effect=RuntimeError('timeout')
    with pytest.raises(OrderCreateAmbiguousFailure):value.app.execute(value.req,intent())
    value.session.get.return_value=Response({},404)
    with pytest.raises(OrderCreateAmbiguousFailure):value.writer.reconcile_completed('order-session-001',101)
    assert value.store.inspect_operation('order-session-001')['state']=='UNKNOWN_OUTCOME'


def test_dispatch_cannot_be_consumed_twice_even_by_direct_writer_call(writer_setup):
    value=writer_setup
    command_holder=[]
    old=value.policy.side_effect
    def capture(command,now):command_holder.append(command);return old(command,now)
    value.policy.side_effect=capture
    value.session.post.side_effect=RuntimeError('timeout')
    with pytest.raises(OrderCreateAmbiguousFailure):value.app.execute(value.req,intent())
    # Operation is quarantined; direct reentry cannot regain provider authority.
    with pytest.raises(Exception):value.writer.create_order(command_holder[0])
    assert value.session.post.call_count==1


@pytest.mark.parametrize('base',['http://woo.example.test','https://user:pass@woo.example.test','https://woo.example.test/path','https://woo.example.test/?key=x'])
def test_origin_policy_rejects_insecure_or_credential_urls(api,composed,base):
    with pytest.raises(ValueError):WooCommerceOrderWriter(base_url=base,consumer_key=SecretStr('x'),consumer_secret=SecretStr('y'),
        ledger=composed[1],clock=lambda:api.time.now,authorize_once=lambda *args:None,resolve_customer=lambda value:55)
