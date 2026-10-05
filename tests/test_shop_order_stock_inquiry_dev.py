from types import SimpleNamespace
import sqlite3
from unittest.mock import Mock
import pytest
from test_shop_order_001d_telegram import api,clients,deny_network,composed,complete,Transport,update,CHAT,OPERATOR,REFERENCE
from core.shopping.order_core.telegram import OrderTelegramIntegration
from ops.macos.shopping.dev_order_operator import DevOperatorAdapter,local_phone
from ops.macos.shopping.dev_inquiry_queue import DevInquiryQueue,sanitize
from core.shopping.order_core.guest_checkout import PrivateCheckoutStore
from test_shop_guest_checkout import draft

def test_confirm_requires_stock_and_duplicate_never_reduces_again(api,composed):
    req=complete(api,composed);app,ledger,_=composed;guard=Mock(return_value=False)
    transport=Transport();driver=OrderTelegramIntegration(ledger=ledger,transport=transport,
        operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),confirmation_guard=guard)
    transport.updates=[update(1)]
    assert driver.poll_once()["results"][0]["outcome"]=="STOCK_BLOCKED"
    assert app.operation_status(req,'order-session-001')["review_state"]=="PENDING_REVIEW"
    guard.return_value=True;transport.updates=[update(2)]
    assert driver.poll_once()["results"][0]["outcome"]=="CONFIRMED"
    transport.updates=[update(3)]
    assert driver.poll_once()["results"][0]["outcome"]=="ALREADY_CONFIRMED"
    assert guard.call_count==2
def test_disallowed_operator_cannot_invoke_stock_or_alias(api,composed):
    complete(api,composed);_,ledger,_=composed;guard=Mock();adapter=Mock()
    t=Transport();t.updates=[update(user=OPERATOR+1)]
    d=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),confirmation_guard=guard,operator_adapter=adapter)
    d.poll_once();guard.assert_not_called();adapter.resolve.assert_not_called()
def test_phone_alias_ambiguity_and_order_selection():
    adapter=DevOperatorAdapter(ledger=None,store=None)
    rows=[dict(phone="01012345678",state="PENDING_REVIEW",reference="a"*24,provider_order_id=1),
          dict(phone="01012345678",state="PENDING_REVIEW",reference="b"*24,provider_order_id=2)]
    adapter.rows=lambda:rows
    assert adapter.resolve("01012345678 고객 주문확인")[1] is None
    assert "#1" in adapter.resolve("01012345678 고객 주문확인")[2]
    assert adapter.resolve("010-1234-5678 고객님 주문확인 #2")[:2]==("b"*24,"CONFIRMED")
    rows.pop()
    assert adapter.resolve("01012345678고객 주문확인")[:2]==("a"*24,"CONFIRMED")
    assert adapter.resolve("01012345678 주문확인")[1] is None
def test_inquiry_escalation_answer_approval_expiry_and_exclusion(tmp_path):
    clock=[100.];t=Transport();q=DevInquiryQueue(tmp_path/"inquiries.sqlite3",t,clock=lambda:clock[0])
    ticket=q.submit("10","세탁 방법이 궁금해요")
    assert q.status(ticket["inquiry_token"])["answer"] is None
    q.dispatch_one();q.dispatch_one()
    assert len(t.messages)==1
    cmd="문의 #"+ticket["inquiry_id"]
    q.command(cmd+" 답변 찬물로 손세탁해 주세요.",1)
    assert q.status(ticket["inquiry_token"])["answer"]=="찬물로 손세탁해 주세요."
    assert q.lookup("10","세탁 방법이 궁금해요") is None
    q.command(cmd+" 학습승인",2)
    assert q.lookup("10","세탁 방법이 궁금해요")=="찬물로 손세탁해 주세요."
    assert q.lookup("11","세탁 방법이 궁금해요") is None
    assert q.export(tmp_path/"dataset.jsonl")==1
    q.command(cmd+" 학습제외",3);assert q.lookup("10","세탁 방법이 궁금해요") is None
    q.command(cmd+" 학습승인",4);clock[0]+=31*86400
    assert q.lookup("10","세탁 방법이 궁금해요") is None
