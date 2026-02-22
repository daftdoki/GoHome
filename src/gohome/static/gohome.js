/* GoHome — client-side theme and mode management.
 *
 * Reads the current theme and mode from cookies, provides UI controls
 * for switching themes and toggling light/dark mode, and persists
 * preferences via cookies.  The server never sets cookies — all cookie
 * writes happen here.
 */
(function () {
    "use strict";

    /**
     * Set a cookie with a 1-year expiry, path=/, SameSite=Lax.
     * @param {string} name  - Cookie name.
     * @param {string} value - Cookie value.
     */
    function setCookie(name, value) {
        var maxAge = 365 * 24 * 60 * 60; // 1 year in seconds
        document.cookie =
            name +
            "=" +
            encodeURIComponent(value) +
            ";path=/;max-age=" +
            maxAge +
            ";SameSite=Lax";
    }

    /* ------------------------------------------------------------------ */
    /* Theme selector                                                     */
    /* ------------------------------------------------------------------ */
    var themeSelect = document.getElementById("theme-select");
    if (themeSelect) {
        themeSelect.addEventListener("change", function () {
            setCookie("gohome_theme", themeSelect.value);
            window.location.reload();
        });
    }

    /* ------------------------------------------------------------------ */
    /* Mode toggle                                                        */
    /* ------------------------------------------------------------------ */
    var modeToggle = document.getElementById("mode-toggle");
    var body = document.body;

    /**
     * Update the toggle button text to show the opposite mode.
     */
    function updateButtonText() {
        if (!modeToggle) return;
        if (body.classList.contains("dark")) {
            modeToggle.textContent = "Light";
        } else if (body.classList.contains("light")) {
            modeToggle.textContent = "Dark";
        } else {
            modeToggle.textContent = "Toggle Mode";
        }
    }

    if (modeToggle) {
        modeToggle.addEventListener("click", function () {
            var currentMode;
            if (body.classList.contains("dark")) {
                currentMode = "dark";
            } else if (body.classList.contains("light")) {
                currentMode = "light";
            } else {
                /* No class set — detect browser preference */
                if (
                    window.matchMedia &&
                    window.matchMedia("(prefers-color-scheme: dark)").matches
                ) {
                    currentMode = "dark";
                } else {
                    currentMode = "light";
                }
            }

            /* Toggle to the opposite mode */
            var newMode = currentMode === "dark" ? "light" : "dark";
            body.classList.remove("light", "dark");
            body.classList.add(newMode);
            setCookie("gohome_mode", newMode);
            updateButtonText();
        });
    }

    updateButtonText();
})();
