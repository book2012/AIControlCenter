"""Explicit one-order DEV live probe; persist identity before any create attempt."""
from pathlib import Path
import json, os, sqlite3, time, uuid
import requests
from ops.macos.shopping.dev_order_provision import private_write

ROOT=Path('/Users/kyouhan/.config/aicontrolcenter-dev-order')
DATA=Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/data')
API='http://127.0.0.1:18445'
ORIGIN='https://dev.bokstory.duckdns.org'

def main():
    cfg=json.loads((ROOT/'runtime.private.json').read_text());commerce=json.loads((ROOT/'commerce.private.json').read_text())
    path=ROOT/'live-test.private.json'
    if path.exists():
        state=json.loads(path.read_text())
        if state.get('post_attempted'):raise RuntimeError('EXISTING_LIVE_TEST_INSPECT_ONLY')
    else:
        state={'operation_key':'dev-live-'+uuid.uuid4().hex,'post_attempted':False}
        private_write(path,state)
    denied=requests.post(API+'/dev-order/credentials',json={'username':'bad','password':'bad'},headers={'Origin':ORIGIN},timeout=5)
    if denied.status_code!=401:raise RuntimeError('DEV_DENIAL_TEST_FAILED')
    credential=requests.post(API+'/dev-order/credentials',json={'username':'aicc-dev-test-customer','password':cfg['login_password']},
        headers={'Origin':ORIGIN},timeout=5)
    if credential.status_code!=200:raise RuntimeError('DEV_LOGIN_FAILED')
    session=requests.post(API+'/shopping/auth/session',json=credential.json(),headers={'Origin':ORIGIN},timeout=5)
    if session.status_code!=201:raise RuntimeError('DEV_SESSION_FAILED')
    state['cookie']=session.cookies['__Host-aicc_customer'];state['csrf']=session.headers['X-CSRF-Token']
    private_write(path,state)
    headers={'Origin':ORIGIN,'Cookie':'__Host-aicc_customer='+state['cookie'],'X-CSRF-Token':state['csrf']}
    body={'line_items':[{'product_id':str(cfg['provider_product_id']),
        'variation_id':str(commerce['test_product']['variation_id']),'quantity':1}],'idempotency_key':state['operation_key']}
    bad=dict(headers);bad['X-CSRF-Token']='0'*64
    denial=requests.post(API+'/shopping/orders',json=body,headers=bad,timeout=5)
    if denial.status_code!=403:raise RuntimeError('DEV_CSRF_DENIAL_FAILED')
    state['post_attempted']=True;private_write(path,state)
    response=requests.post(API+'/shopping/orders',json=body,headers=headers,timeout=45)
    state['first_http_status']=response.status_code;state['public_response']=response.json();private_write(path,state)
    if response.status_code!=201:raise RuntimeError('LIVE_ORDER_OUTCOME_REQUIRES_INSPECTION_NO_RETRY')
    replay=requests.post(API+'/shopping/orders',json=body,headers=headers,timeout=10)
    if replay.status_code!=200 or replay.json().get('idempotent_replay') is not True:raise RuntimeError('LIVE_REPLAY_FAILED')
    with sqlite3.connect(DATA/'orders.sqlite3') as connection:
        reference=connection.execute('SELECT reference FROM shopping_order_operator_review WHERE operation_key=?',
            (state['operation_key'],)).fetchone()[0]
    state['operator_reference']=reference;private_write(path,state)
    notification=None
    for _ in range(20):
        with sqlite3.connect(DATA/'orders.sqlite3') as connection:
            notification=connection.execute("SELECT state,message_id FROM shopping_order_notification_outbox WHERE operation_key=? AND event_type='ORDER_CREATED'",(state['operation_key'],)).fetchone()
        if notification and notification[0] in ('SENT','UNKNOWN_OUTCOME','FAILED'):break
        time.sleep(1)
    status=requests.get(API+'/shopping/orders/operations/'+state['operation_key'],headers=headers,timeout=5)
    report={'environment':'DEV','first_http':response.status_code,'replay_http':replay.status_code,
            'provider_order_id':response.json()['provider_order_id'],'total':response.json()['total'],
            'notification_state':notification[0] if notification else None,'telegram_message_id':notification[1] if notification else None,
            'operator_reference':reference,'customer_status':status.json(),'phone_verification_tested':False,
            'prod_mutation':False,'auth_denial':denied.status_code,'csrf_denial':denial.status_code}
    private_write(Path('/Users/kyouhan/AIControlCenterRuntime/dev-order/live-order-evidence.json'),report)
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except Exception as error:
        text=str(error);print(text if __import__('re').fullmatch('[A-Z_]+',text) else 'LIVE_PROBE_FAILED_NO_SECRET_OUTPUT')
        raise SystemExit(1)
