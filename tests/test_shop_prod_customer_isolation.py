from datetime import datetime,timezone,timedelta
import hashlib,sqlite3,uuid
from types import SimpleNamespace
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretBytes
from core.shopping.guest_phone_runtime import GuestPhoneBridge,PhoneDenied,mount_phone_routes,COOKIE
from core.shopping.customer_persistence import initialize_schema
from core.shopping.customer_session_service import CustomerSessionService
from core.api.dependencies.customer_session import CustomerSessionBoundary,get_customer_session_boundary
from core.api.routes.customer_sessions import router
from core.shopping.ports.phone_verification import ChallengeStartResult,ProviderVerificationIdentifier,ChallengeStatus,ChallengeVerificationResult,VerificationStatus
from core.shopping.guest_checkout_runtime import mount_checkout_routes,mount_order_lookup
from core.shopping.order_core.guest_checkout import PrivateCheckoutStore
from core.shopping.operator_environment import OperatorEnvironmentRouter

class FakePort:
    def __init__(self,phone,clock,calls,failures):self.phone=phone;self.clock=clock;self.calls=calls;self.failures=failures
    def start_challenge(self,r):
        self.calls.append(("start",self.phone))
        if self.phone in self.failures:raise TimeoutError()
        return ChallengeStartResult(provider_source=r.provider_source,provider_verification_id=ProviderVerificationIdentifier(value="VE"+hashlib.md5(str(r.challenge_reference).encode()).hexdigest()),purpose=r.purpose,challenge_reference=r.challenge_reference,replay_reference=r.replay_reference,phone_binding=r.subject.phone_binding,status=ChallengeStatus.PENDING,started_at=self.clock())
    def verify_challenge(self,r):
        self.calls.append(("check",self.phone))
        return ChallengeVerificationResult(provider_source=r.provider_source,provider_verification_id=r.provider_verification_id,purpose=r.purpose,challenge_reference=r.challenge_reference,replay_reference=r.replay_reference,phone_binding=r.phone_binding,status=VerificationStatus.SUCCESS if r.otp=="123456" else VerificationStatus.REJECTED,verified_at=self.clock())

@pytest.fixture
def setup(tmp_path):
    now=[datetime.now(timezone.utc)];calls=[];failures=set();path=tmp_path/"customers.sqlite3";initialize_schema(path)
    kwargs=dict(cfg={"environment":"PROD","enabled":True},binding_key=b"b"*32,customer_path=path,bridge_path=tmp_path/"bridge.sqlite3",clock=lambda:now[0],port_factory=lambda phone:FakePort(phone,lambda:now[0],calls,failures))
    return GuestPhoneBridge(**kwargs),kwargs,now,calls,failures

def verified(bridge,phone):
    token,_=bridge.start(phone)
    return str(bridge.verify(token,"123456").receipt.customer_id)

def test_two_phones_have_distinct_durable_identities_and_independent_quotas(setup):
    bridge,kwargs,now,calls,_=setup
    a=verified(bridge,"01012345678");b=verified(bridge,"01087654321")
    assert a!=b and bridge.verified_phone(a)=="+821012345678" and bridge.verified_phone(b)=="+821087654321"
    restarted=GuestPhoneBridge(**kwargs);assert restarted.verified_phone(a)=="+821012345678"
    now[0]+=timedelta(seconds=301)
    assert verified(restarted,"+821012345678")==a
    assert len(calls)==6
    with sqlite3.connect(bridge.path) as c:
        assert all(cell!="123456" for row in c.execute("SELECT * FROM guest_phone_browser") for cell in row)

def test_phone_switch_and_unverified_identity_cannot_inherit_browser_auth(setup):
    bridge,_,_,calls,_=setup
    token,_=bridge.start("01012345678")
    with pytest.raises(PhoneDenied):bridge.start("01087654321",token)
    with sqlite3.connect(bridge.path) as c:customer=c.execute("SELECT customer FROM guest_identity WHERE phone=?",("+821012345678",)).fetchone()[0]
    with pytest.raises(PhoneDenied):bridge.verified_phone(customer)
    with pytest.raises(PhoneDenied):bridge.verify("A"*43,"123456")
    assert len(calls)==1

def test_unknown_sms_does_not_resend_or_block_other_customer(setup):
    bridge,_,_,calls,failures=setup;failures.add("+821012345678")
    with pytest.raises(PhoneDenied):bridge.start("01012345678")
    with pytest.raises(PhoneDenied):bridge.start("01012345678")
    assert verified(bridge,"01087654321")
    assert sum(v==("start","+821012345678") for v in calls)==1

def test_wrong_otp_replay_and_expiry_fail_closed(setup):
    bridge,_,now,calls,_=setup;token,_=bridge.start("01012345678")
    with pytest.raises(PhoneDenied):bridge.verify(token,"000000")
    with pytest.raises(PhoneDenied):bridge.verify(token,"123456")
    token,_=bridge.start("01087654321");now[0]+=timedelta(minutes=6)
    with pytest.raises(PhoneDenied):bridge.verify(token,"123456")
    assert len(calls)==3

