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

    /**
     * Delete a cookie by setting its max-age to 0.
     * @param {string} name - Cookie name.
     */
    function deleteCookie(name) {
        document.cookie = name + "=;path=/;max-age=0;SameSite=Lax";
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
    /* Category links — prevent toggle when clicking the navigation link  */
    /* ------------------------------------------------------------------ */
    var categoryLinks = document.querySelectorAll(".category-link");
    for (var i = 0; i < categoryLinks.length; i++) {
        categoryLinks[i].addEventListener("click", function (e) {
            e.stopPropagation();
        });
    }

    /* ------------------------------------------------------------------ */
    /* Mode selector                                                      */
    /* ------------------------------------------------------------------ */
    var modeSelect = document.getElementById("mode-select");
    if (modeSelect) {
        modeSelect.addEventListener("change", function () {
            var newMode = modeSelect.value;
            if (newMode === "") {
                deleteCookie("gohome_mode");
            } else {
                setCookie("gohome_mode", newMode);
            }
            window.location.reload();
        });
    }
})();
