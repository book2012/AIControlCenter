from core.shopping.sqlite_resource import connection
"""Private customer-owned order fulfillment and aftersales state; no provider defaults."""
from pathlib import Path
import hashlib,json,os,re,secrets,sqlite3,time
from pydantic import BaseModel,ConfigDict,Field
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

RETURN_WINDOW=14*86400
REFUND_ACCOUNT_NOTICE_VERSION="refund-account-dev-001"
MAX_ATTACHMENT=5*1024*1024
MEDIA={"image/jpeg":(".jpg",b"\xff\xd8\xff"),"image/png":(".png",b"\x89PNG\r\n\x1a\n"),"image/webp":(".webp",b"RIFF")}

class CaseCreate(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    order_id:int=Field(gt=0)
    kind:str=Field(pattern=r"^(RETURN|SIZE_EXCHANGE|ORDER_CHANGE)$")
    reason:str=Field(strict=True,min_length=2,max_length=1000)
    reason_type:str|None=Field(default=None,pattern=r"^(CHANGE_OF_MIND|DEFECT_OR_WRONG)$")
    target_variation_id:str|None=Field(default=None,pattern=r"^[1-9][0-9]*$")

class RefundAccountDetails(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    bank_name:str=Field(strict=True,min_length=2,max_length=40,pattern=r"^[가-힣A-Za-z0-9 ._-]+$")
    account_holder:str=Field(strict=True,min_length=2,max_length=40,pattern=r"^[가-힣A-Za-z ._-]+$")
    account_number:str=Field(strict=True,min_length=7,max_length=32,pattern=r"^[0-9-]+$")

from core.shopping.guest_returns import ReturnWorkflow
from core.shopping.manual_refunds import ManualRefundRecords
from core.shopping.public_order_number import public_order_number, is_public_order_number

class GuestAftersalesStore(ReturnWorkflow,ManualRefundRecords):
    def __init__(self,path,attachments,*,ledger,checkout,catalog,clock=time.time,stock_cancellation=None,stock_return=None,refund_account_key=None):
        self.path=Path(path);self.attachments=Path(attachments);self.ledger=ledger;self.checkout=checkout;self.catalog=catalog;self.clock=clock
        self.refund_account_key=refund_account_key
        self.stock_return=stock_return
        self.stock_cancellation=stock_cancellation
        if self.path.is_symlink() or self.attachments.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        self.attachments.mkdir(parents=True,exist_ok=True);os.chmod(self.attachments,0o700)
        with connection(self.path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS fulfillment(
                order_id INTEGER PRIMARY KEY,state TEXT NOT NULL,carrier TEXT,tracking TEXT,shipped REAL,delivered REAL,updated REAL NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS cases(
                id TEXT PRIMARY KEY,order_id INTEGER NOT NULL,customer TEXT NOT NULL,kind TEXT NOT NULL,target_variation_id TEXT,
                target_option TEXT,reason TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,
                reason_type TEXT,shipping_fee_payer TEXT)""")
            case_columns={row[1] for row in c.execute("PRAGMA table_info(cases)")}
            if "reason_type" not in case_columns:c.execute("ALTER TABLE cases ADD COLUMN reason_type TEXT")
            if "shipping_fee_payer" not in case_columns:c.execute("ALTER TABLE cases ADD COLUMN shipping_fee_payer TEXT")
            if "refund_account_consent_version" not in case_columns:c.execute("ALTER TABLE cases ADD COLUMN refund_account_consent_version TEXT")
            if "refund_account_consent_at" not in case_columns:c.execute("ALTER TABLE cases ADD COLUMN refund_account_consent_at REAL")
            c.execute("""CREATE TABLE IF NOT EXISTS attachments(
                id TEXT PRIMARY KEY,case_id TEXT NOT NULL,media_type TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT NOT NULL,
                stored_name TEXT NOT NULL,created REAL NOT NULL)""")
            c.execute("CREATE TABLE IF NOT EXISTS shipping_notices(order_id INTEGER PRIMARY KEY,carrier TEXT NOT NULL,tracking TEXT NOT NULL,state TEXT NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS fulfillment_settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
            if not c.execute("SELECT 1 FROM fulfillment_settings WHERE key='shipping_seeded'").fetchone():
                c.execute("INSERT OR IGNORE INTO shipping_notices SELECT order_id,carrier,tracking,'HISTORICAL' FROM fulfillment WHERE state IN ('SHIPPED','DELIVERED')")
                c.execute("INSERT INTO fulfillment_settings VALUES('shipping_seeded','1')")
            c.execute("CREATE TABLE IF NOT EXISTS return_stock_operations(case_id TEXT PRIMARY KEY,order_id INTEGER UNIQUE NOT NULL,state TEXT NOT NULL,updated REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS cancellations(order_id INTEGER PRIMARY KEY,state TEXT NOT NULL,updated REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS payments(order_id INTEGER PRIMARY KEY,state TEXT NOT NULL,updated REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS manual_refunds(case_id TEXT PRIMARY KEY,order_id INTEGER UNIQUE NOT NULL,amount TEXT NOT NULL,currency TEXT NOT NULL,evidence TEXT UNIQUE NOT NULL,actor TEXT NOT NULL,update_id INTEGER NOT NULL,recorded REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS refund_destinations(case_id TEXT PRIMARY KEY,ciphertext BLOB NOT NULL,notice_version TEXT NOT NULL,created REAL NOT NULL)")
            c.execute("CREATE TABLE IF NOT EXISTS operator_updates(update_id INTEGER PRIMARY KEY,reply TEXT NOT NULL)")
        os.chmod(self.path,0o600)
    def _fulfillment(self,order_id):
        with connection("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            row=c.execute("SELECT state,carrier,tracking,shipped,delivered,updated FROM fulfillment WHERE order_id=?",(order_id,)).fetchone()
        if not row:return {"state":"NOT_SHIPPED","carrier":None,"tracking":None,"shipped":None,"delivered":None,"updated":None}
        return dict(zip(("state","carrier","tracking","shipped","delivered","updated"),row))
    def _case_rows(self,order_id=None,customer=None,limit=100,case_id=None):
        q="SELECT id,order_id,customer,kind,target_variation_id,target_option,reason,state,created,updated,reason_type,shipping_fee_payer FROM cases"
        where=[];args=[]
        if order_id is not None:where.append("order_id=?");args.append(order_id)
        if customer is not None:where.append("customer=?");args.append(customer)
        if case_id is not None:where.append("id=?");args.append(case_id)
        if where:q+=" WHERE "+" AND ".join(where)
        q+=" ORDER BY created DESC LIMIT ?";args.append(max(1,min(int(limit),100)))
        with connection("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row;rows=[dict(r) for r in c.execute(q,args)]
            for row in rows:
                row["attachments"]=c.execute("SELECT COUNT(*) FROM attachments WHERE case_id=?",(row["id"],)).fetchone()[0]
        return rows
    def _customer_order(self,customer,order_id):
        rows=[r for r in self.ledger.customer_orders(customer) if r["provider_order_id"]==order_id]
        if len(rows)!=1:raise ValueError("ORDER_NOT_OWNED")
        row=rows[0];draft=self.checkout.by_customer_operation(row["operation_key"],customer,allow_expired=True)
        if draft["state"]!="CONFIRMED":raise ValueError("ORDER_NOT_CONFIRMED")
        if getattr(self,"verified_phone",None):
            from core.shopping.guest_operator import local_phone
            if local_phone(draft["body"]["billing"]["phone"])!=local_phone(self.verified_phone):raise ValueError("ORDER_NOT_OWNED")
        return row,draft
    def customer_orders(self,customer):
        result=[]
        for row in self.ledger.customer_orders(customer):
            try:draft=self.checkout.by_customer_operation(row["operation_key"],customer,allow_expired=True)
            except Exception:continue
            if draft["state"]!="CONFIRMED":continue
            f=self._fulfillment(row["provider_order_id"]);cases=self._case_rows(order_id=row["provider_order_id"],customer=customer,limit=20)
            now=self.clock();within=f["state"]=="DELIVERED" and type(f["delivered"]) in (int,float) and f["delivered"]<=now<f["delivered"]+RETURN_WINDOW
            active=any(v["state"]!="REJECTED" for v in cases)
            order_number=public_order_number(requested_at=row["requested_at"],phone=draft["body"]["billing"]["phone"],entropy=row.get("reference") or row["operation_key"])
            payment=self.payment(row["provider_order_id"])
            pre_ship=row["review_state"] in ("PENDING_REVIEW","CONFIRMED") and f["state"]=="NOT_SHIPPED" and not active and self.cancellation(row["provider_order_id"])["state"]=="NONE"
            result.append({"order_id":row["provider_order_id"],"order_number":order_number,"review_state":row["review_state"],"requested_at":row["requested_at"],
                "items":draft["body"]["quote"]["line_items"],"total":draft["body"]["quote"]["final_total"],"currency":draft["body"]["quote"]["currency"],
                "fulfillment":f,"payment":payment,"refund":self.refund(row["provider_order_id"]),"cancellation":self.cancellation(row["provider_order_id"]),"return_status":self.return_status(row["provider_order_id"]),"return_available":bool(row["review_state"]=="CONFIRMED" and within and not active and self.cancellation(row["provider_order_id"])["state"]=="NONE"),
                "exchange_available":bool(row["review_state"]=="CONFIRMED" and within and not active and self.cancellation(row["provider_order_id"])["state"]=="NONE"),
                "cancel_request_available":bool(pre_ship),
                "order_change_available":bool(pre_ship),"cases":cases})
        return result
    def payment(self,order_id):
        with connection(self.path) as c:
            row=c.execute("SELECT state,updated FROM payments WHERE order_id=?",(order_id,)).fetchone()
        return {"state":row[0] if row else "AWAITING_DEPOSIT","updated":row[1] if row else None}
    def cancellation(self,order_id):
        with connection(self.path) as c:
            row=c.execute("SELECT state,updated FROM cancellations WHERE order_id=?",(order_id,)).fetchone()
        return {"state":row[0] if row else "NONE","updated":row[1] if row else None}
    @staticmethod
    def _deny_cancelled(c,order_id):
        if c.execute("SELECT 1 FROM cancellations WHERE order_id=?",(order_id,)).fetchone():
            raise ValueError("ORDER_CANCELLATION_ACTIVE")
    def cancel_order(self,order_id,*,refund_case_id=None):
        rows=[r for r in self.ledger.operator_orders() if r["provider_order_id"]==order_id and r["state"]=="CONFIRMED"]
        if len(rows)!=1:raise ValueError("CONFIRMED_ORDER_REQUIRED")
        row=rows[0]
        draft=self.checkout.by_customer_operation(row["operation_key"],row["customer_id"],allow_expired=True)
        if draft["state"]!="CONFIRMED":raise ValueError("ORDER_NOT_CONFIRMED")
        if self.stock_cancellation is None:raise ValueError("CANCELLATION_NOT_CONFIGURED")
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            old=c.execute("SELECT state FROM cancellations WHERE order_id=?",(order_id,)).fetchone()
            if old:
                if old[0]=="CANCELLED":return self.cancellation(order_id)
                raise ValueError("CANCELLATION_RECONCILIATION_REQUIRED")
            payment=c.execute("SELECT state FROM payments WHERE order_id=?",(order_id,)).fetchone()
            if payment and payment[0]=="PAID":
                if refund_case_id is None:
                    approved=c.execute("SELECT id FROM cases WHERE order_id=? AND kind='RETURN' AND state='RETURN_APPROVED'",(order_id,)).fetchall()
                    if len(approved)==1:refund_case_id=approved[0][0]
                if type(refund_case_id) is not str or not re.fullmatch(r"[a-f0-9]{8}",refund_case_id):
                    raise ValueError("PAID_CANCELLATION_REQUIRES_REFUND_REVIEW")
                case=c.execute("SELECT order_id,kind,state FROM cases WHERE id=?",(refund_case_id,)).fetchone()
                if not case or case!=(order_id,"RETURN","RETURN_APPROVED"):
                    raise ValueError("PAID_CANCELLATION_REQUIRES_REFUND_REVIEW")
            shipment=c.execute("SELECT state FROM fulfillment WHERE order_id=?",(order_id,)).fetchone()
            if shipment and shipment[0] in ("SHIPPED","DELIVERED"):raise ValueError("SHIPPED_CANCELLATION_DENIED")
            c.execute("INSERT INTO cancellations VALUES(?,?,?)",(order_id,"SENDING",self.clock()))
        try:
            receipt=self.stock_cancellation(row,draft)
            if receipt.get("outcome")!="STOCK_CANCELLED" or receipt.get("order_id")!=order_id:
                raise ValueError("CANCELLATION_RECEIPT_INVALID")
        except Exception:
            with connection(self.path) as c:
                c.execute("UPDATE cancellations SET state='UNKNOWN',updated=? WHERE order_id=?",(self.clock(),order_id))
            raise ValueError("CANCELLATION_RECONCILIATION_REQUIRED") from None
        with connection(self.path) as c:
            c.execute("UPDATE cancellations SET state='CANCELLED',updated=? WHERE order_id=?",(self.clock(),order_id))
        return self.cancellation(order_id)
    def reconcile_cancellation(self,order_id):
        current=self.cancellation(order_id)
        if current["state"]=="CANCELLED":return current
        if current["state"] not in ("SENDING","UNKNOWN") or not hasattr(self.stock_cancellation,"reconcile"):
            raise ValueError("CANCELLATION_RECONCILIATION_REQUIRED")
        rows=[r for r in self.ledger.operator_orders() if r["provider_order_id"]==order_id and r["state"]=="CONFIRMED"]
        if len(rows)!=1:raise ValueError("CONFIRMED_ORDER_REQUIRED")
        row=rows[0];draft=self.checkout.by_customer_operation(row["operation_key"],row["customer_id"],allow_expired=True)
        receipt=self.stock_cancellation.reconcile(row,draft)
        if not receipt or receipt.get("outcome")!="STOCK_CANCELLED" or receipt.get("order_id")!=order_id:
            raise ValueError("CANCELLATION_RECONCILIATION_REQUIRED")
        with connection(self.path) as c:
            c.execute("UPDATE cancellations SET state='CANCELLED',updated=? WHERE order_id=? AND state IN ('SENDING','UNKNOWN')",(self.clock(),order_id))
        return self.cancellation(order_id)
    def confirm_payment(self,order_id):
        rows=[r for r in self.ledger.operator_orders() if r["provider_order_id"]==order_id and r["state"]=="CONFIRMED"]
        if len(rows)!=1:raise ValueError("CONFIRMED_ORDER_REQUIRED")
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            self._deny_cancelled(c,order_id)
            c.execute("INSERT OR IGNORE INTO payments VALUES(?,?,?)",(order_id,"PAID",self.clock()))
        return self.payment(order_id)
    def lookup(self,customer,order_number,phone,verified_phone):
        from core.shopping.guest_operator import local_phone
        if type(phone) is not str or not re.fullmatch(r"[+0-9 ()-]{8,32}",phone):raise ValueError("ORDER_NOT_FOUND")
        if local_phone(phone)!=local_phone(verified_phone):raise ValueError("ORDER_NOT_FOUND")
        number=str(order_number).strip().removeprefix("#")
        if not re.fullmatch(r"[0-9]{1,18}",number):raise ValueError("ORDER_NOT_FOUND")
        orders=self.customer_orders(customer)
        matched=[item for item in orders if item["order_number"]==number]
        if not matched and number.isdigit() and int(number)>0:
            matched=[item for item in orders if item["order_id"]==int(number)]
        if len(matched)!=1:raise ValueError("ORDER_NOT_FOUND")
        order=matched[0];order_id=order["order_id"];row,draft=self._customer_order(customer,order_id)
        if local_phone(draft["body"]["billing"]["phone"])!=local_phone(verified_phone):raise ValueError("ORDER_NOT_FOUND")
        order["delivery"]=draft["body"]["shipping"]
        order["payment"]=self.payment(order_id)
        if getattr(self,"sms",None):order["notification_state"]=self.sms.state(order_id)
        return order
    def public_lookup(self,order_number,phone):
        from core.shopping.guest_operator import local_phone
        number=str(order_number).strip().removeprefix("#")
        if not is_public_order_number(number) or type(phone) is not str:raise ValueError("ORDER_NOT_FOUND")
        try:submitted_phone=local_phone(phone)
        except ValueError as error:raise ValueError("ORDER_NOT_FOUND") from error
        for row in self.ledger.operator_orders():
            if row.get("state") not in ("PENDING_REVIEW","CONFIRMED"):continue
            try:draft=self.checkout.by_customer_operation(row["operation_key"],row["customer_id"],allow_expired=True)
            except Exception:continue
            if draft.get("state")!="CONFIRMED":continue
            phone=local_phone(draft["body"]["billing"]["phone"])
            if phone!=submitted_phone:continue
            expected=public_order_number(requested_at=row.get("requested_at"),phone=phone,entropy=row.get("reference") or row["operation_key"])
            if expected!=number:continue
            order_id=row["provider_order_id"]
            return {
                "order_number":number,
                "review_state":row.get("review_state") or row.get("state"),
                "requested_at":row.get("requested_at"),
                "items":draft["body"]["quote"]["line_items"],
                "total":draft["body"]["quote"]["final_total"],
                "currency":draft["body"]["quote"]["currency"],
                "fulfillment":self._fulfillment(order_id),
                "payment":self.payment(order_id),
                "refund":self.refund(order_id),
                "cancellation":self.cancellation(order_id),
                "return_status":self.return_status(order_id),
                "return_available":False,
                "exchange_available":False,
                "cancel_request_available":False,
                "order_change_available":False,
                "cases":[],
                "public_only":True,
            }
        raise ValueError("ORDER_NOT_FOUND")
    def exchange_options(self,customer,order_id):
        _,draft=self._customer_order(customer,order_id);body=draft["body"]
        if len(body["line_items"])!=1:raise ValueError("MULTILINE_EXCHANGE_UNSUPPORTED")
        line=body["line_items"][0];product=self.catalog.get_product(line["product_id"])
        options=[]
        for v in product["variants"]:
            if v.available and v.id!=line["variation_id"]:options.append({"variation_id":v.id,"option":v.label})
        return options
    def create_case(self,customer,data,*,refund_account=None,refund_account_consent=False):
        data=CaseCreate.model_validate(data);row,draft=self._customer_order(customer,data.order_id);f=self._fulfillment(data.order_id);now=self.clock()
        paid=self.payment(data.order_id)["state"]=="PAID"
        refund_required=data.kind=="RETURN" and f["state"]=="NOT_SHIPPED" and paid
        if refund_account is not None:
            refund_account=RefundAccountDetails.model_validate(refund_account)
            if not paid or data.kind!="RETURN" or f["state"]!="NOT_SHIPPED":raise ValueError("REFUND_ACCOUNT_NOT_APPLICABLE")
            if refund_account_consent is not True:raise ValueError("REFUND_ACCOUNT_CONSENT_REQUIRED")
            if not isinstance(self.refund_account_key,bytes) or len(self.refund_account_key)!=32:raise ValueError("REFUND_ACCOUNT_STORAGE_UNAVAILABLE")
        if refund_required and refund_account is None:raise ValueError("REFUND_ACCOUNT_REQUIRED")
        if refund_account is None and refund_account_consent is True:raise ValueError("REFUND_ACCOUNT_NOT_APPLICABLE")
        if not data.reason.strip():raise ValueError("REASON_REQUIRED")
        if row["review_state"] not in ("PENDING_REVIEW","CONFIRMED") or self.cancellation(data.order_id)["state"]!="NONE":raise ValueError("ORDER_NOT_ACTIONABLE")
        if f["state"]=="NOT_SHIPPED":
            if data.kind not in ("RETURN","ORDER_CHANGE"):raise ValueError("DELIVERY_REQUIRED")
            if data.reason_type is not None:raise ValueError("REASON_TYPE_INVALID")
        elif data.kind in ("RETURN","SIZE_EXCHANGE"):
            if f["state"]!="DELIVERED" or not f["delivered"] or not f["delivered"]<=now<f["delivered"]+RETURN_WINDOW:raise ValueError("RETURN_WINDOW_CLOSED")
            if data.reason_type is None:raise ValueError("REASON_TYPE_REQUIRED")
        else:raise ValueError("ORDER_CHANGE_CLOSED")
        if any(v["state"]!="REJECTED" for v in self._case_rows(order_id=data.order_id,customer=customer)):
            raise ValueError("CASE_ALREADY_ACTIVE")
        target=None
        if data.kind=="SIZE_EXCHANGE":
            if not data.target_variation_id:raise ValueError("TARGET_SIZE_REQUIRED")
            opts={v["variation_id"]:v["option"] for v in self.exchange_options(customer,data.order_id)}
            target=opts.get(data.target_variation_id)
            if target is None:raise ValueError("TARGET_SIZE_UNAVAILABLE")
        fee_payer={"CHANGE_OF_MIND":"CUSTOMER","DEFECT_OR_WRONG":"SELLER"}.get(data.reason_type)
        identifier=secrets.token_hex(4)
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM cases WHERE order_id=? AND state!='REJECTED'",(data.order_id,)).fetchone():raise ValueError("CASE_ALREADY_ACTIVE")
            c.execute("INSERT INTO cases(id,order_id,customer,kind,target_variation_id,target_option,reason,state,created,updated,reason_type,shipping_fee_payer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (identifier,data.order_id,customer,data.kind,data.target_variation_id,target,data.reason.strip(),"REQUESTED",now,now,data.reason_type,fee_payer))
            if refund_account is not None:
                c.execute("UPDATE cases SET refund_account_consent_version=?,refund_account_consent_at=? WHERE id=?",(REFUND_ACCOUNT_NOTICE_VERSION,now,identifier))
                nonce=secrets.token_bytes(12)
                plaintext=json.dumps(refund_account.model_dump(),ensure_ascii=False,separators=(",",":")).encode()
                aad=("aicc-dev-refund-account:"+identifier).encode()
                cipher=nonce+AESGCM(self.refund_account_key).encrypt(nonce,plaintext,aad)
                c.execute("INSERT INTO refund_destinations VALUES(?,?,?,?)",(identifier,cipher,REFUND_ACCOUNT_NOTICE_VERSION,now))
        return self.case(customer,identifier)
    def admin_refund_account(self,case_id):
        rows=self._case_rows(case_id=case_id)
        if len(rows)!=1 or rows[0]["kind"]!="RETURN" or rows[0]["state"]!="RETURN_APPROVED":raise ValueError("REFUND_ACCOUNT_NOT_AVAILABLE")
        if self.payment(rows[0]["order_id"])["state"]!="PAID" or self.cancellation(rows[0]["order_id"])["state"]!="CANCELLED":raise ValueError("REFUND_ACCOUNT_NOT_AVAILABLE")
        if not isinstance(self.refund_account_key,bytes) or len(self.refund_account_key)!=32:raise ValueError("REFUND_ACCOUNT_STORAGE_UNAVAILABLE")
        with connection("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            row=c.execute("SELECT ciphertext FROM refund_destinations WHERE case_id=?",(case_id,)).fetchone()
        if not row:raise ValueError("REFUND_ACCOUNT_NOT_AVAILABLE")
        blob=bytes(row[0]);aad=("aicc-dev-refund-account:"+case_id).encode()
        try:value=json.loads(AESGCM(self.refund_account_key).decrypt(blob[:12],blob[12:],aad))
        except Exception:raise ValueError("REFUND_ACCOUNT_UNAVAILABLE") from None
        return RefundAccountDetails.model_validate(value).model_dump()
    def admin_exchange_options(self,order_id):
        row=self._operator_order(int(order_id))
        return self.exchange_options(row["customer_id"],int(order_id))
    def admin_create_case(self,order_id,data):
        data=CaseCreate.model_validate(data)
        if data.order_id!=int(order_id):raise ValueError("ORDER_BINDING_INVALID")
        row=self._operator_order(int(order_id));customer=row["customer_id"]
        if self.cancellation(int(order_id))["state"]!="NONE":raise ValueError("ORDER_CANCELLATION_ACTIVE")
        if data.kind=="RETURN" and self.payment(int(order_id))["state"]!="PAID":
            raise ValueError("REFUND_PAYMENT_REQUIRED")
        target=None
        if data.kind=="SIZE_EXCHANGE":
            if not data.target_variation_id:raise ValueError("TARGET_SIZE_REQUIRED")
            options={v["variation_id"]:v["option"] for v in self.exchange_options(customer,int(order_id))}
            target=options.get(data.target_variation_id)
            if target is None:raise ValueError("TARGET_SIZE_UNAVAILABLE")
        identifier=secrets.token_hex(4);stamp=self.clock()
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM cancellations WHERE order_id=?",(int(order_id),)).fetchone():
                raise ValueError("ORDER_CANCELLATION_ACTIVE")
            if data.kind=="RETURN":
                payment=c.execute("SELECT state FROM payments WHERE order_id=?",(int(order_id),)).fetchone()
                if not payment or payment[0]!="PAID":raise ValueError("REFUND_PAYMENT_REQUIRED")
            if c.execute("SELECT 1 FROM cases WHERE order_id=? AND state!='REJECTED'",(int(order_id),)).fetchone():
                raise ValueError("CASE_ALREADY_ACTIVE")
            if c.execute("SELECT 1 FROM manual_refunds WHERE order_id=?",(int(order_id),)).fetchone():
                raise ValueError("REFUND_ALREADY_RECORDED")
            c.execute("INSERT INTO cases(id,order_id,customer,kind,target_variation_id,target_option,reason,state,created,updated,reason_type,shipping_fee_payer) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (identifier,int(order_id),customer,data.kind,data.target_variation_id,target,data.reason.strip(),"REQUESTED",stamp,stamp,data.reason_type,{"CHANGE_OF_MIND":"CUSTOMER","DEFECT_OR_WRONG":"SELLER"}.get(data.reason_type)))
        matches=self._case_rows(case_id=identifier)
        if not matches:raise ValueError("CASE_NOT_FOUND")
        return matches[0]
    def case(self,customer,case_id):
        rows=self._case_rows(customer=customer,case_id=case_id)
        if len(rows)!=1:raise ValueError("CASE_NOT_OWNED")
        return rows[0]
    def attach(self,customer,case_id,media_type,raw):
        case=self.case(customer,case_id)
        if case["state"]!="REQUESTED":raise ValueError("CASE_NOT_EDITABLE")
        if media_type not in MEDIA or not raw or len(raw)>MAX_ATTACHMENT:raise ValueError("ATTACHMENT_INVALID")
        suffix,magic=MEDIA[media_type]
        if not raw.startswith(magic) or media_type=="image/webp" and (len(raw)<12 or raw[8:12]!=b"WEBP"):raise ValueError("ATTACHMENT_INVALID")
        if case["attachments"]>=5:raise ValueError("ATTACHMENT_LIMIT")
        identifier=secrets.token_hex(8);stored=identifier+suffix;target=self.attachments/stored
        with target.open("xb") as f:f.write(raw)
        os.chmod(target,0o600);stamp=self.clock()
        with connection(self.path) as c:c.execute("INSERT INTO attachments VALUES(?,?,?,?,?,?,?)",(identifier,case_id,media_type,len(raw),hashlib.sha256(raw).hexdigest(),stored,stamp))
        return {"attachment_id":identifier,"media_type":media_type,"size":len(raw)}
    def _operator_order(self,order_id):
        rows=[r for r in self.ledger.operator_orders() if r["provider_order_id"]==int(order_id)]
        if len(rows)!=1 or rows[0]["state"]!="CONFIRMED":raise ValueError("ORDER_NOT_READY_FOR_FULFILLMENT")
        return rows[0]
    def mark_shipped(self,order_id,carrier,tracking):
        self._operator_order(order_id)
        if not re.fullmatch(r"[가-힣A-Za-z0-9 ._-]{2,40}",carrier) or not re.fullmatch(r"[A-Za-z0-9-]{5,40}",tracking):raise ValueError("TRACKING_INVALID")
        stamp=self.clock()
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            self._deny_cancelled(c,order_id)
            current=c.execute("SELECT state,carrier,tracking FROM fulfillment WHERE order_id=?",(order_id,)).fetchone()
            if current and current[0] in ("SHIPPED","DELIVERED"):
                if (current[1],current[2])!=(carrier,tracking):raise ValueError("SHIPMENT_ALREADY_REGISTERED")
            else:
                payment=c.execute("SELECT state FROM payments WHERE order_id=?",(order_id,)).fetchone()
                if not payment or payment[0]!="PAID":raise ValueError("PAYMENT_REQUIRED")
                c.execute("INSERT INTO fulfillment VALUES(?,?,?,?,?,?,?)",(order_id,"SHIPPED",carrier,tracking,stamp,None,stamp))
                c.execute("INSERT OR IGNORE INTO shipping_notices VALUES(?,?,?,'PENDING')",(order_id,carrier,tracking))
        return self._fulfillment(order_id)
    def mark_delivered(self,order_id):
        self._operator_order(order_id)
        with connection(self.path) as c:
            # Serialize delivery completion so concurrent commands preserve the
            # first receipt and the customer return-window start time.
            c.execute("BEGIN IMMEDIATE")
            self._deny_cancelled(c,order_id)
            current=c.execute("SELECT state FROM fulfillment WHERE order_id=?",(order_id,)).fetchone()
            if not current or current[0] not in ("SHIPPED","DELIVERED"):
                raise ValueError("SHIPMENT_REQUIRED")
            if current[0]=="SHIPPED":
                stamp=self.clock()
                c.execute("UPDATE fulfillment SET state='DELIVERED',delivered=?,updated=? WHERE order_id=?",(stamp,stamp,order_id))
        return self._fulfillment(order_id)
    def admin_fulfillment(self,order_id):return self._fulfillment(order_id)
    def admin_cases(self,kind=None):
        rows=self._case_rows(limit=100)
        if kind:rows=[r for r in rows if r["kind"]==kind]
        return rows
    def decide(self,case_id,approve):
        with connection(self.path) as c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT kind,state FROM cases WHERE id=?",(case_id,)).fetchone()
            if row is None:raise ValueError("CASE_NOT_FOUND")
            kind,state=row
            if state=="REQUESTED":
                state=("RETURN_APPROVED" if kind=="RETURN" else "EXCHANGE_APPROVED" if kind=="SIZE_EXCHANGE" else "ORDER_CHANGE_APPROVED") if approve else "REJECTED"
                c.execute("UPDATE cases SET state=?,updated=? WHERE id=?",(state,self.clock(),case_id))
                if state=="REJECTED":c.execute("DELETE FROM refund_destinations WHERE case_id=?",(case_id,))
            elif state!="REJECTED" and not state.startswith("RETURN_") and state not in ("EXCHANGE_APPROVED","ORDER_CHANGE_APPROVED"):
                raise ValueError("CASE_STATE_INVALID")
            elif (state=="REJECTED")==approve:
                # A later opposite decision cannot change history or claim success.
                raise ValueError("CASE_DECISION_CONFLICT")
        matches=self._case_rows(case_id=case_id)
        if not matches:raise ValueError("CASE_NOT_FOUND")
        return matches[0]
    def operator_command(self,text,update_id,actor=None):
        clean=text.strip()
        if clean in ("배송","배송 완료","배송완료","입금확인","입금 확인"):
            return "입금확인 #주문번호 / 배송 #주문번호 택배사 운송장번호 / 배송완료 #주문번호 형식으로 입력해 주세요."
        if re.fullmatch(r"배송\s*#[1-9][0-9]*",clean):return "택배사와 운송장번호를 함께 입력해 주세요. 예: 배송 #15 CJ대한통운 1234567890"
        patterns=[
            (r"환불기록\s*#([a-f0-9]{8})\s+([1-9][0-9]{0,7})원\s+증빙\s+([가-힣A-Za-z0-9._-]{3,80})","refund_record"),
            (r"반품\s*(회수|검수완료|복원확인)\s*#([a-f0-9]{8})","return_stock"),
            (r"(?:주문)?취소\s*#([1-9][0-9]*)","cancel"),
            (r"취소\s*확인\s*#([1-9][0-9]*)","cancel_reconcile"),
            (r"입금\s*(확인|상태)\s*#([1-9][0-9]*)","payment"),
            (r"(?:주문발송|배송)\s*#([1-9][0-9]*)\s+([가-힣A-Za-z0-9 ._-]{2,40})\s+([A-Za-z0-9-]{5,40})","ship"),
            (r"배송\s*완료\s*#([1-9][0-9]*)","delivered"),
            (r"배송상태\s*#([1-9][0-9]*)","status"),
            (r"(환불|교환)목록","cases"),
            (r"(환불|교환)(승인|거절)\s*#([a-f0-9]{8})","decision")]
        matched=None
        for pattern,kind in patterns:
            m=re.fullmatch(pattern,clean)
            if m:matched=(m,kind);break
        if matched is None:return None
        with connection("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            old=c.execute("SELECT reply FROM operator_updates WHERE update_id=?",(update_id,)).fetchone()
        if old:return old[0]
        m,kind=matched
        try:
            if kind=="refund_record":
                value=self.record_refund(m[1],int(m[2]),m[3],actor,update_id)
                reply="환불 #"+m[1]+" · 환불완료 기록 · "+value["amount"]+" KRW · 실제 송금은 실행하지 않았습니다."
            elif kind=="return_stock":
                method={"회수":self.receive_return,"검수완료":self.inspect_return,"복원확인":self.reconcile_return}[m[1]]
                value=method(m[2]);reply="반품 #"+m[2]+" · "+{"RETURN_RECEIVED":"회수완료 · 검수 대기","RETURN_RESTOCKED":"검수완료 · 재고 복원 확인 · 환불 검토 필요"}.get(value["state"],"처리 결과 확인중")
                if self.refund(self._return_case(m[2])[0]["order_id"])["state"]=="RECORDED":reply="반품 #"+m[2]+" · 검수완료 · 재고 복원 확인 · 환불완료 기록"
            elif kind in ("cancel","cancel_reconcile"):
                value=self.cancel_order(int(m[1])) if kind=="cancel" else self.reconcile_cancellation(int(m[1]))
                reply="주문 #"+m[1]+" 취소완료 · 재고 복원 확인 · 결제 환불은 실행하지 않았습니다."
            elif kind=="payment":
                value=self.confirm_payment(int(m[2])) if m[1]=="확인" else self.payment(int(m[2]))
                shipping_label={"SHIPPED":"배송중","DELIVERED":"배송완료"}.get(self._fulfillment(int(m[2]))["state"],"배송준비")
                reply="주문 #"+m[2]+" · "+("입금완료 · "+shipping_label if value["state"]=="PAID" else "입금대기")
            elif kind=="ship":
                v=self.mark_shipped(int(m[1]),m[2],m[3]);reply="주문 #"+m[1]+" 발송 등록 · "+("배송완료" if v["state"]=="DELIVERED" else "배송중")+" · "+v["carrier"]+" "+v["tracking"]
            elif kind=="delivered":
                self.mark_delivered(int(m[1]));reply="주문 #"+m[1]+" 배송완료 · 지금부터 14일 환불/사이즈교환 접수 가능"
            elif kind=="status":
                v=self._fulfillment(int(m[1]));reply="주문 #"+m[1]+" 배송상태: "+v["state"]+(("\n"+str(v["carrier"])+" "+str(v["tracking"])) if v["tracking"] else "")
            elif kind=="cases":
                target="RETURN" if m[1]=="환불" else "SIZE_EXCHANGE";rows=self.admin_cases(target)
                reply=(m[1]+" 요청이 없습니다." if not rows else "\n".join("#"+r["id"]+" · 주문 #"+str(r["order_id"])+" · "+r["state"]+" · "+r["reason"][:80]+(" · 환불완료 기록 "+self.refund(r["order_id"])["amount"]+" KRW" if self.refund(r["order_id"])["state"]=="RECORDED" else "") for r in rows[:20]))
            else:
                target="RETURN" if m[1]=="환불" else "SIZE_EXCHANGE";rows=[r for r in self.admin_cases(target) if r["id"]==m[3]]
                if len(rows)!=1:reply="해당 요청을 찾지 못했습니다."
                else:
                    v=self.decide(m[3],m[2]=="승인");reply=m[1]+" #"+m[3]+" "+("승인" if m[2]=="승인" else "거절")+" · "+v["state"]
        except ValueError as error:
            reply={"MANUAL_REFUND_DISABLED":"환불완료 기록은 DEV 검증에서만 활성화되어 있습니다.",
                "REFUND_ACTOR_REQUIRED":"허용된 운영자 확인이 필요합니다.",
                "REFUND_INSPECTION_REQUIRED":"반품 회수·검수와 재고 복원 확인 후 환불완료를 기록해 주세요.",
                "FULL_REFUND_AMOUNT_REQUIRED":"현재는 주문 전체 금액만 환불 기록할 수 있습니다. 금액을 확인해 주세요.",
                "REFUND_RECORD_CONFLICT":"이미 기록된 환불 금액·증빙과 다릅니다. 기존 기록을 변경하지 않았습니다.",
                "REFUND_EVIDENCE_REUSED":"다른 환불에 사용된 증빙입니다. 기록을 확인해 주세요.",
                "CASE_DECISION_CONFLICT":"기존 승인·거절 결정과 충돌합니다. 상태를 변경하지 않았습니다. 케이스 내역을 확인해 주세요.",
                "RETURN_APPROVAL_REQUIRED":"반품 승인 후 회수를 등록해 주세요.",
                "RETURN_RECEIPT_REQUIRED":"실물 회수 후 재판매 가능한 상품의 검수완료를 등록해 주세요.",
                "RETURN_RECONCILIATION_REQUIRED":"재고 복원 결과 확인이 필요합니다. 반품 복원확인 #케이스번호로 기존 결과를 확인해 주세요. 재고는 다시 복원하지 않습니다.",
                "RETURN_RESTORATION_NOT_CONFIGURED":"반품 재고 복원 기능이 아직 활성화되지 않았습니다.",
                "PAID_CANCELLATION_REQUIRES_REFUND_REVIEW":"입금된 주문은 자동 취소하지 않습니다. 환불 검토가 필요합니다.",
                "SHIPPED_CANCELLATION_DENIED":"배송이 시작된 주문은 취소할 수 없습니다. 반품 접수로 진행해 주세요.",
                "CANCELLATION_RECONCILIATION_REQUIRED":"취소 결과 확인이 필요합니다. 취소확인 #주문번호로 기존 처리 결과를 확인해 주세요. 재고 복원은 다시 실행하지 않습니다.",
                "ORDER_CANCELLATION_ACTIVE":"취소 처리 중이거나 취소된 주문입니다. 입금·배송 변경을 중단합니다.",
                "CANCELLATION_NOT_CONFIGURED":"취소 기능이 아직 활성화되지 않았습니다.",
                "PAYMENT_REQUIRED":"입금확인 후 배송을 등록해 주세요.",
                "SHIPMENT_ALREADY_REGISTERED":"기존 배송정보가 있습니다. 이미 배송된 주문은 다시 변경하지 않습니다.",
                "SHIPMENT_REQUIRED":"배송을 먼저 등록해 주세요."}.get(str(error),"요청을 처리하지 못했습니다. 주문/케이스 상태를 확인해 주세요.")
        except Exception:
            reply="요청을 처리하지 못했습니다. 주문/케이스 상태를 확인해 주세요."
        try:
            with connection(self.path) as c:c.execute("INSERT INTO operator_updates VALUES(?,?)",(update_id,reply))
        except sqlite3.IntegrityError:
            with connection("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
                existing=c.execute("SELECT reply FROM operator_updates WHERE update_id=?",(update_id,)).fetchone()
            if existing:return existing[0]
        return reply

PORTAL="""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>주문·환불·사이즈교환</title><style>
body{font:15px system-ui;background:#f6f4f1;color:#222;margin:0}main{max-width:760px;margin:auto;padding:20px}.card{background:#fff;border:1px solid #ddd;border-radius:14px;padding:16px;margin:12px 0}
button,input,select,textarea{font:inherit;padding:10px;border:1px solid #bbb;border-radius:9px;margin:4px}textarea{width:calc(100% - 24px);min-height:80px}.muted{color:#666}.case{background:#f6f6f4;padding:10px;border-radius:9px;margin-top:8px}
</style><main><h1>내 주문 / 환불·사이즈교환</h1><p class="muted">휴대폰 인증 후 본인 주문만 조회합니다. 환불·사이즈교환은 배송완료 후 14일 이내에 신청할 수 있습니다.</p>
<section id="auth" class="card" hidden><h2>휴대폰 인증</h2><input id="phone" type="tel" placeholder="01012345678"><label><input id="consent" type="checkbox">인증 문자 수신 동의</label><button id="send">인증문자 받기</button><br><input id="code" inputmode="numeric" placeholder="인증번호"><button id="check">인증 확인</button></section>
<p id="message"></p><section id="orders"></section></main>
<script>
const by=id=>document.getElementById(id);let csrf=null;
async function session(){const r=await fetch("/shopping/auth/session",{credentials:"same-origin"});if(!r.ok)return false;csrf=r.headers.get("X-CSRF-Token");return !!csrf}
async function load(){if(!(await session())){by("auth").hidden=false;return}by("auth").hidden=true;const r=await fetch("/__order-dev/aftersales/orders",{credentials:"same-origin"}),d=await r.json();by("orders").replaceChildren();
 for(const o of d.orders){const c=document.createElement("div");c.className="card";const h=document.createElement("h2");h.textContent="주문 #"+o.order_id;const p=document.createElement("p");p.textContent=o.items.map(v=>v.name+" / "+(v.option||"기본")+" / "+v.quantity+"개").join(", ");
 const s=document.createElement("p");s.textContent="배송: "+o.fulfillment.state+" · "+o.total+" "+o.currency;c.append(h,p,s);
 for(const v of o.cases){const x=document.createElement("div");x.className="case";x.textContent=(v.kind==="RETURN"?"환불":"사이즈교환")+" #"+v.id+" · "+v.state+" · 첨부 "+v.attachments+"개";c.appendChild(x)}
 if(o.return_available){const b=document.createElement("button");b.textContent="환불 요청";b.onclick=()=>form(c,o,"RETURN");c.appendChild(b)}
 if(o.exchange_available){const b=document.createElement("button");b.textContent="사이즈 교환";b.onclick=()=>form(c,o,"SIZE_EXCHANGE");c.appendChild(b)}
 by("orders").appendChild(c)}if(!d.orders.length)by("orders").textContent="확인 가능한 주문이 없습니다."}
async function form(card,order,kind){if(card.querySelector(".request"))return;const box=document.createElement("div");box.className="request";let select=null;
 if(kind==="SIZE_EXCHANGE"){const r=await fetch("/__order-dev/aftersales/orders/"+order.order_id+"/exchange-options",{credentials:"same-origin"}),d=await r.json();select=document.createElement("select");for(const v of d.options){const o=document.createElement("option");o.value=v.variation_id;o.textContent=v.option;select.appendChild(o)}box.appendChild(select)}
 const reason=document.createElement("textarea");reason.placeholder=kind==="RETURN"?"환불 사유":"교환 사유";const file=document.createElement("input");file.type="file";file.accept="image/jpeg,image/png,image/webp";file.multiple=true;
 const submit=document.createElement("button");submit.textContent="요청 접수";submit.onclick=async()=>{const payload={order_id:order.order_id,kind,reason:reason.value,target_variation_id:select?select.value:null};const r=await fetch("/__order-dev/aftersales/cases",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json","X-CSRF-Token":csrf},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok){by("message").textContent=d.message||"접수하지 못했습니다.";return}
 for(const f of Array.from(file.files).slice(0,5)){await fetch("/__order-dev/aftersales/cases/"+d.case.id+"/attachments",{method:"POST",credentials:"same-origin",headers:{"Content-Type":f.type,"X-CSRF-Token":csrf},body:f})}by("message").textContent="요청이 접수됐습니다.";await load()};box.append(reason,file,submit);card.appendChild(box)}
by("send").onclick=async()=>{const r=await fetch("/__order-dev/phone/start",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({phone:by("phone").value,consent:by("consent").checked})});const d=await r.json();by("message").textContent=d.message||""};
by("check").onclick=async()=>{const r=await fetch("/__order-dev/phone/check",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({code:by("code").value})});by("code").value="";if(!r.ok){by("message").textContent="인증을 완료하지 못했습니다.";return}csrf=r.headers.get("X-CSRF-Token");by("message").textContent="인증 완료";await load()};load();
</script></html>"""