def test_two_real_core_sessions_use_distinct_receipts_and_no_phone_disclosure(setup):
    bridge,_,now,calls,_=setup;evidence={}
    boundary=CustomerSessionBoundary(service=CustomerSessionService(str(bridge.customer_path)),trusted_origin="https://bokstory.duckdns.org",csrf_key=SecretBytes(b"c"*32),clock=lambda:now[0],resolve_evidence=lambda payload:evidence.pop((payload.receipt_id,payload.browser_challenge)))
    def register(value):
        r="VRF-"+uuid.uuid4().hex.upper();c="CHL-"+uuid.uuid4().hex.upper();evidence[r,c]=value;return dict(receipt_id=r,browser_challenge=c)
    app=FastAPI();mount_phone_routes(app,bridge=bridge,boundary=boundary,register_evidence=register)
    app.include_router(router);app.dependency_overrides[get_customer_session_boundary]=lambda:boundary
    clients=[TestClient(app,base_url="https://bokstory.duckdns.org") for _ in range(2)];ids=[]
    for client,phone in zip(clients,["01012345678","01087654321"]):
        headers={"Origin":"https://bokstory.duckdns.org"}
        assert client.post("/shopping/phone/start",json={"phone":phone,"consent":True},headers={"Origin":"https://dev.bokstory.duckdns.org"}).status_code==422
        assert client.post("/shopping/phone/start",json={"phone":phone,"consent":True},headers=headers).status_code==200
        result=client.post("/shopping/phone/check",json={"code":"123456"},headers=headers)
        assert result.status_code==201 and phone not in result.text and "123456" not in result.text
        session=client.get("/shopping/auth/session");assert session.status_code==200
        secret=client.cookies.get("__Host-aicc_customer")
        ids.append(boundary.authenticate(secret,now=now[0]).customer_id)
    assert ids[0]!=ids[1] and len(calls)==4

def test_checkout_drafts_bind_phone_customer_and_session(setup,tmp_path):
    bridge,_,_,_,_=setup;a=verified(bridge,"01012345678");b=verified(bridge,"01087654321")
    store=PrivateCheckoutStore(tmp_path/"draft.sqlite3")
    class App:
        def _authenticate(self,request,write=True):return SimpleNamespace(customer_id=request.headers["X-Test-Customer"],session_id=request.headers["X-Test-Session"])
    app=FastAPI()
    quote=lambda catalog,cart:{"line_items":[],"items_total":"100","shipping_fee":"3000","total_tax":"0","final_total":"3100","currency":"KRW","shipping_policy":"PROD_FIXED_SHIPPING"}
    mount_checkout_routes(app,store=store,verified_phone=bridge.verified_phone,application=App(),catalog=None,ledger=None,quote=quote)
    client=TestClient(app);body={"cart":{"line_items":[{"product_id":"10","variation_id":"11","quantity":1}]},"delivery":{"recipient":"테스트","postcode":"12345","address1":"테스트 주소 123","address2":""}}
    draft=client.post("/shopping/checkout/prepare",json=body,headers={"X-Test-Customer":a,"X-Test-Session":"session-a"})
    assert draft.status_code==200
    value=store.get(draft.json()["draft_id"],a,"session-a")
    assert value["body"]["billing"]["phone"]==bridge.verified_phone(a)
    with pytest.raises(ValueError):store.get(draft.json()["draft_id"],b,"session-a")
    with pytest.raises(ValueError):store.get(draft.json()["draft_id"],a,"session-b")

def test_lookup_uses_authenticated_customer_phone_and_generic_denial(setup):
    bridge,_,_,_,_=setup;a=verified(bridge,"01012345678");b=verified(bridge,"01087654321")
    class App:
        def _authenticate(self,request,write=True):return SimpleNamespace(customer_id=request.headers["X-Test-Customer"])
    class Store:
        def lookup(self,customer,number,input_phone,phone):
            if customer!=a or number!="42" or phone!="+821012345678" or input_phone!=phone:raise ValueError()
            return {"order_number":"42","order_id":42,"items":[],"total":"0","currency":"KRW","review_state":"PENDING_REVIEW"}
    app=FastAPI();mount_order_lookup(app,store=Store(),application=App(),verified_phone=bridge.verified_phone)
    client=TestClient(app);body={"order_number":"42","phone":"+821012345678"}
    assert client.post("/shopping/orders/lookup",json=body,headers={"X-Test-Customer":a}).status_code==200
    denied=client.post("/shopping/orders/lookup",json=body,headers={"X-Test-Customer":b})
    assert denied.status_code==403 and "42" not in denied.text and "12345678" not in denied.text

