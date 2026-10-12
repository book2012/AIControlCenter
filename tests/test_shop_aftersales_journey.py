"""Dialog approvals and customer notices share isolated cancellation/return state."""
import pytest
from core.shopping.operator_conversation import OperatorConversation
from core.shopping.customer_order_notices import order_notices
from test_shop_aftersales_dev import fixture,CUSTOMER,ORDER
from test_shop_return_stock_workflow import delivered,provider
from test_shop_telegram_fulfillment_sms import adapter
ACTOR='telegram-user-123'

def engine(tmp_path,op,plans):
    return OperatorConversation(path=tmp_path/'dialogue.sqlite3',judge=lambda text,context:plans.pop(0),orders=op.admin_orders,products=lambda:[],validate_product=lambda text:None,executor=lambda text,i,actor:op.resolve(text,i)[2])

def test_dialog_cancel_requires_approval_restores_once_and_hides_deposit(tmp_path):
    store,draft=fixture(tmp_path,[1000.0]);calls=[]
    store.stock_cancellation=lambda row,draft:calls.append(row['provider_order_id']) or {'outcome':'STOCK_CANCELLED','order_id':ORDER}
    plans=[{'action':'CANCEL','order_id':ORDER}];e=engine(tmp_path,adapter(store,draft),plans)
    assert '처리할까요' in e.handle('15번 취소해줘',1,ACTOR) and not calls
    assert '확인 대기' in e.handle('응',2,'telegram-user-456') and not calls
    reply=e.handle('응',3,ACTOR);assert '취소완료' in reply and e.handle('응',3,ACTOR)==reply and calls==[ORDER]
    order=store.lookup(CUSTOMER,str(ORDER),'+821012345678','+821012345678')
    notice=order_notices(order,{'name':'bank','account':'NO-DEPOSIT','holder':'holder'})
    assert notice[0]['kind']=='CANCELLED' and 'NO-DEPOSIT' not in str(notice)
    assert store.payment(ORDER)['state']=='AWAITING_DEPOSIT'

def test_dialog_return_receipt_and_inspection_do_not_claim_refund_payment(tmp_path):
    store,case,_=delivered(tmp_path);calls=[];store.stock_return=provider(calls)
    _,draft=store._customer_order(CUSTOMER,ORDER);op=adapter(store,draft)
    store.decide(case['id'],True)
    plans=[{'action':'RETURN_RECEIVE','case_id':case['id']},{'action':'RETURN_INSPECT','case_id':case['id']}]
    e=engine(tmp_path,op,plans)
    assert '처리할까요' in e.handle('반품 도착했어',1,ACTOR) and not calls
    assert '회수완료' in e.handle('응',2,ACTOR) and not calls
    assert '재판매 가능' in e.handle('검수 끝났고 재판매 가능해',3,ACTOR) and not calls
    reply=e.handle('응',4,ACTOR);assert '환불 검토 필요' in reply
    assert e.handle('응',4,ACTOR)==reply and calls==[case['id']]
    order=store.lookup(CUSTOMER,str(ORDER),'+821012345678','+821012345678')
    notice=order_notices(order,{'name':'bank','account':'NO-DEPOSIT','holder':'holder'})
    assert order['return_status']['state']=='RETURN_RESTOCKED' and order['payment']['state']=='PAID'
    assert notice[0]['kind']=='RETURN' and '환불완료' not in str(notice) and 'NO-DEPOSIT' not in str(notice)

@pytest.mark.parametrize('approved',[True,False])
def test_case_decision_conflict_is_denied_and_command_is_truthful(tmp_path,approved):
    store,case,_=delivered(tmp_path);first=store.decide(case['id'],approved)
    with pytest.raises(ValueError,match='CASE_DECISION_CONFLICT'):store.decide(case['id'],not approved)
    command=('환불거절 #' if approved else '환불승인 #')+case['id']
    reply=store.operator_command(command,1)
    assert '기존 승인·거절' in reply
    assert store.case(CUSTOMER,case['id'])['state']==first['state']
