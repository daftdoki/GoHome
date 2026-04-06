"""Tests for Tailscale identity header display.

Tailscale serve proxies requests and adds identity headers.  GoHome reads
these headers only when listening on localhost, preventing header injection
from untrusted sources.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from gohome import create_app
from gohome.models import AppConfig

if TYPE_CHECKING:
    from flask.testing import FlaskClient


class TestAppConfigIsLocalhost:
    """Verify the is_localhost property on AppConfig."""

    def test_ipv4_loopback(self) -> None:
        """127.0.0.1 is recognised as localhost."""
        assert AppConfig(host="127.0.0.1").is_localhost is True

    def test_ipv6_loopback(self) -> None:
        """::1 is recognised as localhost."""
        assert AppConfig(host="::1").is_localhost is True

    def test_localhost_string(self) -> None:
        """The string 'localhost' is recognised as localhost."""
        assert AppConfig(host="localhost").is_localhost is True

    def test_all_interfaces_is_not_localhost(self) -> None:
        """0.0.0.0 binds to all interfaces and is not localhost."""
        assert AppConfig(host="0.0.0.0").is_localhost is False

    def test_lan_ip_is_not_localhost(self) -> None:
        """A LAN IP is not localhost."""
        assert AppConfig(host="192.168.1.1").is_localhost is False

    def test_default_is_not_localhost(self) -> None:
        """The default host (0.0.0.0) is not localhost."""
        assert AppConfig().is_localhost is False


_DIRECTORY_YML = """\
directory:
  - name: Google
    url: https://google.com
  - name: Streaming
    entries:
      - name: Netflix
        url: https://netflix.com
"""

_TS_HEADERS = {
    "Tailscale-User-Login": "alice@example.com",
    "Tailscale-User-Name": "Alice Smith",
}


@pytest.fixture
def localhost_client(tmp_path: Path) -> FlaskClient:
    """Create a test client for an app listening on localhost."""
    (tmp_path / "directory.yml").write_text(_DIRECTORY_YML, encoding="utf-8")
    (tmp_path / "config.yml").write_text("host: '127.0.0.1'\n", encoding="utf-8")
    app = create_app(str(tmp_path))
    app.config["TESTING"] = True
    return app.test_client()


class TestTailscaleHeadersLocalhost:
    """Verify Tailscale header display when listening on localhost."""

    def test_both_headers_shown(self, localhost_client: FlaskClient) -> None:
        """Both Tailscale identity values appear in the page."""
        html = localhost_client.get("/", headers=_TS_HEADERS).get_data(
            as_text=True,
        )
        assert "Tailscale ID:" in html
        assert "Alice Smith" in html
        assert "alice@example.com" in html
        assert "tailscale-user" in html

    def test_only_login_shown(self, localhost_client: FlaskClient) -> None:
        """Only the login appears when the name header is absent."""
        html = localhost_client.get(
            "/",
            headers={"Tailscale-User-Login": "alice@example.com"},
        ).get_data(as_text=True)
        assert "alice@example.com" in html
        assert "tailscale-user" in html

    def test_only_name_shown(self, localhost_client: FlaskClient) -> None:
        """Only the display name appears when the login header is absent."""
        html = localhost_client.get(
            "/",
            headers={"Tailscale-User-Name": "Alice Smith"},
        ).get_data(as_text=True)
        assert "Alice Smith" in html
        assert "tailscale-user" in html

    def test_no_headers_no_element(self, localhost_client: FlaskClient) -> None:
        """Without Tailscale headers the element is not rendered."""
        html = localhost_client.get("/").get_data(as_text=True)
        assert "tailscale-user" not in html

    def test_headers_on_category_page(self, localhost_client: FlaskClient) -> None:
        """Tailscale identity appears on category pages too."""
        html = localhost_client.get("/streaming", headers=_TS_HEADERS).get_data(
            as_text=True,
        )
        assert "Alice Smith" in html
        assert "alice@example.com" in html


class TestTailscaleHeadersNonLocalhost:
    """Verify Tailscale headers are ignored when NOT on localhost."""

    def test_headers_not_shown(self, client: FlaskClient) -> None:
        """Even with Tailscale headers, they are not rendered."""
        html = client.get("/", headers=_TS_HEADERS).get_data(as_text=True)
        assert "Alice Smith" not in html
        assert "alice@example.com" not in html

    def test_no_tailscale_div(self, client: FlaskClient) -> None:
        """The tailscale-user div never appears."""
        html = client.get("/", headers=_TS_HEADERS).get_data(as_text=True)
        assert "tailscale-user" not in html
