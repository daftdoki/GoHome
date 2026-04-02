"""End-to-end browser tests for GoHome.

These tests exercise JavaScript behaviour and full browser rendering that
the Flask test client cannot verify: theme and mode switching via
JS-driven cookie writes and page reloads, cookie persistence across
navigation, directory page DOM rendering, and category navigation.
"""

from __future__ import annotations

from playwright.sync_api import Page, expect


# ---------------------------------------------------------------------------
# Theme switching (JS sets cookie + reloads)
# ---------------------------------------------------------------------------


class TestThemeSwitching:
    """Verify that the JS-driven theme selector works end-to-end."""

    def test_theme_select_changes_stylesheet(self, page: Page) -> None:
        """Selecting a theme reloads the page with the new theme CSS."""
        page.goto("/")

        with page.expect_navigation():
            page.select_option("#theme-select", "retro-green")

        href = page.locator("link[rel='stylesheet']").get_attribute("href")
        assert href is not None
        assert "retro-green" in href

    def test_theme_cookie_set_on_change(self, page: Page) -> None:
        """Selecting a theme sets the ``gohome_theme`` cookie."""
        page.goto("/")

        with page.expect_navigation():
            page.select_option("#theme-select", "retro-amber")

        cookies = page.context.cookies()
        theme_cookie = next((c for c in cookies if c["name"] == "gohome_theme"), None)
        assert theme_cookie is not None
        assert theme_cookie["value"] == "retro-amber"


# ---------------------------------------------------------------------------
# Mode switching (JS sets/deletes cookie + reloads)
# ---------------------------------------------------------------------------


class TestModeSwitching:
    """Verify that the JS-driven mode selector works end-to-end."""

    def test_mode_select_dark(self, page: Page) -> None:
        """Selecting 'Dark' adds the ``dark`` class to ``<body>``."""
        page.goto("/")

        with page.expect_navigation():
            page.select_option("#mode-select", "dark")

        expect(page.locator("body")).to_have_class("dark")

    def test_mode_select_light(self, page: Page) -> None:
        """Selecting 'Light' adds the ``light`` class to ``<body>``."""
        page.goto("/")

        with page.expect_navigation():
            page.select_option("#mode-select", "light")

        expect(page.locator("body")).to_have_class("light")

    def test_mode_auto_clears_cookie(self, page: Page) -> None:
        """Selecting 'Auto' after 'Dark' removes the body class and cookie."""
        page.goto("/")

        # First set dark mode
        with page.expect_navigation():
            page.select_option("#mode-select", "dark")

        # Then switch to Auto
        with page.expect_navigation():
            page.select_option("#mode-select", "")

        body_class = page.locator("body").get_attribute("class") or ""
        assert "dark" not in body_class
        assert "light" not in body_class

        cookies = page.context.cookies()
        mode_cookie = next((c for c in cookies if c["name"] == "gohome_mode"), None)
        assert mode_cookie is None


# ---------------------------------------------------------------------------
# Cookie persistence across navigation
# ---------------------------------------------------------------------------


class TestCookiePersistence:
    """Verify that theme and mode preferences survive page navigation."""

    def test_theme_persists_across_navigation(self, page: Page) -> None:
        """Theme selection persists when navigating to a category page."""
        page.goto("/")

        with page.expect_navigation():
            page.select_option("#theme-select", "retro-amber")

        # Navigate to category page
        page.goto("/streaming")

        href = page.locator("link[rel='stylesheet']").get_attribute("href")
        assert href is not None
        assert "retro-amber" in href

    def test_mode_persists_across_navigation(self, page: Page) -> None:
        """Mode selection persists when navigating to a category page."""
        page.goto("/")

        with page.expect_navigation():
            page.select_option("#mode-select", "dark")

        page.goto("/streaming")

        expect(page.locator("body")).to_have_class("dark")


# ---------------------------------------------------------------------------
# Directory page rendering
# ---------------------------------------------------------------------------


class TestDirectoryRendering:
    """Verify that the directory page renders correctly in a real browser."""

    def test_top_level_links_visible(self, page: Page) -> None:
        """Top-level links are visible on the root page."""
        page.goto("/")
        expect(page.locator(".link a", has_text="Google")).to_be_visible()
        expect(page.locator(".link a", has_text="Wikipedia")).to_be_visible()
        expect(page.locator(".link a", has_text="Kagi")).to_be_visible()

    def test_categories_visible(self, page: Page) -> None:
        """Category headings are visible on the root page."""
        page.goto("/")
        expect(page.locator(".category h2", has_text="Streaming")).to_be_visible()
        expect(page.locator(".category h2", has_text="Development")).to_be_visible()

    def test_descriptions_visible(self, page: Page) -> None:
        """Link descriptions are rendered and visible."""
        page.goto("/")
        expect(
            page.locator(".description", has_text="most popular search engine")
        ).to_be_visible()

    def test_aliases_visible(self, page: Page) -> None:
        """Alias labels are rendered for links that have them."""
        page.goto("/")
        expect(page.locator(".aliases", has_text="search")).to_be_visible()

    def test_nested_links_visible(self, page: Page) -> None:
        """Links nested inside categories are visible on the root page."""
        page.goto("/")
        expect(page.locator(".category .link a", has_text="Netflix")).to_be_visible()
        expect(page.locator(".category .link a", has_text="YouTube")).to_be_visible()
        expect(page.locator(".category .link a", has_text="GitHub")).to_be_visible()
        expect(
            page.locator(".category .link a", has_text="Stack Overflow")
        ).to_be_visible()


# ---------------------------------------------------------------------------
# Category navigation
# ---------------------------------------------------------------------------


class TestCategoryNavigation:
    """Verify clicking into and out of category pages."""

    def test_click_category_loads_category_page(self, page: Page) -> None:
        """Clicking a category heading navigates to its listing page."""
        page.goto("/")

        page.locator(".category h2 a", has_text="Streaming").click()
        page.wait_for_load_state("load")

        # Category page shows its title and links
        expect(page.locator("h2", has_text="Streaming")).to_be_visible()
        expect(page.locator(".link a", has_text="Netflix")).to_be_visible()
        expect(page.locator(".link a", has_text="YouTube")).to_be_visible()

    def test_category_page_has_breadcrumbs(self, page: Page) -> None:
        """Category pages show breadcrumb navigation."""
        page.goto("/streaming")

        breadcrumbs = page.locator(".breadcrumbs")
        expect(breadcrumbs).to_contain_text("Home")
        expect(breadcrumbs).to_contain_text("Streaming")

    def test_breadcrumb_home_navigates_to_root(self, page: Page) -> None:
        """Clicking 'Home' in breadcrumbs returns to the root page."""
        page.goto("/streaming")

        with page.expect_navigation():
            page.locator(".breadcrumbs a", has_text="Home").click()

        # Back on root — all categories visible
        expect(page.locator(".category h2", has_text="Streaming")).to_be_visible()
        expect(page.locator(".category h2", has_text="Development")).to_be_visible()
