import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_shop_return_stock_workflow import delivered,provider
from test_shop_aftersales_dev import CUSTOMER,ORDER
from test_shop_telegram_fulfillment_sms import adapter
from core.shopping.operator_conversation import OperatorConversation
from core.shopping.customer_order_notices import order_notices
from core.shopping.operator_intent import resolve_explicit_slots
from ops.macos.shopping.dev_aftersales import DevAftersalesStore
ACTOR='telegram-user-123';EVIDENCE='BANK-20261012-001'

def ready(tmp_path):
    store,case,clock=delivered(tmp_path);calls=[];store.stock_return=provider(calls)
    store.manual_refund_records_enabled=True;store.decide(case['id'],True);store.receive_return(case['id']);store.inspect_return(case['id'])
    return store,case,clock,calls

def test_manual_record_durable_once_preserves_paid_and_no_extra_restock(tmp_path):
    store,case,clock,calls=ready(tmp_path)
    before=store.payment(ORDER);first=store.record_refund(case['id'],58000,EVIDENCE,ACTOR,1)
    assert first['state']=='RECORDED' and first['amount']=='58000'
    clock[0]+=60
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts=list(pool.map(lambda _:store.record_refund(case['id'],58000,EVIDENCE,ACTOR,2),range(8)))
    assert all(x==first for x in receipts) and calls==[case['id']]
    restarted=DevAftersalesStore(store.path,store.attachments,ledger=store.ledger,checkout=store.checkout,catalog=store.catalog)
    assert restarted.refund(ORDER)==first and restarted.payment(ORDER)==before
    assert restarted.manual_refund_records_enabled is False
    order=store.lookup(CUSTOMER,str(ORDER),'+821012345678','+821012345678')
    notice=order_notices(order,{'name':'bank','account':'NO-DEPOSIT','holder':'holder'})
    assert notice[0]['kind']=='REFUND' and '환불완료' in notice[0]['message'] and '58000' in notice[0]['message']
    assert EVIDENCE not in str(order) and ACTOR not in str(order) and 'NO-DEPOSIT' not in str(notice)
    _,draft=store._customer_order(CUSTOMER,ORDER);op=adapter(store,draft)
    assert op.display_state(op.rows()[0])=='REFUND_RECORDED' and '환불완료 기록' in op.list_message()

@pytest.mark.parametrize('amount,evidence,actor',[(1,EVIDENCE,ACTOR),(58001,EVIDENCE,ACTOR),(True,EVIDENCE,ACTOR),(58000,'bad evidence',ACTOR),(58000,EVIDENCE,None)])
def test_invalid_record_never_changes_state(tmp_path,amount,evidence,actor):
    store,case,_,_=ready(tmp_path)
    with pytest.raises(ValueError):store.record_refund(case['id'],amount,evidence,actor,1)
    assert store.refund(ORDER)['state']=='NOT_RECORDED'

def test_record_requires_completed_inspection_and_dev_enable(tmp_path):
    store,case,_=delivered(tmp_path)
    with pytest.raises(ValueError,match='DISABLED'):store.record_refund(case['id'],58000,EVIDENCE,ACTOR,1)
    store.manual_refund_records_enabled=True
    with pytest.raises(ValueError,match='INSPECTION_REQUIRED'):store.record_refund(case['id'],58000,EVIDENCE,ACTOR,1)
    assert store.refund(ORDER)['state']=='NOT_RECORDED'

def test_existing_record_conflict_and_reused_evidence_are_blocked(tmp_path):
    store,case,_,_=ready(tmp_path);store.record_refund(case['id'],58000,EVIDENCE,ACTOR,1)
    with pytest.raises(ValueError,match='CONFLICT'):store.record_refund(case['id'],58000,'OTHER-REF',ACTOR,2)
    with sqlite3.connect(store.path) as c:
        assert c.execute('SELECT count(*) FROM manual_refunds').fetchone()[0]==1
    assert store.refund(ORDER)['state']=='RECORDED'

def test_dialogue_requires_actor_bound_approval_before_record(tmp_path):
    store,case,_,calls=ready(tmp_path);_,draft=store._customer_order(CUSTOMER,ORDER);op=adapter(store,draft)
    e=OperatorConversation(path=tmp_path/'dialogue.sqlite3',judge=lambda *a:pytest.fail('explicit record must not need model'),orders=op.admin_orders,products=lambda:[],validate_product=lambda text:None,executor=lambda text,i,actor:op.resolve(text,i,actor=actor)[2])
    text='환불완료 #'+case['id']+' 58000원 증빙 '+EVIDENCE
    reply=e.handle(text,1,ACTOR)
    assert '실제 송금은 실행하지 않습니다' in reply and '처리할까요' in reply
    assert store.refund(ORDER)['state']=='NOT_RECORDED'
    e.handle('응',2,'telegram-user-456');assert store.refund(ORDER)['state']=='NOT_RECORDED'
    reply=e.handle('응',3,ACTOR);assert '환불완료 기록' in reply
    assert e.handle('응',3,ACTOR)==reply and calls==[case['id']]

def test_model_cannot_convert_transfer_request_into_record():
    plan={'action':'REFUND_RECORD','case_id':'a1b2c3d4','price':58000,'evidence':EVIDENCE}
    assert resolve_explicit_slots(plan,'58000원 송금해줘',{})=={'action':'UNKNOWN'}


def test_evidence_reuse_on_another_record_is_denied(tmp_path):
    store,case,_,_=ready(tmp_path)
    with sqlite3.connect(store.path) as c:c.execute('INSERT INTO manual_refunds VALUES(?,?,?,?,?,?,?,?)',('deadbeef',999,'58000','KRW',EVIDENCE,ACTOR,1,1000))
    with pytest.raises(ValueError,match='EVIDENCE_REUSED'):store.record_refund(case['id'],58000,EVIDENCE,ACTOR,2)
    assert store.refund(ORDER)['state']=='NOT_RECORDED'

def test_customer_http_refund_projection_is_owned_and_evidence_private(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_shop_aftersales_dev import Boundary
    from ops.macos.shopping.dev_aftersales import mount_aftersales
    store,case,_,_=ready(tmp_path);store.record_refund(case['id'],58000,EVIDENCE,ACTOR,1)
    app=FastAPI();mount_aftersales(app,store=store,boundary=Boundary(),phone_cfg={'guest_customer_id':CUSTOMER,'test_phone':'+821012345678'})
    with TestClient(app,base_url='https://dev.bokstory.duckdns.org') as client:
        headers={'Origin':'https://dev.bokstory.duckdns.org','X-CSRF-Token':'csrf'};data={'order_number':str(ORDER),'phone':'01012345678'}
        assert client.post('/__order-dev/orders/lookup',json=data,headers=headers).status_code==403
        client.cookies.set('__Host-aicc_customer','secret')
        response=client.post('/__order-dev/orders/lookup',json=data,headers=headers)
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert response.json()['order']['refund']['state']=='RECORDED' and '환불완료' in response.text
        assert EVIDENCE not in response.text and ACTOR not in response.text
        assert client.post('/__order-dev/orders/lookup',json={**data,'phone':'01099999999'},headers=headers).status_code==403
