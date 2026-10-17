"""DEV order console and guarded operator chat behind the existing Basic Auth edge."""
import json
import re
import secrets
import sqlite3
import time
from pathlib import Path
from fastapi import Request
from fastapi.responses import HTMLResponse,JSONResponse

HTML="""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIControlCenter DEV 주문 관리자</title>
<style>
body{font:15px system-ui;background:#f5f5f3;color:#222;margin:0}main{max-width:1100px;margin:auto;padding:20px}header{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
button{font:inherit;padding:9px 12px;border:1px solid #bbb;border-radius:9px;background:#fff;cursor:pointer}.grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(280px,.9fr);gap:18px}
.panel{background:#fff;border:1px solid #ddd;border-radius:14px;padding:16px}.order{padding:12px 0;border-bottom:1px solid #eee}.order:last-child{border-bottom:0}
.meta{color:#666;font-size:13px}.state{font-weight:700}.items{white-space:pre-wrap}.detail{white-space:pre-wrap;background:#fafafa;padding:12px;border-radius:10px}
.inquiry{padding:10px 0;border-bottom:1px solid #eee}.approved{color:#176b2c}.pending{color:#9a5a00}
.chat #chat-log{min-height:110px;max-height:380px;overflow:auto;background:#fafafa;border-radius:10px;padding:12px;margin:12px 0}.chat #chat-log p{white-space:pre-wrap;overflow-wrap:anywhere}.chat .you{color:#70462f}.chat .bot{color:#174a2b}.chat form{display:grid;gap:8px}.chat textarea{width:100%;box-sizing:border-box;font:inherit;border:1px solid #bbb;border-radius:9px;padding:10px}.chat button{justify-self:end;background:#ebae8c;border-color:#d49572}
@media(max-width:760px){.grid{grid-template-columns:1fr}main{padding:12px}.panel{padding:13px}}
</style>
<main><header><div><h1>DEV 주문 관리자</h1><p>DEV 실운영 관리 · 주문 주소는 상세에서만 표시 · 쓰기 작업은 별도 확인</p></div><button id="refresh">새로고침</button></header>
<div class="grid"><section class="panel"><h2>최근 주문</h2><div id="orders">불러오는 중…</div></section>
<section class="panel"><h2>주문 상세</h2><div id="detail">주문을 선택하세요.</div></section></div>
<section class="panel" style="margin-top:18px"><h2>환불 / 사이즈교환 요청</h2><div id="cases">불러오는 중…</div></section><section class="panel" style="margin-top:18px"><h2>문의 / 자동학습</h2><div id="inquiries">불러오는 중…</div></section><section class="panel chat" style="margin-top:18px"><h2>주문·상품 챗봇</h2><p class="meta">주문 조회와 DEV 상품관리를 대화로 요청하세요. 새 상품 등록은 Codex 초안 검토 후 DEV 등록 단계로 진행합니다.</p><div id="chat-log" role="log" aria-live="polite"><p>예: “주문 목록 보여줘” 또는 “상품 등록 초안: 린넨 셔츠, 상의, 39,000원”</p></div><form id="chat-form"><label for="chat-input">요청</label><textarea id="chat-input" maxlength="1500" rows="3" required placeholder="주문번호나 상품 요청을 입력하세요"></textarea><button type="submit">보내기</button></form></section>
<script>
const by=id=>document.getElementById(id);
const stateLabel=v=>({PENDING_REVIEW:"확인대기",CONFIRMED:"확인완료",READY_TO_SHIP:"배송준비",AWAITING_DEPOSIT:"입금대기",SHIPPED:"배송중",COMPLETED:"배송완료",REJECTED:"거절",STOCK_BLOCKED:"재고확인"}[v]||v);
const inquiryLabel=v=>({APPROVED:"자동학습",ANSWERED:"학습제외",PENDING:"답변대기"}[v]||v);
async function detail(id){
 const r=await fetch("/__order-dev/admin/orders/"+id,{credentials:"same-origin"});const d=await r.json();
 if(!r.ok){by("detail").textContent="상세를 불러오지 못했습니다.";return;}
 const lines=["주문 #"+d.order_id,"상태: "+stateLabel(d.display_state||d.state),"고객: "+d.phone,"수령인: "+d.delivery.recipient,
 "우편번호: "+d.delivery.postcode,"주소: "+d.delivery.address1+" "+d.delivery.address2,""];
 d.items.forEach(v=>lines.push("- "+v.name+" / "+(v.option||"기본")+" / "+v.quantity+"개"));
 lines.push("총액: "+d.total+" "+d.currency);by("detail").textContent=lines.join("\\n");
}
async function load(){
 by("orders").textContent="불러오는 중…";by("inquiries").textContent="불러오는 중…";
 const [or,ir,cr]=await Promise.all([fetch("/__order-dev/admin/orders",{credentials:"same-origin"}),fetch("/__order-dev/admin/inquiries",{credentials:"same-origin"}),fetch("/__order-dev/admin/aftersales",{credentials:"same-origin"})]);
 const orders=await or.json(),inquiries=await ir.json(),cases=await cr.json();by("orders").replaceChildren();
 for(const o of orders.orders){const wrap=document.createElement("div");wrap.className="order";const title=document.createElement("div");title.className="state";title.textContent="#"+o.order_id+" · "+o.phone+" · "+stateLabel(o.display_state||o.state);
 const meta=document.createElement("div");meta.className="meta";meta.textContent=o.total+" "+o.currency+" · "+(o.requested_at||"")+" · 배송 "+(o.fulfillment?.state||"NOT_SHIPPED");const items=document.createElement("div");items.className="items";items.textContent=o.items.map(v=>v.name+" / "+(v.option||"기본")+" / "+v.quantity+"개").join("\\n");
 const b=document.createElement("button");b.textContent="상세·주소";b.onclick=()=>detail(o.order_id);wrap.append(title,meta,items,b);by("orders").appendChild(wrap);}
 if(!orders.orders.length)by("orders").textContent="주문이 없습니다.";by("cases").replaceChildren();
 for(const x of cases.cases){const wrap=document.createElement("div");wrap.className="inquiry";const t=document.createElement("div");t.className="state";t.textContent=(x.kind==="RETURN"?"환불":"사이즈교환")+" #"+x.id+" · 주문 #"+x.order_id+" · "+x.state;const reason=document.createElement("div");reason.textContent=x.reason+(x.target_option?" · 희망 "+x.target_option:"")+" · 첨부 "+x.attachments+"개";wrap.append(t,reason);by("cases").appendChild(wrap);}if(!cases.cases.length)by("cases").textContent="요청이 없습니다.";
 by("inquiries").replaceChildren();
 for(const q of inquiries.inquiries){const wrap=document.createElement("div");wrap.className="inquiry";const t=document.createElement("div");t.className=q.state==="APPROVED"?"approved":"pending";t.textContent="#"+q.id+" · "+inquiryLabel(q.state)+" · 상품 "+q.product;
 const question=document.createElement("div");question.textContent="Q. "+q.question;const answer=document.createElement("div");answer.textContent=q.answer?"A. "+q.answer:"A. 답변 대기";wrap.append(t,question,answer);by("inquiries").appendChild(wrap);}
 if(!inquiries.inquiries.length)by("inquiries").textContent="문의가 없습니다.";
}
by("refresh").onclick=load;load();
const log=by("chat-log");
function chatLine(label,text,kind){const p=document.createElement("p");p.className=kind;p.textContent=label+": "+text;log.appendChild(p);log.scrollTop=log.scrollHeight;}
by("chat-form").addEventListener("submit",async event=>{
 event.preventDefault();const input=by("chat-input"),text=input.value.trim();if(!text)return;
 input.value="";chatLine("나",text,"you");
 const product=/^(?:상품\\s*(?:등록|추가)|신규\\s*상품)/.test(text);
 try{
  const lookup=text.match(/^초안 확인\\s+([a-f0-9]{8})$/);
  const response=lookup
   ? await fetch("/__order-dev/admin/product-drafts/"+lookup[1],{credentials:"same-origin"})
   : await fetch(product?"/__order-dev/admin/product-drafts":"/__order-dev/admin/chat",{
      method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({text})
     });
  const data=await response.json();
  if(!response.ok)throw new Error(data.message||"요청을 처리하지 못했습니다.");
  if(lookup){chatLine("Codex 상태",data.state+(data.draft?"\n"+JSON.stringify(data.draft,null,2):""),"bot");}
  else if(product){
   chatLine("Codex 초안",data.reply||("작업 #"+data.job_id+"를 시작했습니다."),"bot");
   for(let attempt=0;attempt<30&&data.job_id;attempt++){
    await new Promise(resolve=>setTimeout(resolve,3000));
    const poll=await fetch("/__order-dev/admin/product-drafts/"+data.job_id,{credentials:"same-origin"});
    const status=await poll.json();
    if(status.state!=="WAITING_CODEX"&&status.state!=="CODEX_RUNNING"){
     chatLine("Codex 결과",status.state+(status.draft?"\n"+JSON.stringify(status.draft,null,2):""),"bot");break;
    }
   }
  }else chatLine("챗봇",data.reply,"bot");
 }catch(error){chatLine("오류",error.message||"잠시 후 다시 시도해 주세요.","bot");}
});
</script></main></html>"""

