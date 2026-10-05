"""Durable order/Telegram/operator DEV chain with network-denied fake providers."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
import json
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
from pydantic import SecretStr
import pytest

from test_shop_order_001c_session_composition import api, clients, composed, deny_network, intent, authenticated_request
from test_shop_ai_001b3_session_api import issue, auth_headers, ORIGIN, SECRET, COOKIE_NAME, SECOND_PAYLOAD, SECOND_SECRET
from test_shop_order_001c_catalog_resolution import Catalog, product
from core.shopping.order_core import SQLiteOrderCreateLedger, OrderCreateOperationUnknownOutcome
from core.shopping.order_core.dev_app import create_order_dev_app
from core.shopping.order_core.ledger import (
    BASE_SCHEMA_SQL, APPLICATION_ID, OrderLedgerError, _execute_schema, _result_json, _result_digest,
)
from core.shopping.order_core.telegram import (
    OrderTelegramIntegration, OrderTelegramTransport, TelegramDeliveryUnknown, TelegramDeliveryRejected,
)
from core.shopping.product_drafts.persistence.path_policy import IsolatedTestDatabasePathPolicy

CHAT=-100123456789
OPERATOR=99123
REFERENCE=hashlib.sha256(b"order-review:order-session-001").hexdigest()[:24]


class Transport:
    chat_id=CHAT
    def __init__(self): self.messages=[];self.updates=[];self.error=None;self.offsets=[]
    def send_message(self,text):
        self.messages.append(text)
        if self.error: raise self.error
        return len(self.messages)
    def get_updates(self,offset):
        self.offsets.append(offset)
        return self.updates


def integration(store,transport):
    return OrderTelegramIntegration(ledger=store,transport=transport,operator_chat_id=CHAT,
                                   operator_user_ids=frozenset({OPERATOR}))


def update(update_id=1,command='confirm',*,chat=CHAT,user=OPERATOR,bot=False):
    return {"update_id":update_id,"message":{"chat":{"id":chat},"from":{"id":user,"is_bot":bot},
            "text":"/order_"+command+" "+REFERENCE}}


def complete(api,composed):
    app,store,writer=composed
    req=authenticated_request(api)
    app.execute(req,intent())
    return req


def test_full_dev_http_order_telegram_confirm_and_customer_status(api,composed):
    app,store,writer=composed
    transport=Transport();telegram=integration(store,transport)
    dev=create_order_dev_app(session_boundary=api.boundary,catalog=Catalog(product()),ledger=store,
                             writer=writer,telegram_integration=telegram)
    issued=issue(api)
    headers={**auth_headers(issued),"Cookie":COOKIE_NAME+'='+SECRET}
    with TestClient(dev,base_url=ORIGIN) as client:
        page=client.get('/order-preview/123')
        assert page.status_code==200 and '>주문하기<' in page.text
        assert client.get('/__order-dev/storefront-order.js').status_code==200
        payload={"line_items":[{"product_id":"123","quantity":1}],"idempotency_key":"order-session-001"}
        assert client.post('/shopping/orders',json=payload,headers=headers).status_code==201
        status_path='/shopping/orders/operations/order-session-001'
        assert client.get(status_path,headers=headers).json()['review_state']=='PENDING_REVIEW'
        assert telegram.dispatch_one()['outcome']=='SENT'
        assert REFERENCE in transport.messages[0]
        transport.updates=[update()]
        assert telegram.poll_once()['results'][0]['outcome']=='CONFIRMED'
        assert client.get(status_path,headers=headers).json()['review_state']=='CONFIRMED'
        assert telegram.dispatch_one()['outcome']=='SENT'
        assert '운영자 확인 완료' in transport.messages[-1]
        assert client.post('/shopping/orders',json=payload,headers=headers).status_code==200
        assert telegram.dispatch_one()['outcome']=='IDLE'
        assert len(writer.calls)==1 and len(transport.messages)==2
        assert store.telegram_offset()==2
        assert SECRET not in ''.join(transport.messages)
        for value in transport.messages:
            assert 'AG-CUS-' not in value and 'AG-SES-' not in value and 'Canonical Product' not in value


def test_restart_and_concurrent_workers_send_once(api,composed,tmp_path):
    complete(api,composed);_,store,_=composed
    transport=Transport()
    second=SQLiteOrderCreateLedger(tmp_path/'orders.sqlite3',clock=lambda:api.time.now,
                                  path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    drivers=[integration(store,transport),integration(second,transport)]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda driver: driver.dispatch_one()['outcome'],drivers))
    assert sorted(results)==['IDLE','SENT'] and len(transport.messages)==1


@pytest.mark.parametrize('error,outcome,state',[(TelegramDeliveryUnknown('UNKNOWN'),'UNKNOWN_OUTCOME','UNKNOWN_OUTCOME'),
    (TelegramDeliveryRejected('DENIED'),'FAILED','FAILED'),(RuntimeError('credential-marker'),'UNKNOWN_OUTCOME','UNKNOWN_OUTCOME')])
def test_send_failure_never_auto_retries_order_or_notification(api,composed,error,outcome,state):
    req=complete(api,composed);app,store,writer=composed
    transport=Transport();transport.error=error;telegram=integration(store,transport)
    assert telegram.dispatch_one()['outcome']==outcome
    assert store.notification_statuses()[0]['state']==state
    assert telegram.dispatch_one()['outcome']=='IDLE'
    assert app.execute(req,intent()).idempotent_replay
    assert len(writer.calls)==1 and len(transport.messages)==1


def test_completion_and_notification_are_atomic(api,composed,monkeypatch):
    app,store,writer=composed
    req=authenticated_request(api)
    def fail(*args): raise sqlite3.OperationalError('injected outbox insert failure')
    monkeypatch.setattr(store,'_enqueue_notification',fail)
    with pytest.raises(sqlite3.OperationalError):app.execute(req,intent())
    assert store.inspect_operation('order-session-001')['state']=='UNKNOWN_OUTCOME'
    assert store.notification_statuses()==[]
    with pytest.raises(OrderCreateOperationUnknownOutcome):app.execute(req,intent())
    assert len(writer.calls)==1


def test_crashed_notification_claim_stays_blocked(api,composed):
    complete(api,composed);_,store,_=composed
    assert store.claim_notification() is not None
    transport=Transport()
    assert integration(store,transport).dispatch_one()['outcome']=='IDLE'
    assert transport.messages==[] and store.notification_statuses()[0]['state']=='CLAIMED'


@pytest.mark.parametrize('change',[{'chat':CHAT+1},{'user':OPERATOR+1},{'bot':True},{'user':True}])
def test_operator_allowlist_prevents_mutation(api,composed,change):
    req=complete(api,composed);app,store,_=composed
    transport=Transport();transport.updates=[update(**change)]
    assert integration(store,transport).poll_once()['results'][0]['outcome']=='IGNORED'
    assert app.operation_status(req,'order-session-001')['review_state']=='PENDING_REVIEW'
    assert len(store.notification_statuses())==1


def test_operator_duplicate_conflicting_decision_and_cursor_survive_restart(api,composed,tmp_path):
    req=complete(api,composed);app,store,_=composed
    transport=Transport();telegram=integration(store,transport)
    transport.updates=[update(5,'reject')]
    assert telegram.poll_once()['results'][0]['outcome']=='REJECTED'
    assert telegram.poll_once()['results'][0]['outcome']=='DUPLICATE'
    transport.updates=[update(6,'confirm')]
    assert telegram.poll_once()['results'][0]['outcome']=='CONFLICT'
    assert app.operation_status(req,'order-session-001')['review_state']=='REJECTED'
    assert len(store.notification_statuses())==2
    second=SQLiteOrderCreateLedger(tmp_path/'orders.sqlite3',clock=lambda:api.time.now,
                                  path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    assert second.telegram_offset()==7


def test_status_command_returns_current_review_via_durable_outbox(api,composed):
    complete(api,composed);_,store,_=composed
    transport=Transport();telegram=integration(store,transport)
    telegram.dispatch_one()
    transport.updates=[update(1,'confirm'),update(2,'status')]
    result=telegram.poll_once()
    assert [item['outcome'] for item in result['results']]==['CONFIRMED','CONFIRMED']
    telegram.dispatch_one();telegram.dispatch_one()
    assert '운영자 확인 완료' in transport.messages[-1]


def test_customer_status_requires_current_same_session(api,composed):
    req=complete(api,composed);app,store,_=composed
    api.client.cookies.clear()
    response=issue(api,payload=SECOND_PAYLOAD)
    from test_shop_order_001c_session_composition import request
    other=request({**auth_headers(response),'Cookie':COOKIE_NAME+'='+SECOND_SECRET})
    assert app.operation_status(other,'order-session-001') is None
    api.time.now+=timedelta(minutes=30)
    from core.api.dependencies.customer_session import SessionAPIDenied
    with pytest.raises(SessionAPIDenied):app.operation_status(req,'order-session-001')


@pytest.mark.parametrize('status,body,error',[
    (200,{'ok':True,'result':{'message_id':1,'chat':{'id':CHAT}}},None),
    (200,{'ok':False},TelegramDeliveryUnknown),
    (200,{'ok':True,'result':{'message_id':True,'chat':{'id':CHAT}}},TelegramDeliveryUnknown),
    (200,{'ok':True,'result':{'message_id':1,'chat':{'id':CHAT+1}}},TelegramDeliveryUnknown),
    (302,{},TelegramDeliveryUnknown),(500,{},TelegramDeliveryUnknown),(429,{},TelegramDeliveryRejected),
    (403,{},TelegramDeliveryRejected)])
def test_transport_receipt_and_redirect_checks(status,body,error):
    session=Mock();session.post.return_value=SimpleNamespace(status_code=status,json=lambda:body)
    transport=OrderTelegramTransport(token=SecretStr('123:'+('a'*30)),chat_id=CHAT,session=session)
    if error:
        with pytest.raises(error):transport.send_message('bounded safe text')
    else:assert transport.send_message('bounded safe text')==1
    assert session.post.call_args.kwargs['allow_redirects'] is False
    assert 'a'*30 not in repr(transport)


def test_transport_does_not_leak_credential_in_exceptions():
    session=Mock();session.post.side_effect=RuntimeError('https://api.telegram.org/bot123:credential-marker/sendMessage')
    transport=OrderTelegramTransport(token=SecretStr('123:'+('a'*30)),chat_id=CHAT,session=session)
    with pytest.raises(TelegramDeliveryUnknown) as error:transport.send_message('safe')
    assert 'credential-marker' not in str(error.value)


def test_delivery_receipt_persistence_failure_is_blocked(api,composed,monkeypatch):
    complete(api,composed);_,store,_=composed
    transport=Transport()
    def fail(*args,**kwargs): raise sqlite3.OperationalError('injected persistence failure')
    monkeypatch.setattr(store,'finish_notification',fail)
    telegram=integration(store,transport)
    assert telegram.dispatch_one()['outcome']=='UNKNOWN_OUTCOME'
    assert telegram.dispatch_one()['outcome']=='IDLE' and len(transport.messages)==1


def test_operator_audit_and_outbox_cannot_be_deleted(api,composed):
    complete(api,composed);_,store,_=composed
    connection=sqlite3.connect(store.database_path)
    try:
        for table in ['shopping_order_operator_review','shopping_order_notification_outbox']:
            with pytest.raises(sqlite3.DatabaseError): connection.execute('DELETE FROM '+table)
    finally:connection.close()


@pytest.mark.parametrize("corrupt", [None, "binding", "digest"])
def test_explicit_v1_migration_preserves_completed_and_is_idempotent(api,composed,tmp_path,corrupt):
    app,store,_=composed
    result=app.execute(authenticated_request(api),intent())
    path=tmp_path/'old-v1.sqlite3'
    connection=sqlite3.connect(path,isolation_level=None)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute(f'PRAGMA application_id={APPLICATION_ID}')
    _execute_schema(connection,BASE_SCHEMA_SQL)
    connection.execute("INSERT INTO order_ledger_metadata VALUES (1,?,'SHOP_ORDER_001B')",(api.time.now.isoformat(),))
    # Copy the original immutable operation/audit rows, preserving all evidence.
    original=sqlite3.connect(store.database_path)
    try:
        row=list(original.execute('SELECT * FROM shopping_order_create_operations').fetchone())
        columns=[v[1] for v in original.execute('PRAGMA table_info(shopping_order_create_operations)')]
        if corrupt:
            import hashlib
            document=json.loads(row[columns.index('result_json')])
            document['idempotency_key']='another-order-operation'
            raw=json.dumps(document,sort_keys=True,separators=(',',':'),ensure_ascii=False)
            row[columns.index('result_json')]=raw
            if corrupt=='binding':row[columns.index('result_digest')]=hashlib.sha256(raw.encode()).hexdigest()
        connection.execute('INSERT INTO shopping_order_create_operations VALUES ('+','.join('?' for _ in row)+')',row)
        for row in original.execute('SELECT * FROM shopping_order_create_audit'):
            connection.execute('INSERT INTO shopping_order_create_audit VALUES ('+','.join('?' for _ in row)+')',row)
    finally:original.close()
    connection.execute('PRAGMA user_version=1');connection.close()
    old=SQLiteOrderCreateLedger(path,clock=lambda:api.time.now,path_policy=IsolatedTestDatabasePathPolicy(tmp_path))
    with pytest.raises(OrderLedgerError,match='unsupported'):old.initialize()
    if corrupt:
        with pytest.raises(OrderLedgerError,match="invalid"):old.migrate_v1()
        check=sqlite3.connect(path)
        try:
            assert check.execute("PRAGMA user_version").fetchone()[0]==1
            assert not check.execute("SELECT 1 FROM sqlite_master WHERE name='shopping_order_notification_outbox'").fetchone()
        finally:check.close()
        return
    old.migrate_v1();old.migrate_v1()
    assert old.inspect_operation('order-session-001')['command_digest']==result.command_digest
    assert len(old.notification_statuses())==1 and old.notification_statuses()[0]['state']=='PENDING'
