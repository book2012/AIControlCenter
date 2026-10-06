"use strict";

(() => {
  const target=document.getElementById("commerce-panel");
  if(!target)return;
  const demo=target.dataset.demoProduct||"";
  if(!/^oc-demo-(top|bottom|outer|dress|bag)-0001$/.test(demo)){
    target.textContent="주문 기능을 사용할 수 없습니다.";
    return;
  }
  const load=async()=>{
    try{
      const response=await fetch("/__order-dev/chat/embed/"+encodeURIComponent(demo),{credentials:"same-origin",headers:{Accept:"text/html"}});
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
