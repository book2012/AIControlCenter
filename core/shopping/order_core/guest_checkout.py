"""Private immutable delivery draft bound to a verified customer and session."""
from pathlib import Path
import hashlib,json,os,secrets,sqlite3,time
from pydantic import BaseModel,ConfigDict,Field
from core.shopping.order_core.guest_chat import GuestCart

def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def fingerprint(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
class Delivery(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    recipient:str=Field(strict=True,min_length=1,max_length=64,repr=False)
    postcode:str=Field(strict=True,pattern=r"^[0-9]{5}$",repr=False)
    address1:str=Field(strict=True,min_length=5,max_length=200,repr=False)
    address2:str=Field(default="",strict=True,max_length=100,repr=False)
class CheckoutPrepare(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    cart:GuestCart
    delivery:Delivery
class CheckoutConfirm(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    draft_id:str=Field(strict=True,pattern=r"^[a-f0-9]{48}$")
class PrivateCheckoutStore:
    def __init__(self,path,clock=time.time):
        self.path=Path(path);self.clock=clock
        if self.path.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        with sqlite3.connect(self.path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS checkout_delivery(draft_id TEXT PRIMARY KEY,operation_key TEXT UNIQUE NOT NULL,customer TEXT NOT NULL,session TEXT NOT NULL,body TEXT NOT NULL,digest TEXT NOT NULL,expires REAL NOT NULL,state TEXT NOT NULL)")
        os.chmod(self.path,0o600)
    def prepare(self,customer,session,cart,delivery,quote,verified_phone):
        delivery=Delivery.model_validate(delivery);cart=GuestCart.model_validate(cart)
        if not delivery.recipient.strip() or not delivery.address1.strip():raise ValueError("INVALID_DELIVERY")
        address={"first_name":delivery.recipient.strip(),"last_name":"","address_1":delivery.address1.strip(),
            "address_2":delivery.address2.strip(),"postcode":delivery.postcode,"country":"KR"}
        billing={**address,"phone":verified_phone}
        draft=secrets.token_hex(24);key="guest-order-"+secrets.token_hex(24)
        body={"line_items":cart.model_dump(mode="json")["line_items"],"shipping":address,"billing":billing,"quote":quote}
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO checkout_delivery VALUES(?,?,?,?,?,?,?,?)",
                (draft,key,customer,session,canonical(body),fingerprint(body),self.clock()+900,"PREPARED"))
        return self.get(draft,customer,session)
    def get(self,draft,customer,session,*,allow_expired=False):
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            row=c.execute("SELECT operation_key,body,digest,expires,state FROM checkout_delivery WHERE draft_id=? AND customer=? AND session=?",
                (draft,customer,session)).fetchone()
        if not row or not allow_expired and self.clock()>=row[3]:raise ValueError("DRAFT_UNAVAILABLE")
        body=json.loads(row[1])
        if fingerprint(body)!=row[2]:raise ValueError("DRAFT_CORRUPT")
        return {"draft_id":draft,"operation_key":row[0],"body":body,"digest":row[2],"expires":row[3],"customer":customer,"session":session,"state":row[4]}
    def confirm(self,draft,customer,session):
        value=self.get(draft,customer,session)
        with sqlite3.connect(self.path) as c:
            changed=c.execute("UPDATE checkout_delivery SET state='CONFIRMED' WHERE draft_id=? AND customer=? AND session=? AND state IN ('PREPARED','CONFIRMED') AND expires>?",
                (draft,customer,session,self.clock())).rowcount
        if changed!=1:raise ValueError("CONFIRMATION_DENIED")
        return self.get(draft,customer,session)
    def operation(self,key,customer,session):
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            row=c.execute("SELECT draft_id FROM checkout_delivery WHERE operation_key=? AND customer=? AND session=?",(key,customer,session)).fetchone()
        if not row:raise ValueError("OPERATION_UNBOUND")
        value=self.get(row[0],customer,session)
        if value["state"]!="CONFIRMED":raise ValueError("EXPLICIT_CONFIRMATION_REQUIRED")
        return value
    def by_provider_tag(self,tag,*,allow_expired=False):
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            rows=c.execute("SELECT draft_id,operation_key,customer,session FROM checkout_delivery").fetchall()
        # DEV-only bounded corpus. No delivery data is loaded until exact binding.
        matches=[r for r in rows if hashlib.sha256(("aicc-order:"+r[1]).encode()).hexdigest()==tag]
        if len(matches)!=1:raise ValueError("DELIVERY_BINDING_INVALID")
        r=matches[0];return self.get(r[0],r[2],r[3],allow_expired=allow_expired)
