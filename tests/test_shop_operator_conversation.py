"""Actor-scoped dialogue, explicit approval, deterministic execution and reminder boundaries."""
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
from types import SimpleNamespace
import pytest
from core.shopping.operator_conversation import OperatorConversation
from core.shopping.operator_intent import validate_plan,LocalOperatorJudge
from ops.macos.shopping.dev_product_operator import parse_command

ACTOR="telegram-user-123"
OTHER="telegram-user-456"

@pytest.fixture
def env(tmp_path):
    now=[1000]
    rows=[dict(order_id=15,phone="01012345678",display_state="AWAITING_DEPOSIT"),
          dict(order_id=16,phone="01012345678",display_state="PENDING_REVIEW")]
    products=[dict(id="coat",name="카멜 코트",category="outer",inventory={"S":1,"M":1,"L":1},size_options=["S","M","L"])]
    calls=[];plans=[];contexts=[]
    def judge(text,context):
        contexts.append(context)
        return plans.pop(0)
    def execute(*args):
        calls.append(args)
        return "처리 완료"
    engine=OperatorConversation(path=tmp_path/"dialogue.sqlite3",judge=judge,orders=lambda:rows,
        products=lambda:products,validate_product=lambda text:parse_command(text,products),
        executor=execute,clock=lambda:now[0])
    return SimpleNamespace(engine=engine,now=now,rows=rows,products=products,calls=calls,plans=plans,contexts=contexts)

def test_natural_payment_requires_bound_confirmation_and_duplicate_is_once(env):
    e=env.engine;env.plans.append({"action":"DEPOSIT_CONFIRM","order_id":15})
    reply=e.handle("15번 입금했어",1,ACTOR)
    assert "입금확인 #15" in reply and "응" in reply and env.calls==[]
    assert e.handle("응",2,OTHER).startswith("확인 대기 중인 요청이 없습니다")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:e.handle("응",3,ACTOR),range(2)))
    assert results==["처리 완료"]*2 and env.calls==[("입금확인 #15",3,ACTOR)]
    assert e.handle("응",4,ACTOR).startswith("확인 대기 중인 요청이 없습니다")
    with pytest.raises(ValueError,match="CONFLICT"):e.handle("다른 요청",3,ACTOR)

def test_ambiguous_phone_followup_keeps_intent_and_never_guesses_order(env):
    env.plans.append({"action":"DEPOSIT_CONFIRM","phone":"01012345678"})
    reply=env.engine.handle("이 고객 입금했어",1,ACTOR)
    assert "#15" in reply and "#16" in reply and "01012345678" in reply
    env.plans.append({"action":"DEPOSIT_CONFIRM","order_id":16})
    assert "입금확인 #16" in env.engine.handle("16번",2,ACTOR)
    assert env.calls==[]
    assert env.contexts[-1]["previous_plan"]["action"]=="DEPOSIT_CONFIRM"
    env.engine.handle("응",3,ACTOR)
    assert env.calls[0][0]=="입금확인 #16"

def test_references_are_actor_scoped_and_expire(env):
    env.plans.extend([{"action":"ORDER_DETAIL","order_id":15},{"action":"UNKNOWN"},{"action":"UNKNOWN"}])
    env.engine.handle("15번 자세히",1,ACTOR)
    env.engine.handle("그 고객 입금했어",2,OTHER)
    assert env.contexts[-1]["last_order_id"] is None
    env.now[0]+=1801
    env.engine.handle("그 고객 상태",3,ACTOR)
    assert env.contexts[-1]["last_order_id"] is None

def test_mutation_expiry_cancel_and_unknown_result_never_retry(env):
    env.plans.append({"action":"CANCEL","order_id":15})
    env.engine.handle("15번 취소해줘",1,ACTOR);env.now[0]+=1801
    assert "시간이 지났" in env.engine.handle("응",2,ACTOR) and not env.calls
    env.plans.append({"action":"CANCEL","order_id":15})
    env.engine.handle("15번 취소해줘",3,ACTOR)
    assert "요청을 취소" in env.engine.handle("아니",4,ACTOR) and not env.calls
    env.plans.append({"action":"CANCEL","order_id":15})
    env.engine.handle("15번 취소해줘",5,ACTOR)
    def failed(*args):
        env.calls.append(args)
        raise TimeoutError()
    env.engine.executor=failed
    assert "불확실" in env.engine.handle("응",6,ACTOR)
    env.engine.handle("응",7,ACTOR)
    env.plans.append({"action":"CANCEL","order_id":15})
    assert "이전 처리 결과" in env.engine.handle("다시 취소",8,ACTOR)
    assert len(env.calls)==1

