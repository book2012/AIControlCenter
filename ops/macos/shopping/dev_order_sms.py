from core.shopping.sqlite_resource import connection
"""Private DEV order confirmation SMS outbox; ambiguous sends never auto-retry."""
import json,os,re,sqlite3,time
from pathlib import Path
from urllib.parse import quote
from ops.macos.shopping.dev_order_operator import local_phone
from ops.macos.shopping.dev_customer_messages import greeting

class DevOrderSMS:
    def __init__(self,path,*,aftersales,phone_cfg,config_path,transport=None,solapi_config_path=None):
        self.path=Path(path);self.store=aftersales;self.phone_cfg=phone_cfg;self.config_path=Path(config_path);self.transport=transport
        self.solapi_config_path=Path(solapi_config_path) if solapi_config_path else None
        if self.path.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        with connection(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS notices(order_id INTEGER PRIMARY KEY,state TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS provider_receipts(event_key TEXT PRIMARY KEY,kind TEXT,order_id INTEGER,receipt TEXT,state TEXT,next_check REAL)")
            c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS sms_previews(event_key TEXT PRIMARY KEY,order_id INTEGER NOT NULL,body TEXT NOT NULL,created_at REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS resend_notices(order_id INTEGER PRIMARY KEY,update_id INTEGER NOT NULL,state TEXT NOT NULL,claimed_at REAL NOT NULL)")
            c.execute("UPDATE resend_notices SET state='UNKNOWN' WHERE state='SENDING'")
            if not c.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
                # Historical orders are visible but must not receive surprise backfill SMS.
                for row in self.store.ledger.customer_orders(phone_cfg["guest_customer_id"]):
                    c.execute("INSERT OR IGNORE INTO notices VALUES(?,?)",(row["provider_order_id"],"HISTORICAL"))
                c.execute("INSERT INTO settings VALUES('seeded','1')")
            # A crash after claiming may have reached Twilio. Require manual reconciliation.
            c.execute("UPDATE notices SET state='UNKNOWN' WHERE state='SENDING'")
        with connection(self.store.path) as c:c.execute("UPDATE shipping_notices SET state='UNKNOWN' WHERE state='SENDING'")
        os.chmod(self.path,0o600)
    def arm_solapi_from_now(self):
        """Explicit activation checkpoint: no historical order/shipping SMS backfill."""
        with connection(self.path) as c:
            for row in self.store.ledger.customer_orders(self.phone_cfg["guest_customer_id"]):
                c.execute("INSERT OR IGNORE INTO notices VALUES(?,'HISTORICAL')",(row["provider_order_id"],))
            c.execute("UPDATE notices SET state='HISTORICAL' WHERE state='PENDING'")
            c.execute("INSERT OR REPLACE INTO settings VALUES('solapi_armed','1')")
        with connection(self.store.path) as c:c.execute("UPDATE shipping_notices SET state='SUPPRESSED' WHERE state='PENDING'")

    def config(self):
        if self.config_path.is_symlink() or self.config_path.stat().st_mode&0o077:raise ValueError("PRIVATE_CONFIG_REQUIRED")
        value=json.loads(self.config_path.read_text())
        if value.get("environment")!="DEV":raise ValueError("DEV_SMS_REQUIRED")
        bank=value["bank"]
        for k in ("name","account","holder"):
            if type(bank.get(k)) is not str or not bank[k].strip() or len(bank[k])>100 or any(ch in bank[k] for ch in "\n\r"):raise ValueError("BANK_REQUIRED")
        if value.get("provider")=="DEV_PREVIEW":
            if value.get("enabled") is not True or bank!={"name":"가상 테스트은행","account":"DEV-0000-0000","holder":"아가치치 DEV"}:
                raise ValueError("DEV_PREVIEW_CONFIGURATION_REQUIRED")
            return value
        if bank["account"].strip()=="123456":raise ValueError("REAL_BANK_REQUIRED")
        if self.solapi_config_path and self.solapi_config_path.exists():
            if self.solapi_config_path.is_symlink() or self.solapi_config_path.stat().st_mode&0o077:raise ValueError("PRIVATE_CONFIG_REQUIRED")
            solapi=json.loads(self.solapi_config_path.read_text())
            if solapi.get("enabled") is True:
                from ops.macos.shopping.dev_solapi_sms import SolapiSMS
                client=SolapiSMS(solapi);client.session.close()
                purposes=solapi.get("purposes",{})
                if not any(purposes.get(k) is True for k in ("order_confirmation","shipping_started")):raise ValueError("SMS_PURPOSE_DISABLED")
                with connection(self.path) as c:
                    if not c.execute("SELECT 1 FROM settings WHERE key='solapi_armed'").fetchone():raise ValueError("SOLAPI_ACTIVATION_CHECKPOINT_REQUIRED")
                return {**value,"provider":"SOLAPI","solapi":solapi,"enabled":True}
        if value.get("enabled") is not True:raise ValueError("SMS_DISABLED")
        credentials=value["credentials"]
        if not re.fullmatch(r"AC[0-9a-fA-F]{32}",credentials["account_sid"]) or not credentials["auth_token"]:raise ValueError("SMS_CREDENTIALS_REQUIRED")
        if not re.fullmatch(r"MG[0-9a-fA-F]{32}",credentials["messaging_service_sid"]):raise ValueError("SMS_SERVICE_REQUIRED")
        return value

    def _send_notice(self,cfg,text,kind,oid):
        event=kind+":"+str(oid)
        if cfg.get("provider")=="DEV_PREVIEW":
            if self.transport is not None:raise ValueError("DEV_PREVIEW_EXTERNAL_TRANSPORT_DENIED")
            with connection(self.path) as c:
                c.execute("INSERT INTO sms_previews VALUES(?,?,?,?)",(event,oid,text,time.time()))
            return
        if self.transport:receipt=self.transport(cfg,self.phone_cfg["test_phone"],text)
        elif cfg.get("provider")=="SOLAPI":
            from ops.macos.shopping.dev_solapi_sms import SolapiSMS
            receipt=SolapiSMS(cfg["solapi"]).send(self.phone_cfg["test_phone"],text,event)
        else:receipt=self.send(cfg,self.phone_cfg["test_phone"],text)
        if isinstance(receipt,dict) and receipt.get("provider")=="SOLAPI":
            with connection(self.path) as c:c.execute("INSERT INTO provider_receipts VALUES(?,?,?,?,?,?)",(event,kind,oid,json.dumps(receipt),"ACCEPTED",time.time()+30))

    def reconcile_one(self,cfg):
        if cfg.get("provider")!="SOLAPI":return None
        with connection(self.path) as c:
            row=c.execute("SELECT event_key,kind,order_id,receipt FROM provider_receipts WHERE state='ACCEPTED' AND next_check<=? ORDER BY next_check LIMIT 1",(time.time(),)).fetchone()
            if row:c.execute("UPDATE provider_receipts SET next_check=? WHERE event_key=?",(time.time()+30,row[0]))
        if not row:return None
        from ops.macos.shopping.dev_solapi_sms import SolapiSMS
        result=SolapiSMS(cfg["solapi"]).status(json.loads(row[3]))
        if result["state"] in {"DELIVERED","FAILED"}:
            with connection(self.path) as c:
                c.execute("UPDATE provider_receipts SET state=? WHERE event_key=?",(result["state"],row[0]))
                if row[1]=="order":c.execute("UPDATE notices SET state=? WHERE order_id=? AND state='ACCEPTED'",(result["state"],row[2]))
            if row[1]=="shipping":
                with connection(self.store.path) as c:c.execute("UPDATE shipping_notices SET state=? WHERE order_id=? AND state='ACCEPTED'",(result["state"],row[2]))
        return result["state"]

    def state(self,order_id):
        with connection(self.path) as c:
            row=c.execute("SELECT state FROM notices WHERE order_id=?",(order_id,)).fetchone()
        return row[0] if row else "WAITING_CONFIRMATION"
    def confirmation_text(self,cfg,order,oid):
        text="주문확인 및 입금 안내\n주문번호: "+str(oid)+"\n"+"\n".join(v["name"]+" / "+v.get("option","기본")+" / "+str(v["quantity"])+"개" for v in order["items"])
        bank=cfg["bank"]
        text+="\n총액: "+order["total"]+"원"
        if order.get("payment",{}).get("state")=="PAID":text+="\n입금 확인 완료"
        else:text+="\n입금계좌: "+bank["name"]+" "+bank["account"]+" ("+bank["holder"]+")"
        text+="\n주문조회: https://dev.bokstory.duckdns.org/homepage/storefront/my-orders"
        text=greeting(text)
        if cfg.get("provider")=="SOLAPI":
            if len(text.encode("euc-kr"))>2000:
                suffix=text[text.index("총액:"):]
                text=greeting("주문확인 및 입금 안내\n주문번호: "+str(oid)+"\n상품 "+str(len(order["items"]))+"종 · 상세내역은 주문조회에서 확인해 주세요.\n"+suffix)
            from ops.macos.shopping.dev_solapi_sms import payload
            payload(cfg["solapi"]["sender_number"],self.phone_cfg["test_phone"],text,"order:"+str(oid))
        elif len(text)>1600:raise ValueError("SMS_TOO_LARGE")
        return text

    def resend_notice(self,order_id,update_id):
        if type(order_id) is not int or order_id<=0 or type(update_id) is not int or update_id<0:
            return "문자 재전송 요청이 올바르지 않습니다."
        try:cfg=self.config()
        except Exception:return "문자 발송 설정이 필요합니다. 실제 입금계좌와 발신 서비스를 확인해 주세요."
        rows=[r for r in self.store.ledger.customer_orders(self.phone_cfg["guest_customer_id"]) if r["provider_order_id"]==order_id]
        if len(rows)!=1 or rows[0]["review_state"]!="CONFIRMED":return "주문확인 완료 후 문자 재전송이 가능합니다."
        try:order=self.store.lookup(self.phone_cfg["guest_customer_id"],str(order_id),self.phone_cfg["test_phone"],self.phone_cfg["test_phone"])
        except ValueError:return "이 주문의 인증된 수신번호를 확인할 수 없습니다."
        if order.get("cancellation",{}).get("state","NONE")!="NONE" or order.get("return_status",{}).get("state","NONE")!="NONE":
            return "취소·환불 처리 중인 주문에는 안내문자를 재전송하지 않습니다."
        now=time.time()
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            previous=c.execute("SELECT update_id,state,claimed_at FROM resend_notices WHERE order_id=?",(order_id,)).fetchone()
            if previous:
                if previous[1] in ("SENDING","UNKNOWN"):return "이전 문자 발송 결과 확인이 필요합니다. 다시 보내지 않았습니다."
                if previous[0]==update_id or now-previous[2]<60:return "최근 재전송 요청이 있습니다. 중복 발송하지 않았습니다."
            c.execute("INSERT OR REPLACE INTO resend_notices VALUES(?,?,?,?)",(order_id,update_id,"SENDING",now))
        try:
            text=self.confirmation_text(cfg,order,order_id)
            self._send_notice(cfg,text,"order-resend-"+str(update_id),order_id)
            result="PREVIEW" if cfg.get("provider")=="DEV_PREVIEW" else "ACCEPTED"
        except Exception:result="UNKNOWN"
        with connection(self.path) as c:c.execute("UPDATE resend_notices SET state=? WHERE order_id=? AND update_id=?",(result,order_id,update_id))
        if result=="PREVIEW":return "[DEV 문자 미리보기 · 실제 발송 없음]\n"+text
        return ("주문확인·입금 안내 문자 재전송을 요청했습니다. 발송 상태를 확인해 주세요."
                if result=="ACCEPTED" else "문자 발송 결과 확인이 필요합니다. 재전송을 멈췄습니다.")

    def dispatch_one(self):
        rows=self.store.ledger.customer_orders(self.phone_cfg["guest_customer_id"])
        try:cfg=self.config()
        except Exception:
            # No sender/bank is available: every order observed during this
            # disabled interval is historical, including pre-existing pending rows.
            # An explicit operator resend remains the only later send path.
            with connection(self.path) as c:
                for row in rows:c.execute("INSERT OR IGNORE INTO notices VALUES(?,?)",(row["provider_order_id"],"HISTORICAL"))
                c.execute("UPDATE notices SET state='HISTORICAL' WHERE state='PENDING'")
            return "CONFIGURATION_REQUIRED"
        with connection(self.path) as c:
            for row in rows:c.execute("INSERT OR IGNORE INTO notices VALUES(?,?)",(row["provider_order_id"],"PENDING"))
        try:
            reconciled=self.reconcile_one(cfg)
            if reconciled:return reconciled
        except Exception:pass # Read-only status uncertainty never permits another POST.
        for row in rows:
            if cfg.get("provider")=="SOLAPI" and cfg["solapi"]["purposes"].get("order_confirmation") is not True:continue
            oid=row["provider_order_id"]
            if row["review_state"]!="CONFIRMED":continue
            try:order=self.store.lookup(self.phone_cfg["guest_customer_id"],str(oid),self.phone_cfg["test_phone"],self.phone_cfg["test_phone"])
            except ValueError:
                with connection(self.path) as c:c.execute("UPDATE notices SET state='RECIPIENT_NOT_ALLOWED' WHERE order_id=? AND state='PENDING'",(oid,))
                continue
            if order.get("cancellation",{}).get("state","NONE")!="NONE" or order.get("return_status",{}).get("state","NONE")!="NONE":
                with connection(self.path) as c:c.execute("UPDATE notices SET state='SUPPRESSED' WHERE order_id=? AND state='PENDING'",(oid,))
                continue
            text=self.confirmation_text(cfg,order,oid)
            with connection(self.path) as c:
                if c.execute("UPDATE notices SET state='SENDING' WHERE order_id=? AND state='PENDING'",(oid,)).rowcount!=1:continue
            try:
                self._send_notice(cfg,text,"order",oid)
                state="PREVIEW" if cfg.get("provider")=="DEV_PREVIEW" else "ACCEPTED"
            except Exception:state="UNKNOWN"
            with connection(self.path) as c:c.execute("UPDATE notices SET state=? WHERE order_id=?",(state,oid))
            return state
        return self.dispatch_shipping(cfg)
    def dispatch_shipping(self,cfg):
        if cfg.get("provider")=="SOLAPI" and cfg["solapi"]["purposes"].get("shipping_started") is not True:return "IDLE"
        with connection(self.store.path) as c:
            rows=c.execute("SELECT order_id,carrier,tracking FROM shipping_notices WHERE state='PENDING' ORDER BY order_id").fetchall()
        for oid,carrier,tracking in rows:
            try:order=self.store.lookup(self.phone_cfg["guest_customer_id"],str(oid),self.phone_cfg["test_phone"],self.phone_cfg["test_phone"])
            except ValueError:
                with connection(self.store.path) as c:c.execute("UPDATE shipping_notices SET state='RECIPIENT_NOT_ALLOWED' WHERE order_id=? AND state='PENDING'",(oid,))
                continue
            if order["fulfillment"]["state"]=="DELIVERED":
                with connection(self.store.path) as c:c.execute("UPDATE shipping_notices SET state='SUPPRESSED' WHERE order_id=? AND state='PENDING'",(oid,))
                continue
            if order["review_state"]!="CONFIRMED" or order["payment"]["state"]!="PAID" or order["fulfillment"]["state"]!="SHIPPED":continue
            text=greeting("주문번호: "+str(oid)+"\n주문하신 상품의 배송이 시작되었습니다.\n택배사: "+carrier+"\n운송장번호: "+tracking+"\n주문조회: https://dev.bokstory.duckdns.org/homepage/storefront/my-orders")
            if cfg.get("provider")=="SOLAPI":
                from ops.macos.shopping.dev_solapi_sms import payload
                payload(cfg["solapi"]["sender_number"],self.phone_cfg["test_phone"],text,"shipping:"+str(oid))
            with connection(self.store.path) as c:
                if c.execute("UPDATE shipping_notices SET state='SENDING' WHERE order_id=? AND state='PENDING'",(oid,)).rowcount!=1:continue
            try:
                self._send_notice(cfg,text,"shipping",oid)
                state="PREVIEW" if cfg.get("provider")=="DEV_PREVIEW" else "ACCEPTED"
            except Exception:state="UNKNOWN"
            with connection(self.store.path) as c:c.execute("UPDATE shipping_notices SET state=? WHERE order_id=?",(state,oid))
            return state
        return "IDLE"
    @staticmethod
    def send(cfg,phone,text):
        import requests
        credentials=cfg["credentials"];sid=credentials["account_sid"]
        session=requests.Session();session.trust_env=False
        try:
            response=session.post("https://api.twilio.com/2010-04-01/Accounts/"+quote(sid,safe="")+"/Messages.json",
                auth=(sid,credentials["auth_token"]),data={"To":phone,"MessagingServiceSid":credentials["messaging_service_sid"],"Body":text},
                timeout=15,allow_redirects=False)
            if response.status_code!=201 or len(response.content)>32768:raise ValueError("SMS_RECEIPT_INVALID")
            body=response.json()
            if body.get("account_sid")!=sid or body.get("to")!=phone or not re.fullmatch(r"SM[0-9a-fA-F]{32}",body.get("sid","")):raise ValueError("SMS_RECEIPT_INVALID")
        finally:session.close()
