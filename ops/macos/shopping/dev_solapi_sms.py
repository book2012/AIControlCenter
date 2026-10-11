"""Pinned SOLAPI transport. API acceptance is distinct from handset delivery; no write retry."""
from datetime import datetime,timezone
import hashlib,hmac,re,secrets
from ops.macos.shopping.dev_order_operator import local_phone

class SolapiUnknown(RuntimeError):
    pass

def payload(sender,phone,text,event_key):
    phone=local_phone(phone)
    if not re.fullmatch(r"0[1-9][0-9]{7,10}",sender):raise ValueError("REGISTERED_SENDER_REQUIRED")
    if type(text) is not str or not text.strip():raise ValueError("SMS_CONTENT_REQUIRED")
    size=len(text.encode("euc-kr"))
    if size>2000:raise ValueError("LMS_BYTE_LIMIT")
    kind="SMS" if size<=90 else "LMS"
    value={"from":sender,"to":phone,"country":"82","text":text,"type":kind,
        "customFields":{"aicc_event":hashlib.sha256(event_key.encode()).hexdigest()}}
    if kind=="LMS":value["subject"]="agachichi 주문 안내"
    return value

class SolapiSMS:
    def __init__(self,cfg,*,session=None):
        import requests
        if cfg.get("environment")!="DEV" or str(cfg.get("provider")).upper()!="SOLAPI":
            raise ValueError("DEV_SOLAPI_CONFIGURATION_REQUIRED")
        credentials=cfg["credentials"];self.key=credentials["api_key"];self.secret=credentials["api_secret"]
        if any(type(v) is not str or not v.strip() or v!=v.strip() or len(v)>256 for v in (self.key,self.secret)):
            raise ValueError("SOLAPI_CREDENTIALS_REQUIRED")
        self.last_document=None;self.sender=cfg["sender_number"];self.session=session or requests.Session();self.session.trust_env=False

    def __repr__(self):return "SolapiSMS(configured=True)"

    def auth(self):
        date=datetime.now(timezone.utc).isoformat().replace("+00:00","Z");salt=secrets.token_hex(16)
        signature=hmac.new(self.secret.encode(),(date+salt).encode(),hashlib.sha256).hexdigest()
        return {"Authorization":f"HMAC-SHA256 apiKey={self.key}, date={date}, salt={salt}, signature={signature}"}

    def request(self,method,path,**kwargs):
        if path not in {"/messages/v4/send-many/detail","/messages/v4/list","/cash/v1/balance"}:
            raise ValueError("SOLAPI_ENDPOINT_DENIED")
        try:
            response=self.session.request(method,"https://api.solapi.com"+path,headers=self.auth(),
                timeout=15,allow_redirects=False,**kwargs)
            if response.status_code!=200 or len(response.content)>131072:raise ValueError()
            value=response.json()
            if type(value) is not dict:raise ValueError()
            self.last_document=value
            return value
        except Exception:raise SolapiUnknown("SOLAPI_RESPONSE_UNAVAILABLE") from None

    def send(self,phone,text,event_key):
        message=payload(self.sender,phone,text,event_key)
        doc=self.request("POST","/messages/v4/send-many/detail",json={"messages":[message],
            "allowDuplicates":False,"showMessageList":True,"strict":True})
        group=doc.get("groupInfo",{});messages=doc.get("messageList",group.get("messageList"))
        if (type(group) is not dict or group.get("count",{}).get("registeredSuccess")!=1
            or doc.get("failedMessageList") or type(messages) is not list or len(messages)!=1):
            raise SolapiUnknown("SOLAPI_ACCEPTANCE_INVALID")
        item=messages[0];gid=group.get("groupId",group.get("_id"));mid=item.get("messageId")
        if not re.fullmatch(r"G[A-Za-z0-9]{10,63}",gid or "") or not re.fullmatch(r"M[A-Za-z0-9]{10,63}",mid or ""):
            raise SolapiUnknown("SOLAPI_RECEIPT_INVALID")
        if item.get("customFields",{}).get("aicc_event")!=message["customFields"]["aicc_event"]:
            raise SolapiUnknown("SOLAPI_RECEIPT_BINDING_INVALID")
        return {"provider":"SOLAPI","group_id":gid,"message_id":mid,"to":message["to"],"sender":self.sender,
            "text_hash":hashlib.sha256(text.encode()).hexdigest(),"event_hash":message["customFields"]["aicc_event"],
            "type":message["type"],"state":"ACCEPTED"}

    def status(self,receipt):
        doc=self.request("GET","/messages/v4/list",params={"groupId":receipt["group_id"],"limit":1})
        rows=doc.get("messageList")
        if type(rows) is not dict or set(rows)!={receipt["message_id"]}:raise SolapiUnknown("SOLAPI_STATUS_BINDING")
        row=rows[receipt["message_id"]]
        if (row.get("groupId")!=receipt["group_id"] or row.get("to")!=receipt["to"]
            or row.get("from")!=receipt["sender"] or row.get("customFields",{}).get("aicc_event")!=receipt["event_hash"]
            or hashlib.sha256(row.get("text","").encode()).hexdigest()!=receipt["text_hash"]):
            raise SolapiUnknown("SOLAPI_STATUS_BINDING")
        code=row.get("statusCode")
        if code=="4000":state="DELIVERED"
        elif type(code) is str and code.startswith(("1","3")):state="FAILED"
        else:state="ACCEPTED"
        return {"state":state,"status_code":code}
