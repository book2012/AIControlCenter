"""Isolated operator dialogue -> durable fulfillment -> authenticated customer lookup."""
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_shop_aftersales_dev import fixture,Boundary,CUSTOMER,ORDER
from test_shop_customer_order_lookup import PHONE
from core.shopping.operator_conversation import OperatorConversation
from ops.macos.shopping.dev_order_operator import DevOperatorAdapter
from ops.macos.shopping.dev_aftersales import DevAftersalesStore,mount_aftersales
ACTOR='telegram-user-123'

def test_operator_approval_customer_lookup_and_restart_share_fulfillment(tmp_path):
    store,draft=fixture(tmp_path,[1000.0])
    op=DevOperatorAdapter(ledger=store.ledger,store=store.checkout,aftersales=store)
    op.rows=lambda:[{'provider_order_id':ORDER,'phone':'01012345678','state':'CONFIRMED','reference':'a'*24,'requested_at':'2026-10-12T00:00:00Z','quote':draft['body']['quote'],'delivery':draft['body']['shipping']}]
    plans=[];calls=[]
    def execute(text,i,actor):
        calls.append(text);ref,decision,reply=op.resolve(text,i)
        assert ref is None and decision is None
        return reply
    e=OperatorConversation(path=tmp_path/'dialogue.sqlite3',judge=lambda text,context:plans.pop(0),orders=op.admin_orders,products=lambda:[],validate_product=lambda text:None,executor=execute)
    app=FastAPI();mount_aftersales(app,store=store,boundary=Boundary(),phone_cfg={'guest_customer_id':CUSTOMER,'test_phone':PHONE})
    with TestClient(app,base_url='https://dev.bokstory.duckdns.org') as client:
        client.cookies.set('__Host-aicc_customer','secret')
        def lookup():
            r=client.post('/__order-dev/orders/lookup',json={'order_number':str(ORDER),'phone':'01012345678'},headers={'Origin':'https://dev.bokstory.duckdns.org','X-CSRF-Token':'csrf'})
            assert r.status_code==200
            return r.json()['order']
        assert lookup()['payment']['state']=='AWAITING_DEPOSIT'
        # An approved shipping command must still fail until deposit is confirmed.
        plans.append({'action':'SHIP','order_id':ORDER,'carrier':'CJ대한통운','tracking':'1234567890'})
        assert '처리할까요' in e.handle('15번 배송해줘',1,ACTOR)
        assert lookup()['fulfillment']['state']=='NOT_SHIPPED'
        assert '입금확인 후' in e.handle('응',2,ACTOR)
        for index,plan,text,payment,fulfillment in [
            (3,{'action':'DEPOSIT_CONFIRM','order_id':ORDER},'15번 입금했어','PAID','NOT_SHIPPED'),
            (5,{'action':'SHIP','order_id':ORDER,'carrier':'CJ대한통운','tracking':'1234567890'},'15번 보냈어','PAID','SHIPPED'),
            (7,{'action':'DELIVERED','order_id':ORDER},'15번 배송끝났어','PAID','DELIVERED')]:
            before=lookup();count=len(calls);plans.append(plan)
            assert '처리할까요' in e.handle(text,index,ACTOR)
            assert len(calls)==count and lookup()['fulfillment']==before['fulfillment']
            first=e.handle('응',index+1,ACTOR);assert e.handle('응',index+1,ACTOR)==first and len(calls)==count+1
            current=lookup();assert current['payment']['state']==payment and current['fulfillment']['state']==fulfillment
        assert op.display_state(op.rows()[0])=='COMPLETED'
        details=e.handle('주문상세 #15',9,ACTOR)
        assert '배송완료' in details and 'DEV 수령인' in details and '2026-10-12 09:00' in details
    restarted=DevAftersalesStore(store.path,store.attachments,ledger=store.ledger,checkout=store.checkout,catalog=store.catalog)
    assert restarted.customer_orders(CUSTOMER)[0]['fulfillment']['state']=='DELIVERED'
    assert restarted.payment(ORDER)['state']=='PAID'
    with sqlite3.connect(store.path) as c:assert c.execute('SELECT count(*) FROM shipping_notices').fetchone()[0]==1