def mount_admin(app,*,operator_adapter,inquiry_queue,aftersales=None,conversation=None,codex_drafts=None):
    @app.get("/dev-order/admin",include_in_schema=False)
    def admin_page():
        return HTMLResponse(HTML,headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
    def same_origin(request):
        return request.headers.get("origin") == "https://dev.bokstory.duckdns.org"

    @app.post("/__order-dev/admin/chat",include_in_schema=False)
    async def admin_chat(request:Request):
        if not same_origin(request):return JSONResponse({"message":"관리자 페이지에서 다시 요청해 주세요."},status_code=403)
        if conversation is None:return JSONResponse({"message":"DEV 관리자 챗봇이 준비되지 않았습니다."},status_code=503)
        try:body=await request.json()
        except Exception:return JSONResponse({"message":"요청 형식을 확인해 주세요."},status_code=400)
        text=body.get("text") if isinstance(body,dict) else None
        if type(text) is not str or not 1<=len(text.strip())<=1500:return JSONResponse({"message":"요청은 1~1500자로 입력해 주세요."},status_code=422)
        actor="telegram-user-9223372036854775807"
        try:reply=conversation.handle(text.strip(),time.time_ns(),actor)
        except Exception:return JSONResponse({"message":"요청 결과를 확인할 수 없습니다. 같은 변경을 반복 실행하지 말고 주문·상품 상태를 확인해 주세요."},status_code=503)
        return JSONResponse({"reply":reply},headers={"Cache-Control":"no-store"})

    @app.post("/__order-dev/admin/product-drafts",include_in_schema=False)
    async def product_draft_create(request:Request):
        if not same_origin(request):return JSONResponse({"message":"관리자 페이지에서 다시 요청해 주세요."},status_code=403)
        if conversation is None or codex_drafts is None:return JSONResponse({"message":"Codex 상품 초안 기능이 준비되지 않았습니다."},status_code=503)
        try:body=await request.json()
        except Exception:return JSONResponse({"message":"요청 형식을 확인해 주세요."},status_code=400)
        text=body.get("text") if isinstance(body,dict) else None
        if type(text) is not str or not 1<=len(text.strip())<=1500:return JSONResponse({"message":"상품 설명을 1~1500자로 입력해 주세요."},status_code=422)
        job=secrets.token_hex(4);actor="telegram-user-9223372036854775807"
        try:
            with sqlite3.connect("file:"+str(conversation.path.resolve())+"?mode=rw",uri=True,timeout=5) as db:
                db.execute("INSERT INTO website_jobs VALUES(?,?,?,'WAITING_CODEX',?)",(job,actor,"PRODUCT_INTAKE::"+text.strip(),time.time()))
        except (OSError,sqlite3.Error):return JSONResponse({"message":"Codex 작업을 저장하지 못했습니다."},status_code=503)
        return JSONResponse({"job_id":job,"reply":"Codex가 DEV 상품 초안을 작성합니다. 초안은 WooCommerce에 등록되거나 공개되지 않습니다. 등록하려면 가격·옵션·재고와 상품 사진을 확인한 뒤 기존 DEV 등록 검토를 거쳐야 합니다."},status_code=202,headers={"Cache-Control":"no-store"})

    @app.get("/__order-dev/admin/product-drafts/{job_id}",include_in_schema=False)
    def product_draft_status(job_id:str):
        if codex_drafts is None or not re.fullmatch(r"[a-f0-9]{8}",job_id):return JSONResponse({"message":"초안을 찾을 수 없습니다."},status_code=404)
        try:
            with sqlite3.connect("file:"+str(conversation.path.resolve())+"?mode=ro",uri=True) as db:
                row=db.execute("SELECT state,request FROM website_jobs WHERE id=?",(job_id,)).fetchone()
            if not row or not row[1].startswith("PRODUCT_INTAKE::"):return JSONResponse({"message":"초안을 찾을 수 없습니다."},status_code=404)
            result={"job_id":job_id,"state":row[0]}
            candidate=Path(codex_drafts.root)/job_id/"brands/agachichi/catalog/intake-drafts"/(job_id+".json")
            if row[0]=="PRODUCT_REVIEW_REQUIRED" and not candidate.is_symlink() and candidate.is_file():
                value=json.loads(candidate.read_text(encoding="utf-8"))
                result["draft"]=value
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except (OSError,sqlite3.Error,json.JSONDecodeError):return JSONResponse({"message":"초안 상태를 확인할 수 없습니다."},status_code=503)

    @app.get("/__order-dev/admin/orders",include_in_schema=False)
    def admin_orders():
        orders=operator_adapter.admin_orders(50)
        if aftersales is not None:
            for order in orders:order["fulfillment"]=aftersales.admin_fulfillment(order["order_id"])
        return JSONResponse({"orders":orders},headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/admin/orders/{order_id}",include_in_schema=False)
    def admin_order_detail(order_id:int):
        value=operator_adapter.admin_detail(order_id)
        return JSONResponse(value or {"message":"주문을 찾지 못했습니다."},status_code=200 if value else 404,headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/admin/inquiries",include_in_schema=False)
    def admin_inquiries():
        return JSONResponse({"inquiries":inquiry_queue.admin_rows(50)},headers={"Cache-Control":"no-store"})
    @app.get("/__order-dev/admin/aftersales",include_in_schema=False)
    def admin_aftersales():
        return JSONResponse({"cases":aftersales.admin_cases() if aftersales is not None else []},headers={"Cache-Control":"no-store"})
