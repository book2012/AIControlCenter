"use strict";

const COLLECTION_ENDPOINT = "/shopping/product-drafts?page=1&page_size=100";
const DETAIL_ENDPOINT = (draftId) => `/shopping/product-drafts/${encodeURIComponent(draftId)}`;
const REVISION_ENDPOINT = (draftId, revisionId) => `/shopping/product-drafts/${encodeURIComponent(draftId)}/revisions/${encodeURIComponent(revisionId)}`;
const FETCH_TIMEOUT_MS = 8000;
const LIST_LIMIT = 100;
let revisions = [];
let selectedDraftId = null;

const byId = (id) => document.getElementById(id);
const setText = (id, value) => { byId(id).textContent = String(value ?? "—"); };
const stateOf = (value, fallback = "UNAVAILABLE") => typeof value === "string" && value.trim() ? value.toUpperCase() : fallback;

const listOf = (value) => (
  Array.isArray(value) ? value : []
);

function replaceText(target, message) {
  const paragraph = document.createElement("p");
  paragraph.textContent = message;
  target.replaceChildren(paragraph);
}

function clearRevisionPanel(state, message) {
  setText("revision-state", state);
  replaceText(byId("revision-detail"), message);
}

function clearDraftPanels(state, message) {
  setText("detail-state", state);
  replaceText(byId("draft-detail"), message);
  replaceList(byId("revision-list"), [message], textItem);
  clearRevisionPanel(state, message);
}

function resetSelection(state, message) {
  selectedDraftId = null;
  clearDraftPanels(state, message);
}


function replaceList(element, values, render) {
  element.replaceChildren();
  values.forEach((value) => element.appendChild(render(value)));
}

function textItem(text) {
  const item = document.createElement("li");
  item.textContent = text;
  return item;
}

function fieldList(target, fields) {
  const list = document.createElement("dl");
  fields.forEach(([label, value]) => {
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = label;
    detail.textContent = value === null || value === undefined || value === "" ? "Not returned" : String(value);
    list.append(term, detail);
  });
  target.replaceChildren(list);
}

function groupedDrafts() {
  const groups = new Map();
  revisions.forEach((revision) => {
    if (!revision || typeof revision !== "object" || typeof revision.draft_id !== "string") return;
    const existing = groups.get(revision.draft_id) || [];
    existing.push(revision);
    groups.set(revision.draft_id, existing);
  });
  groups.forEach((items) => items.sort((a, b) => Number(b.revision_number) - Number(a.revision_number)));
  return groups;
}

function renderSummary(payload) {
  const groups = groupedDrafts();
  const current = Array.from(groups.values(), (items) => items[0]);
  const lifecycle = {};
  current.forEach((item) => { const state = stateOf(item.state, "UNAVAILABLE"); lifecycle[state] = (lifecycle[state] || 0) + 1; });
  setText("draft-count", groups.size);
  setText("revision-count", payload.pagination && Number.isInteger(payload.pagination.total_items) ? payload.pagination.total_items : revisions.length);
  setText("pending-count", current.filter((item) => item.state === "REVIEW_REQUIRED").length);
  setText("availability", payload.status === "AVAILABLE" ? (revisions.length ? "AVAILABLE" : "EMPTY") : "DEGRADED");
  const rows = Object.entries(lifecycle);
  replaceList(byId("lifecycle-counts"), rows.length ? rows : [["EMPTY", 0]], ([state, count]) => {
    const row = document.createElement("div");
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = state;
    detail.textContent = String(count);
    row.append(term, detail);
    return row;
  });
}

function renderFilters() {
  const select = byId("state-filter");
  const selected = select.value;
  const states = [...new Set(revisions.map((item) => item && item.state).filter(Boolean))].sort();
  select.replaceChildren();
  [["ALL", "All"], ...states.map((state) => [state, state])].forEach(([value, label]) => {
    const option = document.createElement("option"); option.value = value; option.textContent = label; select.appendChild(option);
  });
  select.value = states.includes(selected) ? selected : "ALL";
}

function renderDraftList() {
  const filter = byId("state-filter").value;
  const groups = groupedDrafts();
  const drafts = Array.from(groups.entries()).filter(([, items]) => filter === "ALL" || items[0].state === filter).slice(0, LIST_LIMIT);
  if (!drafts.length) {
    replaceList(byId("draft-list"), [revisions.length ? "No drafts match this state." : "EMPTY — Source available with no ProductDrafts."], textItem);
    return;
  }
  replaceList(byId("draft-list"), drafts, ([draftId, items]) => {
    const item = document.createElement("li"); const button = document.createElement("button"); const current = items[0];
    button.type = "button"; button.textContent = `${current.proposed_fields && current.proposed_fields.name || draftId} · ${stateOf(current.state)} · ${items.length} revision${items.length === 1 ? "" : "s"}`;
    button.setAttribute("aria-current", String(draftId === selectedDraftId));
    button.addEventListener("click", () => selectDraft(draftId)); item.appendChild(button); return item;
  });
}

async function getJson(endpoint) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
  try {
    const response = await fetch(endpoint, {method: "GET", credentials: "same-origin", headers: {Accept: "application/json"}, signal: controller.signal});
    if (!response.ok) throw new Error(`Read returned ${response.status}`);
    return await response.json();
  } finally { window.clearTimeout(timeout); }
}

