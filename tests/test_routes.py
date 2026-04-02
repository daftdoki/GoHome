"""Tests for Flask route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient


class TestRootPage:
    """Verify the root directory page."""

    def test_returns_200(self, client: FlaskClient) -> None:
        """The root URL returns HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_contains_link_names(self, client: FlaskClient) -> None:
        """The root page includes all link names."""
        response = client.get("/")
        html = response.get_data(as_text=True)
        assert "Google" in html
        assert "Kagi" in html

    def test_contains_category_heading(self, client: FlaskClient) -> None:
        """The root page includes category headings."""
        response = client.get("/")
        html = response.get_data(as_text=True)
        assert "Streaming" in html

    def test_contains_nested_links(self, client: FlaskClient) -> None:
        """Links inside categories appear on the root page."""
        response = client.get("/")
        html = response.get_data(as_text=True)
        assert "Netflix" in html
        assert "YouTube" in html

    def test_cache_control_header(self, client: FlaskClient) -> None:
        """HTML responses include Cache-Control: no-cache."""
        response = client.get("/")
        assert response.headers.get("Cache-Control") == "no-cache"


class TestLinkRedirect:
    """Verify link name redirects."""

    def test_redirect_to_url(self, client: FlaskClient) -> None:
        """A known link name redirects to its configured URL."""
        response = client.get("/google")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://google.com"

    def test_case_insensitive(self, client: FlaskClient) -> None:
        """Slug lookup is case-insensitive."""
        response = client.get("/GOOGLE")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://google.com"

    def test_nested_link_redirect(self, client: FlaskClient) -> None:
        """Links inside categories are accessible at the top level."""
        response = client.get("/netflix")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://netflix.com"

    def test_redirect_via_alias(self, client: FlaskClient) -> None:
        """An alias slug redirects to the same URL as the primary name."""
        response = client.get("/search")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://google.com"

    def test_redirect_via_nested_alias(self, client: FlaskClient) -> None:
        """An alias on a nested link redirects correctly."""
        response = client.get("/nf")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://netflix.com"


class TestCategoryPage:
    """Verify category rendering."""

    def test_category_returns_200(self, client: FlaskClient) -> None:
        """A known category name returns HTTP 200."""
        response = client.get("/streaming")
        assert response.status_code == 200

    def test_category_contains_links(self, client: FlaskClient) -> None:
        """The category page lists its child links."""
        response = client.get("/streaming")
        html = response.get_data(as_text=True)
        assert "Netflix" in html
        assert "YouTube" in html

    def test_category_breadcrumb(self, client: FlaskClient) -> None:
        """The category page shows breadcrumb navigation."""
        response = client.get("/streaming")
        html = response.get_data(as_text=True)
        assert "Home" in html
        assert "Streaming" in html

    def test_category_title(self, client: FlaskClient) -> None:
        """The category page title includes the site title and category name."""
        response = client.get("/streaming")
        html = response.get_data(as_text=True)
        assert "GoHome — Streaming" in html


class TestUnknownPaths:
    """Verify handling of unknown and multi-segment paths."""

    def test_unknown_path_redirects(self, client: FlaskClient) -> None:
        """An unknown path redirects to the root."""
        response = client.get("/nonexistent")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"

    def test_multi_segment_redirects(self, client: FlaskClient) -> None:
        """Multi-segment paths redirect to the root."""
        response = client.get("/streaming/netflix")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"
