from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_shop_aftersales_dev import fixture,Boundary,CUSTOMER,ORDER
from core.shopping.customer_order_notices import mount_order_notices,order_notices,GREETING
PHONE='+821012345678'
BANK={'name':'TEST BANK','account':'TEST ACCOUNT','holder':'TEST HOLDER'}
def test_chat_notices_are_owned_no_store_and_follow_real_operator_state(tmp_path):
    store,_=fixture(tmp_path,[1000.0]);app=FastAPI();boundary=Boundary()
    def auth(request):
        boundary.check_origin(request,required=True);secret=boundary.cookie_secret(request)
        value=boundary.authenticate(secret,now=None);boundary.check_csrf(request,secret,value);return value
    mount_order_notices(app,path='/shopping/chat/orders/notices',store=store,authenticate=auth,verified_phone=lambda customer:PHONE,bank_provider=lambda:BANK)
    client=TestClient(app,base_url='https://dev.bokstory.duckdns.org');h={'Origin':'https://dev.bokstory.duckdns.org','X-CSRF-Token':'csrf'};body={'order_number':'15'}
    assert client.post('/shopping/chat/orders/notices',json=body,headers=h).status_code==403
    client.cookies.set('__Host-aicc_customer','secret')
    for data,headers in [(body,{}),({'order_number':'999'},h),({**body,'customer_id':CUSTOMER},h)]:
        denied=client.post('/shopping/chat/orders/notices',json=data,headers=headers)
        assert denied.status_code==403 and 'TEST ACCOUNT' not in denied.text
    def messages():
        response=client.post('/shopping/chat/orders/notices',json=body,headers=h)
        assert response.status_code==200 and response.headers['cache-control']=='no-store'
        assert response.json()['transaction_sms'] is False
        assert 'delivery' not in response.json() and PHONE not in response.text
        assert all(v['message'].startswith(GREETING) for v in response.json()['messages'])
        return response.json()['messages']
    confirmed=messages();assert 'TEST ACCOUNT' in confirmed[0]['message']
    store.confirm_payment(ORDER);paid=messages();assert paid[-1]['kind']=='PAID' and all('TEST ACCOUNT' not in v['message'] for v in paid)
    store.mark_shipped(ORDER,'CJ대한통운','1234567890');shipped=messages();assert shipped[-1]['kind']=='SHIPPED' and '1234567890' in shipped[-1]['message']
    store.mark_delivered(ORDER);done=messages();assert done[-1]['kind']=='DELIVERED'
    assert messages()==done

def test_pending_and_rejected_orders_never_show_deposit_account():
    order={'order_id':15,'items':[{'name':'상품','quantity':1,'option':'S'}],'total':'29000','currency':'KRW','review_state':'PENDING_REVIEW'}
    assert order_notices(order,BANK)[0]['kind']=='RECEIVED'
    assert 'TEST ACCOUNT' not in order_notices(order,BANK)[0]['message']
    order['review_state']='REJECTED';assert order_notices(order,BANK)[0]['kind']=='REJECTED'
    assert 'TEST ACCOUNT' not in order_notices(order,BANK)[0]['message']
