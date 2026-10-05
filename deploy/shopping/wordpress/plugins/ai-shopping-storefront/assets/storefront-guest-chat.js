/* Guest inquiry/cart only. No identity, PII, credentials or automatic order POST. */
(() => {
  "use strict";
  const root=document.querySelector("main[data-product]"); if(!root)return;
  const by=id=>document.getElementById(id);
  const product=root.dataset.product;
  let cart=[], busy=false;
  const key="aicc-guest-cart-v1";
  const valid=line=>line&&typeof line.product_id==="string"&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(line.product_id)&&
    (line.variation_id===null||typeof line.variation_id==="string"&&/^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$/.test(line.variation_id))&&Number.isInteger(line.quantity)&&line.quantity>=1&&line.quantity<=10&&Object.keys(line).sort().join(",")==="product_id,quantity,variation_id";
  try{const value=JSON.parse(sessionStorage.getItem(key)||"[]");if(Array.isArray(value)&&value.length<=20&&value.every(valid))cart=value;}catch(_){}
  const say=(text,customer=false)=>{const p=document.createElement("p");p.textContent=text;if(customer)p.className="customer";by("messages").appendChild(p);};
  const render=()=>{by("cart").replaceChildren();cart.forEach((line,index)=>{const row=document.createElement("p");row.textContent=(line.product_id===product?"현재 상품":"상품 "+line.product_id)+" / 옵션 "+ (line.variation_id||"기본")+" · "+line.quantity+"개 ";const remove=document.createElement("button");remove.textContent="삭제";remove.onclick=()=>{cart.splice(index,1);save();};row.appendChild(remove);by("cart").appendChild(row);});by("checkout").disabled=cart.length===0;};
  const save=()=>{try{sessionStorage.setItem(key,JSON.stringify(cart));}catch(_){by("error").textContent="장바구니는 이 화면에서만 유지됩니다.";}render();by("order").hidden=true;};
  const request=async(path,payload)=>{const response=await fetch("/__order-dev/chat/"+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload),credentials:"same-origin"});const data=await response.json();if(!response.ok)throw new Error(data.message||"요청에 실패했습니다.");return data;};
  const selected=()=>{const line={product_id:product,variation_id:by("variation").value||null,quantity:Number(by("quantity").value)};if(!valid(line)||by("variation").selectedOptions[0]?.disabled)throw new Error("상품 옵션과 수량을 선택해 주세요.");return line;};
  const run=async work=>{if(busy)return;busy=true;by("error").textContent="";try{await work();}catch(error){by("error").textContent=error.message||"요청에 실패했습니다.";}finally{busy=false;}};
  const ask=message=>run(async()=>{say(message,true);const data=await request("inquiry",{product_id:product,message});say(data.message);if(data.action==="START_ORDER")by("single").focus();});
  by("ask").onsubmit=event=>{event.preventDefault();const text=by("question").value.trim();if(!text)return;by("question").value="";ask(text);};
  by("stock").onclick=()=>ask("재고와 사이즈 옵션 알려주세요");
  by("add").onclick=()=>run(async()=>{const line=selected();await request("quote",{line_items:[line]});const existing=cart.find(v=>v.product_id===line.product_id&&v.variation_id===line.variation_id);if(existing){if(existing.quantity+line.quantity>10)throw new Error("옵션당 최대 10개입니다.");existing.quantity+=line.quantity;}else{if(cart.length>=20)throw new Error("장바구니는 최대 20개 옵션입니다.");cart.push(line);}save();say("장바구니에 담았습니다. 계속 문의하거나 장바구니 주문하기를 누르세요.");});
  const checkout=lines=>run(async()=>{const quote=await request("quote",{line_items:lines});const response=await fetch("/__order-dev/chat/capabilities",{credentials:"same-origin"});if(!response.ok)throw new Error("주문 가능 상태를 확인할 수 없습니다.");const capability=await response.json();by("summary").replaceChildren();quote.line_items.forEach(line=>{const p=document.createElement("p");p.textContent=line.name+" / "+(line.option||"기본")+" · "+line.quantity+"개 · "+line.subtotal+" "+quote.currency;by("summary").appendChild(p);});const total=document.createElement("p");total.textContent="상품 합계 "+quote.items_total+" "+quote.currency+" · 배송비 및 최종 금액은 미확정";by("summary").appendChild(total);by("auth-note").textContent=capability.message;by("phone").disabled=true;by("confirm").disabled=true;by("order").hidden=false;by("order").scrollIntoView({behavior:"smooth"});});
  by("single").onclick=()=>{try{checkout([selected()]);}catch(error){by("error").textContent=error.message;}};
  by("checkout").onclick=()=>checkout(cart.map(v=>({...v})));
  by("clear").onclick=()=>{cart=[];save();};
  render();say("안녕하세요. 재고·옵션·가격·상품 설명을 물어보세요. 문의에는 회원가입이나 휴대폰 인증이 필요 없습니다.");
})();
