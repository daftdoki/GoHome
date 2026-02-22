"""Tests for theme discovery and resolution."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from gohome.themes import BUNDLED_THEMES, discover_themes, resolve_theme

if TYPE_CHECKING:
    from flask.testing import FlaskClient


class TestBundledThemes:
    """Verify the BUNDLED_THEMES constant."""

    def test_default_is_bundled(self) -> None:
        """'default' is always a bundled theme."""
        assert "default" in BUNDLED_THEMES

    def test_retro_green_is_bundled(self) -> None:
        """'retro-green' is a bundled theme."""
        assert "retro-green" in BUNDLED_THEMES

    def test_retro_amber_is_bundled(self) -> None:
        """'retro-amber' is a bundled theme."""
        assert "retro-amber" in BUNDLED_THEMES

    def test_retro_ansi_is_bundled(self) -> None:
        """'retro-ansi' is a bundled theme."""
        assert "retro-ansi" in BUNDLED_THEMES


class TestDiscoverThemes:
    """Verify theme discovery from config directories."""

    def test_bundled_themes_always_present(self, tmp_path: Path) -> None:
        """All bundled themes appear even with no config-dir themes directory."""
        themes = discover_themes(str(tmp_path))
        for name in BUNDLED_THEMES:
            assert name in themes

    def test_bundled_themes_come_first(self, tmp_path: Path) -> None:
        """Bundled themes occupy the leading positions in the list."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "zzz.css").write_text("/* zzz */", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        bundled = list(BUNDLED_THEMES)
        assert themes[: len(bundled)] == bundled

    def test_custom_themes_appended(self, tmp_path: Path) -> None:
        """CSS files in themes/ are appended after bundled themes."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "nord.css").write_text("/* nord */", encoding="utf-8")
        (themes_dir / "dracula.css").write_text("/* dracula */", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert "nord" in themes
        assert "dracula" in themes

    def test_non_css_files_ignored(self, tmp_path: Path) -> None:
        """Non-CSS files in themes/ are ignored."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "readme.txt").write_text("not a theme", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert "readme" not in themes

    def test_no_duplicate_default(self, tmp_path: Path) -> None:
        """A themes/default.css file does not create a duplicate entry."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "default.css").write_text("/* override */", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert themes.count("default") == 1

    def test_custom_cannot_shadow_bundled(self, tmp_path: Path) -> None:
        """A custom theme/retro-green.css cannot shadow the bundled retro-green theme."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "retro-green.css").write_text("/* fake */", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert themes.count("retro-green") == 1


class TestResolveTheme:
    """Verify theme resolution and fallback logic."""

    def test_requested_available(self) -> None:
        """An available requested theme is returned as-is."""
        assert (
            resolve_theme("nord", ["default", "retro-green", "nord"], "default")
            == "nord"
        )

    def test_requested_unavailable_falls_to_default(self) -> None:
        """An unavailable requested theme falls back to the admin default."""
        assert (
            resolve_theme("gone", ["default", "retro-green", "nord"], "nord") == "nord"
        )

    def test_both_unavailable_falls_to_builtin(self) -> None:
        """If both requested and admin default are gone, use 'default'."""
        assert resolve_theme("gone", ["default"], "also-gone") == "default"

    def test_retro_green_resolves(self) -> None:
        """The retro-green theme resolves when it is in the available list."""
        themes = list(BUNDLED_THEMES)
        assert resolve_theme("retro-green", themes, "default") == "retro-green"


class TestThemeCSSRoute:
    """Verify CSS serving for bundled and custom themes."""

    def test_bundled_default_css_served_from_static(self, client: FlaskClient) -> None:
        """The bundled default theme is served from the static endpoint."""
        response = client.get("/static/default.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type

    def test_bundled_retro_green_css_served_from_static(
        self, client: FlaskClient
    ) -> None:
        """The bundled retro-green theme is served from the static endpoint."""
        response = client.get("/static/retro-green.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type

    def test_bundled_retro_amber_css_served_from_static(
        self, client: FlaskClient
    ) -> None:
        """The bundled retro-amber theme is served from the static endpoint."""
        response = client.get("/static/retro-amber.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type

    def test_bundled_retro_ansi_css_served_from_static(
        self, client: FlaskClient
    ) -> None:
        """The bundled retro-ansi theme is served from the static endpoint."""
        response = client.get("/static/retro-ansi.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type

    def test_custom_theme_served(
        self, sample_config_dir: Path, client: FlaskClient
    ) -> None:
        """A custom theme CSS file is served with text/css content type."""
        themes_dir = sample_config_dir / "themes"
        themes_dir.mkdir()
        (themes_dir / "nord.css").write_text("body { color: blue; }", encoding="utf-8")
        response = client.get("/themes/nord.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type
        assert "color: blue" in response.get_data(as_text=True)

    def test_missing_theme_returns_404(self, client: FlaskClient) -> None:
        """A non-existent custom theme CSS file returns 404."""
        response = client.get("/themes/nonexistent.css")
        assert response.status_code == 404
