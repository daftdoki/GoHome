"""Tests for Flask route handlers."""

from __future__ import annotations

import logging
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


def _client_for(tmp_path: Path, directory_yml: str) -> FlaskClient:
    """Build a test client for an app loaded from *directory_yml*."""
    (tmp_path / "directory.yml").write_text(directory_yml, encoding="utf-8")
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

    def test_raw_non_ascii_bytes_percent_encoded_once(
        self, client: FlaskClient
    ) -> None:
        """Raw UTF-8 query bytes become single percent-escapes."""
        response = client.get(
            "/kagi", environ_overrides={"QUERY_STRING": "q=caf\xc3\xa9"}
        )
        assert response.headers["Location"] == "https://kagi.com?q=caf%C3%A9"

    def test_raw_hash_in_query_encoded(self, tmp_path: Path) -> None:
        """A raw ``#`` in the query is escaped so the target fragment survives."""
        client = _client_for(tmp_path, _QUERY_DIRECTORY_YML)
        response = client.get("/fragment", environ_overrides={"QUERY_STRING": "q=a#b"})
        assert response.headers["Location"] == "https://x.test/page?q=a%23b#sec"

    def test_existing_query_joined_with_ampersand(self, tmp_path: Path) -> None:
        """A target that already has a query gets ``&`` plus the new one."""
        response = _client_for(tmp_path, _QUERY_DIRECTORY_YML).get("/existing?q=hello")
        assert response.headers["Location"] == "https://x.test/?a=1&q=hello"

    def test_query_goes_before_fragment(self, tmp_path: Path) -> None:
        """The query is inserted ahead of the target's fragment."""
        response = _client_for(tmp_path, _QUERY_DIRECTORY_YML).get("/fragment?q=hello")
        assert response.headers["Location"] == "https://x.test/page?q=hello#sec"

    def test_existing_query_and_fragment(self, tmp_path: Path) -> None:
        """A target with both gets the query joined and the fragment kept last."""
        response = _client_for(tmp_path, _QUERY_DIRECTORY_YML).get("/both?q=hello")
        assert response.headers["Location"] == "https://x.test/page?a=1&q=hello#sec"

    def test_category_page_ignores_query(self, client: FlaskClient) -> None:
        """Category pages still render normally with a query string."""
        response = client.get("/streaming?q=hello")
        assert response.status_code == 200

    def test_unknown_slug_drops_query(self, client: FlaskClient) -> None:
        """Unknown slugs redirect to the not-found notice and drop the query."""
        response = client.get("/nope?q=hello")
        assert response.status_code == 302
        assert response.headers["Location"] == "/?notfound=nope"


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
        """An unknown single-segment path redirects with a notfound hint."""
        response = client.get("/nonexistent")
        assert response.status_code == 302
        assert response.headers["Location"] == "/?notfound=nonexistent"

    def test_unknown_path_is_url_encoded(self, client: FlaskClient) -> None:
        """Special characters in the requested path are percent-encoded."""
        response = client.get("/a%20b%26c%3Cd")
        assert response.status_code == 302
        assert response.headers["Location"] == "/?notfound=a%20b%26c%3Cd"

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
        return _client_for(
            tmp_path, "directory:\n  - name: Café\n    url: https://cafe.example.com\n"
        )

    @pytest.mark.parametrize("path", ["/café", "/cafe", "/Café"])
    def test_accented_and_plain_paths_resolve(
        self, accent_client: FlaskClient, path: str
    ) -> None:
        """Both the accented and plain forms redirect to the link."""
        response = accent_client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"] == "https://cafe.example.com"


class TestFavicon:
    """Verify /favicon.ico serves the bundled icon."""

    def test_favicon_served(self, client: FlaskClient) -> None:
        """/favicon.ico returns the icon, not a redirect."""
        response = client.get("/favicon.ico")
        assert response.status_code == 200
        assert response.mimetype in ("image/x-icon", "image/vnd.microsoft.icon")
        assert response.get_data()[:4] == b"\x00\x00\x01\x00"
        response.close()


class TestNotFoundNotice:
    """Verify the notfound notice on the root page."""

    def test_notice_shown(self, client: FlaskClient) -> None:
        """A notfound value renders a status notice naming the link."""
        html = client.get("/?notfound=foo").get_data(as_text=True)
        assert 'class="notfound"' in html
        assert 'role="status"' in html
        assert 'No link named "foo"' in html

    def test_notice_absent_by_default(self, client: FlaskClient) -> None:
        """The notice is not rendered without the parameter."""
        html = client.get("/").get_data(as_text=True)
        assert "notfound" not in html

    def test_notice_absent_when_empty(self, client: FlaskClient) -> None:
        """An empty notfound value renders no notice."""
        html = client.get("/?notfound=").get_data(as_text=True)
        assert 'class="notfound"' not in html

    def test_notice_shows_normalized_slug(self, client: FlaskClient) -> None:
        """The notice shows the slug, so HTML and prose cannot be injected."""
        html = client.get("/?notfound=<script>alert(1)</script>").get_data(as_text=True)
        assert "<script>alert" not in html
        assert "&lt;script" not in html
        assert 'No link named "scriptalert1script"' in html

    def test_notice_rejects_spoofed_text(self, client: FlaskClient) -> None:
        """Crafted prose is reduced to a slug instead of shown as written."""
        html = client.get("/?notfound=Links moved, sign in at evil.example").get_data(
            as_text=True
        )
        assert "sign in at" not in html
        assert 'No link named "links-moved-sign-in-at-evilexample"' in html

    def test_notice_absent_when_slug_empty(self, client: FlaskClient) -> None:
        """A value with no slug characters renders no notice."""
        html = client.get("/?notfound=!!!").get_data(as_text=True)
        assert 'class="notfound"' not in html

    def test_notice_truncated(self, client: FlaskClient) -> None:
        """Values longer than 100 characters are cut to 100."""
        html = client.get("/?notfound=" + "x" * 300).get_data(as_text=True)
        assert "x" * 100 in html
        assert "x" * 101 not in html

    def test_redirect_then_notice(self, client: FlaskClient) -> None:
        """Following an unknown-path redirect shows the notice."""
        response = client.get("/nonexistent", follow_redirects=True)
        assert 'No link named "nonexistent"' in response.get_data(as_text=True)


class TestAccessLog:
    """Verify each request is logged, since waitress has no access log."""

    def test_redirect_logged(
        self, client: FlaskClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A link redirect logs the method, path, status and target."""
        with caplog.at_level(logging.INFO, logger="gohome.routes"):
            client.get("/google?q=1")
        assert "GET /google?q=1 302 -> https://google.com?q=1" in caplog.text

    def test_page_logged(
        self, client: FlaskClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A page request logs the method, path and status."""
        with caplog.at_level(logging.INFO, logger="gohome.routes"):
            client.get("/")
        assert "GET / 200" in caplog.text

    def test_control_characters_escaped(
        self, client: FlaskClient, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A decoded newline in the path can't forge a second log line."""
        with caplog.at_level(logging.INFO, logger="gohome.routes"):
            client.get("/foo%0aERROR:%20fake%0d%09line")
        messages = [r.getMessage() for r in caplog.records]
        assert not any(c in m for m in messages for c in "\r\n\t")
        assert any("GET /foo%0AERROR: fake%0D%09line " in m for m in messages)
