"""DEV after-sales workflow: fulfillment, customer return/exchange cases and private attachments.

No payment refund, carrier API, fulfillment mutation or PROD composition exists here.
"""
from pathlib import Path
import hashlib,json,os,re,secrets,sqlite3,time
from fastapi import Request
from fastapi.responses import HTMLResponse,JSONResponse
from pydantic import BaseModel,ConfigDict,Field

RETURN_WINDOW=14*86400
MAX_ATTACHMENT=5*1024*1024
MEDIA={"image/jpeg":(".jpg",b"\xff\xd8\xff"),"image/png":(".png",b"\x89PNG\r\n\x1a\n"),"image/webp":(".webp",b"RIFF")}

class CaseCreate(BaseModel):
    model_config=ConfigDict(extra="forbid",hide_input_in_errors=True)
    order_id:int=Field(gt=0)
    kind:str=Field(pattern=r"^(RETURN|SIZE_EXCHANGE)$")
    reason:str=Field(strict=True,min_length=2,max_length=1000)
    target_variation_id:str|None=Field(default=None,pattern=r"^[1-9][0-9]*$")
class DevAftersalesStore:
    def __init__(self,path,attachments,*,ledger,checkout,catalog,clock=time.time):
        self.path=Path(path);self.attachments=Path(attachments);self.ledger=ledger;self.checkout=checkout;self.catalog=catalog;self.clock=clock
        if self.path.is_symlink() or self.attachments.is_symlink():raise ValueError("PRIVATE_STORAGE_REQUIRED")
        self.attachments.mkdir(parents=True,exist_ok=True);os.chmod(self.attachments,0o700)
        with sqlite3.connect(self.path) as c:
            c.execute("""CREATE TABLE IF NOT EXISTS fulfillment(
                order_id INTEGER PRIMARY KEY,state TEXT NOT NULL,carrier TEXT,tracking TEXT,shipped REAL,delivered REAL,updated REAL NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS cases(
                id TEXT PRIMARY KEY,order_id INTEGER NOT NULL,customer TEXT NOT NULL,kind TEXT NOT NULL,target_variation_id TEXT,
                target_option TEXT,reason TEXT NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS attachments(
                id TEXT PRIMARY KEY,case_id TEXT NOT NULL,media_type TEXT NOT NULL,size INTEGER NOT NULL,sha256 TEXT NOT NULL,
                stored_name TEXT NOT NULL,created REAL NOT NULL)""")
            c.execute("CREATE TABLE IF NOT EXISTS operator_updates(update_id INTEGER PRIMARY KEY,reply TEXT NOT NULL)")
        os.chmod(self.path,0o600)
    def _fulfillment(self,order_id):
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            row=c.execute("SELECT state,carrier,tracking,shipped,delivered,updated FROM fulfillment WHERE order_id=?",(order_id,)).fetchone()
        if not row:return {"state":"NOT_SHIPPED","carrier":None,"tracking":None,"shipped":None,"delivered":None,"updated":None}
        return dict(zip(("state","carrier","tracking","shipped","delivered","updated"),row))
    def _case_rows(self,order_id=None,customer=None,limit=100):
        q="SELECT id,order_id,customer,kind,target_variation_id,target_option,reason,state,created,updated FROM cases"
        where=[];args=[]
        if order_id is not None:where.append("order_id=?");args.append(order_id)
        if customer is not None:where.append("customer=?");args.append(customer)
        if where:q+=" WHERE "+" AND ".join(where)
        q+=" ORDER BY created DESC LIMIT ?";args.append(max(1,min(int(limit),100)))
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            c.row_factory=sqlite3.Row;rows=[dict(r) for r in c.execute(q,args)]
            for row in rows:
                row["attachments"]=c.execute("SELECT COUNT(*) FROM attachments WHERE case_id=?",(row["id"],)).fetchone()[0]
        return rows
    def _customer_order(self,customer,order_id):
        rows=[r for r in self.ledger.customer_orders(customer) if r["provider_order_id"]==order_id]
        if len(rows)!=1:raise ValueError("ORDER_NOT_OWNED")
        row=rows[0];draft=self.checkout.by_customer_operation(row["operation_key"],customer,allow_expired=True)
        if draft["state"]!="CONFIRMED":raise ValueError("ORDER_NOT_CONFIRMED")
        return row,draft
    def customer_orders(self,customer):
        result=[]
        for row in self.ledger.customer_orders(customer):
            try:draft=self.checkout.by_customer_operation(row["operation_key"],customer,allow_expired=True)
            except Exception:continue
            if draft["state"]!="CONFIRMED":continue
            f=self._fulfillment(row["provider_order_id"]);cases=self._case_rows(order_id=row["provider_order_id"],customer=customer,limit=20)
            now=self.clock();within=f["state"]=="DELIVERED" and type(f["delivered"]) in (int,float) and f["delivered"]<=now<f["delivered"]+RETURN_WINDOW
            active=any(v["state"] in ("REQUESTED","RETURN_APPROVED","EXCHANGE_APPROVED") for v in cases)
            result.append({"order_id":row["provider_order_id"],"review_state":row["review_state"],"requested_at":row["requested_at"],
                "items":draft["body"]["quote"]["line_items"],"total":draft["body"]["quote"]["final_total"],"currency":draft["body"]["quote"]["currency"],
                "fulfillment":f,"return_available":bool(row["review_state"]=="CONFIRMED" and within and not active),
                "exchange_available":bool(row["review_state"]=="CONFIRMED" and within and not active),"cases":cases})
        return result
    def exchange_options(self,customer,order_id):
        _,draft=self._customer_order(customer,order_id);body=draft["body"]
        if len(body["line_items"])!=1:raise ValueError("MULTILINE_EXCHANGE_UNSUPPORTED")
        line=body["line_items"][0];product=self.catalog.get_product(line["product_id"])
        options=[]
        for v in product["variants"]:
            if v.available and v.id!=line["variation_id"]:options.append({"variation_id":v.id,"option":v.label})
        return options
    def create_case(self,customer,data):
        data=CaseCreate.model_validate(data);row,draft=self._customer_order(customer,data.order_id);f=self._fulfillment(data.order_id);now=self.clock()
        if row["review_state"]!="CONFIRMED" or f["state"]!="DELIVERED" or not f["delivered"] or not f["delivered"]<=now<f["delivered"]+RETURN_WINDOW:
            raise ValueError("RETURN_WINDOW_CLOSED")
        if any(v["state"] in ("REQUESTED","RETURN_APPROVED","EXCHANGE_APPROVED") for v in self._case_rows(order_id=data.order_id,customer=customer)):
            raise ValueError("CASE_ALREADY_ACTIVE")
        target=None
        if data.kind=="SIZE_EXCHANGE":
            if not data.target_variation_id:raise ValueError("TARGET_SIZE_REQUIRED")
            opts={v["variation_id"]:v["option"] for v in self.exchange_options(customer,data.order_id)}
            target=opts.get(data.target_variation_id)
            if target is None:raise ValueError("TARGET_SIZE_UNAVAILABLE")
        identifier=secrets.token_hex(4)
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO cases VALUES(?,?,?,?,?,?,?,?,?,?)",(identifier,data.order_id,customer,data.kind,data.target_variation_id,target,data.reason.strip(),"REQUESTED",now,now))
        return self.case(customer,identifier)
    def case(self,customer,case_id):
        rows=[r for r in self._case_rows(customer=customer) if r["id"]==case_id]
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
        with sqlite3.connect(self.path) as c:c.execute("INSERT INTO attachments VALUES(?,?,?,?,?,?,?)",(identifier,case_id,media_type,len(raw),hashlib.sha256(raw).hexdigest(),stored,stamp))
        return {"attachment_id":identifier,"media_type":media_type,"size":len(raw)}
    def _operator_order(self,order_id):
        rows=[r for r in self.ledger.operator_orders() if r["provider_order_id"]==int(order_id)]
        if len(rows)!=1 or rows[0]["state"]!="CONFIRMED":raise ValueError("ORDER_NOT_READY_FOR_FULFILLMENT")
        return rows[0]
    def mark_shipped(self,order_id,carrier,tracking):
        self._operator_order(order_id)
        if not re.fullmatch(r"[가-힣A-Za-z0-9 ._-]{2,40}",carrier) or not re.fullmatch(r"[A-Za-z0-9-]{5,40}",tracking):raise ValueError("TRACKING_INVALID")
        stamp=self.clock()
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO fulfillment VALUES(?,?,?,?,?,?,?) ON CONFLICT(order_id) DO UPDATE SET state='SHIPPED',carrier=excluded.carrier,tracking=excluded.tracking,shipped=COALESCE(fulfillment.shipped,excluded.shipped),delivered=NULL,updated=excluded.updated",
                (order_id,"SHIPPED",carrier,tracking,stamp,None,stamp))
        return self._fulfillment(order_id)
    def mark_delivered(self,order_id):
        self._operator_order(order_id);current=self._fulfillment(order_id)
        if current["state"] not in ("SHIPPED","DELIVERED"):raise ValueError("SHIPMENT_REQUIRED")
        stamp=current["delivered"] if current["state"]=="DELIVERED" and current["delivered"] else self.clock()
        with sqlite3.connect(self.path) as c:c.execute("UPDATE fulfillment SET state='DELIVERED',delivered=?,updated=? WHERE order_id=?",(stamp,self.clock(),order_id))
        return self._fulfillment(order_id)
    def admin_fulfillment(self,order_id):return self._fulfillment(order_id)
    def admin_cases(self,kind=None):
        rows=self._case_rows(limit=100)
        if kind:rows=[r for r in rows if r["kind"]==kind]
        return rows
    def decide(self,case_id,approve):
        rows=[r for r in self._case_rows(limit=100) if r["id"]==case_id]
        if len(rows)!=1:raise ValueError("CASE_NOT_FOUND")
        row=rows[0]
        if row["state"]=="REJECTED" or row["state"] in ("RETURN_APPROVED","EXCHANGE_APPROVED"):return row
        if row["state"]!="REQUESTED":raise ValueError("CASE_STATE_INVALID")
        state=("RETURN_APPROVED" if row["kind"]=="RETURN" else "EXCHANGE_APPROVED") if approve else "REJECTED";stamp=self.clock()
        with sqlite3.connect(self.path) as c:c.execute("UPDATE cases SET state=?,updated=? WHERE id=?",(state,stamp,case_id))
        return [r for r in self._case_rows(limit=100) if r["id"]==case_id][0]
    def operator_command(self,text,update_id):
        clean=text.strip()
        patterns=[
            (r"주문발송\s*#([1-9][0-9]*)\s+([가-힣A-Za-z0-9 ._-]{2,40})\s+([A-Za-z0-9-]{5,40})","ship"),
            (r"배송완료\s*#([1-9][0-9]*)","delivered"),
            (r"배송상태\s*#([1-9][0-9]*)","status"),
            (r"(환불|교환)목록","cases"),
            (r"(환불|교환)(승인|거절)\s*#([a-f0-9]{8})","decision")]
        matched=None
        for pattern,kind in patterns:
            m=re.fullmatch(pattern,clean)
            if m:matched=(m,kind);break
        if matched is None:return None
        with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
            old=c.execute("SELECT reply FROM operator_updates WHERE update_id=?",(update_id,)).fetchone()
        if old:return old[0]
        m,kind=matched
        try:
            if kind=="ship":
                v=self.mark_shipped(int(m[1]),m[2],m[3]);reply="주문 #"+m[1]+" 발송 등록 · "+v["carrier"]+" "+v["tracking"]
            elif kind=="delivered":
                self.mark_delivered(int(m[1]));reply="주문 #"+m[1]+" 배송완료 · 지금부터 14일 환불/사이즈교환 접수 가능"
            elif kind=="status":
                v=self._fulfillment(int(m[1]));reply="주문 #"+m[1]+" 배송상태: "+v["state"]+(("\n"+str(v["carrier"])+" "+str(v["tracking"])) if v["tracking"] else "")
            elif kind=="cases":
                target="RETURN" if m[1]=="환불" else "SIZE_EXCHANGE";rows=self.admin_cases(target)
                reply=(m[1]+" 요청이 없습니다." if not rows else "\n".join("#"+r["id"]+" · 주문 #"+str(r["order_id"])+" · "+r["state"]+" · "+r["reason"][:80] for r in rows[:20]))
            else:
                target="RETURN" if m[1]=="환불" else "SIZE_EXCHANGE";rows=[r for r in self.admin_cases(target) if r["id"]==m[3]]
                if len(rows)!=1:reply="해당 요청을 찾지 못했습니다."
                else:
                    v=self.decide(m[3],m[2]=="승인");reply=m[1]+" #"+m[3]+" "+("승인" if m[2]=="승인" else "거절")+" · "+v["state"]
        except Exception:
            reply="요청을 처리하지 못했습니다. 주문/케이스 상태를 확인해 주세요."
        try:
            with sqlite3.connect(self.path) as c:c.execute("INSERT INTO operator_updates VALUES(?,?)",(update_id,reply))
        except sqlite3.IntegrityError:
            with sqlite3.connect("file:"+str(self.path.resolve())+"?mode=ro",uri=True) as c:
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

