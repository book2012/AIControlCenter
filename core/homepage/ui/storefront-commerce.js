"use strict";

(() => {
  const target=document.getElementById("commerce-panel");
  if(!target)return;
  const cartPage=target.dataset.cartPage==="true";
  const demo=target.dataset.demoProduct||"";
  if(!cartPage&&!/^(?:oc-demo-(?:top|bottom|outer|dress|bag)-0001|ag-upload-(?:top|bottom|outer|dress|bag|acc)-[0-9]{4})$/.test(demo)){
    target.textContent="주문 기능을 사용할 수 없습니다.";
    return;
  }
  const load=async()=>{
    try{
      const response=await fetch(cartPage?"/__order-dev/chat/cart":"/__order-dev/chat/embed/"+encodeURIComponent(demo),{credentials:"same-origin",headers:{Accept:"text/html"}});
      if(!response.ok)throw new Error("주문 기능을 불러오지 못했습니다.");
      const type=response.headers.get("content-type")||"";
      if(!type.includes("text/html"))throw new Error("주문 기능 응답이 올바르지 않습니다.");
      const text=await response.text();
      if(/<script\b/i.test(text))throw new Error("주문 기능 응답이 올바르지 않습니다.");
      const template=document.createElement("template");
      template.innerHTML=text.trim();
      const node=template.content.firstElementChild;
      if(!node||!node.matches("[data-guest-shop-product]"))throw new Error("주문 기능을 불러오지 못했습니다.");
      target.replaceChildren(node);
      // Retain the provider variant ID for checkout, but show one canonical option area.
      if(!cartPage){
        const quantity=document.getElementById("quantity"), slot=document.getElementById("purchase-quantity");
        const actions=document.getElementById("purchase-actions");
        if(!quantity||!slot||!actions)throw new Error("주문 선택 영역을 확인하지 못했습니다.");
        const label=quantity.closest("label");quantity.setAttribute("aria-label","주문 수량");
        slot.replaceChildren(label);
        actions.replaceChildren(node.querySelector(".commerce-actions"));
        document.getElementById("add").textContent="장바구니";
        document.getElementById("single").textContent="주문하기";
        node.querySelector(".commerce-choice").hidden=true;
        node.querySelector("h2").hidden=true;
      }
      const options=document.getElementById("variation");
      if(!cartPage&&options){
        const sync=button=>{
          const option=Array.from(options.options).find(v=>v.textContent.split(" · ")[0]===button.textContent.trim());
          if(option&&!option.disabled){options.value=option.value;options.dispatchEvent(new Event("change",{bubbles:true}));}
        };
        document.getElementById("detail-variants")?.addEventListener("click",event=>{
          const button=event.target.closest("button.variant-option");
          if(button&&!button.disabled)sync(button);
        });
        options.addEventListener("change",()=>{
          const label=options.selectedOptions[0]?.textContent.split(" · ")[0];
          const buttons=Array.from(document.querySelectorAll("#detail-variants button.variant-option"));
          buttons.forEach(button=>button.setAttribute("aria-pressed",String(button.textContent.trim()===label)));
          const button=buttons.find(v=>v.textContent.trim()===label);
          if(button)document.getElementById("detail-variants").dispatchEvent(new CustomEvent("shop:variant-selected",{detail:{variantId:button.dataset.variantId}}));
        });
      }
      if(!cartPage&&options&&options.selectedOptions[0]&&!options.selectedOptions[0].disabled)options.dispatchEvent(new Event("change",{bubbles:true}));
      const script=document.createElement("script");
      script.src="/__order-dev/guest-chat.js";
      script.defer=true;
      document.body.appendChild(script);
    }catch(error){
      target.replaceChildren();
      const p=document.createElement("p");
      p.className="commerce-load-error";
      p.textContent=error?.message||"주문 기능을 불러오지 못했습니다.";
      target.appendChild(p);
    }
  };
  load();
})();
