"use strict";
(() => {
  const commercePath = path => (window.location.hostname === "bokstory.duckdns.org" ? "/shopping" : "/__order-dev") + path;
  const by = id => document.getElementById(id);
  const dialog = by("shop-chat");
  if (!dialog) return;

  let activeProductId = dialog.dataset.context || "";
  const log = by("shop-chat-messages");
  const error = by("shop-chat-error");
  const question = by("shop-chat-question");
  const form = by("shop-chat-form");
  const context = JSON.parse(dialog.dataset.pageContext || "{}");
  const storage = "aicc-shared-chat-v2";
  let busy = false, authBusy = false, greeted = false, lastContext = "", epoch = 0, provider = null, turns = [], pendingReplies = [];

  const ready = fetch(commercePath("/chat/history/session"), {credentials: "same-origin"})
    .then(response => { if (!response.ok) throw Error("문의 기록을 준비하지 못했습니다."); return true; })
    .catch(() => false);
  const save = () => {
    try { sessionStorage.setItem(storage, JSON.stringify({pageKey: context.key || context.type || "home", context: lastContext, turns: turns.slice(-100), pending: pendingReplies.slice(-20)})); } catch (_) {}
  };
  try {
    const state = JSON.parse(sessionStorage.getItem(storage) || "null");
    if (state && Array.isArray(state.turns) && state.turns.length <= 100 && state.turns.every(turn => typeof turn.text === "string" && turn.text.length <= 3000 && typeof turn.customer === "boolean")) {
      turns = state.turns;
      lastContext = typeof state.context === "string" ? state.context : "";
      if (Array.isArray(state.pending)) pendingReplies = state.pending.filter(item => /^[a-f0-9]{48}$/.test(item.token || "") && typeof item.pid === "string" && typeof item.name === "string" && item.name.length <= 300).slice(-20);
      const pageKey = context.key || context.type || "home";
      for (const turn of turns) say(turn.text, turn.customer, false);
      greeted = turns.length > 0;
    }
  } catch (_) {}

  function say(text, customer = false, persist = true) {
    const bubble = document.createElement("p");
    bubble.textContent = text;
    bubble.className = customer ? "customer" : "assistant";
    log.appendChild(bubble);
    if (persist) {
      turns.push({text: text.slice(0, 3000), customer});
      turns = turns.slice(-100);
      save();
    }
    bubble.scrollIntoView({block: "nearest"});
  }

  function selectedSummary() {
    return activeProductId && activeProductId === dialog.dataset.context ? context.product || null : null;
  }

  function pageHelp(message) {
    const answers = {
      home: "상품 카테고리와 HOT·UPDATE 목록에서 원하는 상품을 찾아보세요. 상품 상세에서 챗봇을 열면 해당 상품 정보가 자동 연결됩니다.",
      search: "검색 결과에서 상품을 선택해 상세 페이지로 이동하면 사이즈·소재 등 해당 상품 기준으로 문의할 수 있어요.",
      cart: "장바구니의 상품·수량을 확인한 뒤 주문하기를 누르세요. 상품별 질문은 해당 상품 상세 페이지에서 챗봇을 열면 자동 연결됩니다.",
      orders: "주문번호를 입력한 뒤 배송 조회 추천 질문을 누르면 주문 상태를 확인할 수 있어요. 교환·환불은 해당 주문 내역을 확인해 주세요.",
      checkout: "로그인 또는 비회원 주문을 선택해 진행하세요. 주소 검색과 최종 주문 금액은 비회원 주문 화면에서 확인할 수 있어요.",
      "guest-order": "휴대폰 인증을 완료한 뒤 배송정보를 입력하고 최종 주문 내용을 확인해 주세요."
    };
    say(message, true);
    say(answers[context.type] || "상품 상세 페이지에서 챗봇을 열면 해당 상품 정보와 함께 문의할 수 있어요.");
  }

  function showSuggestions(items) {
    const target = by("shop-chat-suggestions");
    target.replaceChildren();
    for (const item of (items || []).slice(0, 4)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "shop-chat-suggestion";
      button.textContent = item.label;
      button.addEventListener("click", () => {
        error.textContent = "";
        if (item.action === "order_status") {
          const numberField = by("orders-number");
          const number = numberField?.value.trim() || "";
          if (!/^[0-9]{1,12}$/.test(number)) {
            error.textContent = "주문 내역 화면에서 주문번호를 먼저 입력해 주세요.";
            dialog.close();
            numberField?.focus();
            return;
          }
          question.value = "주문 " + number + " 조회";
        } else if (item.action === "page_help" || !activeProductId) {
          pageHelp(item.text || item.label);
          return;
        } else {
          question.value = item.text || "";
        }
        form.requestSubmit();
      });
      target.appendChild(button);
    }
  }

  function presentContext() {
    const product = selectedSummary();
    const subtitle = by("shop-chat-page-label");
    const tag = by("shop-chat-tag");
    const key = product && activeProductId ? "product:" + activeProductId : (context.key || context.type || "home");
    tag.textContent = product && activeProductId ? "#" + product.name : context.title || "agachichi 쇼핑 안내";
    subtitle.textContent = product && activeProductId ? product.name : context.title || "쇼핑 안내";
    showSuggestions(product && activeProductId ? product.questions : context.questions);
    if (greeted && lastContext === key) return;

    if (product) {
      const lines = [product.name, [product.category, product.price].filter(Boolean).join(" · "), ""];
      if (product.options?.length) lines.push("옵션 · " + product.options.join(", "));
      if (product.description) lines.push("상품 설명 · " + product.description);
      lines.push("추천 질문을 누르면 바로 전송돼요. 직접 질문도 입력할 수 있어요.");
      say("현재 보고 계신 상품 정보예요.\n" + lines.filter(Boolean).join("\n"));
    } else {
      say((context.summary || context.title || "쇼핑 안내") + "\n추천 질문을 누르면 바로 전송돼요. 직접 질문도 입력할 수 있어요.");
    }
    greeted = true;
    lastContext = key;
    save();
  }

  const open = productId => {
    if (productId && /^[A-Za-z0-9_-]{1,128}$/.test(productId) && activeProductId !== productId) {
      activeProductId = productId;
      provider = null;
      epoch++;
      greeted = false;
    }
    presentContext();
    if (!dialog.open) dialog.showModal();
    question.placeholder = "질문을 입력해 주세요"
  };

  by("shop-chat-launcher").onclick = () => open(dialog.dataset.context);
  by("shop-chat-close").onclick = () => dialog.close();
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-shop-chat-product]");
    if (button) open(button.dataset.shopChatProduct);
  });
  const resolve = async (productId, stamp) => {
    if (provider) return provider;
    const response = await fetch(commercePath("/chat/embed/") + encodeURIComponent(productId), {credentials: "same-origin", headers: {Accept: "text/html"}});
    if (!response.ok || !(response.headers.get("content-type") || "").includes("text/html")) throw Error("상품 정보를 불러오지 못했습니다.");
    const text = await response.text();
    if (/<script\b/i.test(text)) throw Error("상품 정보를 확인하지 못했습니다.");
    const template = document.createElement("template");
    template.innerHTML = text;
    const node = template.content.firstElementChild;
    const value = node?.dataset.guestShopProduct;
    if (!node?.matches("[data-guest-shop-product]") || !/^\d{1,10}$/.test(value || "") || stamp !== epoch) throw Error("상품 연결을 다시 확인해 주세요.");
    provider = value;
    return value;
  };

  const headers = async () => {
    const response = await fetch("/shopping/auth/session", {credentials: "same-origin"});
    const csrf = response.headers.get("X-CSRF-Token");
    if (!response.ok || !csrf) throw Error("휴대폰 인증이 필요합니다.");
    return {"Content-Type": "application/json", "X-CSRF-Token": csrf};
  };
  const recent = async () => {
    if (!await ready) throw Error("문의 기록을 준비하지 못했습니다.");
    const requestHeaders = await headers();
    const link = await fetch(commercePath("/chat/history/link"), {method: "POST", credentials: "same-origin", headers: requestHeaders});
    if (!link.ok) throw Error("문의 기록을 연결하지 못했습니다.");
    const response = await fetch(commercePath("/chat/history"), {credentials: "same-origin"});
    if (!response.ok) throw Error("최근 문의를 확인하지 못했습니다.");
    const data = await response.json(), target = by("shop-chat-recent");
    target.replaceChildren();
    const heading = document.createElement("h3"); heading.textContent = "최근 30일 문의"; target.appendChild(heading);
    if (!data.items.length) { const empty = document.createElement("p"); empty.textContent = "아직 문의 내역이 없습니다."; target.appendChild(empty); }
    for (const item of data.items) { const bubble = document.createElement("p"); bubble.textContent = "상품 #" + item.product_id + " · " + new Date(item.created_at * 1000).toLocaleString() + "\n문의: " + item.question + "\n답변: " + item.answer; target.appendChild(bubble); }
    target.hidden = false;
    by("shop-chat-phone").hidden = true;
  };
  const authRun = async callback => {
    if (authBusy) return;
    authBusy = true; error.textContent = "";
    try { await callback(); } catch (exception) { error.textContent = exception.message || "인증 상태를 확인해 주세요."; }
    finally { authBusy = false; }
  };
  by("shop-chat-history").onclick = () => authRun(async () => {
    try { await headers(); } catch (_) { by("shop-chat-phone").hidden = false; return; }
    await recent();
  });
  by("shop-chat-sms").onclick = () => authRun(async () => {
    if (!by("shop-chat-consent").checked) throw Error("인증 문자 수신에 동의해 주세요.");
    const response = await fetch(commercePath("/phone/start"), {method: "POST", credentials: "same-origin", headers: {"Content-Type": "application/json"}, body: JSON.stringify({phone: by("shop-chat-phone-number").value, consent: true})});
    const data = await response.json();
    if (!response.ok) throw Error(data.message || "인증 문자를 요청하지 못했습니다.");
    error.textContent = data.message;
  });
  by("shop-chat-verify").onclick = () => authRun(async () => {
    const requestHeaders = {"Content-Type": "application/json"};
    try { Object.assign(requestHeaders, await headers()); } catch (_) {}
    const code = by("shop-chat-code").value; by("shop-chat-code").value = "";
    const response = await fetch(commercePath("/phone/check"), {method: "POST", credentials: "same-origin", headers: requestHeaders, body: JSON.stringify({code})});
    if (!response.ok) throw Error("인증번호와 요청 상태를 확인해 주세요.");
    by("shop-chat-phone-number").value = "";
    await recent();
  });

  const watch = (token, productId, name) => {
    if (!pendingReplies.some(item => item.token === token)) { pendingReplies.push({token, pid: productId, name}); save(); }
    let count = 0;
    const check = async () => {
      if (++count > 120) return;
      try {
        const response = await fetch(commercePath("/chat/inquiries/") + encodeURIComponent(token), {credentials: "same-origin"});
        if (!response.ok) return;
        const data = await response.json();
        if (data.answer) { pendingReplies = pendingReplies.filter(item => item.token !== token); say("#" + name + " · 운영자 답변: " + data.answer); return; }
      } catch (_) {}
      setTimeout(check, 5000);
    };
    setTimeout(check, 5000);
  };
  form.onsubmit = async event => {
    event.preventDefault();
    if (busy) return;
    const message = question.value.trim();
    const orderMatch = message.match(/^(?:주문|주문조회|배송|배송조회|입금|거래안내)\s*#?\s*([1-9][0-9]{0,18})(?:\s*(?:조회|확인|상태|안내))?$/);
    if (orderMatch) {
      busy = true; error.textContent = "";
      try {
        const requestHeaders = await headers();
        const response = await fetch(commercePath("/chat/orders/notices"), {method: "POST", credentials: "same-origin", headers: requestHeaders, body: JSON.stringify({order_number: orderMatch[1]})});
        const data = await response.json();
        if (!response.ok) throw Error(data.message || "주문을 확인하지 못했습니다.");
        log.querySelectorAll("[data-order-notice]").forEach(node => node.remove());
        for (const item of data.messages) { const bubble = document.createElement("p"); bubble.dataset.orderNotice = item.id; bubble.textContent = item.message; log.appendChild(bubble); }
        question.value = "";
      } catch (exception) { error.textContent = exception.message || "주문을 확인하지 못했습니다."; if (error.textContent.includes("인증")) by("shop-chat-phone").hidden = false; }
      finally { busy = false; }
      return;
    }

    if (!message) return;
    const productId = activeProductId;
    if (!productId) { question.value = ""; pageHelp(message); return; }
    const productName = context.product?.name || "상품", stamp = epoch;
    busy = true; by("shop-chat-send").disabled = true; error.textContent = ""; say(message, true);
    try {
      if (!await ready) throw Error("문의 기록 연결이 불안정합니다. 새로고침 후 다시 문의해 주세요.");
      const id = await resolve(productId, stamp);
      const response = await fetch(commercePath("/chat/inquiry"), {method: "POST", credentials: "same-origin", headers: {"Content-Type": "application/json"}, body: JSON.stringify({product_id: id, message})});
      const data = await response.json();
      if (!response.ok) throw Error(data.message || "문의에 답변하지 못했습니다.");
      say("#" + productName + " · " + data.message);
      question.value = "";
      if (data.inquiry_token) watch(data.inquiry_token, productId, productName);
      if (data.action === "START_ORDER") { const link = document.createElement("a"); link.href = "/homepage/storefront/product/" + encodeURIComponent(productId) + "#commerce-panel"; link.textContent = "이 상품 주문하기"; log.appendChild(link); }
    } catch (exception) { error.textContent = exception.message || "잠시 후 다시 문의해 주세요."; }
    finally { busy = false; by("shop-chat-send").disabled = false; }
  };

  by("shop-chat-tag").textContent = context.product?.name ? "#" + context.product.name : context.title || "쇼핑 안내";
  for (const item of [...pendingReplies]) watch(item.token, item.pid, item.name);
})();
