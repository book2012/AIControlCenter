from datetime import datetime,timezone,timedelta
from pathlib import Path
import secrets,sqlite3,uuid
import pytest
from pydantic import SecretBytes
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.shopping.customer_persistence import initialize_schema
from core.shopping.ports.phone_verification import *
from core.shopping.phone_normalization import derive_phone_binding,normalize_phone
from ops.macos.shopping.dev_guest_phone import *
from core.api.dependencies.customer_session import CustomerSessionBoundary
from core.shopping.customer_session_service import CustomerSessionService
from core.api.routes.customer_sessions import router
def cfg():
 return dict(environment="DEV",provider="twilio_verify",enabled=True,test_phone="+821012345678",
 credentials=dict(account_sid="AC"+"a"*32,auth_token="private-token",verify_service_sid="VA"+"b"*32),
 guest_customer_id=ref("CUS"),guest_contact_ref=ref("CON"))
class Port:
 def __init__(self,clock):self.clock=clock;self.calls=[];self.last_error_code=None;self.fail=False
 def start_challenge(self,r):
  self.calls.append("start")
  if self.fail:raise TimeoutError("SECRET PHONE")
  return ChallengeStartResult(provider_source=r.provider_source,provider_verification_id=ProviderVerificationIdentifier(value="VE"+"c"*32),purpose=r.purpose,challenge_reference=r.challenge_reference,replay_reference=r.replay_reference,phone_binding=r.subject.phone_binding,status=ChallengeStatus.PENDING,started_at=self.clock())
 def verify_challenge(self,r):
  self.calls.append("verify")
  return ChallengeVerificationResult(provider_source=r.provider_source,provider_verification_id=r.provider_verification_id,purpose=r.purpose,challenge_reference=r.challenge_reference,replay_reference=r.replay_reference,phone_binding=r.phone_binding,status=VerificationStatus.SUCCESS if r.otp=="123456" else VerificationStatus.REJECTED,verified_at=self.clock())
@pytest.fixture
def setup(tmp_path):
 now=[datetime.now(timezone.utc)];clock=lambda:now[0];p=tmp_path/"customers.sqlite3";initialize_schema(p);port=Port(clock)
 bridge=DevPhoneBridge(cfg=cfg(),binding_key=b"binding-secret",customer_path=p,bridge_path=tmp_path/"bridge.sqlite3",clock=clock,port=port)
 return bridge,port,now
def test_success_is_real_service_receipt_and_browser_bound(setup):
 b,p,_=setup;token,sent=b.start("01012345678");assert sent
 assert b.start("+821012345678",token)==(token,False)
 with pytest.raises(PhoneDenied):b.start("+821012345678")
 out=b.verify(token,"123456")
 assert out.receipt.customer_id==b.customer_id and p.calls==["start","verify"]
 with pytest.raises(PhoneDenied):b.verify(token,"123456")
 with sqlite3.connect(b.customer_path) as c:assert c.execute("SELECT status FROM shopping_verification_challenges").fetchone()[0]=="VERIFIED"
def test_other_phone_and_fake_browser_rejected_without_provider(setup):
 b,p,_=setup
 with pytest.raises(PhoneDenied):b.start("+821099999999")
 with pytest.raises(PhoneDenied):b.verify("A"*43,"123456")
 assert p.calls==[]
def test_timeout_never_automatically_resends(setup):
 b,p,_=setup;p.fail=True
 with pytest.raises(PhoneDenied):b.start("+821012345678")
 with pytest.raises(PhoneDenied):b.start("+821012345678")
 assert p.calls==["start"]
def test_expiry_and_wrong_code_do_not_verify(setup):
 b,p,now=setup;token,_=b.start("+821012345678");now[0]+=timedelta(minutes=6)
 with pytest.raises(PhoneDenied):b.verify(token,"123456")
 assert p.calls==["start"]
def test_wrong_otp_terminal_and_no_retry(setup):
 b,p,_=setup;token,_=b.start("+821012345678")
 with pytest.raises(PhoneDenied):b.verify(token,"000000")
 with pytest.raises(PhoneDenied):b.verify(token,"123456")
 assert p.calls==["start","verify"]
class Response:
 status_code=201
 def __init__(self,document):self.document=document;self.headers={"Content-Type":"application/json"}
 def iter_content(self,chunk_size):yield json.dumps(self.document).encode()
 def close(self):pass
class Session:
 trust_env=True
 def __init__(self,document):self.document=document;self.calls=[]
 def post(self,*a,**k):self.calls.append((a,k));return Response(self.document)
def document(c):
 return dict(account_sid=c["credentials"]["account_sid"],service_sid=c["credentials"]["verify_service_sid"],sid="VE"+"c"*32,to=c["test_phone"],channel="sms",status="pending",date_created=datetime.now(timezone.utc).isoformat(),date_updated=datetime.now(timezone.utc).isoformat())
@pytest.mark.parametrize("field,value",[("to","+821099999999"),("channel","email"),("service_sid","VA"+"d"*32),("account_sid","AC"+"d"*32),("sid","invalid")])
def test_twilio_response_binding_rejected(field,value):
 c=cfg();s=Session({**document(c),field:value});p=FixedDevTwilioPort(c,b"binding",session=s)
 with pytest.raises(PhoneDenied):p.invoke("Verifications",{})