def test_inquiry_redaction_no_contacts_in_messages_dataset_and_private_mode(tmp_path):
    t=Transport();q=DevInquiryQueue(tmp_path/"q.sqlite3",t)
    ticket=q.submit("10","연락 01012345678 test@example.com\n주소: 서울 테스트로 12\n세탁?")
    q.dispatch_one();message=t.messages[0]
    assert "01012345678" not in message and "test@example.com" not in message and "테스트로" not in message
    reply=q.command("문의 #"+ticket["inquiry_id"]+" 답변 01012345678로 연락",1)
    assert "저장할 수 없습니다" in reply
    assert q.status(ticket["inquiry_token"])["answer"] is None
    assert q.path.stat().st_mode&0o077==0
def test_inquiry_unknown_delivery_never_auto_resends(tmp_path):
    t=Transport();t.error=RuntimeError("unknown");q=DevInquiryQueue(tmp_path/"q.sqlite3",t)
    q.submit("10","배송기간?");q.dispatch_one();q.dispatch_one()
    assert len(t.messages)==1
    with sqlite3.connect(q.path) as c:assert c.execute("SELECT delivery FROM inquiries").fetchone()[0]=="UNKNOWN_OUTCOME"
def test_guard_unknown_outcome_rolls_back_review_and_cursor(api,composed):
    req=complete(api,composed);app,ledger,_=composed
    def guard(*a):raise RuntimeError("ambiguous stock")
    with pytest.raises(RuntimeError):ledger.process_operator_update(1,reference=REFERENCE,decision="CONFIRMED",actor_reference="telegram-user-99123",confirmation_guard=guard)
    assert ledger.telegram_offset()==0
    assert app.operation_status(req,'order-session-001')["review_state"]=="PENDING_REVIEW"

def test_guest_escalation_operator_reply_and_approved_automation_http(api,composed,tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from core.shopping.order_core.guest_chat_app import mount_guest_chat
    from ops.macos.shopping.dev_inquiry_queue import mount_inquiry_status
    from test_shop_guest_chat import Catalog
    from test_shop_ai_001b3_session_api import ORIGIN
    _,ledger,_=composed;t=Transport();q=DevInquiryQueue(tmp_path/"inquiries.sqlite3",t)
    app=FastAPI();mount_guest_chat(app,catalog=Catalog(),session_boundary=api.boundary,
        intent_classifier=lambda m,p:"OPERATOR",inquiry_queue=q);mount_inquiry_status(app,q)
    adapter=DevOperatorAdapter(ledger=ledger,store=PrivateCheckoutStore(tmp_path/"draft.sqlite3"),inquiry_queue=q)
    driver=OrderTelegramIntegration(ledger=ledger,transport=t,operator_chat_id=CHAT,operator_user_ids=frozenset({OPERATOR}),operator_adapter=adapter)
    with TestClient(app,base_url=ORIGIN) as client:
        payload={"product_id":"10","message":"교환 기준은 어떻게 되나요?"}
        r=client.post("/__order-dev/chat/inquiry",json=payload,headers={"Origin":ORIGIN})
        assert r.status_code==200 and r.json()["action"]=="OPERATOR_QUEUED"
        ticket=r.json();q.dispatch_one();assert len(t.messages)==1
        def command(id,text):
            u=update(id);u["message"]["text"]="문의 #"+ticket["inquiry_id"]+" "+text;t.updates=[u];driver.poll_once()
        command(1,"답변 DEV 정책은 운영자 상담 후 결정합니다.")
        status=client.get("/__order-dev/chat/inquiries/"+ticket["inquiry_token"]).json()
        assert status["answer"]=="DEV 정책은 운영자 상담 후 결정합니다."
        command(2,"학습승인")
        r=client.post("/__order-dev/chat/inquiry",json=payload,headers={"Origin":ORIGIN})
        assert r.json()["answer_engine"]=="OPERATOR_APPROVED_FAQ"
        assert r.json()["message"]==status["answer"]
        before=len(t.messages);driver.poll_once();assert len(t.messages)==before
        assert client.get("/__order-dev/chat/inquiries/"+"a"*48).status_code==404
def test_compound_shipping_question_never_auto_answers_just_stock():
    from core.shopping.order_core.guest_chat import GuestShoppingChat
    from test_shop_guest_chat import Catalog
    called=[]
    def classifier(m,p):called.append(m);return "STOCK"
    result=GuestShoppingChat(Catalog(),intent_classifier=classifier).answer({"product_id":"10","message":"재고 있나요 그리고 배송은 언제 되나요?"})
    assert result["action"]=="OPERATOR_REQUIRED" and called==[]
