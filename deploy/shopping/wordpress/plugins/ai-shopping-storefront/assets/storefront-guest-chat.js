/* Guest inquiry/cart only. No identity, PII, credentials or automatic order POST. */
(() => {
  "use strict";
  const root=document.querySelector("[data-guest-shop-product]")||document.querySelector("main[data-product]"); if(!root)return;
  const by=id=>document.getElementById(id);
  const product=root.dataset.guestShopProduct||root.dataset.product;
  let cart=[], busy=false,inquiryBusy=false,postcodeLoader=null,selectedCart=[],prepared=null,checkoutAvailable=false,pending=null;
  try{pending=JSON.parse(sessionStorage.getItem("aicc-guest-operation-v1")||"null");if(pending&&(!/^[a-f0-9]{48}$/.test(pending.draft_id)||!/^guest-order-[a-f0-9]{48}$/.test(pending.operation_key)))throw new Error();}catch(_){pending={blocked:true};}
  const authHeaders=async()=>{const r=await fetch("/shopping/auth/session",{credentials:"same-origin"});if(!r.ok)throw new Error("휴대폰 인증이 필요합니다.");const token=r.headers.get("X-CSRF-Token");if(!token)throw new Error("인증 상태를 확인할 수 없습니다.");return {"Content-Type":"application/json","X-CSRF-Token":token};};
  const showDelivery=async()=>{if(!checkoutAvailable)return;try{const headers=await authHeaders();const r=await fetch("/__order-dev/checkout/session",{credentials:"same-origin",headers});if(r.ok){by("delivery-form").hidden=false;by("phone-form").hidden=true;by("auth-note").textContent="인증된 연락처로 주문합니다. 배송정보를 입력해 주세요.";}}catch(_){}};

  const key="aicc-guest-cart-v1";
  const valid=line=>line&&typeof line.product_id==="string"&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(line.product_id)&&
    (line.variation_id===null||typeof line.variation_id==="string"&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(line.variation_id))&&Number.isInteger(line.quantity)&&line.quantity>=1&&line.quantity<=10&&Object.keys(line).sort().join(",")==="product_id,quantity,variation_id";
  try{const value=JSON.parse(sessionStorage.getItem(key)||"[]");if(Array.isArray(value)&&value.length<=20&&value.every(valid))cart=value;}catch(_){}
  const say=(text,customer=false)=>{const p=document.createElement("p");p.textContent=text;if(customer)p.className="customer";by("messages").appendChild(p);};
  const render=()=>{by("cart").replaceChildren();cart.forEach((line,index)=>{const row=document.createElement("p");row.textContent=(line.product_id===product?"현재 상품":"상품 "+line.product_id)+" / 옵션 "+ (line.variation_id||"기본")+" · "+line.quantity+"개 ";const remove=document.createElement("button");remove.textContent="삭제";remove.onclick=()=>{cart.splice(index,1);save();};row.appendChild(remove);by("cart").appendChild(row);});by("checkout").disabled=cart.length===0;};
  const save=()=>{try{sessionStorage.setItem(key,JSON.stringify(cart));}catch(_){by("error").textContent="장바구니는 이 화면에서만 유지됩니다.";}render();by("order").hidden=!pending;};
  const request=async(path,payload)=>{const response=await fetch("/__order-dev/chat/"+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),credentials:"same-origin"});const data=await response.json();if(!response.ok)throw new Error(data.message||"요청에 실패했습니다.");return data;};
  const selected=()=>{const line={product_id:product,variation_id:by("variation").value||null,quantity:Number(by("quantity").value)};if(!valid(line)||by("variation").selectedOptions[0]?.disabled)throw new Error("상품 옵션과 수량을 선택해 주세요.");return line;};
  const run=async work=>{if(busy)return;busy=true;by("error").textContent="";try{await work();}catch(error){by("error").textContent=error.message||"요청에 실패했습니다.";}finally{busy=false;}};
  const runInquiry=async work=>{if(inquiryBusy)return;inquiryBusy=true;by("error").textContent="";try{await work();}catch(error){by("error").textContent=error.message||"요청에 실패했습니다.";}finally{inquiryBusy=false;}};
  const invalidatePrepared=()=>{prepared=null;by("confirm").disabled=true;by("final-review").replaceChildren();};
  const loadPostcode=()=>{if(window.kakao?.Postcode)return Promise.resolve();if(postcodeLoader)return postcodeLoader;postcodeLoader=new Promise((resolve,reject)=>{const script=document.createElement("script");script.src="https://t1.kakaocdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js";script.async=true;script.onload=()=>window.kakao?.Postcode?resolve():reject(new Error("주소 검색 서비스를 불러오지 못했습니다."));script.onerror=()=>reject(new Error("주소 검색 서비스를 불러오지 못했습니다."));document.head.appendChild(script);});return postcodeLoader;};
  const openPostcode=async()=>{by("error").textContent="";try{await loadPostcode();const layer=by("address-search-layer"),frame=by("address-search-frame");frame.replaceChildren();layer.hidden=false;new window.kakao.Postcode({oncomplete:data=>{const address=data.userSelectedType==="J"?data.jibunAddress:data.roadAddress;if(!/^[0-9]{5}$/.test(data.zonecode||"")||!address){by("error").textContent="선택한 주소를 사용할 수 없습니다. 다른 주소를 선택해 주세요.";return;}by("postcode").value=data.zonecode;by("address1").value=address;invalidatePrepared();layer.hidden=true;frame.replaceChildren();by("address2").focus();},width:"100%",height:"100%"}).embed(frame);}catch(error){by("error").textContent=error.message||"주소 검색 서비스를 열지 못했습니다.";}};
  const watchInquiry=data=>{let attempts=0,delivered=false,checking=false;const button=document.createElement("button");button.textContent="운영자 답변 확인";by("messages").appendChild(button);const check=async manual=>{if(delivered||checking)return;checking=true;try{const r=await fetch("/__order-dev/chat/inquiries/"+data.inquiry_token,{credentials:"same-origin"});if(!r.ok){if(manual)say("문의 확인 기간이 지났습니다. 다시 문의해 주세요.");return;}const status=await r.json();if(status.answer){say(status.answer);delivered=true;button.disabled=true;button.textContent="운영자 답변 도착";}else if(manual)say("운영자가 답변을 확인 중입니다.");}catch(_){if(manual)say("문의 상태를 확인하지 못했습니다. 다시 확인해 주세요.");}finally{checking=false;}};button.onclick=()=>check(true);const poll=async()=>{if(++attempts>120||delivered)return;await check(false);if(!delivered)setTimeout(poll,5000);};setTimeout(poll,5000);};
  const ask=message=>runInquiry(async()=>{say(message,true);const data=await request("inquiry",{product_id:product,message});const route=data.inquiry_token?"운영자에게 전달됨 · ":data.answer_engine==="OPERATOR_APPROVED_FAQ"?"승인된 답변 · ":"자동 답변 · ";say(route+data.message);if(data.inquiry_token)watchInquiry(data);if(data.action==="START_ORDER")by("single").focus();});
  by("ask").onsubmit=event=>{event.preventDefault();const text=by("question").value.trim();if(!text)return;by("question").value="";ask(text);};
  by("stock").onclick=()=>ask("재고와 사이즈 옵션 알려주세요");
  by("add").onclick=()=>run(async()=>{const line=selected();await request("quote",{line_items:[line]});const existing=cart.find(v=>v.product_id===line.product_id&&v.variation_id===line.variation_id);if(existing){if(existing.quantity+line.quantity>10)throw new Error("옵션당 최대 10개입니다.");existing.quantity+=line.quantity;}else{if(cart.length>=20)throw new Error("장바구니는 최대 20개 옵션입니다.");cart.push(line);}save();say("장바구니에 담았습니다. 계속 문의하거나 장바구니 주문하기를 누르세요.");});
  const checkout=lines=>run(async()=>{if(pending)throw new Error("진행 중인 주문의 상태를 먼저 확인해 주세요.");selectedCart=lines.map(v=>({...v}));prepared=null;const quote=await request("quote",{line_items:lines});const response=await fetch("/__order-dev/chat/capabilities",{credentials:"same-origin"});if(!response.ok)throw new Error("주문 가능 상태를 확인할 수 없습니다.");const capability=await response.json();checkoutAvailable=capability.order_confirmation===true;by("delivery-form").hidden=true;by("final-review").replaceChildren();by("summary").replaceChildren();quote.line_items.forEach(line=>{const p=document.createElement("p");p.textContent=line.name+" / "+(line.option||"기본")+" · "+line.quantity+"개 · "+line.subtotal+" "+quote.currency;by("summary").appendChild(p);});const total=document.createElement("p");total.textContent="상품 합계 "+quote.items_total+" "+quote.currency+" · 배송비 및 최종 금액은 미확정";by("summary").appendChild(total);by("auth-note").textContent=capability.message;by("phone-form").hidden=!capability.phone_verification;by("phone").disabled=!capability.phone_verification;by("confirm").disabled=true;by("order").hidden=false;by("order").scrollIntoView({behavior:"smooth"});await showDelivery();});
  by("single").onclick=()=>{try{checkout([selected()]);}catch(error){by("error").textContent=error.message;}};
  by("checkout").onclick=()=>checkout(cart.map(v=>({...v})));
  by("clear").onclick=()=>{cart=[];save();};
  by("phone").onclick=()=>run(async()=>{
    if(!by("phone-consent").checked)throw new Error("인증 문자 수신에 동의해 주세요.");
    by("phone").disabled=true;
    const r=await fetch("/__order-dev/phone/start",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({phone:by("phone-number").value,consent:true})});
    const data=await r.json();by("auth-note").textContent=data.message;
    if(!r.ok)throw new Error(data.message);by("phone-check").disabled=false;
  });
  by("phone-check").onclick=()=>run(async()=>{
    const code=by("phone-code").value;by("phone-code").value="";by("phone-check").disabled=true;
    const headers={"Content-Type":"application/json"};
    const current=await fetch("/shopping/auth/session",{credentials:"same-origin"});
    if(current.ok){const csrf=current.headers.get("X-CSRF-Token");if(csrf)headers["X-CSRF-Token"]=csrf;}
    const r=await fetch("/__order-dev/phone/check",{method:"POST",credentials:"same-origin",headers,body:JSON.stringify({code})});
    if(!r.ok)throw new Error("인증을 완료하지 못했습니다. 요청 상태를 확인해 주세요.");
    by("phone-number").value="";by("auth-note").textContent="휴대폰 인증이 완료됐습니다.";await showDelivery();
  });
  by("address-search").onclick=openPostcode;by("address-search-close").onclick=()=>{by("address-search-layer").hidden=true;by("address-search-frame").replaceChildren();};
  for(const id of ["recipient","postcode","address1","address2"])by(id).oninput=invalidatePrepared;
  by("prepare").onclick=()=>run(async()=>{
    if(pending)throw new Error("진행 중인 주문을 먼저 확인해 주세요.");
    const headers=await authHeaders();const delivery={recipient:by("recipient").value,postcode:by("postcode").value,address1:by("address1").value,address2:by("address2").value};
    const r=await fetch("/__order-dev/checkout/prepare",{method:"POST",credentials:"same-origin",headers,body:JSON.stringify({cart:{line_items:selectedCart},delivery})});
    const result=await r.json();if(!r.ok)throw new Error(result.message);prepared=result;
    by("final-review").replaceChildren();const review=document.createElement("p");
    review.textContent=result.delivery.recipient+" / "+result.delivery.postcode+" / "+result.delivery.address1+" "+result.delivery.address2+"\n상품 "+result.quote.items_total+" + DEV 배송비 "+result.quote.shipping_fee+" = 총 "+result.quote.final_total+" "+result.quote.currency+"\n연락처: 인증된 휴대폰 번호. 결제·배송은 별도이며, 주문 접수 후 운영자가 확인합니다.";
    by("final-review").appendChild(review);by("confirm").disabled=false;
  });
  by("confirm").onclick=()=>run(async()=>{
    if(!prepared||pending)throw new Error("주문 내용을 먼저 확인해 주세요.");
    const headers=await authHeaders();
    pending={draft_id:prepared.draft_id,operation_key:prepared.operation_key};
    try{sessionStorage.setItem("aicc-guest-operation-v1",JSON.stringify(pending));}catch(_){pending=null;throw new Error("주문 기록을 저장할 수 없습니다. 접수하지 않았습니다.");}
    by("confirm").disabled=true;by("guest-status").disabled=false;
    const r=await fetch("/__order-dev/checkout/confirm",{method:"POST",credentials:"same-origin",headers,body:JSON.stringify({draft_id:pending.draft_id})});
    const result=await r.json();if(!r.ok)throw new Error(result.message);
    for(const id of ["recipient","postcode","address1","address2"])by(id).value="";
    by("final-review").replaceChildren();by("delivery-form").hidden=true;
    by("auth-note").textContent="주문 #"+result.provider_order_id+" 접수 완료. 운영자 알림을 준비했으며 확인을 기다립니다.";
    by("guest-new").hidden=false;
  });
  by("guest-status").onclick=()=>run(async()=>{
    if(!pending||pending.blocked)throw new Error("주문 기록 확인이 필요합니다.");
    const headers=await authHeaders();const r=await fetch("/shopping/orders/operations/"+pending.operation_key,{credentials:"same-origin",headers});
    const status=await r.json();if(!r.ok)throw new Error("주문 상태를 확인하지 못했습니다. 새 주문을 만들지 마세요.");
    by("auth-note").textContent=status.state==="COMPLETED" ? "주문 #"+status.provider_order_id+" / "+({CONFIRMED:"운영자가 주문을 확인했습니다.",REJECTED:"운영자가 주문을 거절했습니다.",PENDING_REVIEW:"운영자 확인 대기 중입니다."}[status.review_state]||status.review_state) : "주문 처리 상태: "+status.state+" · 중복 접수하지 마세요.";
    by("guest-new").hidden=status.state!=="COMPLETED";
  });
  by("guest-new").onclick=()=>{sessionStorage.removeItem("aicc-guest-operation-v1");pending=null;prepared=null;by("order").hidden=true;by("guest-new").hidden=true;by("guest-status").disabled=true;};
  render();if(pending){by("order").hidden=false;by("guest-status").disabled=!!pending.blocked;by("auth-note").textContent="기존 주문 기록이 있습니다. 상태 확인 후 계속해 주세요.";}say("안녕하세요. 재고·옵션·가격·상품 설명을 물어보세요. 문의에는 회원가입이나 휴대폰 인증이 필요 없습니다.");
})();