def test_pinned_tls_endpoint_and_no_redirect():
 c=cfg();s=Session(document(c));p=FixedDevTwilioPort(c,b"binding",session=s);p.invoke("Verifications",{})
 args,kwargs=s.calls[0];assert args[0].startswith("https://verify.twilio.com/v2/Services/VA")
 assert kwargs["allow_redirects"] is False and kwargs["timeout"]==15 and s.trust_env is False
def test_http_phone_routes_require_consent_origin_and_issue_session(setup):
 b,p,now=setup;evidence={}
 boundary=CustomerSessionBoundary(service=CustomerSessionService(str(b.customer_path)),trusted_origin="https://dev.bokstory.duckdns.org",csrf_key=SecretBytes(b"c"*32),clock=lambda:now[0],resolve_evidence=lambda payload:evidence.pop((payload.receipt_id,payload.browser_challenge)))
 def register(value):
  r="VRF-"+uuid.uuid4().hex.upper();c="CHL-"+uuid.uuid4().hex.upper();evidence[r,c]=value;return dict(receipt_id=r,browser_challenge=c)
 app=FastAPI();mount_phone_routes(app,bridge=b,boundary=boundary,register_evidence=register)
 from core.api.dependencies.customer_session import get_customer_session_boundary
 app.include_router(router);app.dependency_overrides[get_customer_session_boundary]=lambda:boundary
 client=TestClient(app,base_url="https://dev.bokstory.duckdns.org");headers={"Origin":"https://dev.bokstory.duckdns.org"}
 assert client.post("/__order-dev/phone/start",json={"phone":"+821012345678","consent":False},headers=headers).status_code==422
 assert p.calls==[]
 start=client.post("/__order-dev/phone/start",json={"phone":"+821012345678","consent":True},headers=headers)
 assert start.status_code==200 and COOKIE in client.cookies
 result=client.post("/__order-dev/phone/check",json={"code":"123456"},headers=headers)
 assert result.status_code==201 and "__Host-aicc_customer" in client.cookies
 assert client.get("/shopping/auth/session").status_code==200
 assert "123456" not in result.text and "+821012345678" not in result.text

def test_twilio_endpoint_cannot_escape_verify_scope():
 c=cfg();s=Session(document(c));p=FixedDevTwilioPort(c,b"binding",session=s)
 with pytest.raises(PhoneDenied):p.invoke("../../Accounts",{})
 assert s.calls==[]

def test_small_twilio_clock_skew_waits_without_rewriting_provider_evidence():
 c=cfg();now=[datetime.now(timezone.utc)];waits=[];future=now[0]+timedelta(seconds=2)
 def sleep(seconds):waits.append(seconds);now[0]+=timedelta(seconds=seconds)
 raw={**document(c),"date_created":future.isoformat()};session=Session(raw)
 port=FixedDevTwilioPort(c,b"binding",session=session,clock=lambda:now[0],sleeper=sleep)
 stamp=port.provider_timestamp(raw["date_created"])
 assert stamp==future and stamp<=now[0] and waits==[2.02]
 with pytest.raises(PhoneDenied):port.provider_timestamp((now[0]+timedelta(seconds=6)).isoformat())
 assert len(waits)==1

def test_future_provider_time_without_advancing_local_clock_denies():
 c=cfg();now=datetime.now(timezone.utc);port=FixedDevTwilioPort(c,b"binding",session=Session(document(c)),clock=lambda:now,sleeper=lambda seconds:None)
 with pytest.raises(PhoneDenied):port.provider_timestamp((now+timedelta(seconds=2)).isoformat())

def test_actual_adapter_skew_start_and_check_publish_trusted_receipt(setup):
 bridge,old,now=setup;raw=document(bridge.cfg);raw["date_created"]=(now[0]+timedelta(seconds=2)).isoformat()
 session=Session(raw);waits=[]
 def sleep(seconds):waits.append(seconds);now[0]+=timedelta(seconds=seconds)
 port=FixedDevTwilioPort(bridge.cfg,b"binding-secret",session=session,clock=lambda:now[0],sleeper=sleep)
 bridge.port=port;bridge.service._port=port
 token,sent=bridge.start("01012345678")
 assert sent and len(waits)==1
 session.document={**raw,"status":"approved","date_updated":(now[0]+timedelta(seconds=2)).isoformat()}
 outcome=bridge.verify(token,"123456")
 assert outcome.receipt.customer_id==bridge.customer_id and len(waits)==2
 with sqlite3.connect(bridge.path) as c:assert c.execute("SELECT state FROM dev_phone_browser").fetchone()[0]=="VERIFIED"

def test_expired_unknown_cookie_allows_explicit_new_request_without_replaying(setup):
 bridge,port,now=setup;port.fail=True
 with pytest.raises(PhoneDenied):bridge.start("01012345678")
 # A cookie retained by a browser must not block a new request forever.
 old_token="A"*43
 with sqlite3.connect(bridge.path) as c:c.execute("UPDATE dev_phone_browser SET token_hash=?",(digest(old_token),))
 with pytest.raises(PhoneDenied):bridge.start("01012345678",old_token)
 assert port.calls==["start"]
 now[0]+=timedelta(seconds=301);port.fail=False
 new_token,sent=bridge.start("01012345678",old_token)
 assert sent and new_token!=old_token and port.calls==["start","start"]
 with sqlite3.connect(bridge.path) as c:assert c.execute("SELECT count(*) FROM dev_phone_browser WHERE state='UNKNOWN'").fetchone()[0]==1
