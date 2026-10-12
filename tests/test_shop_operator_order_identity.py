from core.shopping.guest_operator import GuestOperatorAdapter,order_date,order_identity

def test_operator_list_detail_and_admin_keep_identity_and_korean_order_date():
    a=GuestOperatorAdapter(ledger=None,store=None)
    row={'provider_order_id':901,'phone':'01000000000','state':'PENDING_REVIEW','requested_at':'2026-10-11T23:30:00Z','delivery':{'first_name':'테스트고객','address_1':'테스트주소'},'quote':{'final_total':'200000','currency':'KRW','line_items':[{'name':'테스트 코트','option':'L / 카멜','quantity':1}]}}
    a.rows=lambda:[row]
    for text in [a.list_message(),a.detail_message(901)]:
        assert '테스트고객' in text and '01000000000' in text and '테스트 코트' in text and '2026-10-12 08:30' in text
    admin=a.admin_orders()[0];assert admin['customer_name']=='테스트고객'
    assert '테스트 코트' in order_identity(admin)
    row['requested_at']=None;row['delivery']={}
    assert '일자 미확인' in a.list_message() and '이름 미등록' in a.list_message()

def test_order_date_preserves_unknown_and_converts_timezone():
    assert order_date('broken')=='일자 미확인'
    assert order_date(None)=='일자 미확인'
    assert order_date('2026-10-11T23:30:00+00:00')=='2026-10-12 08:30'
