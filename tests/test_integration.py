"""Integration tests using the sample configuration directory.

These tests verify the three core scenarios described in the requirements:
1. Root URL returns the directory page with all entries.
2. Link name path returns a 302 redirect to the configured URL.
3. Category name path returns that category's link listing.

Additional scenarios verify unknown paths, multi-segment paths, and
the custom theme CSS endpoint.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from gohome import create_app

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient

SAMPLE_CONFIG_DIR = str(Path(__file__).resolve().parent.parent / "sample_config")


@pytest.fixture
def integration_app() -> Flask:
    """Create a GoHome app from the real sample_config directory."""
    application = create_app(SAMPLE_CONFIG_DIR)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def integration_client(integration_app: Flask) -> FlaskClient:
    """Create a test client for the integration app."""
    return integration_app.test_client()


class TestRootDirectory:
    """Scenario 1: Root URL returns the directory page with all entries."""

    def test_root_returns_200(self, integration_client: FlaskClient) -> None:
        """The root URL responds with HTTP 200."""
        response = integration_client.get("/")
        assert response.status_code == 200

    def test_root_contains_all_links(self, integration_client: FlaskClient) -> None:
        """The root page contains all top-level link names."""
        html = integration_client.get("/").get_data(as_text=True)
        assert "Google" in html
        assert "Wikipedia" in html
        assert "Kagi" in html

    def test_root_contains_categories(self, integration_client: FlaskClient) -> None:
        """The root page contains all category headings."""
        html = integration_client.get("/").get_data(as_text=True)
        assert "Streaming" in html
        assert "Development" in html

    def test_root_contains_nested_links(self, integration_client: FlaskClient) -> None:
        """The root page contains links nested inside categories."""
        html = integration_client.get("/").get_data(as_text=True)
        assert "Netflix" in html
        assert "YouTube" in html
        assert "GitHub" in html
        assert "Stack Overflow" in html

    def test_root_content_type(self, integration_client: FlaskClient) -> None:
        """The root page is served as HTML."""
        response = integration_client.get("/")
        assert "text/html" in response.content_type


class TestLinkRedirect:
    """Scenario 2: Link name path returns a 302 redirect."""

    def test_google_redirect(self, integration_client: FlaskClient) -> None:
        """Visiting /google redirects to https://google.com."""
        response = integration_client.get("/google")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://google.com"

    def test_case_insensitive_redirect(self, integration_client: FlaskClient) -> None:
        """Slug lookup is case-insensitive."""
        response = integration_client.get("/GOOGLE")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://google.com"

    def test_nested_link_redirect(self, integration_client: FlaskClient) -> None:
        """Links inside categories redirect from the top level."""
        response = integration_client.get("/netflix")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://netflix.com"

    def test_hyphenated_name_redirect(self, integration_client: FlaskClient) -> None:
        """Multi-word names with hyphens redirect correctly."""
        response = integration_client.get("/stack-overflow")
        assert response.status_code == 302
        assert response.headers["Location"] == "https://stackoverflow.com"


class TestCategoryListing:
    """Scenario 3: Category name path returns that category's link listing."""

    def test_streaming_returns_200(self, integration_client: FlaskClient) -> None:
        """Visiting /streaming returns HTTP 200."""
        response = integration_client.get("/streaming")
        assert response.status_code == 200

    def test_streaming_contains_category_links(
        self, integration_client: FlaskClient
    ) -> None:
        """The streaming page contains only its category links."""
        html = integration_client.get("/streaming").get_data(as_text=True)
        assert "Netflix" in html
        assert "YouTube" in html

    def test_development_contains_category_links(
        self, integration_client: FlaskClient
    ) -> None:
        """The development page contains its category links."""
        html = integration_client.get("/development").get_data(as_text=True)
        assert "GitHub" in html
        assert "Stack Overflow" in html


class TestUnknownPaths:
    """Verify handling of unknown and multi-segment paths."""

    def test_nonexistent_redirects_to_root(
        self, integration_client: FlaskClient
    ) -> None:
        """An unknown path redirects to the root."""
        response = integration_client.get("/nonexistent")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"

    def test_multi_segment_redirects_to_root(
        self, integration_client: FlaskClient
    ) -> None:
        """Multi-segment paths redirect to the root."""
        response = integration_client.get("/streaming/netflix")
        assert response.status_code == 302
        assert response.headers["Location"] == "/"


class TestThemeCSS:
    """Verify the default theme CSS endpoint."""

    def test_default_css_served(self, integration_client: FlaskClient) -> None:
        """The default theme CSS is served via the static endpoint."""
        response = integration_client.get("/static/default.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type
