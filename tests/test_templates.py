"""Tests for the Jinja2 template rendering."""

from __future__ import annotations

import importlib.metadata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient


class TestRootTemplate:
    """Verify the root page template renders correctly."""

    def test_site_title_in_heading(self, client: FlaskClient) -> None:
        """The site title appears in the heading."""
        html = client.get("/").get_data(as_text=True)
        assert "<h1>GoHome</h1>" in html

    def test_title_tag_root(self, client: FlaskClient) -> None:
        """The <title> on the root page shows only the site title."""
        html = client.get("/").get_data(as_text=True)
        assert "<title>GoHome</title>" in html

    def test_link_names_rendered(self, client: FlaskClient) -> None:
        """All top-level link names appear in the rendered HTML."""
        html = client.get("/").get_data(as_text=True)
        assert "Google" in html
        assert "Kagi" in html

    def test_category_heading_rendered(self, client: FlaskClient) -> None:
        """Category headings appear in the rendered HTML."""
        html = client.get("/").get_data(as_text=True)
        assert "Streaming" in html

    def test_nested_link_names_rendered(self, client: FlaskClient) -> None:
        """Links inside categories appear on the root page."""
        html = client.get("/").get_data(as_text=True)
        assert "Netflix" in html
        assert "YouTube" in html

    def test_descriptions_rendered(self, client: FlaskClient) -> None:
        """Link and category descriptions appear inline with ' - ' prefix."""
        html = client.get("/").get_data(as_text=True)
        assert " - A search engine" in html
        assert " - Video services" in html

    def test_slugs_rendered_with_aliases(self, client: FlaskClient) -> None:
        """Entries with aliases show primary slug and alias slugs."""
        html = client.get("/").get_data(as_text=True)
        assert "google, search" in html

    def test_nested_slugs_rendered(self, client: FlaskClient) -> None:
        """Nested link aliases show primary slug and alias slugs."""
        html = client.get("/").get_data(as_text=True)
        assert "netflix, nf" in html

    def test_no_also_prefix(self, client: FlaskClient) -> None:
        """The 'Also:' prefix is no longer used."""
        html = client.get("/").get_data(as_text=True)
        assert "Also:" not in html

    def test_primary_slug_always_shown(self, client: FlaskClient) -> None:
        """Every entry shows at least its primary slug."""
        html = client.get("/").get_data(as_text=True)
        for slug in ("google", "kagi", "netflix", "youtube", "streaming"):
            assert slug in html

    def test_description_inline_with_link(self, client: FlaskClient) -> None:
        """Descriptions appear inline with the link name, prefixed by ' - '."""
        html = client.get("/").get_data(as_text=True)
        assert " - A search engine" in html

    def test_breadcrumbs_root(self, client: FlaskClient) -> None:
        """The root page shows 'Home' as plain text (no link)."""
        html = client.get("/").get_data(as_text=True)
        assert "<span>Home</span>" in html

    def test_category_nav_in_header(self, client: FlaskClient) -> None:
        """The category nav is inside the header, not in main."""
        html = client.get("/").get_data(as_text=True)
        header_start = html.index("<header>")
        header_end = html.index("</header>")
        main_start = html.index("<main>")
        main_end = html.index("</main>")
        cat_nav_pos = html.index('class="category-nav"')
        assert header_start < cat_nav_pos < header_end
        assert not (main_start < cat_nav_pos < main_end)

    def test_meta_charset(self, client: FlaskClient) -> None:
        """The template includes a charset meta tag."""
        html = client.get("/").get_data(as_text=True)
        assert '<meta charset="utf-8">' in html

    def test_meta_viewport(self, client: FlaskClient) -> None:
        """The template includes a viewport meta tag."""
        html = client.get("/").get_data(as_text=True)
        assert "viewport" in html

    def test_theme_select_in_footer(self, client: FlaskClient) -> None:
        """The footer contains a theme select dropdown."""
        html = client.get("/").get_data(as_text=True)
        assert 'id="theme-select"' in html

    def test_mode_select_in_footer(self, client: FlaskClient) -> None:
        """The footer contains a mode select dropdown."""
        html = client.get("/").get_data(as_text=True)
        assert 'id="mode-select"' in html

    def test_default_theme_selected(self, client: FlaskClient) -> None:
        """The default theme is pre-selected in the dropdown."""
        html = client.get("/").get_data(as_text=True)
        assert 'value="default" selected' in html

    def test_retro_theme_options_present(self, client: FlaskClient) -> None:
        """All three retro themes appear as options in the dropdown."""
        html = client.get("/").get_data(as_text=True)
        assert 'value="retro-green"' in html
        assert 'value="retro-amber"' in html
        assert 'value="retro-ansi"' in html

    def test_bundled_theme_served_from_static(self, client: FlaskClient) -> None:
        """Bundled themes are linked from the static endpoint, not /themes/."""
        html = client.get("/").get_data(as_text=True)
        assert "/static/default.css" in html


class TestCategoryTemplate:
    """Verify category page template rendering."""

    def test_title_tag_category(self, client: FlaskClient) -> None:
        """The <title> on category pages includes site title and category name."""
        html = client.get("/streaming").get_data(as_text=True)
        assert "<title>GoHome — Streaming</title>" in html

    def test_breadcrumbs_category(self, client: FlaskClient) -> None:
        """Category pages show Home (link) > CategoryName (plain text)."""
        html = client.get("/streaming").get_data(as_text=True)
        assert '<a href="/">Home</a>' in html
        assert "<span>Streaming</span>" in html

    def test_category_links_rendered(self, client: FlaskClient) -> None:
        """Only the category's links appear on its page."""
        html = client.get("/streaming").get_data(as_text=True)
        assert "Netflix" in html
        assert "YouTube" in html

    def test_category_description_rendered(self, client: FlaskClient) -> None:
        """The category description appears on the category page."""
        html = client.get("/streaming").get_data(as_text=True)
        assert "Video services" in html


class TestVersionFooter:
    """Verify the version footer renders on all pages."""

    def test_version_on_root_page(self, client: FlaskClient) -> None:
        """The version string appears on the root page."""
        html = client.get("/").get_data(as_text=True)
        version = importlib.metadata.version("gohome")
        assert f"GoHome Version {version}" in html

    def test_version_on_category_page(self, client: FlaskClient) -> None:
        """The version string appears on category pages."""
        html = client.get("/streaming").get_data(as_text=True)
        version = importlib.metadata.version("gohome")
        assert f"GoHome Version {version}" in html

    def test_version_matches_package_metadata(self, client: FlaskClient) -> None:
        """The rendered version matches importlib.metadata."""
        html = client.get("/").get_data(as_text=True)
        version = importlib.metadata.version("gohome")
        assert version in html

    def test_github_link_rendered(self, client: FlaskClient) -> None:
        """The GitHub repo link is rendered as a clickable anchor."""
        html = client.get("/").get_data(as_text=True)
        assert '<a href="https://github.com/daftdoki/GoHome">' in html
