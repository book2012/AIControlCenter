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

    const createHeader = () => {
        const header = document.createElement("header");
        header.className = "orange-coco-header";

        header.innerHTML = `
            <div class="orange-coco-header__inner">
                <button
                    class="orange-coco-header__mobile-button"
                    type="button"
                    aria-label="메뉴 열기"
                    aria-expanded="false"
                >
                    <span></span>
                    <span></span>
                    <span></span>
                </button>

                <a
                    class="orange-coco-logo"
                    href="/ai-shopping/"
                    aria-label="Orange Coco 홈"
                >
                    orange coco
                </a>

                <nav
                    class="orange-coco-nav"
                    aria-label="상품 카테고리"
                >
                    <a
                        href="${categoryUrl("")}"
                        data-category=""
                    >
                        ALL
                    </a>

                    <a
                        href="${categoryUrl("women-outer")}"
                        data-category="women-outer"
                    >
                        OUTER
                    </a>

                    <a
                        href="${categoryUrl("women-dresses")}"
                        data-category="women-dresses"
                    >
                        DRESS
                    </a>

                    <div class="orange-coco-nav__group">
                        <button type="button">
                            TOP
                        </button>

                        <div class="orange-coco-nav__submenu">
                            <a
                                href="${categoryUrl("women-tops")}"
                                data-category="women-tops"
                            >
                                TOP
                            </a>

                            <a
                                href="${categoryUrl("women-knitwear")}"
                                data-category="women-knitwear"
                            >
                                KNIT
                            </a>

                            <a
                                href="${categoryUrl("women-shirts-blouses")}"
                                data-category="women-shirts-blouses"
                            >
                                BLOUSE
                            </a>
                        </div>
                    </div>

                    <div class="orange-coco-nav__group">
                        <button type="button">
                            BOTTOM
                        </button>

                        <div class="orange-coco-nav__submenu">
                            <a
                                href="${categoryUrl("women-pants")}"
                                data-category="women-pants"
                            >
                                PANTS
                            </a>

                            <a
                                href="${categoryUrl("women-skirts")}"
                                data-category="women-skirts"
                            >
                                SKIRT
                            </a>
                        </div>
                    </div>

                    <a
                        href="${categoryUrl("women-bags")}"
                        data-category="women-bags"
                    >
                        BAG
                    </a>

                    <a
                        href="${categoryUrl("women-shoes")}"
                        data-category="women-shoes"
                    >
                        SHOES
                    </a>

                    <a
                        href="${categoryUrl("women-accessories")}"
                        data-category="women-accessories"
                    >
                        ACC
                    </a>

                    <a
                        href="${categoryUrl("men")}"
                        data-category="men"
                    >
                        MEN
                    </a>
                </nav>

                <div class="orange-coco-header__actions">
                    <button
                        class="orange-coco-icon-button"
                        id="orange-coco-search-open"
                        type="button"
                        aria-label="검색 열기"
                    >
                        <span aria-hidden="true">⌕</span>
                    </button>

                    <button
                        class="orange-coco-ai-button"
                        id="orange-coco-ai-open"
                        type="button"
                        aria-label="AI 메뉴 열기"
                    >
                        AI
                    </button>
                </div>
            </div>
        `;

        return header;
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

                <div class="orange-coco-search-tools">
                    <button type="button" data-search-tool="style">
                        <strong>스타일 추천</strong>
                        <span>데이트룩, 하객룩처럼 문장으로 찾아보세요.</span>
                    </button>

                    <button type="button" data-search-tool="image">
                        <strong>사진으로 찾기</strong>
                        <span>비슷한 디자인의 상품을 찾아드려요.</span>
                    </button>

                    <button type="button" data-search-tool="inventory">
                        <strong>재고·예약 확인</strong>
                        <span>상품의 현재 상태를 확인하세요.</span>
                    </button>
                </div>
            </div>
        `;

        return overlay;
    };

    const createAiDrawer = () => {
        const drawer = document.createElement("aside");

        drawer.className = "orange-coco-ai-drawer";
        drawer.id = "orange-coco-ai-drawer";
        drawer.setAttribute("aria-hidden", "true");

        drawer.innerHTML = `
            <div class="orange-coco-ai-drawer__backdrop"></div>

            <div
                class="orange-coco-ai-drawer__panel"
                role="dialog"
                aria-modal="true"
                aria-labelledby="orange-coco-ai-title"
            >
                <button
                    class="orange-coco-ai-drawer__close"
                    type="button"
                    aria-label="AI 메뉴 닫기"
                >
                    ×
                </button>

                <p class="orange-coco-ai-drawer__eyebrow">
                    ORANGE COCO AI
                </p>

                <h2 id="orange-coco-ai-title">
                    무엇을 도와드릴까요?
                </h2>

                <div class="orange-coco-ai-menu">
                    <button type="button" data-ai-action="recommend">
                        <strong>오늘의 스타일 추천</strong>
                        <span>상황과 분위기에 맞는 상품을 찾아드려요.</span>
                    </button>

                    <button type="button" data-ai-action="image-search">
                        <strong>사진으로 비슷한 상품 찾기</strong>
                        <span>원하는 옷 사진을 기준으로 찾아드려요.</span>
                    </button>

                    <button type="button" data-ai-action="inventory">
                        <strong>재고와 예약 확인</strong>
                        <span>상품 재고와 예약 가능 여부를 확인해요.</span>
                    </button>

                    <button
                        class="orange-coco-ai-menu__operator"
                        type="button"
                        data-ai-action="operator"
                    >
                        <strong>운영자 상품 등록</strong>
                        <span>사진을 분석해 상품 초안을 만들어요.</span>
                    </button>
                </div>

                <div
                    class="orange-coco-ai-placeholder"
                    aria-live="polite"
                >
                    AI 기능은 다음 Sprint에서 연결됩니다.
                </div>
            </div>
        `;

        return drawer;
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
