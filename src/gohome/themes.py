"""Theme discovery and resolution for GoHome.

Scans the ``themes/`` subdirectory of the configuration directory for
custom CSS theme files and provides fallback logic when a requested
theme is unavailable.
"""

from __future__ import annotations

from pathlib import Path


def discover_themes(config_dir: str) -> list[str]:
    """Discover all available themes.

    Always includes the bundled ``"default"`` theme.  Custom themes are
    ``.css`` files found in ``<config_dir>/themes/``, named after the
    file stem (e.g. ``themes/nord.css`` → ``"nord"``).

    Args:
        config_dir: Path to the configuration directory.

    Returns:
        A sorted list of theme names with ``"default"`` first.
    """
    themes: list[str] = ["default"]
    themes_dir = Path(config_dir) / "themes"
    if themes_dir.is_dir():
        for css_file in sorted(themes_dir.glob("*.css")):
            name = css_file.stem
            if name != "default":
                themes.append(name)
    return themes


def resolve_theme(requested: str, available: list[str], default: str) -> str:
    """Resolve a requested theme to an available one.

    If the requested theme is available, return it.  Otherwise fall back
    to the admin's configured default.  If even that is unavailable, fall
    back to ``"default"``.

    Args:
        requested: The theme name the user requested (e.g. from a cookie).
        available: The list of available theme names.
        default: The admin's configured default theme.

    Returns:
        The name of the theme to use.
    """
    if requested in available:
        return requested
    if default in available:
        return default
    return "default"
