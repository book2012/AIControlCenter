"""DEV order console and guarded operator chat behind the existing Basic Auth edge."""
import asyncio
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
.chat #chat-log{min-height:110px;max-height:380px;overflow:auto;background:#fafafa;border-radius:10px;padding:12px;margin:12px 0}.chat #chat-log p{white-space:pre-wrap;overflow-wrap:anywhere}.chat .you{color:#70462f}.chat .bot{color:#174a2b}.chat form{display:grid;gap:8px}.chat textarea{width:100%;box-sizing:border-box;font:inherit;border:1px solid #bbb;border-radius:9px;padding:10px}.chat button{justify-self:end;background:#ebae8c;border-color:#d49572}.chat #product-review{margin-top:16px;padding:14px;border:1px solid #dfcfc2;border-radius:12px;background:#fffdf9}.chat #product-review input:not([type=checkbox]),.chat #product-review select,.chat #product-review textarea{box-sizing:border-box;width:100%;font:inherit;padding:9px;border:1px solid #bbb;border-radius:8px;margin-top:4px}.chat #product-review label{line-height:1.5}.chat #product-review button{margin-top:8px}
@media(max-width:760px){.grid{grid-template-columns:1fr}main{padding:12px}.panel{padding:13px}}
</style>
<main><header><div><h1>DEV 주문 관리자</h1><p>DEV 실운영 관리 · 주문 주소는 상세에서만 표시 · 쓰기 작업은 별도 확인</p></div><button id="refresh">새로고침</button></header>
<div class="grid"><section class="panel"><h2>최근 주문</h2><div id="orders">불러오는 중…</div></section>
<section class="panel"><h2>주문 상세</h2><div id="detail">주문을 선택하세요.</div></section></div>
<section class="panel" style="margin-top:18px"><h2>환불 / 사이즈교환 요청</h2><div id="cases">불러오는 중…</div></section><section class="panel" style="margin-top:18px"><h2>문의 / 자동학습</h2><div id="inquiries">불러오는 중…</div></section><section class="panel chat" style="margin-top:18px"><h2>주문·상품 챗봇</h2><p class="meta">주문 조회와 DEV 상품관리를 대화로 요청하세요. 새 상품 등록은 Codex 초안 검토 후 DEV 등록 단계로 진행합니다.</p><div id="chat-log" role="log" aria-live="polite"><p>예: “주문 목록 보여줘” 또는 “상품 등록 초안: 린넨 셔츠, 상의, 39,000원”</p></div><form id="chat-form"><label for="chat-input">요청</label><textarea id="chat-input" maxlength="1500" rows="3" required placeholder="주문번호나 상품 요청을 입력하세요"></textarea><button type="submit">보내기</button></form><div id="product-review" hidden></div></section>
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
const log=by("chat-log"),reviewBox=by("product-review");
function chatLine(label,text,kind){const p=document.createElement("p");p.className=kind;p.textContent=label+": "+text;log.appendChild(p);log.scrollTop=log.scrollHeight;}
const roles=["hero","original","model-front","garment-cutout","model-other"];
const roleLabels={hero:"대표 이미지 (JPG)",original:"원본 상품 사진 (JPG)", "model-front":"모델 정면 (JPG)", "garment-cutout":"상품 누끼 (WEBP)", "model-other":"추가 상품 사진 (JPG)"};
function renderReview(jobId,draft,registration={}){
 reviewBox.hidden=false;
 reviewBox.innerHTML='<hr><h3>Codex 초안 검토 · DEV 상품 등록</h3><p class="meta">Codex 문안은 제안입니다. 가격·옵션·재고·이미지 원본과 AI 생성 여부를 직접 확인하세요. 이미지 5종이 모두 필요합니다. 검증 후 상품명 재입력 확인을 거쳐 DEV WooCommerce에 등록합니다.</p><div id="draft-questions" class="detail"></div><form id="intake-review-form" style="display:grid;gap:10px"><label>상품명<input name="name" required maxlength="200"></label><label>카테고리<select name="category" required><option value="">선택</option><option value="top">상의</option><option value="bottom">하의</option><option value="outer">아우터</option><option value="dress">원피스</option><option value="bag">가방</option><option value="acc">액세서리</option></select></label><label>상품 설명<textarea name="description" required maxlength="20000" rows="4"></textarea></label><label>스타일 팁<textarea name="style_tip" maxlength="1000" rows="2"></textarea></label><label>판매가 (원)<input name="price" type="number" min="1" max="10000000" required></label><label>할인가 (없으면 비움)<input name="sale_price" type="number" min="1"></label><label>가격 근거<select name="price_basis" required><option value="">선택</option><option value="user_set">운영자가 직접 입력·확인</option><option value="user_authorized">사용자 승인</option><option value="user_authorized_temporary">임시 가격 승인</option></select></label><label>옵션 형태<select name="option_type" required><option value="">선택</option><option value="color">색상</option><option value="size">사이즈</option><option value="color_size">색상 + 사이즈</option></select></label><label>색상 옵션 JSON (예: [{"id":"black","label":"블랙"}])<textarea name="color_options" rows="2"></textarea></label><label>사이즈 옵션, 쉼표 구분<input name="size_options" placeholder="S,M,L"></label><label>옵션별 재고 JSON (예: {"black":0})<textarea name="inventory" rows="2" required></textarea></label><label>태그, 쉼표 구분<input name="tags"></label><label><input name="inventory_pending" type="checkbox" checked> 실재고 확인 전 (재고 0으로 등록)</label><div id="media-fields"></div><button type="submit">정보·이미지 저장 후 등록 전 검증</button></form><div id="intake-status" role="status"></div>';
 const questions=[...(draft?.missing_facts||[]).map(v=>"확인 필요: "+v),...(draft?.questions||[])];
 by("draft-questions").textContent=questions.length?questions.join("\\n"):"Codex 초안의 미확인 항목을 검토해 주세요.";
 const form=by("intake-review-form"),existing=registration.fields||{};
 form.elements.name.value=existing.name||"";
 form.elements.category.value=existing.category||"";
 form.elements.description.value=existing.description||draft?.proposed_copy?.description||"";
 form.elements.style_tip.value=existing.style_tip||draft?.proposed_copy?.style_tip||"";
 form.elements.price.value=existing.price??"";
 form.elements.sale_price.value=existing.sale_price??"";
 form.elements.price_basis.value=existing.price_basis||"";
 form.elements.option_type.value=existing.option_type||"";
 form.elements.color_options.value=JSON.stringify(existing.color_options||[],null,2);
 form.elements.size_options.value=(existing.size_options||[]).join(",");
 form.elements.inventory.value=JSON.stringify(existing.inventory||{},null,2);
 form.elements.tags.value=(existing.tags||[]).join(",");
 form.elements.inventory_pending.checked=existing.inventory_pending!==false;
 const mediaBox=by("media-fields");
 for(const role of roles){
  const label=document.createElement("label");label.style.display="grid";label.style.gap="4px";
  const saved=registration.media?.[role];
  label.append(document.createTextNode(roleLabels[role]+(saved?" · 저장됨 "+saved.sha256.slice(0,12):" · 필수")));
  const input=document.createElement("input");input.type="file";input.accept=role==="garment-cutout"?".webp,image/webp":".jpg,.jpeg,image/jpeg";input.dataset.role=role;
  label.appendChild(input);
  if(role!=="original"){
   const provenance=document.createElement("label");provenance.style.fontSize="13px";
   const check=document.createElement("input");check.type="checkbox";check.dataset.aiRole=role;check.checked=saved?.ai_generated===true;
   provenance.append(check,document.createTextNode(" 이 파일은 AI 생성 이미지입니다."));label.appendChild(provenance);
  }
  mediaBox.appendChild(label);
 }
 const status=by("intake-status");
 if(registration.state==="READY_TO_REGISTER"){
  status.textContent="사전검증 통과 · "+registration.catalog_id+" · SKU "+(registration.preflight?.sku||"")+" · 상품은 아직 등록되지 않았습니다.";
  const confirm=document.createElement("form");confirm.style.display="grid";confirm.style.gap="8px";confirm.innerHTML='<label>실제 등록 전 상품명을 그대로 입력해 확인하세요.<input name="confirmation" required autocomplete="off"></label><button type="submit">DEV WooCommerce에 상품 등록</button>';
  status.appendChild(confirm);
  confirm.addEventListener("submit",async event=>{
   event.preventDefault();const phrase=confirm.elements.confirmation.value;
   const button=confirm.querySelector("button");button.disabled=true;status.append(document.createTextNode(" 등록 중…"));
   try{
    const response=await fetch("/__order-dev/admin/product-drafts/"+jobId+"/register",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({confirmation:phrase})});
    const result=await response.json();if(!response.ok)throw new Error(result.message||"등록을 완료하지 못했습니다.");
    chatLine("상품 등록",result.state+" · "+JSON.stringify(result.receipt||{}),"bot");
    renderReview(jobId,draft,result);
   }catch(error){button.disabled=false;chatLine("오류",error.message||"등록 상태를 확인해 주세요.","bot");}
  });
 }else if(registration.state==="REGISTERED"){
  status.textContent="DEV WooCommerce 등록 완료 · "+registration.catalog_id+" · "+JSON.stringify(registration.receipt||{});
 }else if(registration.state==="APPLYING"||registration.state==="APPLY_OUTCOME_UNKNOWN"){
  status.textContent="등록 결과 확인이 필요합니다. 자동 재시도하지 마세요. DEV WooCommerce에서 상품 상태를 먼저 확인하세요.";
 }
 form.addEventListener("submit",async event=>{
  event.preventDefault();const button=form.querySelector("button");button.disabled=true;status.textContent="검토 정보와 이미지를 저장하고 있습니다.";
  try{
   const colors=JSON.parse(form.elements.color_options.value||"[]");
   const inventory=JSON.parse(form.elements.inventory.value||"{}");
   const sizes=form.elements.size_options.value.split(",").map(v=>v.trim()).filter(Boolean);
   const tags=form.elements.tags.value.split(",").map(v=>v.trim()).filter(Boolean);
   const fields={name:form.elements.name.value.trim(),category:form.elements.category.value,description:form.elements.description.value,style_tip:form.elements.style_tip.value,
    price:Number(form.elements.price.value),sale_price:form.elements.sale_price.value===""?null:Number(form.elements.sale_price.value),price_basis:form.elements.price_basis.value,
    tags,option_type:form.elements.option_type.value,color_options:colors,size_options:sizes,inventory,inventory_pending:form.elements.inventory_pending.checked};
   let response=await fetch("/__order-dev/admin/product-drafts/"+jobId+"/review",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({fields})});
   let result=await response.json();if(!response.ok)throw new Error(result.message||"상품 정보를 확인해 주세요.");
   for(const role of roles){
    const input=form.querySelector('input[type="file"][data-role="'+role+'"]'),file=input.files[0];
    if(!file){if(!result.media?.[role])throw new Error(roleLabels[role]+" 파일을 선택해 주세요.");continue;}
    if(file.size>8*1024*1024)throw new Error("이미지는 역할별 8MB 이하만 업로드할 수 있습니다.");
    const provenance=form.querySelector('[data-ai-role="'+role+'"]')?.checked===true;
    const upload=await fetch("/__order-dev/admin/product-drafts/"+jobId+"/media/"+role,{method:"PUT",credentials:"same-origin",headers:{"Content-Type":role==="garment-cutout"?"image/webp":"image/jpeg","X-Filename":file.name,"X-AI-Generated":String(provenance)},body:file});
    const mediaResult=await upload.json();if(!upload.ok)throw new Error(mediaResult.message||roleLabels[role]+" 업로드 실패");
    result.media=result.media||{};result.media[role]=mediaResult;
   }
   response=await fetch("/__order-dev/admin/product-drafts/"+jobId+"/preflight",{method:"POST",credentials:"same-origin"});
   result=await response.json();if(!response.ok)throw new Error((result.message||"등록 전 검증 실패")+" ("+(result.code||"")+")");
   chatLine("DEV 등록 검증","통과 · "+result.catalog_id+" · "+(result.preflight?.sku||""),"bot");
   renderReview(jobId,draft,result);
  }catch(error){status.textContent=error.message||"검증에 실패했습니다.";chatLine("검토 오류",status.textContent,"bot");button.disabled=false;}
 });
}
by("refresh").onclick=load;load();
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
  const data=await response.json();if(!response.ok)throw new Error(data.message||"요청을 처리하지 못했습니다.");
  if(lookup){chatLine("Codex 상태",data.state+(data.draft?"\\n"+JSON.stringify(data.draft,null,2):""),"bot");if(data.draft)renderReview(lookup[1],data.draft,data.registration||{});}
  else if(product){
   chatLine("Codex 초안",data.reply||("작업 #"+data.job_id+"를 시작했습니다."),"bot");
   for(let attempt=0;attempt<60&&data.job_id;attempt++){
    await new Promise(resolve=>setTimeout(resolve,2000));
    const poll=await fetch("/__order-dev/admin/product-drafts/"+data.job_id,{credentials:"same-origin"});const state=await poll.json();
    if(state.state!=="WAITING_CODEX"&&state.state!=="CODEX_RUNNING"){
     chatLine("Codex 결과",state.state+(state.draft?"\\n"+JSON.stringify(state.draft,null,2):""),"bot");
     if(state.draft)renderReview(data.job_id,state.draft,state.registration||{});break;
    }
   }
  }else chatLine("챗봇",data.reply,"bot");
 }catch(error){chatLine("오류",error.message||"잠시 후 다시 시도해 주세요.","bot");}
});
</script></main></html>"""

def mount_admin(app,*,operator_adapter,inquiry_queue,aftersales=None,conversation=None,codex_drafts=None,product_intake=None):
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
            if product_intake is not None:
                result["registration"]=product_intake.status(job_id)
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except (OSError,sqlite3.Error,json.JSONDecodeError,ValueError):return JSONResponse({"message":"초안 상태를 확인할 수 없습니다."},status_code=503)

    def valid_product_job(job_id):
        if codex_drafts is None or conversation is None or not re.fullmatch(r"[a-f0-9]{8}",job_id):
            return False
        try:
            with sqlite3.connect("file:"+str(conversation.path.resolve())+"?mode=ro",uri=True) as db:
                row=db.execute("SELECT request,state FROM website_jobs WHERE id=?",(job_id,)).fetchone()
            return bool(row and row[0].startswith("PRODUCT_INTAKE::") and row[1]=="PRODUCT_REVIEW_REQUIRED")
        except (OSError,sqlite3.Error):
            return False

    async def bounded_body(request, limit):
        try:
            declared=int(request.headers.get("content-length","0") or 0)
        except ValueError:
            raise ValueError("REQUEST_SIZE_INVALID") from None
        if declared > limit:
            raise ValueError("REQUEST_TOO_LARGE")
        chunks=[];total=0
        async for chunk in request.stream():
            total+=len(chunk)
            if total>limit:
                raise ValueError("REQUEST_TOO_LARGE")
            chunks.append(chunk)
        return b"".join(chunks)

    @app.put("/__order-dev/admin/product-drafts/{job_id}/media/{role}",include_in_schema=False)
    async def product_draft_media(request:Request,job_id:str,role:str):
        if not same_origin(request):return JSONResponse({"message":"관리자 페이지에서 다시 요청해 주세요."},status_code=403)
        if product_intake is None or not valid_product_job(job_id):return JSONResponse({"message":"상품 초안을 찾을 수 없습니다."},status_code=404)
        try:
            body=await bounded_body(request,8*1024*1024)
            result=product_intake.upload_media(job_id,role,body,content_type=request.headers.get("content-type",""),
                filename=request.headers.get("x-filename","upload"),ai_generated=request.headers.get("x-ai-generated","").lower()=="true")
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except ValueError as exc:
            return JSONResponse({"message":"이미지 업로드를 확인해 주세요.","code":str(exc)},status_code=422)

    @app.post("/__order-dev/admin/product-drafts/{job_id}/review",include_in_schema=False)
    async def product_draft_review(request:Request,job_id:str):
        if not same_origin(request):return JSONResponse({"message":"관리자 페이지에서 다시 요청해 주세요."},status_code=403)
        if product_intake is None or not valid_product_job(job_id):return JSONResponse({"message":"상품 초안을 찾을 수 없습니다."},status_code=404)
        try:
            body=json.loads(await bounded_body(request,64*1024))
            fields=body.get("fields") if isinstance(body,dict) else None
            result=product_intake.save_review(job_id,fields)
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except (ValueError,json.JSONDecodeError) as exc:
            return JSONResponse({"message":"상품 정보를 확인해 주세요.","code":str(exc)},status_code=422)

    @app.post("/__order-dev/admin/product-drafts/{job_id}/preflight",include_in_schema=False)
    async def product_draft_preflight(request:Request,job_id:str):
        if not same_origin(request):return JSONResponse({"message":"관리자 페이지에서 다시 요청해 주세요."},status_code=403)
        if product_intake is None or not valid_product_job(job_id):return JSONResponse({"message":"상품 초안을 찾을 수 없습니다."},status_code=404)
        try:
            result=await asyncio.to_thread(product_intake.preflight,job_id)
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except ValueError as exc:
            return JSONResponse({"message":"DEV 등록 전 검증에 실패했습니다. 상품 정보와 필수 이미지를 확인해 주세요.","code":str(exc)},status_code=422)

    @app.post("/__order-dev/admin/product-drafts/{job_id}/register",include_in_schema=False)
    async def product_draft_register(request:Request,job_id:str):
        if not same_origin(request):return JSONResponse({"message":"관리자 페이지에서 다시 요청해 주세요."},status_code=403)
        if product_intake is None or not valid_product_job(job_id):return JSONResponse({"message":"상품 초안을 찾을 수 없습니다."},status_code=404)
        try:
            body=json.loads(await bounded_body(request,8*1024))
            confirmation=body.get("confirmation") if isinstance(body,dict) else None
            result=await asyncio.to_thread(product_intake.register,job_id,confirmation)
            return JSONResponse(result,headers={"Cache-Control":"no-store"})
        except (ValueError,json.JSONDecodeError) as exc:
            state=409 if str(exc)=="APPLY_OUTCOME_UNKNOWN" else 422
            message="등록 결과를 확정하지 못했습니다. 재시도하지 말고 DEV 상품을 먼저 조회하세요." if state==409 else "등록 전 확인 문구와 상태를 검토해 주세요."
            return JSONResponse({"message":message,"code":str(exc)},status_code=state)

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
