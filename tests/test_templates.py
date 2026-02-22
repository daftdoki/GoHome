"""Tests for the Jinja2 template rendering."""

from __future__ import annotations

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
        """Link and category descriptions appear in the HTML."""
        html = client.get("/").get_data(as_text=True)
        assert "A search engine" in html
        assert "Video services" in html

    def test_breadcrumbs_root(self, client: FlaskClient) -> None:
        """The root page shows 'Home' as plain text (no link)."""
        html = client.get("/").get_data(as_text=True)
        assert "<span>Home</span>" in html

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

    def test_mode_toggle_in_footer(self, client: FlaskClient) -> None:
        """The footer contains a mode toggle button."""
        html = client.get("/").get_data(as_text=True)
        assert 'id="mode-toggle"' in html

    def test_default_theme_selected(self, client: FlaskClient) -> None:
        """The default theme is pre-selected in the dropdown."""
        html = client.get("/").get_data(as_text=True)
        assert 'value="default" selected' in html

    def test_retro_theme_option_present(self, client: FlaskClient) -> None:
        """The retro theme appears as an option in the dropdown."""
        html = client.get("/").get_data(as_text=True)
        assert 'value="retro"' in html

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
