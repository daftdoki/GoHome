"""Theme discovery and resolution for GoHome.

Bundled themes (shipped with the application) are listed in
:data:`BUNDLED_THEMES` and served from Flask's static directory.
Custom themes are ``.css`` files placed by the administrator in a
``themes/`` subdirectory of the configuration directory.
"""

from __future__ import annotations

from pathlib import Path

BUNDLED_THEMES: tuple[str, ...] = (
    "default",
    "retro-green",
    "retro-amber",
    "retro-ansi",
)
"""Names of themes shipped with GoHome, in display order.

Bundled themes:

- ``default``: clean light/dark theme
- ``retro-green``: classic green phosphor CRT terminal
- ``retro-amber``: classic amber phosphor CRT terminal
- ``retro-ansi``: multi-color ANSI terminal palette

These are served from the application's static directory.  Custom
themes in the config directory cannot use these names.
"""


def discover_themes(config_dir: str) -> list[str]:
    """Discover all available themes.

    Bundled themes (from :data:`BUNDLED_THEMES`) always appear first.
    Custom themes are ``.css`` files found in ``<config_dir>/themes/``,
    named after the file stem (e.g. ``themes/nord.css`` → ``"nord"``).
    Custom themes whose names conflict with a bundled theme name are
    silently skipped to prevent shadowing the built-in theme.

    Args:
        config_dir: Path to the configuration directory.

    Returns:
        A list of theme names with bundled themes first, followed by
        any custom themes in alphabetical order.
    """
    themes: list[str] = list(BUNDLED_THEMES)
    bundled_set: frozenset[str] = frozenset(BUNDLED_THEMES)

    themes_dir = Path(config_dir) / "themes"
    if themes_dir.is_dir():
        for css_file in sorted(themes_dir.glob("*.css")):
            name = css_file.stem
            if name not in bundled_set:
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
