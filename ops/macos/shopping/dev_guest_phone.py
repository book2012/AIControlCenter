"""Explicit one-number DEV Twilio Verify composition. Never a production identity map."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import hashlib,json,os,re,secrets,sqlite3,threading,uuid
import requests
from pydantic import BaseModel,ConfigDict,Field
from fastapi import Request
from fastapi.responses import JSONResponse
from core.shopping.phone_normalization import normalize_phone,derive_phone_binding
from core.shopping.phone_verification_service import PhoneVerificationService
from core.shopping.ports.phone_verification import (ChallengeStartResult,ChallengeStatus,
    ChallengeVerificationResult,VerificationStatus,ProviderVerificationIdentifier)
from core.shopping.customer_identity import Customer,VerifiedContactBinding
from core.shopping.customer_persistence import SQLiteCustomerSessionStore,customer_from_connection
from core.api.dependencies.customer_session import TrustedSessionEvidence
from core.api.schemas.customer_auth import VerificationReceiptConsumeRequest
from core.api.routes.customer_sessions import create_session
from core.shopping.order_core.woocommerce_writer import WooCommerceOrderWriter

COOKIE="__Host-aicc_phone"
SOURCE="twilio.verify.dev"
def utc():return datetime.now(timezone.utc)
def ref(kind):return "AG-"+kind+"-"+uuid.uuid4().hex
def digest(value):return hashlib.sha256(value.encode()).hexdigest()
class PhoneDenied(RuntimeError):
    def __init__(self,code="UNKNOWN_OUTCOME",provider_code=None):
        self.code=code;self.provider_code=provider_code
        super().__init__(code)
class StartPhone(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    phone:str=Field(strict=True,min_length=8,max_length=32,repr=False)
    consent:bool=Field(strict=True)
class CheckPhone(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    code:str=Field(strict=True,min_length=4,max_length=10,pattern=r"^[0-9]+$",repr=False)
def timestamp(value):
    try:result=datetime.fromisoformat(value.replace("Z","+00:00"))
    except (ValueError,AttributeError):result=parsedate_to_datetime(value)
    if result.tzinfo is None:raise PhoneDenied()
    return result.astimezone(timezone.utc)

class FixedDevTwilioPort:
    def __init__(self,cfg,binding_key,session=None):
        c=cfg["credentials"]
        if cfg.get("environment")!="DEV" or cfg.get("provider")!="twilio_verify" or cfg.get("enabled") is not True:raise ValueError("DEV_PHONE_DISABLED")
        if not re.fullmatch(r"AC[0-9a-fA-F]{32}",c["account_sid"]) or not re.fullmatch(r"VA[0-9a-fA-F]{32}",c["verify_service_sid"]) or not c["auth_token"]:raise ValueError("DEV_PHONE_CONFIGURATION_INVALID")
        self.phone=normalize_phone(cfg["test_phone"]);self.binding=derive_phone_binding(self.phone,binding_key)
        self.credentials=c;self.session=session or requests.Session();self.session.trust_env=False
        self.last_error_code=None
    def invoke(self,path,body):
        if path not in ("Verifications","VerificationCheck"):raise PhoneDenied("REJECTED")
        self.last_error_code=None
        try:
            response=self.session.post("https://verify.twilio.com/v2/Services/"+self.credentials["verify_service_sid"]+"/"+path,
                auth=(self.credentials["account_sid"],self.credentials["auth_token"]),data=body,
                timeout=15,allow_redirects=False,stream=True)
            document=WooCommerceOrderWriter._document(response)
        except Exception:raise PhoneDenied() from None
        if response.status_code not in (200,201):
            code=document.get("code") if type(document) is dict else None
            self.last_error_code=code if type(code) is int else None
            raise PhoneDenied("REJECTED" if response.status_code in (400,401,403,404,429) else "UNKNOWN_OUTCOME",self.last_error_code)
        if (type(document) is not dict or document.get("account_sid")!=self.credentials["account_sid"]
            or document.get("service_sid")!=self.credentials["verify_service_sid"]
            or document.get("to")!=self.phone.value or document.get("channel")!="sms"
            or not re.fullmatch(r"VE[0-9a-fA-F]{32}",document.get("sid",""))):raise PhoneDenied()
        return document
    def start_challenge(self,request):
        if str(request.provider_source)!=SOURCE or request.subject.phone_binding!=self.binding:raise PhoneDenied("REJECTED")
        raw=self.invoke("Verifications",{"To":self.phone.value,"Channel":"sms","Locale":"ko"})
        if raw.get("status")!="pending":raise PhoneDenied()
        return ChallengeStartResult(provider_source=request.provider_source,provider_verification_id=ProviderVerificationIdentifier(value=raw["sid"]),
            purpose=request.purpose,challenge_reference=request.challenge_reference,replay_reference=request.replay_reference,
            phone_binding=request.subject.phone_binding,status=ChallengeStatus.PENDING,started_at=timestamp(raw["date_created"]))
    def verify_challenge(self,request):
        if str(request.provider_source)!=SOURCE or request.phone_binding!=self.binding:raise PhoneDenied("REJECTED")
        raw=self.invoke("VerificationCheck",{"VerificationSid":str(request.provider_verification_id),"Code":request.otp})
        if raw["sid"]!=str(request.provider_verification_id):raise PhoneDenied()
        status={"approved":VerificationStatus.SUCCESS,"pending":VerificationStatus.REJECTED,
            "expired":VerificationStatus.EXPIRED,"canceled":VerificationStatus.REJECTED,
            "failed":VerificationStatus.FAILED}.get(raw.get("status"))
        if status is None:raise PhoneDenied()
        return ChallengeVerificationResult(provider_source=request.provider_source,provider_verification_id=request.provider_verification_id,
            purpose=request.purpose,challenge_reference=request.challenge_reference,replay_reference=request.replay_reference,
            phone_binding=request.phone_binding,status=status,verified_at=timestamp(raw["date_updated"]))

class DevPhoneBridge:
    def __init__(self,*,cfg,binding_key,customer_path,bridge_path,clock=utc,port=None):
        self.cfg=cfg;self.clock=clock;self.customer_path=Path(customer_path);self.path=Path(bridge_path);self.lock=threading.Lock()
        self.port=port or FixedDevTwilioPort(cfg,binding_key)
        self.service=PhoneVerificationService(self.port,clock=clock,binding_key=binding_key,provider_source=SOURCE,database_path=self.customer_path)
        self.customer_id=cfg["guest_customer_id"]
        with sqlite3.connect(self.path) as c:c.execute("CREATE TABLE IF NOT EXISTS dev_phone_browser(token_hash TEXT PRIMARY KEY,challenge TEXT NOT NULL,replay TEXT NOT NULL,browser TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,expires REAL NOT NULL)")
        os.chmod(self.path,0o600)
        store=SQLiteCustomerSessionStore(self.customer_path)
        with sqlite3.connect(self.customer_path) as c:c.row_factory=sqlite3.Row;existing=customer_from_connection(c,self.customer_id)
        if existing is None:
            now=self.clock();store.save_customer(Customer(id=self.customer_id,state="ACTIVE",created_at=now,updated_at=now,
                contact_binding=VerifiedContactBinding(customer_id=self.customer_id,state="UNVERIFIED",created_at=now,updated_at=now)))
    def start(self,phone,token=None):
        canonical=normalize_phone(phone) if phone.strip().startswith("+") else normalize_phone(phone,country_calling_code="+82",national_trunk_prefix="0")
        if canonical!=normalize_phone(self.cfg["test_phone"]):raise PhoneDenied("PHONE_NOT_ALLOWED")
        with self.lock:
            stamp=self.clock().timestamp()
            with sqlite3.connect(self.path) as c:
                c.execute("BEGIN IMMEDIATE")
                if token:
                    row=c.execute("SELECT state,expires FROM dev_phone_browser WHERE token_hash=?",(digest(token),)).fetchone()
                    if row and row[0]=="PENDING" and stamp<row[1]:return token,False
                    if row and row[0] in ("START_CLAIMED","UNKNOWN","CHECK_CLAIMED"):raise PhoneDenied("INSPECTION_REQUIRED")
                count=c.execute("SELECT count(*) FROM dev_phone_browser WHERE created>?",(stamp-3600,)).fetchone()[0]
                recent=c.execute("SELECT 1 FROM dev_phone_browser WHERE created>? OR (state IN ('START_CLAIMED','UNKNOWN','CHECK_CLAIMED','PENDING') AND expires>?)",(stamp-60,stamp)).fetchone()
                if count>=3 or recent:raise PhoneDenied("RATE_LIMITED")
                token=secrets.token_urlsafe(32);challenge=ref("CHL");replay=ref("RPL");browser=ref("CHL")
                c.execute("INSERT INTO dev_phone_browser VALUES(?,?,?,?,?,?,?)",(digest(token),challenge,replay,browser,"START_CLAIMED",stamp,stamp+300))
            try:self.service.start_challenge(canonical,customer_id=self.customer_id,browser_challenge=browser,challenge_reference=challenge,replay_reference=replay)
            except Exception:
                with sqlite3.connect(self.path) as c:c.execute("UPDATE dev_phone_browser SET state='UNKNOWN' WHERE token_hash=?",(digest(token),))
                raise PhoneDenied("INSPECTION_REQUIRED",self.port.last_error_code) from None
            with sqlite3.connect(self.path) as c:c.execute("UPDATE dev_phone_browser SET state='PENDING' WHERE token_hash=?",(digest(token),))
            return token,True
    def verify(self,token,code):
        if not token or not re.fullmatch(r"[A-Za-z0-9_-]{43}",token):raise PhoneDenied("DENIED")
        with self.lock:
            with sqlite3.connect(self.path) as c:
                c.execute("BEGIN IMMEDIATE")
                row=c.execute("SELECT challenge,replay,state,expires FROM dev_phone_browser WHERE token_hash=?",(digest(token),)).fetchone()
                if not row or row[2]!="PENDING" or self.clock().timestamp()>=row[3]:raise PhoneDenied("DENIED")
                c.execute("UPDATE dev_phone_browser SET state='CHECK_CLAIMED' WHERE token_hash=?",(digest(token),))
            try:outcome=self.service.verify_challenge(challenge_reference=row[0],replay_reference=row[1],otp=code)
            except Exception:
                with sqlite3.connect(self.path) as c:c.execute("UPDATE dev_phone_browser SET state='CHECK_FAILED' WHERE token_hash=?",(digest(token),))
                raise PhoneDenied("CODE_NOT_APPROVED",self.port.last_error_code) from None
            with sqlite3.connect(self.customer_path) as c:
                c.row_factory=sqlite3.Row;existing=customer_from_connection(c,self.customer_id)
            if existing is None or existing.state.value!="ACTIVE":raise PhoneDenied("DENIED")
            stamp=self.clock()
            if existing.contact_binding.state.value=="UNVERIFIED":
                SQLiteCustomerSessionStore(self.customer_path).save_customer(existing.model_copy(update={
                    "updated_at":stamp,"contact_binding":VerifiedContactBinding(customer_id=self.customer_id,state="VERIFIED",
                    created_at=existing.contact_binding.created_at,updated_at=stamp,verified_at=stamp,contact_ref=self.cfg["guest_contact_ref"])}))
            elif existing.contact_binding.state.value!="VERIFIED":raise PhoneDenied("DENIED")
            with sqlite3.connect(self.path) as c:c.execute("UPDATE dev_phone_browser SET state='VERIFIED' WHERE token_hash=?",(digest(token),))
            return outcome

def mount_phone_routes(app,*,bridge,boundary,register_evidence):
    async def payload(request,model):
        boundary.check_origin(request,required=True);raw=bytearray()
        async for chunk in request.stream():
            if len(raw)+len(chunk)>2048:raise ValueError()
            raw.extend(chunk)
        return model.model_validate_json(bytes(raw))
    @app.post("/__order-dev/phone/start",include_in_schema=False)
    async def start(request:Request):
        try:
            data=await payload(request,StartPhone)
            if data.consent is not True:raise ValueError()
            token,sent=await __import__("asyncio").to_thread(bridge.start,data.phone,request.cookies.get(COOKIE))
            response=JSONResponse({"state":"PENDING","message":"인증번호를 입력해 주세요.","new_sms_requested":sent},headers={"Cache-Control":"no-store"})
            response.set_cookie(COOKIE,token,max_age=300,path="/",secure=True,httponly=True,samesite="strict");return response
        except PhoneDenied as error:return JSONResponse({"message":"인증 요청을 완료하지 못했습니다. 반복 발송하지 말고 연결 상태를 확인해 주세요.","code":error.code,"provider_code":error.provider_code},status_code=429 if error.code=="RATE_LIMITED" else 503,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"휴대폰 번호와 인증 동의를 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/phone/check",include_in_schema=False)
    async def check(request:Request):
        try:
            data=await payload(request,CheckPhone)
            outcome=await __import__("asyncio").to_thread(bridge.verify,request.cookies.get(COOKIE),data.code)
            public=register_evidence(TrustedSessionEvidence(outcome.receipt,outcome.context,outcome.receipt.browser_challenge))
            response=create_session(VerificationReceiptConsumeRequest(**public),request,boundary)
            response.delete_cookie(COOKIE,path="/",secure=True,httponly=True,samesite="strict")
            return response
        except Exception:return JSONResponse({"message":"인증을 완료하지 못했습니다. 인증번호 또는 요청 상태를 확인해 주세요."},status_code=401,headers={"Cache-Control":"no-store"})
