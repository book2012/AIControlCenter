"use strict";

const DASHBOARD_ENDPOINT = "/dashboard";
const FETCH_TIMEOUT_MS = 8000;
const PENDING_ITEM_LIMIT = 8;

const byId = (id) => document.getElementById(id);
const setText = (id, value) => { byId(id).textContent = String(value ?? "—"); };

function statusText(value, fallback = "UNAVAILABLE") {
  return typeof value === "string" && value.trim() ? value.toUpperCase() : fallback;
}

function replaceList(element, values, render) {
  element.replaceChildren();
  values.forEach((value) => element.appendChild(render(value)));
}

function notice(text) {
  const item = document.createElement("li");
  item.textContent = text;
  return item;
}

function renderLifecycle(counts) {
  const entries = counts && typeof counts === "object" ? Object.entries(counts) : [];
  replaceList(byId("lifecycle-summary"), entries.length ? entries : [["UNAVAILABLE", "—"]], ([state, count]) => {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = statusText(state);
    detail.textContent = String(count);
    row.append(term, detail);
    return row;
  });
}

function renderPending(items, available) {
  const bounded = Array.isArray(items) ? items.slice(0, PENDING_ITEM_LIMIT) : [];
  if (!bounded.length) {
    replaceList(byId("pending-items"), [available ? "No drafts require review." : "ProductDraft source unavailable."], notice);
    return;
  }
  replaceList(byId("pending-items"), bounded, (item) => {
    const label = item && typeof item === "object"
      ? `${item.name || item.draft_id || "Draft"} · revision ${item.revision_number ?? "—"} · ${statusText(item.lifecycle_state)}`
      : "Review item unavailable";
    return notice(label);
  });
}

function renderDashboard(payload) {
  const control = payload && typeof payload.control_plane === "object" ? payload.control_plane : {};
  const shopping = payload && typeof payload.shopping_management === "object" ? payload.shopping_management : null;
  const drafts = payload && typeof payload.product_draft_review === "object" ? payload.product_draft_review : null;
  const notices = [];

  setText("control-plane-status", statusText(control.status || control.state, "AVAILABLE"));

  const shoppingState = shopping ? statusText(shopping.status) : "UNAVAILABLE";
  setText("shopping-status", shoppingState);
  setText("shopping-health", shopping ? `Health: ${statusText(shopping.health && shopping.health.status, "UNKNOWN")}` : "Dashboard source unavailable");
  const integration = shopping && shopping.integration && typeof shopping.integration === "object" ? shopping.integration : {};
  const integrationState = !shopping ? "UNAVAILABLE" : integration.configured === true ? "AVAILABLE" : "DEGRADED";
  setText("integration-status", integrationState);
  setText("integration-detail", integration.read_only === false ? "Write capability not surfaced" : "Read-only integration boundary");

  const summary = shopping && shopping.summary && typeof shopping.summary === "object" ? shopping.summary : {};
  const availableCatalog = shoppingState !== "UNAVAILABLE";
  const total = Number.isInteger(summary.catalog_total) ? summary.catalog_total : null;
  const pageItems = Number.isInteger(summary.page_items) ? summary.page_items : null;
  setText("product-count", availableCatalog ? (pageItems ?? 0) : "—");
  setText("catalog-total", availableCatalog ? (total ?? 0) : "—");
  setText("catalog-source", availableCatalog ? "Shopping management adapter" : "UNAVAILABLE");
  const canRead = shopping && shopping.capabilities && shopping.capabilities.read_catalog === true;
  setText("catalog-capability", canRead ? "READ_ONLY" : availableCatalog ? "READ_ONLY" : "UNAVAILABLE");
  const catalogState = !availableCatalog ? "UNAVAILABLE" : total === 0 ? "EMPTY" : shoppingState;
  setText("catalog-state", catalogState);
  if (!availableCatalog) {
    setText("catalog-message", "Catalog source is unavailable; this is not an empty catalog. Safe retry is available.");
    notices.push("UNAVAILABLE — Shopping catalog data could not be read.");
  } else if (total === 0) {
    setText("catalog-message", "Source is AVAILABLE and the catalog is EMPTY (zero products).");
    notices.push("EMPTY — Catalog source is available with zero products.");
  } else {
    setText("catalog-message", `${total} products reported by an available read-only source.`);
  }
  if (shoppingState === "DEGRADED") notices.push("DEGRADED — Shopping data is available with reduced readiness.");

  const draftState = drafts ? statusText(drafts.status) : "UNAVAILABLE";
  const draftAvailable = draftState !== "UNAVAILABLE";
  setText("draft-status", draftState);
  setText("draft-count", draftAvailable ? drafts.summary && drafts.summary.draft_count : "—");
  setText("revision-count", draftAvailable ? drafts.summary && drafts.summary.revision_count : "—");
  setText("pending-count", draftAvailable ? drafts.pending_review_count : "—");
  setText("review-state", !draftAvailable ? "UNAVAILABLE" : drafts.pending_review_count > 0 ? "REVIEW_REQUIRED" : "AVAILABLE");
  renderLifecycle(drafts && drafts.summary && drafts.summary.lifecycle_counts);
  renderPending(drafts && drafts.pending_review_items, draftAvailable);
  if (!draftAvailable) notices.push("UNAVAILABLE — ProductDraft read source is not configured; no empty-state claim is made.");

  if (!notices.length) notices.push("AVAILABLE — All requested dashboard projections responded safely.");
  replaceList(byId("notices"), notices, notice);
}

async function refreshDashboard() {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  byId("retry").disabled = true;
  setText("refresh-status", "Refreshing read-only operational data…");
  try {
    const response = await fetch(DASHBOARD_ENDPOINT, {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`Dashboard returned ${response.status}`);
    renderDashboard(await response.json());
    const refreshed = new Date();
    byId("last-refresh").dateTime = refreshed.toISOString();
    setText("last-refresh", refreshed.toLocaleTimeString());
    setText("refresh-status", "Dashboard refresh complete. Data is read-only.");
  } catch (error) {
    const timedOut = error && error.name === "AbortError";
    setText("refresh-status", timedOut
      ? "Fetch timeout after 8 seconds. No data was changed; safe retry is available."
      : "Dashboard unavailable. No data was changed; safe retry is available.");
    renderDashboard({});
  } finally {
    window.clearTimeout(timeout);
    byId("retry").disabled = false;
  }
}

byId("retry").addEventListener("click", refreshDashboard);
refreshDashboard();