def test_unknown_claim_survives_restart_without_execution(env):
    e=env.engine
    with sqlite3.connect(e.path) as c:
        import hashlib
        c.execute("INSERT INTO dialogue_turns VALUES(?,?,?,'CLAIMED',NULL)",(9,ACTOR,hashlib.sha256("응".encode()).hexdigest()))
    assert "이전 처리 결과" in e.handle("응",9,ACTOR) and not env.calls

def test_shipping_requires_tracking_and_current_order_identity(env):
    env.plans.append({"action":"SHIP","order_id":999,"carrier":"CJ대한통운","tracking":"1234567890"})
    assert "찾지 못" in env.engine.handle("999 배송",1,ACTOR) and not env.calls
    env.plans.append({"action":"SHIP","order_id":15})
    assert "택배사와 운송장번호" in env.engine.handle("15번 보냈어",2,ACTOR)
    env.plans.append({"action":"SHIP","carrier":"CJ대한통운","tracking":"1234567890"})
    reply=env.engine.handle("CJ 1234567890",3,ACTOR)
    assert "주문 확인" in reply and "배송 #15 CJ대한통운 1234567890" in reply
    env.engine.handle("응",4,ACTOR)
    assert env.calls[0][0]=="배송 #15 CJ대한통운 1234567890"

def test_product_option_validation_before_approval(env):
    env.plans.append({"action":"SET_STOCK","product":"카멜 코트","quantity":0})
    assert "옵션을 구분" in env.engine.handle("카멜 코트 품절",1,ACTOR) and not env.calls
    env.plans.append({"action":"SET_STOCK","size":"L"})
    assert "카멜 코트 L 재고 0개" in env.engine.handle("L만",2,ACTOR)
    env.engine.handle("응",3,ACTOR)
    assert env.calls[0][0]=="카멜 코트 L 재고 0개로 변경"

def test_return_inspection_is_explicit_and_case_bound(env):
    env.plans.extend([{"action":"RETURN_RECEIVE","case_id":"a1b2c3d4"},{"action":"RETURN_INSPECT","case_id":"a1b2c3d4"}])
    assert "검수" not in env.engine.handle("반품 도착했어",1,ACTOR)
    env.engine.handle("응",2,ACTOR)
    assert env.calls[0][0]=="반품 회수 #a1b2c3d4"
    assert "재판매 가능" in env.engine.handle("검수완료 재판매가능",3,ACTOR)

def test_website_job_is_queued_only_after_approval_and_never_runs_executor(env):
    env.plans.append({"action":"WEBSITE_TASK"})
    request="홈페이지 로고 글씨를 조금 크게 해줘"
    assert "처리할까요" in env.engine.handle(request,1,ACTOR)
    assert "대기 요청이 없습니다" in env.engine.website_list(ACTOR)
    assert "Codex 작업 대기" in env.engine.handle("응",2,ACTOR)
    assert not env.calls
    assert request in env.engine.website_list(ACTOR)
    assert "대기 요청이 없습니다" in env.engine.website_list(OTHER)

def test_reminders_send_once_cancel_when_done_and_never_retry_unknown(env):
    for row in env.rows:row["display_state"]="AWAITING_DEPOSIT"
    env.plans.append({"action":"DEPOSIT_CONFIRM","order_id":15})
    env.engine.handle("입금 15",1,ACTOR)
    messages=[];transport=SimpleNamespace(send_message=lambda text:messages.append(text))
    assert env.engine.notify_one(transport)=="IDLE"
    env.now[0]+=901
    assert env.engine.notify_one(transport)=="SENT"
    assert messages[0].startswith("안녕하세요 agachichi 입니다\n[개발]") and "입금확인 #15" in messages[0]
    assert env.engine.notify_one(transport)=="IDLE"
    env.plans.append({"action":"SET_PRICE","product":"카멜 코트","price":200000})
    env.engine.handle("가격 바꿔줘",2,ACTOR)
    env.now[0]+=901
    def unknown(text):
        messages.append(text)
        raise TimeoutError()
    assert env.engine.notify_one(SimpleNamespace(send_message=unknown))=="UNKNOWN"
    assert env.engine.notify_one(transport)=="IDLE" and len(messages)==2
    env.engine.handle("응",3,ACTOR)
    assert env.engine.notify_one(transport)=="IDLE"

def test_order_followup_uses_current_state_and_cancels_stale_notice(env):
    e=env.engine;messages=[];transport=SimpleNamespace(send_message=lambda s:messages.append(s))
    env.rows[:]=[dict(order_id=15,phone="01012345678",display_state="READY_TO_SHIP")]
    e.notify_one(transport);env.now[0]+=3601
    env.rows[0]["display_state"]="SHIPPED"
    assert e.notify_one(transport)=="IDLE" and not messages
    env.rows.append(dict(order_id=17,phone="01012345678",display_state="PENDING_REVIEW"))
    e.notify_one(transport);env.now[0]+=1801
    assert e.notify_one(transport)=="SENT" and "#17" in messages[0]
    assert e.notify_one(transport)=="IDLE"

