(() => {
  "use strict";
  const opener = document.querySelector(".header-search");
  const actions = document.querySelector(".header-actions");
  if (actions) {
    let login = actions.querySelector(".header-login");
    if (!login) {
      login = document.createElement("a");
      login.className = "header-login";
      login.href = "/my-account/";
      login.textContent = "LOGIN";
      login.setAttribute("aria-label", "로그인");
      opener?.insertAdjacentElement("afterend", login);
    }
    actions.querySelectorAll(".header-signup").forEach(item => item.remove());
    const orders = actions.querySelector(".header-orders");
    let profile = actions.querySelector(".header-profile");
    if (login) {
      login.addEventListener("click", event => {
        if (login.dataset.authenticated === "true" && !window.confirm("로그아웃하시겠습니까?")) event.preventDefault();
      });
      fetch("/wp-admin/admin-ajax.php?action=aicc_account_navigation", {
        credentials: "same-origin", cache: "no-store", headers: {Accept: "application/json"}
      }).then(response => {
        if (!response.ok) throw new Error("account state unavailable");
        return response.json();
      }).then(result => {
        if (!result.success || !result.data) return;
        const member = result.data.authenticated === true;
        login.dataset.authenticated = member ? "true" : "false";
        login.textContent = member ? "LOG OUT" : "LOGIN";
        login.href = member ? result.data.logoutUrl : "/my-account/";
        login.setAttribute("aria-label", member ? "로그아웃" : "로그인");
        login.classList.toggle("header-logout", member);
        if (orders) {
          orders.href = member ? "/my-account/orders/" : "/homepage/storefront/my-orders";
          orders.textContent = member ? "주문내역" : "비회원 주문 조회";
          orders.setAttribute("aria-label", member ? "주문내역" : "비회원 주문 조회");
        }
        if (member && orders && !profile) {
          profile = document.createElement("a");
          profile.className = "header-profile";
          profile.href = "/my-account/";
          profile.textContent = "내 정보";
          profile.setAttribute("aria-label", "내 정보");
          orders.insertAdjacentElement("afterend", profile);
        } else if (!member && profile) {
          profile.remove();
        }
      }).catch(() => {});
    }
  }
  if (!opener || !window.HTMLDialogElement) return;
  const dialog = document.createElement("dialog");
  dialog.className = "header-search-dialog";
  dialog.setAttribute("aria-labelledby", "header-search-title");
  dialog.innerHTML = `<div class="header-search-heading"><h2 id="header-search-title">상품 검색</h2><button type="button" class="search-close" aria-label="검색 닫기">닫기 ×</button></div><form class="header-search-form"><label for="header-search-input">어떤 옷을 찾으세요?</label><div><input id="header-search-input" type="search" name="q" maxlength="100" placeholder="상품명 · 색상 · 스타일" required><button type="submit" class="solid-button">검색</button></div></form><p class="header-search-status" role="status" aria-live="polite"></p><ul class="product-grid header-search-results" aria-label="검색 결과"></ul>`;
  document.body.append(dialog);
  const input = dialog.querySelector("input"), status = dialog.querySelector(".header-search-status"), results = dialog.querySelector("ul");
  let controller;
  opener.setAttribute("aria-haspopup", "dialog");
  opener.addEventListener("click", event => { event.preventDefault(); dialog.showModal(); input.focus(); });
  dialog.querySelector(".search-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
  dialog.addEventListener("keydown", event => { if (event.key === "Escape") { event.preventDefault(); dialog.close(); } });
  dialog.addEventListener("close", () => { controller?.abort(); opener.focus(); });
  dialog.querySelector("form").addEventListener("submit", async event => {
    event.preventDefault(); const query = input.value.trim(); if (!query) { input.focus(); return; }
    controller?.abort(); const request = controller = new AbortController();
    status.textContent = "검색 중…"; results.replaceChildren();
    try {
      const response = await fetch("/homepage/storefront/search?" + new URLSearchParams({q: query}), {signal: request.signal});
      if (!response.ok) throw Error("search unavailable");
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const cards = page.querySelectorAll("#product-grid > .product-card");
      if (request !== controller || !dialog.open) return;
      results.replaceChildren(...Array.from(cards, card => document.importNode(card, true)));
      status.textContent = cards.length ? (page.querySelector("#product-count")?.textContent || `검색 결과 ${cards.length}개`) : "검색 결과가 없습니다. 다른 검색어를 입력해주세요.";
    } catch (error) { if (error.name !== "AbortError" && request === controller) status.textContent = "검색을 불러오지 못했습니다. 다시 시도해주세요."; }
  });
})();