def mount_aftersales(app,*,store,boundary,phone_cfg):
    def auth(request,write=False):
        if write:boundary.check_origin(request,required=True)
        secret=boundary.cookie_secret(request);projection=boundary.authenticate(secret,now=boundary.now())
        if projection.customer_id!=phone_cfg["guest_customer_id"]:raise ValueError("CUSTOMER_DENIED")
        if write:boundary.check_csrf(request,secret,projection)
        return projection
    @app.get("/dev-order/my-orders",include_in_schema=False)
    def portal():return HTMLResponse(PORTAL,headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
    @app.get("/__order-dev/aftersales/orders",include_in_schema=False)
    def orders(request:Request):
        try:return JSONResponse({"orders":store.customer_orders(auth(request).customer_id)},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"휴대폰 인증이 필요합니다."},status_code=401,headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/aftersales/orders/{order_id}/exchange-options",include_in_schema=False)
    def options(order_id:int,request:Request):
        try:return JSONResponse({"options":store.exchange_options(auth(request).customer_id,order_id)},headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"교환 가능한 옵션을 확인할 수 없습니다."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/aftersales/cases",include_in_schema=False)
    async def create_case(request:Request):
        try:
            projection=auth(request,write=True);raw=await request.body()
            if len(raw)>8192:raise ValueError()
            data=CaseCreate.model_validate_json(raw);case=store.create_case(projection.customer_id,data)
            return JSONResponse({"case":case},status_code=201,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"환불/교환 가능 기간과 입력 내용을 확인해 주세요."},status_code=422,headers={"Cache-Control":"no-store"})
    @app.post("/__order-dev/aftersales/cases/{case_id}/attachments",include_in_schema=False)
    async def attachment(case_id:str,request:Request):
        try:
            if not re.fullmatch(r"[a-f0-9]{8}",case_id):raise ValueError()
            projection=auth(request,write=True);raw=bytearray()
            async for chunk in request.stream():
                if len(raw)+len(chunk)>MAX_ATTACHMENT:raise ValueError("ATTACHMENT_TOO_LARGE")
                raw.extend(chunk)
            value=store.attach(projection.customer_id,case_id,request.headers.get("content-type","").split(";",1)[0],bytes(raw))
            return JSONResponse(value,status_code=201,headers={"Cache-Control":"no-store"})
        except Exception:return JSONResponse({"message":"첨부는 JPEG/PNG/WebP, 파일당 5MB 이하로 최대 5개까지 가능합니다."},status_code=422,headers={"Cache-Control":"no-store"})
