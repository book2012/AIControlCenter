"use strict";

(() => {
  const commercePath=path=>(["bokstory.duckdns.org","agachichi.duckdns.org"].includes(window.location.hostname)?"/shopping":"/__order-dev")+path;

  const by=id=>document.getElementById(id);
  let csrf=null;
  let activeOrder=null;

  const message=text=>{by("orders-message").textContent=text||"";};
  const session=async()=>{
    const response=await fetch("/shopping/auth/session",{credentials:"same-origin"});
    if(!response.ok)return false;
    csrf=response.headers.get("X-CSRF-Token");
    return Boolean(csrf);
  };
  const headers=()=>({"Content-Type":"application/json","X-CSRF-Token":csrf});
  const showProgress=(card,order)=>{
    const fulfillment=order.fulfillment?.state||"NOT_SHIPPED";
    const cancelled=order.cancellation?.state&&order.cancellation.state!=="NONE";
    const step=fulfillment==="DELIVERED"?3:fulfillment==="SHIPPED"?2:order.review_state==="CONFIRMED"?1:0;
    const list=document.createElement("ol");list.className="orders-progress";list.setAttribute("aria-label","주문 진행 단계");
    const names=["주문 접수","주문 확인","배송 중","배송 완료"];
    names.forEach((name,index)=>{const item=document.createElement("li");item.textContent=name;if(index<step)item.classList.add("is-complete");if(index===step){item.classList.add("is-current");item.setAttribute("aria-current","step");}list.appendChild(item);});
    if(cancelled){const note=document.createElement("p");note.className="order-delivery-address";note.textContent=order.cancellation.state==="CANCELLED"?"이 주문은 취소 처리되었습니다.":"취소 상태를 확인하고 있습니다.";card.appendChild(note);}
    card.appendChild(list);
  };
  const orderAnswer=question=>{
    const order=activeOrder;if(!order)return "먼저 주문을 조회해 주세요.";
    const q=question.toLowerCase(),fulfillment=order.fulfillment?.state||"NOT_SHIPPED";
    if(order.refund?.state==="RECORDED")return "운영자가 환불 완료를 기록했습니다. 환불 금액은 "+order.refund.amount+" "+order.refund.currency+"입니다.";
    if(order.cancellation?.state==="CANCELLED")return "주문 취소가 완료되었습니다. 중복 입금을 방지하기 위해 입금하지 마세요.";
    if(order.cancellation?.state&&order.cancellation.state!=="NONE")return "주문 취소 여부를 확인하고 있습니다. 확인이 끝날 때까지 입금하지 말고 고객 문의로 확인해 주세요.";
    if(/배송|택배|운송장|도착|언제/.test(q)){
      if(fulfillment==="DELIVERED")return "조회된 주문은 배송 완료 상태입니다. 배송 관련 추가 확인은 고객 문의로 알려 주세요.";
      if(fulfillment==="SHIPPED")return "상품이 배송 중입니다."+(order.fulfillment?.carrier?" 택배사: "+order.fulfillment.carrier+".":"")+(order.fulfillment?.tracking?" 운송장 번호: "+order.fulfillment.tracking+".":" 운송장 정보가 준비되면 이 화면에 표시됩니다.");
      return "현재 주문은 아직 발송 전입니다. 주문 확인과 입금 상태를 함께 확인해 주세요. 발송이 시작되면 배송 정보가 표시됩니다.";
    }
    if(/환불|반품|교환|사이즈/.test(q)){
      const options=[];if(order.cancel_request_available)options.push("취소/환불");if(order.order_change_available)options.push("주문 변경");if(order.return_available)options.push("반품/환불");if(order.exchange_available)options.push("교환");
      const fee=" 단순 변심·사이즈 변경은 배송비 고객 부담, 상품 하자·오배송은 판매자 부담으로 접수합니다.";
      return options.length?"이 주문은 "+options.join(" 및 ")+" 요청이 가능합니다. 주문 카드에서 접수해 주세요."+(order.return_available||order.exchange_available?fee:""):"현재 배송 상태에서는 요청할 수 없습니다. 발송 전에는 주문 카드에서 취소·변경을 요청하고, 배송완료 후 14일 이내 반품·교환을 신청할 수 있습니다.";
    }
    if(/입금|결제|은행/.test(q))return order.payment?.state==="PAID"?"입금 확인이 완료됐습니다.":"현재 입금 확인 전 상태입니다. 입금 확인 후 주문 상태가 갱신됩니다.";
    const review={CONFIRMED:"주문 확인이 완료됐습니다.",PENDING_REVIEW:"주문 확인을 기다리고 있습니다.",REJECTED:"주문 확인이 완료되지 않았습니다. 고객 문의로 확인해 주세요.",STOCK_BLOCKED:"상품 재고를 확인하고 있습니다."}[order.review_state]||"주문이 접수되어 확인 중입니다.";
    const payment=order.payment?.state==="PAID"?"입금 확인 완료":"입금 확인 대기";
    return review+" 현재 상태는 "+payment+" · "+({NOT_SHIPPED:"발송 전",SHIPPED:"배송 중",DELIVERED:"배송 완료"}[fulfillment]||"발송 전")+"입니다.";
  };
  const addChatMessage=(text,kind)=>{const p=document.createElement("p");p.className=kind==="user"?"user-message":"assistant-message";p.textContent=text;by("order-chat-log").appendChild(p);p.scrollIntoView({block:"nearest"});};
  const askOrder=question=>{const q=question.trim();if(!q||!activeOrder)return;addChatMessage(q,"user");addChatMessage(orderAnswer(q),"assistant");};
  by("order-chat-form").addEventListener("submit",event=>{event.preventDefault();const input=by("order-chat-question");askOrder(input.value);input.value="";input.focus();});
  document.querySelectorAll("[data-order-question]").forEach(button=>button.addEventListener("click",()=>askOrder(button.dataset.orderQuestion)));

  const requestCaseForm=async(card,order,kind)=>{
    if(card.querySelector(".orders-request"))return;
    const box=document.createElement("div");box.className="orders-request";
    let select=null,reasonType=null;
    if(kind==="SIZE_EXCHANGE"){
      const response=await fetch(commercePath('/aftersales/orders/')+order.order_id+"/exchange-options",{credentials:"same-origin",headers:headers()});
      const data=await response.json();
      if(!response.ok||!Array.isArray(data.options)||!data.options.length){message("현재 교환 가능한 옵션이 없습니다.");return;}
      const label=document.createElement("label");label.textContent="교환할 옵션";
      select=document.createElement("select");
      for(const value of data.options){const option=document.createElement("option");option.value=value.variation_id;option.textContent=value.option;select.appendChild(option);}
      label.appendChild(select);box.appendChild(label);
    }
    if((kind==="RETURN"||kind==="SIZE_EXCHANGE")&&(order.fulfillment?.state||"NOT_SHIPPED")==="DELIVERED"){
      const label=document.createElement("label");label.textContent="신청 사유";
      reasonType=document.createElement("select");
      reasonType.innerHTML='<option value="">사유를 선택해 주세요</option><option value="CHANGE_OF_MIND">단순 변심·사이즈 변경</option><option value="DEFECT_OR_WRONG">상품 하자·오배송</option>';
      label.appendChild(reasonType);box.appendChild(label);
      const feeNote=document.createElement("p");feeNote.className="orders-fee-notice";
      feeNote.textContent="단순 변심·사이즈 변경은 반품·교환 배송비를 고객님이 부담합니다. 상품 하자·오배송은 판매자가 부담합니다. 최종 확인 후 접수해 주세요.";
      box.appendChild(feeNote);
    }
    const reason=document.createElement("textarea");reason.maxLength=1000;
    reason.placeholder=kind==="RETURN"?(order.fulfillment?.state==="NOT_SHIPPED"?"취소/환불 요청 사유를 적어 주세요.":"반품/환불 사유를 적어 주세요."):kind==="ORDER_CHANGE"?"변경할 상품·옵션·배송정보를 적어 주세요.":"교환 사유를 적어 주세요.";
    const file=document.createElement("input");file.type="file";file.accept="image/jpeg,image/png,image/webp";file.multiple=true;
    const note=document.createElement("p");note.className="field-note";note.textContent=kind==="ORDER_CHANGE"?"발송 전 변경 요청입니다. 운영자가 확인 후 주문 정보를 별도로 수정하며, 이 요청만으로 주문이 바뀌지는 않습니다.":kind==="RETURN"&&order.fulfillment?.state==="NOT_SHIPPED"?"취소/환불은 운영자 확인 후 처리됩니다. 입금된 주문은 환불 송금이 자동 실행되지 않습니다.":"필요한 경우 사진을 최대 5개 첨부할 수 있습니다.";
    const submit=document.createElement("button");submit.type="button";submit.className="solid-button";
    submit.textContent=kind==="RETURN"?(order.fulfillment?.state==="NOT_SHIPPED"?"취소/환불 요청 접수":"반품/환불 요청 접수"):kind==="ORDER_CHANGE"?"주문 변경 요청 접수":"교환 요청 접수";
    submit.onclick=async()=>{
      if(reasonType&&!reasonType.value){message("신청 사유를 선택해 주세요.");reasonType.focus();return;}
      const confirmCopy=reasonType?.value==="CHANGE_OF_MIND"?"단순 변심 또는 사이즈 변경으로 접수합니다. 반품·교환 배송비는 고객 부담입니다. 계속할까요?":reasonType?.value==="DEFECT_OR_WRONG"?"상품 하자 또는 오배송으로 접수합니다. 확인 후 판매자 부담 여부를 검토합니다. 계속할까요?":kind==="ORDER_CHANGE"?"발송 전 주문 변경 요청을 접수할까요? 운영자가 확인 후 별도로 처리합니다.":"취소/환불 요청을 접수할까요? 실제 취소와 환불은 운영자 확인 후 처리됩니다.";
      if(!window.confirm(confirmCopy))return;
      submit.disabled=true;message("");
      try{
        const payload={order_id:order.order_id,kind,reason:reason.value,target_variation_id:select?select.value:null,reason_type:reasonType?.value||null};
        const response=await fetch(commercePath('/aftersales/cases'),{method:"POST",credentials:"same-origin",headers:headers(),body:JSON.stringify(payload)});
        const data=await response.json();if(!response.ok)throw new Error(data.message||"요청을 접수하지 못했습니다.");
        for(const current of Array.from(file.files).slice(0,5)){
          const uploaded=await fetch(commercePath('/aftersales/cases/')+data.case.id+"/attachments",{method:"POST",credentials:"same-origin",
            headers:{"Content-Type":current.type,"X-CSRF-Token":csrf},body:current});
          if(!uploaded.ok)throw new Error("요청은 접수됐지만 일부 첨부파일을 저장하지 못했습니다.");
        }
        message("요청이 접수됐습니다. 운영자 확인 후 상태가 업데이트됩니다.");await load();
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
    const cancellation=order.cancellation?.state||"NONE";
    const returned=order.return_status?.state||"NONE";
    const refundRecorded=order.refund?.state==="RECORDED";
    const returnLabels={RETURN_APPROVED:"반품승인",RETURN_RECEIVED:"반품회수 · 검수대기",RETURN_RESTOCK_PENDING:"반품 처리 확인중",RETURN_RESTOCK_UNKNOWN:"반품 처리 확인중",RETURN_RESTOCKED:"반품검수완료 · 환불검토"};
    const cancellationLabel=cancellation==="CANCELLED"?"취소완료":"취소 확인중";
    state.textContent=refundRecorded?"환불완료":cancellation!=="NONE"?cancellationLabel:returned!=="NONE"?(returnLabels[returned]||"반품 처리중"):fulfillment==="DELIVERED"?"배송완료":fulfillment==="SHIPPED"?"배송중":order.review_state==="CONFIRMED"?(order.payment?.state==="PAID"?"배송준비":"입금대기"):order.review_state==="REJECTED"?"거절":"확인대기";
    head.append(title,state);card.appendChild(head);showProgress(card,order);
    const details=document.createElement("p");details.className="orders-status-summary";
    const labels={CONFIRMED:"주문확인 완료",PENDING_REVIEW:"주문확인 대기",REJECTED:"주문 거절",STOCK_BLOCKED:"재고확인 중"};
    details.textContent=refundRecorded?"환불완료 · "+order.refund.amount+" "+order.refund.currency+" · 운영자 송금 확인 기록":cancellation!=="NONE"?cancellationLabel+" · 입금하지 마세요.":returned!=="NONE"?(returnLabels[returned]||"반품 처리중")+" · 환불 안내는 별도로 확인해 주세요.":(labels[order.review_state]||"주문확인 대기")+" · "+(order.payment?.state==="PAID"?"입금완료":"입금대기")+" · "+({NOT_SHIPPED:order.payment?.state==="PAID"?"배송준비":"입금대기",SHIPPED:"배송중",DELIVERED:"배송완료"}[fulfillment]||"발송대기");
    card.appendChild(details);
    if(order.notification_state){
      const notice=document.createElement("p");notice.className="field-note";
      notice.textContent=order.notification_state==="ACCEPTED"?"주문 안내 문자 발송 접수":order.notification_state==="HISTORICAL"?"기존 주문 · 문자 자동 재발송 없음":order.notification_state==="UNKNOWN"?"문자 발송 결과 확인 중":"주문 안내 문자 발송 대기";
      card.appendChild(notice);
    }
    const address=document.createElement("p");const delivery=order.delivery||{};
    address.className="order-delivery-address";address.textContent="배송주소: "+[delivery.first_name,delivery.postcode,delivery.address_1,delivery.address_2].filter(Boolean).join(" ");
    card.appendChild(address);
    const items=document.createElement("div");items.className="order-items";
    for(const item of order.items){const p=document.createElement("p");p.textContent=item.name+" / "+(item.option||"기본")+" / "+item.quantity+"개";items.appendChild(p);}
    card.appendChild(items);
    const total=document.createElement("p");total.className="order-total";total.textContent="총 "+order.total+" "+order.currency;card.appendChild(total);
    if(order.fulfillment?.carrier||order.fulfillment?.tracking){
      const shipping=document.createElement("p");shipping.className="field-note";shipping.textContent=[order.fulfillment.carrier,order.fulfillment.tracking].filter(Boolean).join(" · ");card.appendChild(shipping);
    }
    const caseLabels={REQUESTED:"운영자 확인 대기",REJECTED:"거절",RETURN_APPROVED:"반품승인",RETURN_RECEIVED:"회수완료",RETURN_RESTOCK_PENDING:"재고 처리 확인중",RETURN_RESTOCK_UNKNOWN:"재고 처리 확인중",RETURN_RESTOCKED:"검수완료 · 환불검토",EXCHANGE_APPROVED:"교환승인",ORDER_CHANGE_APPROVED:"변경 승인 · 주문 정보 수정 대기"};
    for(const current of order.cases||[]){
      const row=document.createElement("div");row.className="order-case";
      row.textContent=(current.kind==="RETURN"?(fulfillment==="NOT_SHIPPED"?"취소/환불":"반품/환불"):current.kind==="ORDER_CHANGE"?"주문 변경":"사이즈교환")+" #"+current.id+" · "+(refundRecorded&&current.kind==="RETURN"?"환불완료":caseLabels[current.state]||"상태 확인중")+(current.shipping_fee_payer==="CUSTOMER"?" · 배송비 고객 부담":current.shipping_fee_payer==="SELLER"?" · 배송비 판매자 부담":"")+(current.target_option?" · "+current.target_option:"")+" · 첨부 "+current.attachments+"개";
      card.appendChild(row);
      if(current.kind==="ORDER_CHANGE"&&current.state==="ORDER_CHANGE_APPROVED"){const note=document.createElement("p");note.className="field-note";note.textContent="운영자가 실제 주문 정보를 별도로 수정해야 변경이 완료됩니다.";card.appendChild(note);}
    }
    if(fulfillment==="SHIPPED"){const note=document.createElement("p");note.className="field-note";note.textContent="배송이 시작되어 취소·주문 변경은 접수할 수 없습니다. 반품·교환은 배송완료 후 신청할 수 있습니다.";card.appendChild(note);}
    for(const notice of order.customer_messages||[]){const p=document.createElement("p");p.className="order-customer-message";p.style.whiteSpace="pre-wrap";p.textContent=notice.message;card.appendChild(p);}
    const actions=document.createElement("div");actions.className="order-actions";
    if(order.cancel_request_available){const button=document.createElement("button");button.type="button";button.textContent=order.payment?.state==="PAID"?"취소/환불 요청":"주문 취소 요청";button.onclick=()=>requestCaseForm(card,order,"RETURN");actions.appendChild(button);}
    if(order.order_change_available){const button=document.createElement("button");button.type="button";button.textContent="주문 변경 요청";button.onclick=()=>requestCaseForm(card,order,"ORDER_CHANGE");actions.appendChild(button);}
    if(order.return_available){const button=document.createElement("button");button.type="button";button.textContent="반품/환불 요청";button.onclick=()=>requestCaseForm(card,order,"RETURN");actions.appendChild(button);}
    if(order.exchange_available){const button=document.createElement("button");button.type="button";button.textContent="교환 요청";button.onclick=()=>requestCaseForm(card,order,"SIZE_EXCHANGE");actions.appendChild(button);}
    if(actions.childElementCount)card.appendChild(actions);
    return card;
  };

  const renderPublicOrder=order=>{
    const card=document.createElement("article");card.className="order-card";
    const head=document.createElement("div");head.className="order-card-head";
    const title=document.createElement("h2");title.textContent="주문 "+order.order_number;
    const state=document.createElement("strong");state.className="order-state";
    const fulfillment=order.fulfillment?.state||"NOT_SHIPPED";
    state.textContent=fulfillment==="DELIVERED"?"배송완료":fulfillment==="SHIPPED"?"배송중":order.payment?.state==="PAID"?"배송준비":order.review_state==="CONFIRMED"?"입금대기":"확인대기";
    head.append(title,state);card.appendChild(head);showProgress(card,order);
    const date=document.createElement("p");date.textContent="주문일: "+(order.requested_at||"일자 미확인");card.appendChild(date);
    const items=document.createElement("div");items.className="order-items";
    for(const item of order.items||[]){const p=document.createElement("p");p.textContent=item.name+" / "+(item.option||"기본")+" / "+item.quantity+"개";items.appendChild(p);}
    card.appendChild(items);
    const total=document.createElement("p");total.className="order-total";total.textContent="총 "+order.total+" "+order.currency;card.appendChild(total);
    if(order.fulfillment?.carrier||order.fulfillment?.tracking){
      const shipping=document.createElement("p");shipping.className="field-note";shipping.textContent=[order.fulfillment.carrier,order.fulfillment.tracking].filter(Boolean).join(" · ");card.appendChild(shipping);
    }
    const note=document.createElement("p");note.className="order-customer-message";note.textContent="주문번호 조회 결과입니다. 배송주소와 환불·사이즈교환 기능은 휴대폰 인증 후 사용할 수 있습니다.";card.appendChild(note);
    return card;
  };

  const load=async()=>{
    activeOrder=null;by("orders-list").replaceChildren();by("order-chat").hidden=true;by("order-chat-log").replaceChildren();
    const number=by("orders-number").value.trim().replace(/^#/,"");
    if(/^\d{10}$/.test(number)){
      const publicResponse=await fetch(commercePath('/orders/public-lookup'),{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({order_number:number})});
      const publicData=await publicResponse.json();
      if(publicResponse.ok){
        activeOrder=publicData.order;by("orders-auth").hidden=true;by("orders-list").appendChild(renderPublicOrder(activeOrder));by("order-chat").hidden=false;
        message("주문번호만으로 기본 상태를 확인했습니다. 상세 기능은 휴대폰 인증 후 이용할 수 있습니다.");return;
      }
      message(publicResponse.status===404?"주문번호를 찾을 수 없습니다. 10자리 주문번호를 확인해 주세요.":"주문조회 서비스에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.");
      return;
    }
    if(!(await session())){by("orders-phone").value=by("lookup-phone").value;by("orders-auth").hidden=false;message("상세 주문 조회는 휴대폰 인증 후 이용할 수 있습니다.");return;}
    by("orders-auth").hidden=true;message("");
    const response=await fetch(commercePath('/orders/lookup'),{method:"POST",credentials:"same-origin",headers:headers(),
      body:JSON.stringify({order_number:by("orders-number").value,phone:by("lookup-phone").value})});
    const data=await response.json();
    if(!response.ok){message(data.message||"주문을 조회하지 못했습니다.");return;}
    activeOrder=data.order;by("orders-list").appendChild(renderOrder(activeOrder));by("order-chat").hidden=false;message("");
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
  // Public lookup needs no customer session; probe only for private details.
  by("orders-auth").hidden=true;
})();
