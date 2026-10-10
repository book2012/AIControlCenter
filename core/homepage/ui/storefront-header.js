(() => {
  "use strict";
  const opener = document.querySelector(".header-search");
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
