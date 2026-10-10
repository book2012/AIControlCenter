"use strict";

(() => {
  const commercePath=path=>(window.location.hostname==="bokstory.duckdns.org"?"/shopping":"/__order-dev")+path;

  const by=id=>document.getElementById(id);
  let csrf=null;

  const message=text=>{by("orders-message").textContent=text||"";};
  const session=async()=>{
    const response=await fetch("/shopping/auth/session",{credentials:"same-origin"});
    if(!response.ok)return false;
    csrf=response.headers.get("X-CSRF-Token");
    return Boolean(csrf);
  };
  const headers=()=>({"Content-Type":"application/json","X-CSRF-Token":csrf});

  const requestCaseForm=async(card,order,kind)=>{
    if(card.querySelector(".orders-request"))return;
    const box=document.createElement("div");box.className="orders-request";
    let select=null;
    if(kind==="SIZE_EXCHANGE"){
      const response=await fetch(commercePath('/aftersales/orders/')+order.order_id+"/exchange-options",{credentials:"same-origin",headers:headers()});
      const data=await response.json();
      if(!response.ok||!Array.isArray(data.options)||!data.options.length){message("현재 교환 가능한 사이즈가 없습니다.");return;}
      const label=document.createElement("label");label.textContent="교환할 사이즈";
      select=document.createElement("select");
      for(const value of data.options){const option=document.createElement("option");option.value=value.variation_id;option.textContent=value.option;select.appendChild(option);}
      label.appendChild(select);box.appendChild(label);
    }
    const reason=document.createElement("textarea");reason.maxLength=1000;reason.placeholder=kind==="RETURN"?"환불 사유를 입력해 주세요.":"교환 사유를 입력해 주세요.";
    const file=document.createElement("input");file.type="file";file.accept="image/jpeg,image/png,image/webp";file.multiple=true;
    const note=document.createElement("p");note.className="field-note";note.textContent="필요한 경우 사진을 최대 5개 첨부할 수 있습니다.";
    const submit=document.createElement("button");submit.type="button";submit.className="solid-button";submit.textContent=kind==="RETURN"?"환불 요청 접수":"사이즈교환 요청 접수";
    submit.onclick=async()=>{
      submit.disabled=true;message("");
      try{
        const payload={order_id:order.order_id,kind,reason:reason.value,target_variation_id:select?select.value:null};
        const response=await fetch(commercePath('/aftersales/cases'),{method:"POST",credentials:"same-origin",headers:headers(),body:JSON.stringify(payload)});
        const data=await response.json();if(!response.ok)throw new Error(data.message||"요청을 접수하지 못했습니다.");
        for(const current of Array.from(file.files).slice(0,5)){
          const uploaded=await fetch(commercePath('/aftersales/cases/')+data.case.id+"/attachments",{method:"POST",credentials:"same-origin",
            headers:{"Content-Type":current.type,"X-CSRF-Token":csrf},body:current});
          if(!uploaded.ok)throw new Error("요청은 접수됐지만 일부 첨부파일을 저장하지 못했습니다.");
        }
        message("요청이 접수됐습니다.");await load();
      }catch(error){message(error?.message||"요청을 접수하지 못했습니다.");}
      finally{submit.disabled=false;}
    };
    box.append(reason,file,note,submit);card.appendChild(box);
  };

  const renderOrder=order=>{
    const card=document.createElement("article");card.className="order-card";
    const head=document.createElement("div");head.className="order-card-head";
    const title=document.createElement("h2");title.textContent="주문 #"+order.order_id;
    const state=document.createElement("strong");state.className="order-state";
    const fulfillment=order.fulfillment?.state||"NOT_SHIPPED";
    state.textContent=fulfillment==="DELIVERED"?"배송완료":fulfillment==="SHIPPED"?"배송중":order.review_state==="CONFIRMED"?(order.payment?.state==="PAID"?"배송준비":"입금대기"):order.review_state==="REJECTED"?"거절":"확인대기";
    head.append(title,state);card.appendChild(head);
    const details=document.createElement("p");
    const labels={CONFIRMED:"주문확인 완료",PENDING_REVIEW:"주문확인 대기",REJECTED:"주문 거절",STOCK_BLOCKED:"재고확인 중"};
    details.textContent=(labels[order.review_state]||"주문확인 대기")+" · "+(order.payment?.state==="PAID"?"입금완료":"입금대기")+" · "+({NOT_SHIPPED:order.payment?.state==="PAID"?"배송준비":"입금대기",SHIPPED:"배송중",DELIVERED:"배송완료"}[fulfillment]||"발송대기");
    card.appendChild(details);
    if(order.notification_state){
      const notice=document.createElement("p");notice.className="field-note";
      notice.textContent=order.notification_state==="ACCEPTED"?"주문 안내 문자 발송 접수":order.notification_state==="HISTORICAL"?"기존 주문 · 문자 자동 재발송 없음":order.notification_state==="UNKNOWN"?"문자 발송 결과 확인 중":"주문 안내 문자 발송 대기";
      card.appendChild(notice);
    }
    const address=document.createElement("p");const delivery=order.delivery||{};
    address.textContent="배송주소: "+[delivery.first_name,delivery.postcode,delivery.address_1,delivery.address_2].filter(Boolean).join(" ");
    card.appendChild(address);
    const items=document.createElement("div");items.className="order-items";
    for(const item of order.items){const p=document.createElement("p");p.textContent=item.name+" / "+(item.option||"기본")+" / "+item.quantity+"개";items.appendChild(p);}
    card.appendChild(items);
    const total=document.createElement("p");total.className="order-total";total.textContent="총 "+order.total+" "+order.currency;card.appendChild(total);
    if(order.fulfillment?.carrier||order.fulfillment?.tracking){
      const shipping=document.createElement("p");shipping.className="field-note";shipping.textContent=[order.fulfillment.carrier,order.fulfillment.tracking].filter(Boolean).join(" · ");card.appendChild(shipping);
    }
    for(const current of order.cases||[]){
      const row=document.createElement("div");row.className="order-case";
      row.textContent=(current.kind==="RETURN"?"환불":"사이즈교환")+" #"+current.id+" · "+current.state+(current.target_option?" · "+current.target_option:"")+" · 첨부 "+current.attachments+"개";
      card.appendChild(row);
    }
    for(const notice of order.customer_messages||[]){const p=document.createElement("p");p.className="order-customer-message";p.style.whiteSpace="pre-wrap";p.textContent=notice.message;card.appendChild(p);}
    const actions=document.createElement("div");actions.className="order-actions";
    if(order.return_available){const button=document.createElement("button");button.type="button";button.textContent="환불 요청";button.onclick=()=>requestCaseForm(card,order,"RETURN");actions.appendChild(button);}
    if(order.exchange_available){const button=document.createElement("button");button.type="button";button.textContent="사이즈 교환";button.onclick=()=>requestCaseForm(card,order,"SIZE_EXCHANGE");actions.appendChild(button);}
    if(actions.childElementCount)card.appendChild(actions);
    return card;
  };

  const load=async()=>{
    if(!(await session())){by("orders-phone").value=by("lookup-phone").value;by("orders-auth").hidden=false;by("orders-list").replaceChildren();return;}
    by("orders-auth").hidden=true;message("");
    const response=await fetch(commercePath('/orders/lookup'),{method:"POST",credentials:"same-origin",headers:headers(),
      body:JSON.stringify({order_number:by("orders-number").value,phone:by("lookup-phone").value})});
    const data=await response.json();by("orders-list").replaceChildren();
    if(!response.ok){message(data.message||"주문을 조회하지 못했습니다.");return;}
    by("orders-list").appendChild(renderOrder(data.order));
  };
  by("orders-lookup").onclick=()=>load().catch(()=>message("주문을 조회하지 못했습니다."));

  by("orders-send").onclick=async()=>{
    message("");
    if(!by("orders-consent").checked){message("인증 문자 수신에 동의해 주세요.");return;}
    const response=await fetch(commercePath('/phone/start'),{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({phone:by("orders-phone").value,consent:true})});
    const data=await response.json();message(data.message||"");
  };
  by("orders-check").onclick=async()=>{
    message("");
    const requestHeaders={"Content-Type":"application/json"};
    const current=await fetch("/shopping/auth/session",{credentials:"same-origin"});
    if(current.ok){const token=current.headers.get("X-CSRF-Token");if(token)requestHeaders["X-CSRF-Token"]=token;}
    const response=await fetch(commercePath('/phone/check'),{method:"POST",credentials:"same-origin",headers:requestHeaders,
      body:JSON.stringify({code:by("orders-code").value})});
    by("orders-code").value="";
    if(!response.ok){message("인증을 완료하지 못했습니다.");return;}
    if(!by("lookup-phone").value)by("lookup-phone").value=by("orders-phone").value;
    csrf=response.headers.get("X-CSRF-Token")||csrf;message("휴대폰 인증이 완료됐습니다.");await load();
  };
  session().then(verified=>{by("orders-auth").hidden=verified;});
})();
