(function () {
    "use strict";

    const onReady = (callback) => {
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

    const icon = (name) => {
        const icons = {
            search: `
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <circle cx="11" cy="11" r="6.5"></circle>
                    <path d="m16 16 4 4"></path>
                </svg>
            `,
            heart: `
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="
                        M20.8 4.7
                        a5.5 5.5 0 0 0-7.8 0
                        L12 5.7
                        l-1-1
                        a5.5 5.5 0 0 0-7.8 7.8
                        l1 1
                        L12 21
                        l7.8-7.5
                        1-1
                        a5.5 5.5 0 0 0 0-7.8Z
                    "></path>
                </svg>
            `,
            menu: `
                <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M4 7h16"></path>
                    <path d="M4 12h16"></path>
                    <path d="M4 17h16"></path>
                </svg>
            `,
        };

        return icons[name] || "";
    };

    const normalizeHero = () => {
        const hero = document.querySelector(
            ".ai-shopping-storefront__header"
        );

        if (!hero) {
            return;
        }

        const heading = hero.querySelector("h2");

        if (heading) {
            heading.innerHTML =
                "Dress beautifully.<br>Live beautifully.";
        }

        let cta = hero.querySelector(".orange-coco-hero-cta");

        if (!cta) {
            cta = document.createElement("a");
            cta.className = "orange-coco-hero-cta";
            cta.href = "#orange-coco-products";
            cta.textContent = "EXPLORE COLLECTION";
            hero
                .querySelector(".ai-shopping-storefront__hero-copy")
                ?.appendChild(cta);
        }

        const grid =
            document.querySelector(".ai-shopping-storefront__grid");

        if (grid && !grid.id) {
            grid.id = "orange-coco-products";
        }
    };

    const normalizeActions = () => {
        const actions = document.querySelector(
            ".orange-coco-header__actions"
        );

        if (!actions) {
            return;
        }

        actions.innerHTML = `
            <button
                class="orange-coco-action"
                id="orange-coco-search-open"
                type="button"
                aria-label="상품 검색"
            >
                ${icon("search")}
            </button>

            <button
                class="orange-coco-action"
                id="orange-coco-wishlist-open"
                type="button"
                aria-label="관심상품"
            >
                ${icon("heart")}
            </button>
        `;
    };

    const normalizeMobileButton = () => {
        const button = document.querySelector(
            ".orange-coco-header__mobile-button"
        );

        if (!button) {
            return;
        }

        button.innerHTML = icon("menu");
        button.setAttribute("aria-label", "메뉴 열기");
    };

    const normalizeNavigation = () => {
        const navigation = document.querySelector(".orange-coco-nav");

        if (!navigation) {
            return;
        }

        const currentCategory = new URL(
            window.location.href
        ).searchParams.get("ai_shop_category") || "";

        const items = [
            ["NEW", ""],
            ["BEST", "best"],
            ["TOP", "women-tops"],
            ["DRESS", "women-dresses"],
            ["BOTTOM", "women-bottoms"],
            ["OUTER", "women-outer"],
            ["BAG", "women-bags"],
            ["SALE", "sale"],
        ];

        navigation.innerHTML = items
            .map(([label, category]) => {
                const isActive =
                    category === currentCategory
                    || (
                        label === "NEW"
                        && currentCategory === ""
                    );

                return `
                    <a
                        href="${categoryUrl(category)}"
                        data-category="${category}"
                        class="${isActive ? "is-active" : ""}"
                        ${isActive ? 'aria-current="page"' : ""}
                    >
                        ${label}
                    </a>
                `;
            })
            .join("");
    };

    const bindMobileNavigation = () => {
        const button = document.querySelector(
            ".orange-coco-header__mobile-button"
        );

        const navigation = document.querySelector(
            ".orange-coco-nav"
        );

        if (!button || !navigation) {
            return;
        }

        button.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");

            button.setAttribute(
                "aria-expanded",
                isOpen ? "true" : "false"
            );
        });
    };

    const bindTemporaryActions = () => {
        const wishlist = document.getElementById(
            "orange-coco-wishlist-open"
        );

        if (wishlist) {
            wishlist.addEventListener("click", () => {
                window.dispatchEvent(
                    new CustomEvent(
                        "orange-coco:wishlist-open"
                    )
                );
            });
        }
    };

    onReady(() => {
        normalizeHero();
        normalizeActions();
        normalizeMobileButton();
        normalizeNavigation();
        bindMobileNavigation();
        bindTemporaryActions();
    });
})();
