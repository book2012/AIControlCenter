(() => {
    "use strict";

    const ready = (callback) => {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", callback, { once: true });
        } else {
            callback();
        }
    };

    ready(() => {
        document.querySelectorAll(".variant-options").forEach((group) => {
            group.addEventListener("click", (event) => {
                const selected = event.target.closest("button.variant-option:not(:disabled)");
                if (!selected) return;
                group.querySelectorAll("button.variant-option").forEach((button) => {
                    button.setAttribute("aria-pressed", button === selected ? "true" : "false");
                });
            });
        });

        document.querySelectorAll("#home-retry, #retry, #detail-retry").forEach((button) => {
            button.addEventListener("click", () => window.location.reload());
        });

        const detail = document.querySelector("#detail-content");
        const inquiry = document.querySelector("#inquiry-submit");
        if (!detail || !inquiry) return;

        inquiry.addEventListener("click", async () => {
            const selected = detail.querySelector("button.variant-option[aria-pressed=\"true\"]");
            const variants = detail.querySelectorAll("button.variant-option");
            const status = document.querySelector("#inquiry-status");
            if (variants.length && !selected) {
                status.textContent = "문의 전에 사이즈를 선택해주세요.";
                return;
            }
            const payload = {
                product_id: detail.dataset.productId,
                inquiry_type: "purchase",
                message: document.querySelector("#inquiry-message").value,
            };
            if (selected) payload.variant_id = selected.dataset.variantId;
            inquiry.disabled = true;
            status.textContent = "문의를 생성하는 중…";
            try {
                const response = await fetch("/shopping/inquiries", {
                    method: "POST",
                    credentials: "same-origin",
                    headers: { "Content-Type": "application/json", Accept: "application/json" },
                    body: JSON.stringify(payload),
                });
                if (!response.ok) throw new Error("inquiry_failed");
                const result = await response.json();
                status.textContent = "";
                document.querySelector("#inquiry-id").textContent = result.id || "";
                document.querySelector("#inquiry-result").hidden = false;
                document.querySelector("#inquiry-copy").onclick = () => navigator.clipboard.writeText(result.formatted_message || "");
            } catch (error) {
                status.textContent = "문의를 생성하지 못했습니다. 잠시 후 다시 시도해 주세요.";
                inquiry.disabled = false;
            }
        });
    });
})();