@pytest.mark.parametrize("plan",[
    {"action":"SHELL","command":"sudo rm -rf /"},
    {"action":"DEPOSIT_CONFIRM","order_id":True},
    {"action":"SET_STOCK","quantity":-1},
    {"action":"SET_PRICE","price":10000001},
    {"action":"CANCEL","order_id":15,"environment":"PROD"},
    {"action":"SHIP","tracking":"123\n456"},
    {"action":"RETURN_INSPECT","case_id":"invalid"},
    {"action":"ORDER_LIST","phone":"010-1234-5678"}])
def test_invalid_model_data_never_becomes_command(plan):
    with pytest.raises(ValueError):validate_plan(plan)

def test_local_model_uses_private_loopback_and_explicit_template_and_schema():
    captured=[]
    doc=dict(done=True,done_reason="stop",response=json.dumps({"action":"DEPOSIT_CONFIRM","order_id":15}))
    response=SimpleNamespace(status_code=200,content=b"safe",json=lambda:doc)
    session=SimpleNamespace(post=lambda *a,**kw:(captured.append((a,kw)) or response))
    judge=LocalOperatorJudge(session=session)
    assert judge("15번 입금",{})["order_id"]==15
    args,kw=captured[0]
    assert args==("http://127.0.0.1:11434/api/generate",)
    assert kw["allow_redirects"] is False and session.trust_env is False
    assert kw["json"]["raw"] is True and "</think>" in kw["json"]["prompt"]
    doc["done_reason"]="length"
    with pytest.raises(ValueError,match="UNAVAILABLE"):judge("15번 입금",{})

def test_explicit_slots_override_model_omissions_without_guessing():
    from core.shopping.operator_intent import resolve_explicit_slots
    assert resolve_explicit_slots({"action":"DEPOSIT_CONFIRM"},"그 고객 입금했어",{"last_order_id":15})["order_id"]==15
    assert "order_id" not in resolve_explicit_slots({"action":"DEPOSIT_CONFIRM"},"그 고객 입금했어",{})
    plan=resolve_explicit_slots({"action":"SHIP"},"15번 CJ대한통운 운송장 1234567890로 보냈어",{})
    assert plan=={"action":"SHIP","order_id":15,"carrier":"CJ대한통운","tracking":"1234567890"}
    assert resolve_explicit_slots({"action":"SHIP","order_id":177},"Ch택배 운송장 1234567",{})=={"action":"SHIP","order_id":177,"carrier":"Ch택배","tracking":"1234567"}
    assert resolve_explicit_slots({"action":"SHIP","order_id":177},"Ch택배 1234567",{})=={"action":"SHIP","order_id":177,"carrier":"Ch택배","tracking":"1234567"}
    assert resolve_explicit_slots({"action":"SHIP","order_id":177},"택배사 ch택배 운숭장번호 12345667",{})=={"action":"SHIP","order_id":177,"carrier":"ch택배","tracking":"12345667"}
    assert resolve_explicit_slots({"action":"DEPOSIT_CONFIRM","order_id":99},"15번 입금했어",{})["order_id"]==15


def test_exact_registered_product_recovers_omission_without_ambiguity():
    from core.shopping.operator_intent import resolve_explicit_slots
    context={"products":[{"name":"테스트 카멜 코트"},{"name":"브라운 코트"}]}
    plan=resolve_explicit_slots({"action":"SET_PRICE","price":200000},"테스트 카멜 코트 20만원으로 바꿔줘",context)
    assert plan["product"]=="테스트 카멜 코트"
    assert "product" not in resolve_explicit_slots({"action":"SET_PRICE","price":200000},"테스트 카멜 코트와 브라운 코트 가격 바꿔줘",context)
    assert "product" not in resolve_explicit_slots({"action":"SET_PRICE","price":200000},"카멜 옷 가격 바꿔줘",context)
    assert "product" not in resolve_explicit_slots({"action":"UNKNOWN"},"테스트 카멜 코트 삭제를 위해 셸 실행",context)


def test_explicit_order_reads_cannot_inherit_pending_payment_intent(env):
    env.plans.append({"action":"DEPOSIT_CONFIRM","order_id":15})
    env.engine.handle("15번 입금했어",1,ACTOR)
    for i,text,command in [(2,"주문목록","주문목록"),(3,"01012345678 주문목록","01012345678 주문목록"),(4,"주문상세 #16","주문상세 #16")]:
        env.engine.handle(text,i,ACTOR)
        assert env.calls[-1][0]==command
    assert all('입금확인' not in x[0] for x in env.calls)
    assert env.plans==[]
