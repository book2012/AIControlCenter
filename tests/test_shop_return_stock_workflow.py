import sqlite3
from concurrent.futures import ThreadPoolExecutor
import pytest
from test_shop_aftersales_dev import fixture,CUSTOMER,ORDER
from ops.macos.shopping.dev_aftersales import DevAftersalesStore

def delivered(tmp_path):
    clock=[1000.0];store,draft=fixture(tmp_path,clock);store.confirm_payment(ORDER)
    store.mark_shipped(ORDER,'CJ대한통운','1234567890');store.mark_delivered(ORDER)
    case=store.create_case(CUSTOMER,{'order_id':ORDER,'kind':'RETURN','reason':'반품 요청'})
    return store,case,clock

def provider(calls):
    def apply(row,draft,case):
        calls.append(case['id']);return {'outcome':'STOCK_RETURNED','order_id':ORDER,'case_id':case['id']}
    return apply

def test_approval_and_receipt_do_not_restock_inspection_does_once(tmp_path):
    store,case,clock=delivered(tmp_path);calls=[];store.stock_return=provider(calls)
    with pytest.raises(ValueError,match='APPROVAL_REQUIRED'):store.receive_return(case['id'])
    store.decide(case['id'],True);assert not calls
    with pytest.raises(ValueError,match='RECEIPT_REQUIRED'):store.inspect_return(case['id'])
    assert store.receive_return(case['id'])['state']=='RETURN_RECEIVED' and not calls
    first=store.inspect_return(case['id']);assert first['state']=='RETURN_RESTOCKED' and calls==[case['id']]
    before=store.case(CUSTOMER,case['id'])['updated'];clock[0]+=300
    assert store.inspect_return(case['id'])==first
    restarted=DevAftersalesStore(store.path,store.attachments,ledger=store.ledger,checkout=store.checkout,catalog=store.catalog,stock_return=store.stock_return,clock=lambda:clock[0])
    assert restarted.inspect_return(case['id'])==first and calls==[case['id']]
    assert restarted.case(CUSTOMER,case['id'])['updated']==before
    assert restarted.payment(ORDER)['state']=='PAID'
    order=restarted.customer_orders(CUSTOMER)[0]
    assert not order['return_available'] and not order['exchange_available']
    with pytest.raises(ValueError,match='CASE_ALREADY_ACTIVE'):restarted.create_case(CUSTOMER,{'order_id':ORDER,'kind':'RETURN','reason':'다시 반품'})

def test_unknown_return_is_read_only_reconciled_not_replayed(tmp_path):
    store,case,_=delivered(tmp_path);store.decide(case['id'],True);store.receive_return(case['id'])
    class Provider:
        writes=0;found=False
        def __call__(self,*args):self.writes+=1;raise TimeoutError()
        def reconcile(self,row,draft,case):return {'outcome':'STOCK_RETURNED','order_id':ORDER,'case_id':case['id']} if self.found else None
    p=Provider();store.stock_return=p
    for _ in range(2):
        with pytest.raises(ValueError,match='RECONCILIATION_REQUIRED'):store.inspect_return(case['id'])
    assert p.writes==1 and store.return_status(ORDER)['state']=='RETURN_RESTOCK_UNKNOWN'
    with pytest.raises(ValueError):store.reconcile_return(case['id'])
    p.found=True;assert store.reconcile_return(case['id'])['state']=='RETURN_RESTOCKED' and p.writes==1

def test_concurrent_inspection_restores_once(tmp_path):
    store,case,_=delivered(tmp_path);store.decide(case['id'],True);store.receive_return(case['id']);calls=[];store.stock_return=provider(calls)
    def attempt(_):
        try:return store.inspect_return(case['id'])['state']
        except ValueError:return 'BLOCKED'
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(attempt,range(8)))
    assert 'RETURN_RESTOCKED' in results and calls==[case['id']]

def test_exchange_case_cannot_restore_return_stock(tmp_path):
    store,case,_=delivered(tmp_path)
    with sqlite3.connect(store.path) as c:c.execute("UPDATE cases SET kind='SIZE_EXCHANGE' WHERE id=?",(case['id'],))
    store.stock_return=lambda *a:pytest.fail('exchange restock')
    with pytest.raises(ValueError,match='RETURN_CASE_REQUIRED'):store.receive_return(case['id'])

def test_concurrent_return_case_creation_admits_one(tmp_path):
    store,case,_=delivered(tmp_path);store.decide(case['id'],False)
    def create(_):
        try:return store.create_case(CUSTOMER,{'order_id':ORDER,'kind':'RETURN','reason':'새 반품 요청'})['id']
        except ValueError:return None
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(create,range(2)))
    assert sum(x is not None for x in results)==1

def test_operator_return_commands_and_duplicates(tmp_path):
    store,case,_=delivered(tmp_path);calls=[];store.stock_return=provider(calls)
    store.operator_command('환불승인 #'+case['id'],1)
    assert not calls
    assert '회수완료' in store.operator_command('반품 회수 #'+case['id'],2)
    first=store.operator_command('반품 검수완료 #'+case['id'],3)
    assert '환불 검토 필요' in first and store.operator_command('반품 검수완료 #'+case['id'],3)==first
    assert store.operator_command('반품 복원확인 #'+case['id'],4)==first and calls==[case['id']]

def test_return_notices_and_operator_listing_do_not_claim_refund(tmp_path):
    store,case,_=delivered(tmp_path);store.stock_return=provider([])
    store.decide(case['id'],True);store.receive_return(case['id']);store.inspect_return(case['id'])
    from core.shopping.customer_order_notices import order_notices
    notice=order_notices(store.customer_orders(CUSTOMER)[0],{'name':'bank','account':'SECRET BANK','holder':'holder'})
    assert notice[0]['kind']=='RETURN' and '환불은 운영자 검토' in notice[0]['message']
    assert 'SECRET BANK' not in notice[0]['message'] and '환불완료' not in notice[0]['message']
    from test_shop_telegram_fulfillment_sms import adapter
    _,draft=store._customer_order(CUSTOMER,ORDER)
    op=adapter(store,draft)
    assert op.display_state(op.rows()[0])=='RETURN_RESTOCKED'
    assert '환불검토' in op.resolve('주문목록',9)[2]
