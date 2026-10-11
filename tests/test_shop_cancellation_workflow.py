import pytest
from test_shop_aftersales_dev import fixture,ORDER
from ops.macos.shopping.dev_aftersales import DevAftersalesStore

def test_cancel_replay_and_restart_restore_once_and_block_payment_shipping(tmp_path):
    store,_=fixture(tmp_path,[1000.0]);calls=[]
    def provider(row,draft):
        calls.append(row['provider_order_id']);return {'outcome':'STOCK_CANCELLED','order_id':ORDER}
    store.stock_cancellation=provider
    first=store.cancel_order(ORDER)
    assert first['state']=='CANCELLED' and store.cancel_order(ORDER)==first and calls==[ORDER]
    restarted=DevAftersalesStore(store.path,store.attachments,ledger=store.ledger,checkout=store.checkout,catalog=store.catalog,stock_cancellation=provider)
    assert restarted.cancel_order(ORDER)==first and calls==[ORDER]
    for action in [lambda:restarted.confirm_payment(ORDER),lambda:restarted.mark_shipped(ORDER,'CJ대한통운','1234567890')]:
        with pytest.raises(ValueError,match='ORDER_CANCELLATION_ACTIVE'):action()

@pytest.mark.parametrize('state',['paid','shipped'])
def test_paid_or_shipped_cancellation_never_calls_provider(tmp_path,state):
    store,_=fixture(tmp_path,[1000.0]);store.confirm_payment(ORDER)
    if state=='shipped':
        store.mark_shipped(ORDER,'CJ대한통운','1234567890')
        import sqlite3
        with sqlite3.connect(store.path) as c:c.execute('DELETE FROM payments WHERE order_id=?',(ORDER,))
    store.stock_cancellation=lambda *a:pytest.fail('unsafe stock restoration')
    with pytest.raises(ValueError,match='REQUIRES_REFUND_REVIEW|SHIPPED_CANCELLATION_DENIED'):store.cancel_order(ORDER)
    assert store.cancellation(ORDER)['state']=='NONE'

def test_unknown_cancellation_never_resends_and_freezes_fulfillment(tmp_path):
    store,_=fixture(tmp_path,[1000.0]);calls=[]
    def provider(*args):calls.append(1);raise TimeoutError()
    store.stock_cancellation=provider
    for _ in range(2):
        with pytest.raises(ValueError,match='RECONCILIATION_REQUIRED'):store.cancel_order(ORDER)
    assert calls==[1] and store.cancellation(ORDER)['state']=='UNKNOWN'
    with pytest.raises(ValueError,match='ORDER_CANCELLATION_ACTIVE'):store.confirm_payment(ORDER)


def test_ambiguous_provider_commit_is_reconciled_read_only(tmp_path):
    store,_=fixture(tmp_path,[1000.0])
    class Provider:
        def __init__(self):self.writes=0;self.reads=0;self.found=False
        def __call__(self,row,draft):
            self.writes+=1
            with pytest.raises(ValueError,match='ORDER_CANCELLATION_ACTIVE'):store.confirm_payment(ORDER)
            raise TimeoutError()
        def reconcile(self,row,draft):
            self.reads+=1
            return {'outcome':'STOCK_CANCELLED','order_id':ORDER} if self.found else None
    provider=Provider();store.stock_cancellation=provider
    with pytest.raises(ValueError):store.cancel_order(ORDER)
    with pytest.raises(ValueError):store.reconcile_cancellation(ORDER)
    assert store.cancellation(ORDER)['state']=='UNKNOWN'
    provider.found=True
    assert store.reconcile_cancellation(ORDER)['state']=='CANCELLED'
    assert store.cancel_order(ORDER)['state']=='CANCELLED'
    assert provider.writes==1 and provider.reads==2
