import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_shop_aftersales_dev import fixture,Boundary,CUSTOMER,ORDER
from test_shop_telegram_fulfillment_sms import adapter
from test_shop_order_001d_telegram import api,clients,composed,deny_network,Transport,update,CHAT,OPERATOR
from core.shopping.order_core.telegram import OrderTelegramIntegration
from core.shopping.customer_order_notices import mount_order_notices

def test_operator_cancel_duplicate_phone_selection_and_customer_notices(tmp_path):
    store,draft=fixture(tmp_path,[1000.0]);calls=[]
    store.stock_cancellation=lambda row,d: calls.append(row['provider_order_id']) or {'outcome':'STOCK_CANCELLED','order_id':ORDER}
    op=adapter(store,draft)
    first=op.resolve('01012345678 주문취소',1)[2]
    assert '취소완료' in first and op.resolve('주문취소 #15',1)[2]==first
    assert op.resolve('주문취소 #15',2)[2]==first and calls==[ORDER]
    assert op.display_state(op.rows()[0])=='CANCELLED'
    assert '취소완료' in op.resolve('주문내역',3)[2]
    assert '입금대기' not in op.resolve('주문내역',4)[2]
    app=FastAPI();boundary=Boundary();phone=draft['body']['billing']['phone']
    def auth(request):
        boundary.check_origin(request,required=True)
        value=boundary.authenticate(boundary.cookie_secret(request),None)
        boundary.check_csrf(request,'secret',value);return value
    mount_order_notices(app,path='/shopping/chat/orders/notices',store=store,authenticate=auth,verified_phone=lambda c:phone,bank_provider=lambda:{'name':'bank','account':'SECRET BANK','holder':'holder'})
    with TestClient(app,base_url='https://dev.bokstory.duckdns.org') as client:
        client.cookies.set('__Host-aicc_customer','secret')
        r=client.post('/shopping/chat/orders/notices',json={'order_number':'15'},headers={'Origin':'https://dev.bokstory.duckdns.org','X-CSRF-Token':'csrf'})
        assert r.status_code==200 and r.json()['messages'][0]['kind']=='CANCELLED'
        assert 'SECRET BANK' not in r.text and '입금하지 마세요' in r.json()['messages'][0]['message']
        assert r.headers['cache-control']=='no-store' and r.json()['transaction_sms'] is False
        r=client.post('/shopping/chat/orders/notices',json={'order_number':'999'},headers={'Origin':'https://dev.bokstory.duckdns.org','X-CSRF-Token':'csrf'})
        assert r.status_code==403

def test_phone_cancel_ambiguity_and_wrong_customer_are_blocked(tmp_path):
    store,draft=fixture(tmp_path,[1000.0]);op=adapter(store,draft);base=op.rows()[0]
    op.rows=lambda:[base,{**base,'provider_order_id':16}]
    store.stock_cancellation=lambda *a:pytest.fail('ambiguous cancellation')
    assert '주문번호를 함께' in op.resolve('01012345678 주문취소',1)[2]
    assert '해당 고객 주문' in op.resolve('01099999999 주문취소 #15',2)[2]
    assert store.cancellation(ORDER)['state']=='NONE'

@pytest.mark.parametrize('authorized',[False,True])
def test_telegram_allowlist_protects_cancellation(api,composed,tmp_path,authorized):
    store,draft=fixture(tmp_path,[1000.0]);calls=[]
    store.stock_cancellation=lambda row,d: calls.append(1) or {'outcome':'STOCK_CANCELLED','order_id':ORDER}
    op=adapter(store,draft);transport=Transport();u=update(user=OPERATOR if authorized else OPERATOR+1)
    u['message']['text']='주문취소 #15';transport.updates=[u]
    _,ledger,_=composed
    driver=OrderTelegramIntegration(ledger=ledger,transport=transport,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),operator_adapter=op)
    driver.poll_once();driver.poll_once()
    assert calls==([1] if authorized else [])
    assert store.cancellation(ORDER)['state']==('CANCELLED' if authorized else 'NONE')

def test_cancel_result_command_recovers_without_provider_resend(tmp_path):
    store,draft=fixture(tmp_path,[1000.0]);op=adapter(store,draft)
    class Provider:
        writes=0
        def __call__(self,row,draft):self.writes+=1;raise TimeoutError()
        def reconcile(self,row,draft):return {'outcome':'STOCK_CANCELLED','order_id':ORDER}
    provider=Provider();store.stock_cancellation=provider
    assert '취소 결과 확인' in op.resolve('주문취소 #15',1)[2]
    assert op.display_state(op.rows()[0])=='CANCELLATION_PENDING'
    from core.shopping.customer_order_notices import order_notices
    notice=order_notices(store.customer_orders(CUSTOMER)[0],{'name':'bank','account':'SECRET BANK','holder':'holder'})
    assert notice[0]['kind']=='CANCELLATION_PENDING' and 'SECRET BANK' not in notice[0]['message']
    assert '취소완료' in op.resolve('01012345678 취소확인 #15',2)[2]
    assert provider.writes==1 and store.cancellation(ORDER)['state']=='CANCELLED'

@pytest.mark.parametrize('authorized',[False,True])
def test_telegram_allowlist_protects_return_inspection(api,composed,tmp_path,authorized):
    from test_shop_return_stock_workflow import delivered,provider
    store,case,_=delivered(tmp_path);calls=[];store.stock_return=provider(calls)
    store.decide(case['id'],True);store.receive_return(case['id'])
    _,draft=store._customer_order(CUSTOMER,ORDER);op=adapter(store,draft)
    transport=Transport();u=update(user=OPERATOR if authorized else OPERATOR+1)
    u['message']['text']='반품 검수완료 #'+case['id'];transport.updates=[u]
    _,ledger,_=composed
    driver=OrderTelegramIntegration(ledger=ledger,transport=transport,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),operator_adapter=op)
    driver.poll_once();driver.poll_once()
    assert calls==([case['id']] if authorized else [])
