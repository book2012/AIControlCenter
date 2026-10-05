(function (root) {
    "use strict";
    const STORAGE_PREFIX = "aicc.order.operation.v1.";
    function createController({fetcher, storage, randomKey, productId, onState = () => {}}) {
        const slot = STORAGE_PREFIX + productId;
        let busy = false;
        let operation = null;
        const publish = (state) => { onState(state); return state; };
        const save = () => storage.setItem(slot, JSON.stringify(operation));
        try {
            const raw = storage.getItem(slot);
            if (raw) {
                const value = JSON.parse(raw);
                if (!value || typeof value.key !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(value.key)
                    || typeof value.intent !== "object" || !Array.isArray(value.intent.line_items)
                    || value.intent.line_items.length !== 1 || value.intent.line_items[0].product_id !== productId) {
                    throw new Error("invalid_saved_operation");
                }
                operation = {key: value.key, intent: value.intent, terminal: value.terminal === true};
            }
        } catch (_) { publish({kind: "storage_unavailable"}); busy = true; }
        async function csrf() {
            const response = await fetcher("/shopping/auth/session", {credentials: "same-origin", cache: "no-store"});
            const token = response.headers.get("X-CSRF-Token");
            if (!response.ok || typeof token !== "string" || !/^[0-9a-f]{64}$/.test(token)) throw new Error("auth_required");
            return token;
        }
        async function submit({quantity, variationId = null}) {
            if (busy) return publish({kind: "busy"});
            if (!Number.isInteger(quantity) || quantity < 1 || quantity > 1000) return publish({kind: "invalid_quantity"});
            const line = {product_id: productId, quantity};
            if (variationId !== null) line.variation_id = variationId;
            const intent = {line_items: [line]};
            if (operation && (operation.terminal || JSON.stringify(operation.intent) !== JSON.stringify(intent))) {
                return publish({kind: "existing_operation"});
            }
            busy = true;
            try {
                if (!operation) {
                    const key = randomKey();
                    if (typeof key !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(key)) throw new Error("invalid_key");
                    operation = {key, intent, terminal: false};
                    save(); // Persist non-secret intent/key before any create request.
                }
                save(); // Also fail closed if storage becomes unavailable on a replay.
                const token = await csrf();
                publish({kind: "submitting"});
                const response = await fetcher("/shopping/orders", {
                    method: "POST", credentials: "same-origin", cache: "no-store",
                    headers: {"Content-Type": "application/json", "Accept": "application/json", "X-CSRF-Token": token},
                    body: JSON.stringify({...operation.intent, idempotency_key: operation.key})
                });
                const value = await response.json();
                if (!response.ok) {
                    const code = value && value.detail && value.detail.code;
                    if (response.status === 401 || response.status === 403) return publish({kind: "auth_required"});
                    if (code === "order_create_terminal_failed" || code === "order_create_provider_rejected" || code === "order_create_catalog_rejected") {
                        operation.terminal = true; save(); return publish({kind: "terminal_failed"});
                    }
                    return publish({kind: "check_required"});
                }
                if (value.outcome !== "COMPLETED" || !Number.isInteger(value.provider_order_id) || value.provider_order_id <= 0) {
                    return publish({kind: "check_required"});
                }
                operation.terminal = true; save();
                return publish({kind: "completed", orderId: value.provider_order_id, replay: value.idempotent_replay === true});
            } catch (error) {
                return publish({kind: error.message === "auth_required" ? "auth_required" : "check_required"});
            } finally { busy = false; }
        }
        async function inspect() {
            if (busy || !operation) return publish({kind: "no_operation"});
            busy = true;
            try {
                const token = await csrf();
                const response = await fetcher("/shopping/orders/operations/" + encodeURIComponent(operation.key), {
                    credentials: "same-origin", cache: "no-store", headers: {"X-CSRF-Token": token}
                });
                if (!response.ok) return publish({kind: response.status === 404 ? "not_found" : "check_required"});
                const value = await response.json();
                if (!["CLAIMED", "COMPLETED", "TERMINAL_FAILED", "UNKNOWN_OUTCOME"].includes(value.state)) return publish({kind: "check_required"});
                operation.terminal = ["COMPLETED", "TERMINAL_FAILED"].includes(value.state); save();
                return publish({kind: "status", state: value.state, review: value.review_state, orderId: value.provider_order_id});
            } catch (error) {
                return publish({kind: error.message === "auth_required" ? "auth_required" : "check_required"});
            } finally { busy = false; }
        }
        function startNew() {
            if (busy || !operation || !operation.terminal) return publish({kind: "check_required"});
            try { storage.removeItem(slot); operation = null; return publish({kind: "new_operation"}); }
            catch (_) { return publish({kind: "storage_unavailable"}); }
        }
        return {submit, inspect, startNew, hasOperation: () => operation !== null};
    }
    if (typeof module !== "undefined" && module.exports) { module.exports = {createController}; return; }
    root.AICCOrderUI = {createController};
    function mount() {
        const detail = document.querySelector("#detail-content");
        const button = document.querySelector("#order-submit");
        if (!detail || !button || button.disabled) return; // Default PROD remains gated.
        const status = document.querySelector("#order-status");
        const check = document.querySelector("#order-check");
        const newOrder = document.querySelector("#order-new");
        let controller;
        const messages = {
            submitting: "주문 요청을 처리하고 있습니다.", completed: "주문 요청이 접수되었습니다. 운영자 확인을 기다려주세요.",
            auth_required: "고객 인증이 필요합니다.", check_required: "처리 결과를 확인해야 합니다. 새 주문을 만들지 말고 주문 상태를 확인해주세요.",
            existing_operation: "기존 요청의 상태를 먼저 확인해주세요.", terminal_failed: "주문 요청이 거절되었습니다.",
            invalid_quantity: "수량을 확인해주세요.", storage_unavailable: "이 브라우저에서는 안전한 주문 요청을 저장할 수 없습니다.",
            new_operation: "새 주문 요청을 준비했습니다.", not_found: "같은 요청으로 다시 시도할 수 있습니다.",
            busy: "요청을 처리하고 있습니다.", no_operation: "저장된 주문 요청이 없습니다."
        };
        controller = createController({fetcher: root.fetch.bind(root), storage: root.sessionStorage,
            randomKey: () => root.crypto.randomUUID(), productId: detail.dataset.productId,
            onState: (value) => {
                if (value.kind === "status") {
                    status.textContent = {PENDING_REVIEW:"운영자 확인 대기 중입니다.",CONFIRMED:"운영자가 주문을 확인했습니다.",REJECTED:"운영자가 주문 요청을 거절했습니다."}[value.review]
                        || {CLAIMED:"주문 처리 중입니다.",UNKNOWN_OUTCOME:"결과 확인이 필요합니다. 재주문하지 마세요.",TERMINAL_FAILED:"주문 요청이 거절되었습니다."}[value.state] || "주문이 접수되었습니다.";
                } else status.textContent = messages[value.kind] || "주문 상태를 확인해주세요.";
                button.disabled = !["auth_required","not_found","invalid_quantity","new_operation"].includes(value.kind);
                check.disabled = !controller || !controller.hasOperation();
                newOrder.disabled = !(value.kind === "completed" || value.kind === "terminal_failed"
                    || value.kind === "status" && ["COMPLETED","TERMINAL_FAILED"].includes(value.state));
            }});
        check.disabled = !controller.hasOperation();
        if (controller.hasOperation()) { button.disabled = true; status.textContent = "기존 주문 요청이 있습니다. 상태를 확인해주세요."; }
        button.addEventListener("click", () => {
            const variants = detail.querySelectorAll("button.variant-option");
            const selected = detail.querySelector('button.variant-option[aria-pressed="true"]');
            if (variants.length && !selected) { status.textContent = "사이즈를 선택해주세요."; return; }
            controller.submit({quantity: Number(document.querySelector("#order-quantity").value),
                               variationId: selected ? selected.dataset.variantId : null});
        });
        check.addEventListener("click", () => controller.inspect());
        newOrder.addEventListener("click", () => controller.startNew());
    }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, {once: true});
    else mount();
})(typeof window !== "undefined" ? window : globalThis);
