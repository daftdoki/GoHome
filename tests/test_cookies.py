"""Tests for cookie-driven theme and mode selection."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from gohome import create_app

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


class TestNoCookies:
    """Verify behavior when no cookies are set (first visit)."""

    def test_no_body_class(self, client: FlaskClient) -> None:
        """Without cookies, the body has no mode class (empty string)."""
        html = client.get("/").get_data(as_text=True)
        assert '<body class="">' in html

    def test_default_theme_used(self, client: FlaskClient) -> None:
        """Without cookies, the admin's default theme is active."""
        html = client.get("/").get_data(as_text=True)
        assert 'value="default" selected' in html


class TestModeCookie:
    """Verify that the gohome_mode cookie controls the body class."""

    def test_dark_mode_cookie(self, client: FlaskClient) -> None:
        """The dark mode cookie sets body class to 'dark'."""
        client.set_cookie("gohome_mode", "dark")
        html = client.get("/").get_data(as_text=True)
        assert '<body class="dark">' in html

    def test_light_mode_cookie(self, client: FlaskClient) -> None:
        """The light mode cookie sets body class to 'light'."""
        client.set_cookie("gohome_mode", "light")
        html = client.get("/").get_data(as_text=True)
        assert '<body class="light">' in html

    def test_invalid_mode_cookie_ignored(self, client: FlaskClient) -> None:
        """An invalid mode cookie value results in no body class."""
        client.set_cookie("gohome_mode", "invalid")
        html = client.get("/").get_data(as_text=True)
        assert '<body class="">' in html


class TestThemeCookie:
    """Verify that the gohome_theme cookie controls the active theme."""

    def test_theme_cookie_selects_theme(self, sample_config_dir: Path) -> None:
        """A valid theme cookie selects that theme."""
        # Add a custom theme
        themes_dir = sample_config_dir / "themes"
        themes_dir.mkdir()
        (themes_dir / "nord.css").write_text("/* nord */", encoding="utf-8")
        app: Flask = create_app(str(sample_config_dir))
        app.config["TESTING"] = True
        with app.test_client() as c:
            c.set_cookie("gohome_theme", "nord")
            html = c.get("/").get_data(as_text=True)
            assert 'value="nord" selected' in html

    def test_removed_theme_falls_back(self, client: FlaskClient) -> None:
        """A cookie referencing a removed theme falls back to default."""
        client.set_cookie("gohome_theme", "deleted-theme")
        html = client.get("/").get_data(as_text=True)
        assert 'value="default" selected' in html


class TestNoSetCookie:
    """Verify the server never sets cookies."""

    def test_root_no_set_cookie(self, client: FlaskClient) -> None:
        """Root page response has no Set-Cookie header."""
        response = client.get("/")
        assert "Set-Cookie" not in response.headers

    def test_category_no_set_cookie(self, client: FlaskClient) -> None:
        """Category page response has no Set-Cookie header."""
        response = client.get("/streaming")
        assert "Set-Cookie" not in response.headers

    def test_redirect_no_set_cookie(self, client: FlaskClient) -> None:
        """Redirect response has no Set-Cookie header."""
        response = client.get("/google")
        assert "Set-Cookie" not in response.headers
