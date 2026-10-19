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


def test_admin_paid_pre_shipment_cancel_requires_approved_refund_case(tmp_path):
    store,_=fixture(tmp_path,[1000.0])
    with pytest.raises(ValueError,match='REFUND_PAYMENT_REQUIRED'):
        store.admin_create_case(ORDER,{'order_id':ORDER,'kind':'RETURN','reason':'주문 취소 환불'})
    store.confirm_payment(ORDER)
    case=store.admin_create_case(ORDER,{'order_id':ORDER,'kind':'RETURN','reason':'주문 취소 환불'})
    assert case['state']=='REQUESTED'
    store.decide(case['id'],True)
    calls=[]
    store.stock_cancellation=lambda row,draft:(calls.append(row['provider_order_id']) or {'outcome':'STOCK_CANCELLED','order_id':ORDER})
    result=store.cancel_order(ORDER)
    assert result['state']=='CANCELLED' and calls==[ORDER]
    assert store.payment(ORDER)['state']=='PAID'
    with pytest.raises(ValueError,match='ORDER_CANCELLATION_ACTIVE'):
        store.admin_create_case(ORDER,{'order_id':ORDER,'kind':'RETURN','reason':'중복 환불'})


def test_approved_paid_order_cannot_be_cancelled_after_shipment(tmp_path):
    store,_=fixture(tmp_path,[1000.0]);store.confirm_payment(ORDER)
    store.mark_shipped(ORDER,'CJ대한통운','1234567890')
    case=store.admin_create_case(ORDER,{'order_id':ORDER,'kind':'RETURN','reason':'배송 중 환불 문의'})
    store.decide(case['id'],True)
    store.stock_cancellation=lambda *a:pytest.fail('shipped order stock must not be cancelled')
    with pytest.raises(ValueError,match='SHIPPED_CANCELLATION_DENIED'):
        store.cancel_order(ORDER,refund_case_id=case['id'])
    assert store.cancellation(ORDER)['state']=='NONE'


def test_pending_review_order_can_be_cancelled_without_stock_reduction(tmp_path):
    store,_=fixture(tmp_path,[1000.0])
    store.ledger.review_state="PENDING_REVIEW"
    rows=store.ledger.operator_orders()
    for row in rows:row["state"]="PENDING_REVIEW"
    store.ledger.operator_orders=lambda:rows
    calls=[]
    store.stock_cancellation=lambda row,draft:(calls.append(row["state"]) or {"outcome":"STOCK_CANCELLED","order_id":ORDER})
    result=store.cancel_order(ORDER)
    assert result["state"]=="CANCELLED" and calls==["PENDING_REVIEW"]
    history=store.order_status_history(ORDER)
    assert [(event["from_state"],event["to_state"]) for event in history if event["entity"]=="cancellation"]==[
        ("NONE","SENDING"),("SENDING","CANCELLED")]
    assert [event["changed_at"] for event in history if event["entity"]=="cancellation"]==[1000.0,1000.0]


def test_order_status_history_records_each_payment_delivery_and_case_transition(tmp_path):
    clock=[1000.0]
    store,_=fixture(tmp_path,clock)
    store.confirm_payment(ORDER)
    clock[0]+=1;store.mark_shipped(ORDER,"CJ대한통운","1234567890")
    clock[0]+=1;store.mark_delivered(ORDER)
    case=store.create_case("customer",{"order_id":ORDER,"kind":"RETURN","reason":"단순 변심","reason_type":"CHANGE_OF_MIND"})
    clock[0]+=1;store.decide(case["id"],True)
    clock[0]+=1;store.receive_return(case["id"])
    store.stock_return=lambda row,draft,case:{"outcome":"STOCK_RETURNED","order_id":ORDER,"case_id":case["id"]}
    clock[0]+=1;store.inspect_return(case["id"])
    history=store.order_status_history(ORDER)
    assert [(event["entity"],event["from_state"],event["to_state"]) for event in history]==[
        ("payment","AWAITING_DEPOSIT","PAID"),
        ("fulfillment","NOT_SHIPPED","SHIPPED"),
        ("fulfillment","SHIPPED","DELIVERED"),
        ("case","NONE","REQUESTED"),
        ("case","REQUESTED","RETURN_APPROVED"),
        ("case","RETURN_APPROVED","RETURN_RECEIVED"),
        ("return_stock","RETURN_RECEIVED","SENDING"),
        ("case","RETURN_RECEIVED","RETURN_RESTOCK_PENDING"),
        ("return_stock","SENDING","RESTORED"),
        ("case","RETURN_RESTOCK_PENDING","RETURN_RESTOCKED"),
    ]
    assert all(event["changed_at"] is not None for event in history)
    assert store.order_status_history(999)==[]


def test_phone_bound_order_cancel_command_handles_pending_review_safely(tmp_path):
    from core.shopping.guest_operator import GuestOperatorAdapter
    store,_=fixture(tmp_path,[1000.0])
    rows=store.ledger.operator_orders()
    for row in rows:row["state"]="PENDING_REVIEW"
    store.ledger.operator_orders=lambda:rows
    provider_calls=[]
    store.stock_cancellation=lambda row,draft:(provider_calls.append(row["state"]) or {"outcome":"STOCK_CANCELLED","order_id":ORDER})
    adapter=GuestOperatorAdapter(ledger=store.ledger,store=store.checkout,aftersales=store)
    order=adapter.admin_orders(10)[0]
    command=order["phone"]+" 고객 주문 취소 #"+order["order_number"]
    _,decision,reply=adapter.resolve(command,update_id=551,actor="telegram-user-test")
    assert decision is None and "취소완료" in reply
    assert provider_calls==["PENDING_REVIEW"]
    assert store.cancellation(ORDER)["state"]=="CANCELLED"
