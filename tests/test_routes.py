"""Tests for Flask route handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from gohome import create_app

if TYPE_CHECKING:
    from pathlib import Path

    from flask.testing import FlaskClient

_QUERY_DIRECTORY_YML = """\
directory:
  - name: Plain
    url: https://x.test/page
  - name: Existing
    url: https://x.test/?a=1
  - name: Fragment
    url: https://x.test/page#sec
  - name: Both
    url: https://x.test/page?a=1#sec
"""


def _query_client(tmp_path: Path) -> FlaskClient:
    """Build a test client for links with pre-existing queries and fragments."""
    (tmp_path / "directory.yml").write_text(_QUERY_DIRECTORY_YML, encoding="utf-8")
    application = create_app(str(tmp_path))
    application.config["TESTING"] = True
    return application.test_client()


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


class TestQueryPassthrough:
    """Verify the incoming query string is forwarded to the target URL."""

    def test_query_appended(self, client: FlaskClient) -> None:
        """A query string is appended to a target without one."""
        response = client.get("/kagi?q=hello")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://kagi.com?q=hello"

    def test_no_query_leaves_url_unchanged(self, client: FlaskClient) -> None:
        """Without a query string the target is the configured URL."""
        response = client.get("/kagi")
        assert response.headers["Location"] == "https://kagi.com"

    def test_empty_query_leaves_url_unchanged(self, client: FlaskClient) -> None:
        """A bare trailing ``?`` adds nothing to the target."""
        response = client.get("/kagi?")
        assert response.headers["Location"] == "https://kagi.com"

    def test_raw_encoding_preserved(self, client: FlaskClient) -> None:
        """Percent-encoding and ``+`` pass through byte for byte."""
        response = client.get("/kagi?q=a%20b+c%2Fd&x=%E2%9C%93")
        assert response.headers["Location"] == (
            "https://kagi.com?q=a%20b+c%2Fd&x=%E2%9C%93"
        )

    def test_existing_query_joined_with_ampersand(self, tmp_path: Path) -> None:
        """A target that already has a query gets ``&`` plus the new one."""
        response = _query_client(tmp_path).get("/existing?q=hello")
        assert response.headers["Location"] == "https://x.test/?a=1&q=hello"

    def test_query_goes_before_fragment(self, tmp_path: Path) -> None:
        """The query is inserted ahead of the target's fragment."""
        response = _query_client(tmp_path).get("/fragment?q=hello")
        assert response.headers["Location"] == "https://x.test/page?q=hello#sec"

    def test_existing_query_and_fragment(self, tmp_path: Path) -> None:
        """A target with both gets the query joined and the fragment kept last."""
        response = _query_client(tmp_path).get("/both?q=hello")
        assert response.headers["Location"] == "https://x.test/page?a=1&q=hello#sec"

    def test_category_page_ignores_query(self, client: FlaskClient) -> None:
        """Category pages still render normally with a query string."""
        response = client.get("/streaming?q=hello")
        assert response.status_code == 200

    def test_unknown_slug_redirects_to_root_without_query(
        self, client: FlaskClient
    ) -> None:
        """Unknown slugs still redirect to ``/`` and drop the query."""
        response = client.get("/nope?q=hello")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"


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


class TestAccentFolding:
    """Request paths fold accents the same way slugs do."""

    @pytest.fixture
    def accent_client(self, tmp_path: Path) -> FlaskClient:
        """Build a client for a directory with an accented link name."""
        (tmp_path / "directory.yml").write_text(
            "directory:\n  - name: Café\n    url: https://cafe.example.com\n",
            encoding="utf-8",
        )
        app = create_app(str(tmp_path))
        app.config["TESTING"] = True
        return app.test_client()

    @pytest.mark.parametrize("path", ["/café", "/cafe", "/Café"])
    def test_accented_and_plain_paths_resolve(
        self, accent_client: FlaskClient, path: str
    ) -> None:
        """Both the accented and plain forms redirect to the link."""
        response = accent_client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "https://cafe.example.com"