def test_telegram_environment_selection_and_sender_authority_precede_mutation():
    calls=[];r=OperatorEnvironmentRouter(dev=lambda text:calls.append(("DEV",text)) or "완료",prod=lambda text:calls.append(("PROD",text)) or "완료",default="PROD",chat_id=7,user_ids={8})
    assert "[운영]" in r.dispatch("아우터 리스트",chat_id=7,user_id=8)
    assert "[개발]" in r.dispatch("개발 재고 변경",chat_id=7,user_id=8)
    assert "[운영]" in r.dispatch("PROD:주문확인",chat_id=7,user_id=8)
    with pytest.raises(ValueError):r.dispatch("운영 재고 변경",chat_id=7,user_id=9)
    assert calls==[("PROD","아우터 리스트"),("DEV","재고 변경"),("PROD","주문확인")]


def test_telegram_update_environment_survives_default_change_and_restart(tmp_path):
    from core.shopping.operator_environment import DurableOperatorEnvironmentRouter
    calls=[]
    cfg=dict(dev=lambda text,uid:calls.append(("DEV",text,uid)) or "확인",prod=lambda text,uid:calls.append(("PROD",text,uid)) or "확인",chat_id=7,user_ids={8},database_path=tmp_path/"updates.sqlite3")
    first=DurableOperatorEnvironmentRouter(default="DEV",**cfg)
    response=first.dispatch("주문확인",chat_id=7,user_id=8,update_id=100)
    second=DurableOperatorEnvironmentRouter(default="PROD",**cfg)
    assert second.dispatch("주문확인",chat_id=7,user_id=8,update_id=100)==response
    assert calls==[("DEV","주문확인",100)]
    assert "[운영]" in second.dispatch("주문확인",chat_id=7,user_id=8,update_id=101)
    with pytest.raises(ValueError):second.dispatch("다른 주문확인",chat_id=7,user_id=8,update_id=101)

def test_telegram_unknown_handler_result_never_replays(tmp_path):
    from core.shopping.operator_environment import DurableOperatorEnvironmentRouter
    calls=[]
    def failure(text,uid):calls.append(uid);raise TimeoutError()
    r=DurableOperatorEnvironmentRouter(default="PROD",dev=failure,prod=failure,chat_id=7,user_ids={8},database_path=tmp_path/"updates.sqlite3")
    with pytest.raises(TimeoutError):r.dispatch("입금확인 #42",chat_id=7,user_id=8,update_id=100)
    with pytest.raises(ValueError,match="INSPECTION"):r.dispatch("입금확인 #42",chat_id=7,user_id=8,update_id=100)
    assert calls==[100]


def test_suspended_customer_cannot_be_reactivated_by_phone_bridge(setup):
    from core.shopping.customer_persistence import customer_from_connection,SQLiteCustomerSessionStore
    from core.shopping.customer_identity import CustomerState
    bridge,_,_,_,_=setup
    customer=verified(bridge,"01012345678")
    with sqlite3.connect(bridge.customer_path) as c:
        c.row_factory=sqlite3.Row;existing=customer_from_connection(c,customer)
    SQLiteCustomerSessionStore(bridge.customer_path).save_customer(existing.model_copy(update={"state":CustomerState.SUSPENDED}))
    with pytest.raises(PhoneDenied):bridge.verified_phone(customer)
    with pytest.raises(PhoneDenied):bridge.start("01012345678")
    with sqlite3.connect(bridge.customer_path) as c:
        c.row_factory=sqlite3.Row;assert customer_from_connection(c,customer).state.value=="SUSPENDED"


def test_production_twilio_port_is_bound_to_each_customer_phone():
    from core.shopping.guest_phone_runtime import CustomerTwilioVerifyPort
    from test_shop_dev_guest_phone import Session
    cfg={"environment":"PROD","enabled":True,"provider":"twilio_verify","credentials":{"account_sid":"AC"+"a"*32,"verify_service_sid":"VA"+"b"*32,"auth_token":"fake-secret"}}
    raw={"account_sid":cfg["credentials"]["account_sid"],"service_sid":cfg["credentials"]["verify_service_sid"],"sid":"VE"+"c"*32,"to":"+821012345678","channel":"sms","status":"pending"}
    session=Session(raw)
    port=CustomerTwilioVerifyPort(cfg,b"b"*32,"+821087654321",session=session)
    with pytest.raises(PhoneDenied):port.invoke("Verifications",{"To":"+821087654321","Channel":"sms"})
    assert session.calls[0][0][0]=="https://verify.twilio.com/v2/Services/VA"+("b"*32)+"/Verifications"
    assert session.calls[0][1]["allow_redirects"] is False and session.trust_env is False
    with pytest.raises(ValueError):CustomerTwilioVerifyPort({**cfg,"environment":"DEV"},b"b"*32,"+821087654321",session=session)

def test_production_phone_bridge_rejects_missing_live_credentials_before_start(setup):
    _,kwargs,_,calls,_=setup;kwargs={**kwargs,"port_factory":None}
    with pytest.raises((KeyError,ValueError)):GuestPhoneBridge(**kwargs)
    assert calls==[]
