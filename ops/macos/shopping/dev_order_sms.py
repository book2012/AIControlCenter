"""Private DEV order confirmation SMS outbox; ambiguous sends never auto-retry."""
import json,os,re,sqlite3
from pathlib import Path
from urllib.parse import quote
from ops.macos.shopping.dev_order_operator import local_phone
from ops.macos.shopping.dev_customer_messages import greeting

class DevOrderSMS:
    def __init__(self,path,*,aftersales,phone_cfg,config_path,transport=None):
        self.path=Path(path);self.store=aftersales;self.phone_cfg=phone_cfg;self.config_path=Path(config_path);self.transport=transport
        if self.path.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS notices(order_id INTEGER PRIMARY KEY,state TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            if not c.execute("SELECT 1 FROM settings WHERE key='seeded'").fetchone():
                # Historical orders are visible but must not receive surprise backfill SMS.
                for row in self.store.ledger.customer_orders(phone_cfg["guest_customer_id"]):
                    c.execute("INSERT OR IGNORE INTO notices VALUES(?,?)",(row["provider_order_id"],"HISTORICAL"))
                c.execute("INSERT INTO settings VALUES('seeded','1')")
            # A crash after claiming may have reached Twilio. Require manual reconciliation.
            c.execute("UPDATE notices SET state='UNKNOWN' WHERE state='SENDING'")
        with sqlite3.connect(self.store.path) as c:c.execute("UPDATE shipping_notices SET state='UNKNOWN' WHERE state='SENDING'")
        os.chmod(self.path,0o600)
    def config(self):
        if self.config_path.is_symlink() or self.config_path.stat().st_mode&0o077:raise ValueError("PRIVATE_CONFIG_REQUIRED")
        value=json.loads(self.config_path.read_text())
        if value.get("environment")!="DEV" or value.get("enabled") is not True:raise ValueError("SMS_DISABLED")
        bank=value["bank"];credentials=value["credentials"]
        for k in ("name","account","holder"):
            if type(bank.get(k)) is not str or not bank[k].strip() or len(bank[k])>100 or "\n" in bank[k]:raise ValueError("BANK_REQUIRED")
        if not re.fullmatch(r"AC[0-9a-fA-F]{32}",credentials["account_sid"]) or not credentials["auth_token"]:raise ValueError("SMS_CREDENTIALS_REQUIRED")
        if not re.fullmatch(r"MG[0-9a-fA-F]{32}",credentials["messaging_service_sid"]):raise ValueError("SMS_SERVICE_REQUIRED")
        return value
    def state(self,order_id):
        with sqlite3.connect(self.path) as c:
            row=c.execute("SELECT state FROM notices WHERE order_id=?",(order_id,)).fetchone()
        return row[0] if row else "WAITING_CONFIRMATION"
    def dispatch_one(self):
        rows=self.store.ledger.customer_orders(self.phone_cfg["guest_customer_id"])
        with sqlite3.connect(self.path) as c:
            for row in rows:c.execute("INSERT OR IGNORE INTO notices VALUES(?,?)",(row["provider_order_id"],"PENDING"))
        try:cfg=self.config()
        except Exception:return "CONFIGURATION_REQUIRED"
        for row in rows:
            oid=row["provider_order_id"]
            if row["review_state"]!="CONFIRMED":continue
            order=self.store.lookup(self.phone_cfg["guest_customer_id"],str(oid),self.phone_cfg["test_phone"],self.phone_cfg["test_phone"])
            text="주문확인\n주문번호: "+str(oid)+"\n"+"\n".join(v["name"]+" / "+v.get("option","기본")+" / "+str(v["quantity"])+"개" for v in order["items"])
            bank=cfg["bank"]
            text+="\n총액: "+order["total"]+"원\n입금계좌: "+bank["name"]+" "+bank["account"]+" ("+bank["holder"]+")\n주문조회: https://dev.bokstory.duckdns.org/homepage/storefront/my-orders"
            text=greeting(text)
            if len(text)>1600:raise ValueError("SMS_TOO_LARGE")
            with sqlite3.connect(self.path) as c:
                if c.execute("UPDATE notices SET state='SENDING' WHERE order_id=? AND state='PENDING'",(oid,)).rowcount!=1:continue
            try:
                if self.transport:self.transport(cfg,self.phone_cfg["test_phone"],text)
                else:self.send(cfg,self.phone_cfg["test_phone"],text)
                state="ACCEPTED"
            except Exception:state="UNKNOWN"
            with sqlite3.connect(self.path) as c:c.execute("UPDATE notices SET state=? WHERE order_id=?",(state,oid))
            return state
        return self.dispatch_shipping(cfg)
    def dispatch_shipping(self,cfg):
        with sqlite3.connect(self.store.path) as c:
            rows=c.execute("SELECT order_id,carrier,tracking FROM shipping_notices WHERE state='PENDING' ORDER BY order_id").fetchall()
        for oid,carrier,tracking in rows:
            order=self.store.lookup(self.phone_cfg["guest_customer_id"],str(oid),self.phone_cfg["test_phone"],self.phone_cfg["test_phone"])
            if order["fulfillment"]["state"]=="DELIVERED":
                with sqlite3.connect(self.store.path) as c:c.execute("UPDATE shipping_notices SET state='SUPPRESSED' WHERE order_id=? AND state='PENDING'",(oid,))
                continue
            if order["review_state"]!="CONFIRMED" or order["payment"]["state"]!="PAID" or order["fulfillment"]["state"]!="SHIPPED":continue
            text=greeting("주문번호: "+str(oid)+"\n주문하신 상품의 배송이 시작되었습니다.\n택배사: "+carrier+"\n운송장번호: "+tracking+"\n주문조회: https://dev.bokstory.duckdns.org/homepage/storefront/my-orders")
            with sqlite3.connect(self.store.path) as c:
                if c.execute("UPDATE shipping_notices SET state='SENDING' WHERE order_id=? AND state='PENDING'",(oid,)).rowcount!=1:continue
            try:
                if self.transport:self.transport(cfg,self.phone_cfg["test_phone"],text)
                else:self.send(cfg,self.phone_cfg["test_phone"],text)
                state="ACCEPTED"
            except Exception:state="UNKNOWN"
            with sqlite3.connect(self.store.path) as c:c.execute("UPDATE shipping_notices SET state=? WHERE order_id=?",(state,oid))
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
