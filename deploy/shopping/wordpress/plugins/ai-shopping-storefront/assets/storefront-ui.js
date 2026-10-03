(function () {
    "use strict";

    const ready = (callback) => {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", callback);
            return;
        }
        callback();
    };

    const initialize = () => {
        const menuButton = document.querySelector(".agachichi-menu-button");
        const navigation = document.querySelector(".agachichi-navigation");

        if (!menuButton || !navigation) {
            return;
        }

        menuButton.addEventListener("click", () => {
            const isOpen = navigation.classList.toggle("is-open");
            menuButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
        });
    };

    ready(initialize);
})();
