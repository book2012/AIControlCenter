"""Read-only DEV operator console behind the existing DEV Basic Auth edge."""
from fastapi.responses import HTMLResponse,JSONResponse

HTML="""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIControlCenter DEV 주문 관리자</title>
<style>
body{font:15px system-ui;background:#f5f5f3;color:#222;margin:0}main{max-width:1100px;margin:auto;padding:20px}header{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
button{font:inherit;padding:9px 12px;border:1px solid #bbb;border-radius:9px;background:#fff;cursor:pointer}.grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(280px,.9fr);gap:18px}
.panel{background:#fff;border:1px solid #ddd;border-radius:14px;padding:16px}.order{padding:12px 0;border-bottom:1px solid #eee}.order:last-child{border-bottom:0}
.meta{color:#666;font-size:13px}.state{font-weight:700}.items{white-space:pre-wrap}.detail{white-space:pre-wrap;background:#fafafa;padding:12px;border-radius:10px}
.inquiry{padding:10px 0;border-bottom:1px solid #eee}.approved{color:#176b2c}.pending{color:#9a5a00}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
</style>
<main><header><div><h1>DEV 주문 관리자</h1><p>조회 전용 · 주소는 주문 상세에서만 표시</p></div><button id="refresh">새로고침</button></header>
<div class="grid"><section class="panel"><h2>최근 주문</h2><div id="orders">불러오는 중…</div></section>
<section class="panel"><h2>주문 상세</h2><div id="detail">주문을 선택하세요.</div></section></div>
<section class="panel" style="margin-top:18px"><h2>환불 / 사이즈교환 요청</h2><div id="cases">불러오는 중…</div></section><section class="panel" style="margin-top:18px"><h2>문의 / 자동학습</h2><div id="inquiries">불러오는 중…</div></section>
<script>
const by=id=>document.getElementById(id);
const stateLabel=v=>({PENDING_REVIEW:"확인대기",CONFIRMED:"확인완료",READY_TO_SHIP:"발송대기",SHIPPED:"배송중",COMPLETED:"처리완료",REJECTED:"거절",STOCK_BLOCKED:"재고확인"}[v]||v);
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
</script></main></html>"""

def mount_admin(app,*,operator_adapter,inquiry_queue,aftersales=None):
    @app.get("/dev-order/admin",include_in_schema=False)
    def admin_page():
        return HTMLResponse(HTML,headers={"Cache-Control":"no-store","X-Robots-Tag":"noindex, nofollow"})
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
