"""Tests for theme discovery and resolution."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from gohome.themes import discover_themes, resolve_theme

if TYPE_CHECKING:
    from flask.testing import FlaskClient


class TestDiscoverThemes:
    """Verify theme discovery from config directories."""

    def test_default_only(self, tmp_path: Path) -> None:
        """With no themes directory, only 'default' is returned."""
        themes = discover_themes(str(tmp_path))
        assert themes == ["default"]

    def test_custom_themes(self, tmp_path: Path) -> None:
        """CSS files in themes/ are discovered alongside default."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "nord.css").write_text("/* nord */", encoding="utf-8")
        (themes_dir / "dracula.css").write_text("/* dracula */", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert themes[0] == "default"
        assert "nord" in themes
        assert "dracula" in themes

    def test_non_css_files_ignored(self, tmp_path: Path) -> None:
        """Non-CSS files in themes/ are ignored."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "readme.txt").write_text("not a theme", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert themes == ["default"]

    def test_no_duplicate_default(self, tmp_path: Path) -> None:
        """A themes/default.css file does not create a duplicate entry."""
        themes_dir = tmp_path / "themes"
        themes_dir.mkdir()
        (themes_dir / "default.css").write_text("/* override */", encoding="utf-8")
        themes = discover_themes(str(tmp_path))
        assert themes.count("default") == 1


class TestResolveTheme:
    """Verify theme resolution and fallback logic."""

    def test_requested_available(self) -> None:
        """An available requested theme is returned as-is."""
        assert resolve_theme("nord", ["default", "nord"], "default") == "nord"

    def test_requested_unavailable_falls_to_default(self) -> None:
        """An unavailable requested theme falls back to the admin default."""
        assert resolve_theme("gone", ["default", "nord"], "nord") == "nord"

    def test_both_unavailable_falls_to_builtin(self) -> None:
        """If both requested and admin default are gone, use 'default'."""
        assert resolve_theme("gone", ["default"], "also-gone") == "default"


class TestThemeCSSRoute:
    """Verify the custom theme CSS serving route."""

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
        """A non-existent theme CSS file returns 404."""
        response = client.get("/themes/nonexistent.css")
        assert response.status_code == 404