function renderRevision(revision) {
  const validation = revision.validation && typeof revision.validation === "object" ? revision.validation : null;
  const review = revision.human_decision && typeof revision.human_decision === "object" ? revision.human_decision : null;
  const deployment = revision.deployment_intent && typeof revision.deployment_intent === "object" ? revision.deployment_intent : null;
  setText("revision-state", stateOf(revision.state));
  const fields = [
    ["Draft ID", revision.draft_id], ["Revision ID", revision.revision_id], ["Revision number", revision.revision_number], ["Lifecycle", stateOf(revision.state)],
    ["Created", revision.created_at], ["Previous revision", revision.previous_revision_id], ["Name", revision.proposed_fields && revision.proposed_fields.name],
    ["SKU", revision.proposed_fields && revision.proposed_fields.sku], ["Regular price", revision.proposed_fields && revision.proposed_fields.regular_price],
    ["Validation", validation ? stateOf(validation.status) : "Not returned"], ["Validation errors", validation ? listOf(validation.errors).join(" · ") || "None" : "Not returned"],
    ["Validation warnings", validation ? listOf(validation.warnings).join(" · ") || "None" : "Not returned"], ["Human review", review ? stateOf(review.decision) : revision.state === "REVIEW_REQUIRED" ? "REVIEW_REQUIRED" : "Not returned"],
    ["Review reason", review && review.reason], ["Deployment preview", deployment ? stateOf(deployment.readiness_status) : "Not returned"],
    ["Deployment intent", deployment && deployment.intent_id], ["Authorization", deployment && deployment.authorization_reference], ["Audit reference", revision.audit_reference],
  ];
  fieldList(byId("revision-detail"), fields);
}

async function selectRevision(draftId, revisionId) {
  setText("console-status", `Loading immutable revision ${revisionId}…`);
  try { renderRevision(await getJson(REVISION_ENDPOINT(draftId, revisionId))); setText("console-status", "Revision AVAILABLE · read-only."); }
  catch (error) {
    clearRevisionPanel(
      "UNAVAILABLE",
      "Revision detail is unavailable.",
    ); setText("console-status", error && error.name === "AbortError" ? "Revision request timed out after 8 seconds. Safe retry is available." : "Revision UNAVAILABLE. No data was changed; safe retry is available."); }
}

async function selectDraft(draftId) {
  selectedDraftId = draftId; renderDraftList(); setText("console-status", `Loading ProductDraft ${draftId}…`);
  try {
    const detail = await getJson(DETAIL_ENDPOINT(draftId));
    setText("detail-state", stateOf(detail.state));
    fieldList(byId("draft-detail"), [["Draft ID", detail.draft_id], ["Current revision", detail.revision_id], ["Lifecycle", stateOf(detail.state)], ["Validation", detail.validation && stateOf(detail.validation.status)], ["Human review", detail.human_decision ? stateOf(detail.human_decision.decision) : detail.state === "REVIEW_REQUIRED" ? "REVIEW_REQUIRED" : "Not returned"]]);
    const items = groupedDrafts().get(draftId) || [];
    replaceList(byId("revision-list"), items, (revision) => { const item = document.createElement("li"); const button = document.createElement("button"); button.type = "button"; button.textContent = `Revision ${revision.revision_number} · ${stateOf(revision.state)} · ${revision.revision_id}`; button.addEventListener("click", () => selectRevision(draftId, revision.revision_id)); item.appendChild(button); return item; });
    renderRevision(detail); setText("console-status", "ProductDraft AVAILABLE · immutable read-only detail loaded.");
  } catch (error) {
    clearDraftPanels(
      "UNAVAILABLE",
      "ProductDraft detail is unavailable.",
    ); setText("console-status", error && error.name === "AbortError" ? "Draft request timed out after 8 seconds. Safe retry is available." : "Draft detail UNAVAILABLE. No data was changed; safe retry is available."); }
}

async function refreshConsole() {
  byId("retry").disabled = true; setText("source-state", "READ_ONLY"); setText("console-status", "Refreshing bounded ProductDraft reads…");
  try {
    const payload = await getJson(COLLECTION_ENDPOINT);
    revisions = Array.isArray(payload.items) ? payload.items.slice(0, LIST_LIMIT) : [];
    resetSelection(
      "EMPTY",
      revisions.length
        ? "Select a ProductDraft."
        : "No ProductDrafts were returned.",
    );
    renderSummary(payload); renderFilters(); renderDraftList();
    setText("console-status", revisions.length ? "AVAILABLE · bounded ProductDraft data loaded in READ_ONLY mode." : "EMPTY · ProductDraft source is AVAILABLE with zero items.");
  } catch (error) {
    revisions = [];
    resetSelection(
      "UNAVAILABLE",
      "ProductDraft source is unavailable.",
    ); setText("availability", "UNAVAILABLE"); setText("draft-count", "—"); setText("revision-count", "—"); setText("pending-count", "—"); setText("source-state", "DEGRADED");
    replaceList(byId("draft-list"), ["UNAVAILABLE — this is not an empty ProductDraft source."], textItem);
    setText("console-status", error && error.name === "AbortError" ? "Request timed out after 8 seconds. No data was changed; safe retry is available." : "UNAVAILABLE · ProductDraft source could not be read. No data was changed; safe retry is available.");
  } finally { byId("retry").disabled = false; }
}

byId("state-filter").addEventListener("change", renderDraftList);
byId("retry").addEventListener("click", refreshConsole);
refreshConsole();
