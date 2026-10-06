"use strict";

(() => {
  const PAGE_SIZE = 12;
  const FETCH_TIMEOUT_MS = 8000;
  const HOME_PATH = "/homepage/storefront";
  const LIST_PATH = `${HOME_PATH}/search`;
  const DETAIL_PREFIX = `${HOME_PATH}/product/`;
  const byId = (id) => document.getElementById(id);
  const media = new Map();
  try {
    const mapping = JSON.parse(byId("storefront-media")?.textContent || "{}");
    for (const [id, path] of Object.entries(mapping)) {
      const match = /^oc-demo-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/.exec(id);
      if (match && path === `/homepage/assets/storefront/catalog/${match[1]}/${id}.jpg`) media.set(id, path);
    }
  } catch { /* Native links remain available; inactive legacy media is never used. */ }
  const isDetail = Boolean(byId("detail-view"));
  const isHome = Boolean(byId("home-view"));
  const state = { category: "", query: "", collection: "", page: 1 };
  const badges = new Map();
  const categories = new Map();
  const categoryLabels = { new: "신상품", best: "인기 상품", sale: "할인 상품", top: "상의", bottom: "하의", outer: "아우터", dress: "원피스", bag: "가방", acc: "액세서리",
    "women-tops": "상의", "women-bottoms": "하의", "women-outer": "아우터", "women-dresses": "원피스", "women-bags": "가방", "women-accessories": "액세서리" };
  let requestVersion = 0;
  let categoryVersion = 0;
  let activeController;
  let categoryController;

  async function readJSON(path, signal) {
    // Every browser data request terminates at an explicit canonical GET route.
    const url = new URL(path, window.location.origin);
    if (url.origin !== window.location.origin || !/^\/shopping\/(products(?:\/[A-Za-z0-9_-]{1,128})?|search|categories)$/.test(url.pathname)) {
      throw new Error("Invalid read path");
    }
    const response = await fetch(url.pathname + url.search, {
      method: "GET", credentials: "same-origin", redirect: "error",
      headers: { Accept: "application/json" }, signal,
    });
    if (!response.ok) {
      const error = new Error("Product read unavailable");
      error.status = response.status;
      throw error;
    }
    return response.json();
  }

  function parseState(search) {
    const params = new URLSearchParams(search);
    const rawPage = params.get("page") || "1";
    const page = /^\d+$/.test(rawPage) ? Number(rawPage) : 1;
    return { category: (params.get("category") || "").trim().slice(0, 100),
      query: (params.get("q") || "").trim().slice(0, 200),
      collection: (params.get("collection") || "").trim().toLowerCase().slice(0, 40),
      page: Number.isSafeInteger(page) && page > 0 ? page : 1 };
  }

  function homeURL(value) {
    const params = new URLSearchParams();
    if (["hot", "sale", "update"].includes(value.collection)) params.set("collection", value.collection);
    else if (value.category) params.set("category", value.category);
    if (value.page && value.page > 1) params.set("page", String(value.page));
    return `${HOME_PATH}${params.size ? `?${params}` : ""}`;
  }

  function listingURL(value) {
    const params = new URLSearchParams();
    if (value.category) params.set("category", value.category);
    if (value.query) params.set("q", value.query);
    if (value.page > 1) params.set("page", String(value.page));
    return `${LIST_PATH}${params.size ? `?${params}` : ""}`;
  }

  function returnURL() {
    const raw = new URLSearchParams(window.location.search).get("return_to");
    if (!raw || !raw.startsWith("/")) return listingURL(parseState(""));
    try {
      const url = new URL(raw, window.location.origin);
      if (url.origin !== window.location.origin || ![HOME_PATH, LIST_PATH].includes(url.pathname) || url.username || url.password || url.hash) return listingURL(parseState(""));
      if (url.pathname === HOME_PATH) return homeURL({ category: url.searchParams.get("category") || "", collection: url.searchParams.get("collection") || "" });
      // Old SHOP_UI_002 filtered home links now resolve to the discovery page.
      return listingURL(parseState(url.search));
    } catch { return listingURL(parseState("")); }
  }

  function productURL(productId) {
    const params = new URLSearchParams({ return_to: isHome ? homeURL(state) : listingURL(state) });
    return `${DETAIL_PREFIX}${encodeURIComponent(productId)}?${params}`;
  }

  function photoURL(product) {
    // Presentation mapping is repository-owned; product data stays canonical.
    const demo = /^oc-demo-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/.exec(product.id);
    const upload = /^ag-upload-(top|bottom|outer|dress|bag|acc)-[0-9]{4}$/.exec(product.id);
    if (product.source === "demo" && demo && product.category.toLowerCase() === demo[1] && media.has(product.id)) return media.get(product.id);
    if (product.source === "dev_upload" && upload && product.category.toLowerCase() === upload[1] && media.has(product.id)) return media.get(product.id);
    return null;
  }

  function setPhoto(container, product) {
    const image = container.querySelector("img");
    const fallback = container.querySelector(".photo-fallback");
    const unavailable = () => { image.hidden = true; image.removeAttribute("src"); fallback.hidden = false; };
    image.alt = product.name;
    image.onerror = unavailable;
    const photo = photoURL(product);
    image.hidden = !photo;
    fallback.hidden = Boolean(photo);
    if (photo) image.src = photo;
    else unavailable();
  }

  function priceLabel(product) {
    // Zero is reserved for a DEV upload awaiting operator price input.
    if (product.source === "dev_upload" && /^0(?:\.0+)?$/.test(product.price)) return "가격 준비 중";
    const [whole, fraction] = product.price.split(".");
    const amount = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (fraction === undefined ? "" : `.${fraction}`);
    return product.currency === "KRW" ? `${amount}원` : `${product.currency} ${amount}`;
  }

  function validateProduct(product) {
    if (!product || !/^[A-Za-z0-9_-]{1,128}$/.test(product.id) || typeof product.id !== "string" ||
        typeof product.name !== "string" || !product.name.trim() || typeof product.category !== "string" ||
        typeof product.description !== "string" || typeof product.source !== "string" ||
        typeof product.price !== "string" || !/^\d+(\.\d+)?$/.test(product.price) ||
        typeof product.currency !== "string" || !/^[A-Z]{3}$/.test(product.currency) ||
        typeof product.in_stock !== "boolean" || (product.image_url !== null && typeof product.image_url !== "string") ||
        !Array.isArray(product.variants) || product.variants.some((variant) => !variant || typeof variant.id !== "string" ||
          !variant.id || typeof variant.label !== "string" || !variant.label.trim() || /\s/.test(variant.label) ||
          typeof variant.option_type !== "string" || !variant.option_type.trim() || typeof variant.available !== "boolean")) {
      throw new Error("Invalid product response");
    }
    return product;
  }

  function renderVariants(variants) {
    const target = byId("detail-variants");
    if (!target) return;
    target.replaceChildren();
    if (!variants.length) {
      const empty = document.createElement("p"); empty.className = "variant-empty"; empty.textContent = "판매 옵션 준비 중입니다.";
      target.append(empty); return;
    }
    const group = document.createElement("div"); group.className = "variant-options"; group.setAttribute("role", "group"); group.setAttribute("aria-label", "사이즈 선택");
    variants.forEach((variant, index) => {
      const button = document.createElement("button"); button.type = "button"; button.className = "variant-option"; button.dataset.variantId = variant.id;
      button.textContent = variant.label; button.disabled = !variant.available; button.setAttribute("aria-pressed", "false"); group.append(button);
    });
    target.append(group);
  }

  function validatePage(payload, page, size) {
    if (!payload || !Array.isArray(payload.items) || payload.items.length > size ||
        !Number.isSafeInteger(payload.total) || payload.total < 0 || payload.page !== page || payload.page_size !== size ||
        payload.items.length !== Math.min(size, Math.max(0, payload.total - (page - 1) * size)) ||
        new Set(payload.items.map((item) => item && item.id)).size !== payload.items.length) {
      throw new Error("Invalid collection response");
    }
    payload.items.forEach(validateProduct);
    return payload;
  }

  function productCard(product, membership) {
    const card = byId("product-template").content.firstElementChild.cloneNode(true);
    card.dataset.productId = product.id;
    const link = card.querySelector(".product-link");
    link.href = productURL(product.id);
    link.setAttribute("aria-label", "상품 이미지와 해시태그 미리보기");
    setPhoto(card.querySelector(".product-photo"), product);
    card.querySelector(".product-tags").textContent = presentationTags(product);
    return card;
  }

  function presentationTags(product) {
    const category = String(product.category || "").toLowerCase();
    const tags = { top: ["#상의", "#데일리", "#미니멀"], bottom: ["#팬츠", "#클래식", "#심플"], outer: ["#아우터", "#소프트", "#가을무드"], dress: ["#원피스", "#페미닌", "#데일리룩"], bag: ["#가방", "#미니멀", "#데일리백"], acc: ["#액세서리", "#포인트", "#데일리"] };
    const result = tags[category] || ["#아가치치", "#데일리"];
    const name = String(product.name || "");
    if (name.includes("블라우스")) result[0] = "#블라우스";
    else if (name.includes("셔츠")) result[0] = "#셔츠";
    if (name.includes("오버핏") || name.includes("와이드")) result[1] = "#오버핏";
    else if (name.includes("니트") || name.includes("가디건")) result[1] = "#니트";
    return result.slice(0, 3).join(" ");
  }

  function categoryLabel() {
    return state.category ? (categories.get(state.category)?.label || "선택한 카테고리") : "전체 상품";
  }

  function updateControls(syncQuery = true) {
    document.querySelectorAll("[data-category]").forEach((button) => {
      if (button.dataset.category === state.category) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
      button.href = listingURL({ ...state, category: button.dataset.category, page: 1 });
    });
    if (syncQuery) byId("search-input").value = state.query;
    byId("search-category").value = state.category;
    document.querySelectorAll("[data-query]").forEach((link) => {
      link.href = listingURL({ ...state, query: link.dataset.query, page: 1 });
    });
    byId("search-context").textContent = `${categoryLabel()} 안에서 검색합니다.`;
    byId("active-conditions").textContent = [
      `카테고리: ${categoryLabel()}`, state.query ? `검색어: ‘${state.query}’` : "",
    ].filter(Boolean).join(" · ");
    byId("clear-filters").hidden = !state.category && !state.query;
  }

  function beginRead() {
    const version = ++requestVersion;
    if (activeController) activeController.abort();
    const controller = new AbortController();
    activeController = controller;
    const timeout = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    return { version, controller, timeout };
  }

  async function loadProducts() {
    const { version, controller, timeout } = beginRead();
    const requested = { ...state };
    const grid = byId("product-grid");
    grid.setAttribute("aria-busy", "true");
    grid.replaceChildren();
    byId("catalog-status").textContent = "상품을 불러오는 중…";
    byId("product-count").textContent = "상품을 불러오는 중…";
    byId("catalog-note").textContent = "상품 미리보기";
    byId("retry").hidden = true;
    document.querySelector(".pagination").hidden = true;
    updateControls();
    const params = new URLSearchParams({ page: String(requested.page), page_size: String(PAGE_SIZE) });
    if (requested.category) params.set("category", categories.get(requested.category)?.id || requested.category);
    if (requested.query) params.set("q", requested.query);
    const endpoint = requested.category || requested.query ? "/shopping/search" : "/shopping/products";
    try {
      if (requested.category && !categories.has(requested.category)) throw new Error("Unknown category");
      const response = await readJSON(`${endpoint}?${params}`, controller.signal);
      if (version !== requestVersion) return;
      const payload = validatePage(response, requested.page, PAGE_SIZE);
      grid.replaceChildren(...payload.items.map((product) => productCard(product)));
      byId("product-count").textContent = `상품 ${payload.total}개`;
      byId("catalog-note").textContent = payload.items.length && payload.items.every((item) => item.source === "demo") ? "데모 상품 · 미리보기 전용" : "상품 미리보기";
      byId("catalog-status").textContent = !payload.total
        ? (state.query || state.category ? "조건에 맞는 상품이 없습니다. 검색어나 카테고리를 바꿔 보세요." : "아직 등록된 상품이 없습니다.")
        : !payload.items.length ? "이 페이지에 상품이 없습니다. 이전 페이지로 이동해 주세요."
        : state.query ? `${categoryLabel()} · ‘${state.query}’ 검색 결과` : `${categoryLabel()}을 둘러보세요.`;
      const pages = Math.max(1, Math.ceil(payload.total / PAGE_SIZE));
      document.querySelector(".pagination").hidden = pages <= 1 && state.page === 1;
      byId("page-label").textContent = `${state.page} / ${pages} 페이지`;
      byId("previous-page").hidden = state.page <= 1;
      byId("previous-page").href = listingURL({ ...state, page: Math.max(1, state.page - 1) });
      byId("next-page").hidden = state.page >= pages;
      byId("next-page").href = listingURL({ ...state, page: state.page + 1 });
    } catch (error) {
      if (version !== requestVersion) return;
      grid.replaceChildren();
      byId("product-count").textContent = "상품을 불러오지 못했습니다";
      byId("catalog-status").textContent = error && error.name === "AbortError"
        ? "응답 시간이 길어지고 있습니다. 다시 시도해 주세요."
        : "상품을 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.";
      byId("retry").hidden = false;
    } finally {
      window.clearTimeout(timeout);
      if (version === requestVersion) grid.setAttribute("aria-busy", "false");
    }
  }

  function validateCategories(payload) {
    if (!payload || !Array.isArray(payload.items) || payload.items.some((item) => !item || typeof item.id !== "string" || !item.id || item.id.length > 100 || typeof item.slug !== "string" || typeof item.name !== "string") ||
        new Set(payload.items.map((item) => item.id)).size !== payload.items.length) throw new Error("Invalid categories");
    return payload.items.filter((item) => ![item.slug, item.name].some((value) => value.trim().toLowerCase() === "hot"))
      .map((item) => ({ ...item, label: categoryLabels[item.slug.toLowerCase()] || categoryLabels[item.name.toLowerCase()] || item.name }));
  }

  async function loadHome() {
    const { version, controller, timeout } = beginRead();
    byId("home-retry").hidden = true;
    byId("feed-status").textContent = "상품을 불러오는 중…";
    byId("home-feed").replaceChildren();
    try {
      const available = validateCategories(await readJSON("/shopping/categories", controller.signal));
      if (version !== requestVersion) return;
      const requested = { ...state };
      const grid = byId("home-feed");
      let products = [];
      if (requested.collection === "hot" || requested.collection === "sale") {
        products = [];
      } else if (requested.collection === "update") {
        const update = await readJSON("/shopping/search?category=new&page=1&page_size=100", controller.signal);
        products = validatePage(update, 1, 100).items;
      } else {
        const category = available.find((item) => item.slug === requested.category);
        const params = new URLSearchParams({ page: "1", page_size: "100" });
        if (category) params.set("category", category.id);
        const result = await readJSON(`${category ? "/shopping/search" : "/shopping/products"}?${params}`, controller.signal);
        products = validatePage(result, 1, 100).items;
        if (!category && result.total > 100) {
          const next = await readJSON("/shopping/products?page=2&page_size=100", controller.signal);
          products = products.concat(validatePage(next, 2, 100).items);
        }
      }
      if (version !== requestVersion) return;
      grid.replaceChildren(...products.map((product) => productCard(product)));
      byId("feed-count").textContent = `상품 ${products.length}개`;
      byId("feed-status").textContent = products.length ? "" : requested.collection === "sale" ? "SALE 상품이 없습니다. 현재 canonical 할인 데이터가 없습니다." : requested.collection === "hot" ? "HOT 상품이 없습니다. 명시된 HOT 컬렉션이 없습니다." : "조건에 맞는 상품이 없습니다.";
    } catch {
      if (version !== requestVersion) return;
      byId("feed-status").textContent = "상품을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
      byId("home-retry").hidden = false;
    } finally {
      window.clearTimeout(timeout);
      if (version === requestVersion) byId("home-feed").setAttribute("aria-busy", "false");
    }
  }

  async function loadCategories() {
    const version = ++categoryVersion;
    badges.clear();
    if (categoryController) categoryController.abort();
    const controller = new AbortController();
    categoryController = controller;
    const timeout = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const payload = await readJSON("/shopping/categories", controller.signal);
      if (version !== categoryVersion) return;
      const available = validateCategories(payload);
      categories.clear();
      const buttons = [];
      for (const item of available) {
        categories.set(item.slug, item);
        const button = document.createElement("a");
        button.href = listingURL({ ...state, category: item.slug, page: 1 });
        button.dataset.category = item.slug;
        button.dataset.categoryId = item.id;
        button.textContent = item.label;
        buttons.push(button);
      }
      const all = byId("category-nav").querySelector('[data-category=""]');
      byId("category-nav").replaceChildren(all, ...buttons);
      byId("category-status").textContent = "";
      updateControls(false);
      // Source membership only, at most one bounded page per supported collection.
      const results = await Promise.allSettled(["best", "new"].map(async (slug) => {
        const category = [...categories.values()].find((item) => item.slug === slug);
        if (!category) return null;
        const params = new URLSearchParams({ category: category.id, page: "1", page_size: "100" });
        const result = await readJSON(`/shopping/search?${params}`, controller.signal);
        return { slug, items: validatePage(result, 1, 100).items };
      }));
      if (version !== categoryVersion) return;
      badges.clear();
      for (const result of results) {
        if (result.status !== "fulfilled" || !result.value) continue;
        for (const item of result.value.items) {
          if (!badges.has(item.id)) badges.set(item.id, result.value.slug.toUpperCase());
        }
      }
    } catch {
      if (version === categoryVersion) byId("category-status").textContent = "카테고리를 불러오지 못했습니다. 전체 상품과 검색을 이용해 주세요.";
    } finally { window.clearTimeout(timeout); }
  }

  function select(changes) {
    Object.assign(state, changes);
    const url = listingURL(state);
    if (url !== window.location.pathname + window.location.search) window.history.pushState(null, "", url);
    loadProducts();
  }

  async function loadProduct() {
    const { version, controller, timeout } = beginRead();
    const back = returnURL();
    byId("back-to-list").href = back;
    byId("back-to-list").textContent = back === HOME_PATH ? "← 홈으로" : "← 상품 목록으로";
    const content = byId("detail-content");
    content.setAttribute("aria-busy", "true");
    byId("detail-name").textContent = "상품을 불러오는 중입니다";
    byId("detail-status").textContent = "상품을 불러오는 중…";
    byId("detail-price").textContent = "";
    byId("detail-availability").textContent = "";
    byId("detail-description").textContent = "";
    byId("description-section").hidden = true;
    byId("detail-photo").hidden = true;
    byId("detail-retry").hidden = true;
    try {
      const id = decodeURIComponent(window.location.pathname.slice(DETAIL_PREFIX.length));
      if (!/^[A-Za-z0-9_-]{1,128}$/.test(id)) throw Object.assign(new Error("Invalid product"), { status: 404 });
      const product = validateProduct(await readJSON(`/shopping/products/${encodeURIComponent(id)}`, controller.signal));
      if (version !== requestVersion) return;
      if (product.id !== id) throw new Error("Product identity mismatch");
      byId("detail-name").textContent = product.name;
      document.title = `${product.name} | agachichi`;
      byId("detail-price").textContent = priceLabel(product);
      byId("detail-availability").textContent = product.in_stock ? "재고 있음" : "품절";
      renderVariants(product.variants);
      // Canonical descriptions remain text, including any supplied HTML markup.
      byId("detail-description").textContent = product.description || "등록된 상품 설명이 없습니다.";
      byId("description-section").hidden = false;
      setPhoto(byId("detail-photo"), product);
      byId("detail-photo").hidden = false;
      byId("detail-status").textContent = "";
    } catch (error) {
      if (version !== requestVersion) return;
      const absent = error && [404, 422].includes(error.status);
      byId("detail-name").textContent = absent ? "상품을 찾을 수 없습니다" : "상품을 불러오지 못했습니다";
      document.title = `${byId("detail-name").textContent} | agachichi`;
      byId("detail-status").textContent = absent ? "상품이 없거나 현재 공개되지 않았습니다. 목록에서 다른 상품을 둘러보세요."
        : error && error.name === "AbortError" ? "응답 시간이 길어지고 있습니다. 다시 시도해 주세요." : "잠시 후 다시 시도해 주세요.";
      byId("detail-retry").hidden = absent;
    } finally {
      window.clearTimeout(timeout);
      if (version === requestVersion) content.setAttribute("aria-busy", "false");
    }
  }

  async function createInquiry() {
    const section = byId("inquiry-section");
    const productId = byId("detail-content")?.dataset.productId;
    const selected = byId("detail-variants")?.querySelector('button.variant-option[aria-pressed="true"]');
    const hasVariants = Boolean(byId("detail-variants")?.querySelector("button.variant-option"));
    if (hasVariants && !selected) { byId("inquiry-status").textContent = "문의 전에 사이즈를 선택해주세요."; return; }
    const message = byId("inquiry-message").value;
    const payload = { product_id: productId, inquiry_type: "purchase", message };
    if (selected) payload.variant_id = selected.dataset.variantId;
    const button = byId("inquiry-submit"); button.disabled = true; byId("inquiry-status").textContent = "문의를 생성하는 중…";
    try {
      const response = await fetch("/shopping/inquiries", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(payload) });
      if (!response.ok) { const error = new Error("Inquiry unavailable"); error.status = response.status; throw error; }
      const inquiry = await response.json();
      byId("inquiry-status").textContent = ""; byId("inquiry-id").textContent = inquiry.id; byId("inquiry-result").hidden = false;
      byId("inquiry-copy").onclick = () => navigator.clipboard.writeText(inquiry.formatted_message);
      const kakao = inquiry.contact_channels.find((channel) => channel.type === "kakao_openchat" && channel.enabled);
      const kakaoButton = byId("inquiry-kakao");
      if (kakao) { kakaoButton.hidden = false; kakaoButton.onclick = async () => { await navigator.clipboard.writeText(inquiry.formatted_message); window.open(kakao.url, "_blank", "noopener"); }; }
      const instagram = inquiry.contact_channels.find((channel) => channel.type === "instagram" && channel.enabled);
      const instagramButton = byId("inquiry-instagram");
      if (instagram) { instagramButton.hidden = false; instagramButton.onclick = async () => { await navigator.clipboard.writeText(inquiry.formatted_message); window.open(instagram.url, "_blank", "noopener"); }; }
    } catch (error) { byId("inquiry-status").textContent = error.status === 422 ? "선택한 사이즈를 확인해주세요." : "문의를 생성하지 못했습니다. 잠시 후 다시 시도해 주세요."; }
    finally { button.disabled = false; }
  }

  function restoreListing() {
    Object.assign(state, parseState(window.location.search));
    window.history.replaceState(null, "", listingURL(state));
    loadProducts();
  }

  function plainClick(event) {
    return event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey;
  }

  if (isDetail) {
    byId("detail-retry").addEventListener("click", loadProduct);
    byId("inquiry-submit")?.addEventListener("click", createInquiry);
    byId("detail-variants")?.addEventListener("click", (event) => {
      const selected = event.target.closest("button.variant-option");
      if (!selected || selected.disabled) return;
      byId("detail-variants").querySelectorAll("button.variant-option").forEach((button) => button.setAttribute("aria-pressed", button === selected ? "true" : "false"));
    });
    if (!document.body.dataset.serverRendered) loadProduct();
  } else if (isHome) {
    Object.assign(state, parseState(window.location.search));
    byId("home-retry").addEventListener("click", loadHome);
    if (!document.body.dataset.serverRendered) loadHome();
  } else {
    byId("category-nav").addEventListener("click", (event) => {
      const button = event.target.closest("[data-category]");
      if (button && plainClick(event)) {
        event.preventDefault();
        select({ category: button.dataset.category, page: 1 });
      }
    });
    document.querySelectorAll("[data-query]").forEach((button) => button.addEventListener("click", (event) => {
      if (!plainClick(event)) return;
      event.preventDefault();
      select({ query: button.dataset.query, page: 1 });
    }));
    byId("search-panel").addEventListener("submit", (event) => {
      event.preventDefault();
      select({ query: byId("search-input").value.trim(), page: 1 });
    });
    byId("clear-filters").addEventListener("click", (event) => {
      if (!plainClick(event)) return;
      event.preventDefault();
      select({ category: "", query: "", page: 1 });
    });
    byId("retry").addEventListener("click", loadProducts);
    [["previous-page", -1], ["next-page", 1]].forEach(([id, delta]) => byId(id).addEventListener("click", (event) => {
      if (!plainClick(event)) return;
      event.preventDefault();
      select({ page: Math.max(1, state.page + delta) });
      byId("collection-title").setAttribute("tabindex", "-1");
      byId("collection-title").focus({ preventScroll: true });
      byId("collection").scrollIntoView();
    }));
    // The initial HTML is complete; preserve it while enhancing later GET navigation.
    Object.assign(state, parseState(window.location.search));
    document.querySelectorAll("[data-category-id]").forEach((link) => {
      if (link.dataset.category) categories.set(link.dataset.category, {
        id: link.dataset.categoryId, slug: link.dataset.category, label: link.textContent,
      });
    });
    updateControls();
    if (!document.body.dataset.serverRendered) restoreListing();
    loadCategories();
  }
  // Server images may finish before this deferred script runs.
  document.querySelectorAll(".product-photo img[src]").forEach((image) => {
    const fallback = image.parentElement.querySelector(".photo-fallback");
    if (!fallback) return;
    const unavailable = () => { image.hidden = true; image.removeAttribute("src"); fallback.hidden = false; };
    image.addEventListener("error", unavailable, { once: true });
    if (image.complete && image.naturalWidth === 0) unavailable();
  });
  window.addEventListener("popstate", () => {
    if (isDetail) loadProduct();
    else if (!isHome && listingURL(parseState(window.location.search)) !== listingURL(state)) restoreListing();
  });
  window.addEventListener("pagehide", () => {
    ++requestVersion;
    ++categoryVersion;
    activeController?.abort();
    categoryController?.abort();
  });
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) return;
    if (isDetail) loadProduct();
    else if (isHome) loadHome();
    else { restoreListing(); loadCategories(); }
  });
})();
