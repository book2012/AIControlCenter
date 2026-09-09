(function () {
    "use strict";

    const ready = (callback) => {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", callback);
            return;
        }

        callback();
    };

    const categoryUrl = (category) => {
        const url = new URL(window.location.href);

        url.searchParams.set("ai_shop_search", "1");
        url.searchParams.set("ai_shop_page", "1");

        if (category) {
            url.searchParams.set("ai_shop_category", category);
        } else {
            url.searchParams.delete("ai_shop_category");
        }

        return url.toString();
    };

    const createSearchOverlay = () => {
        const overlay = document.createElement("div");

        overlay.className = "orange-coco-overlay";
        overlay.id = "orange-coco-search-overlay";
        overlay.hidden = true;

        overlay.innerHTML = `
            <div
                class="orange-coco-overlay__panel"
                role="dialog"
                aria-modal="true"
                aria-labelledby="orange-coco-search-title"
            >
                <button
                    class="orange-coco-overlay__close"
                    type="button"
                    aria-label="검색 닫기"
                >
                    ×
                </button>

                <p class="orange-coco-overlay__eyebrow">
                    FIND YOUR STYLE
                </p>

                <h2 id="orange-coco-search-title">
                    어떤 스타일을 찾고 있나요?
                </h2>

                <form
                    class="orange-coco-search-form"
                    method="get"
                    action="/ai-shopping/"
                >
                    <input
                        type="hidden"
                        name="ai_shop_search"
                        value="1"
                    >

                    <input
                        type="search"
                        name="ai_shop_q"
                        placeholder="원피스, 데일리룩, 오렌지 니트..."
                        autocomplete="off"
                        autofocus
                    >

                    <button type="submit">
                        검색
                    </button>
                </form>

                <div class="orange-coco-search-suggestions">
                    <span>추천 검색</span>
                    <a href="${categoryUrl("women-dresses")}">원피스</a>
                    <a href="${categoryUrl("women-outer")}">아우터</a>
                    <a href="${categoryUrl("women-bags")}">가방</a>
                    <a href="${categoryUrl("men")}">남성</a>
                </div>

            </div>
        `;

        return overlay;
    };

    const openElement = (element) => {
        element.hidden = false;
        element.classList.add("is-open");
        document.body.classList.add("orange-coco-modal-open");
    };

    const closeElement = (element) => {
        element.classList.remove("is-open");
        element.hidden = true;
        document.body.classList.remove("orange-coco-modal-open");
    };

    const initialize = () => {
        const storefront = document.querySelector(
            ".ai-shopping-storefront"
        );

        if (!storefront) {
            return;
        }

        const applicationHeader = document.querySelector(
            ".orange-coco-header"
        );

        if (!applicationHeader) {
            return;
        }

        const searchOverlay = createSearchOverlay();
        document.body.appendChild(searchOverlay);

        const mobileButton = document.querySelector(
            ".orange-coco-header__mobile-button"
        );

        const navigation = document.querySelector(
            ".orange-coco-nav"
        );

        mobileButton.addEventListener("click", () => {
            const active = navigation.classList.toggle("is-open");

            mobileButton.setAttribute(
                "aria-expanded",
                active ? "true" : "false"
            );
        });

        document
            .getElementById("orange-coco-search-open")
            .addEventListener("click", () => {
                openElement(searchOverlay);

                window.setTimeout(() => {
                    const input = searchOverlay.querySelector(
                        'input[type="search"]'
                    );

                    if (input) {
                        input.focus();
                    }
                }, 50);
            });

        searchOverlay
            .querySelector(".orange-coco-overlay__close")
            .addEventListener("click", () => {
                closeElement(searchOverlay);
            });

        searchOverlay.addEventListener("click", (event) => {
            if (event.target === searchOverlay) {
                closeElement(searchOverlay);
            }
        });

        document.addEventListener("keydown", (event) => {
            if (event.key !== "Escape") {
                return;
            }

            if (!searchOverlay.hidden) {
                closeElement(searchOverlay);
            }

        });
    };

    ready(initialize);
})();
