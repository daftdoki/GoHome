"""Flask route handlers for the GoHome application.

Defines the root directory page, slug-based redirects and category
pages, custom theme CSS serving, and a ``Cache-Control: no-cache`` hook
for HTML responses.
"""

from __future__ import annotations

from pathlib import Path

import werkzeug
from flask import Flask, Response, abort, redirect, render_template

from gohome.models import AppConfig, Directory, LinkEntry
from gohome.normalize import normalize_name
from gohome.themes import resolve_theme


def register_routes(app: Flask) -> None:
    """Register all GoHome URL rules and after-request hooks on *app*.

    Args:
        app: The Flask application to attach routes to.
    """

    @app.after_request
    def _add_cache_control(response: Response) -> Response:
        """Add ``Cache-Control: no-cache`` to HTML responses."""
        content_type = response.content_type or ""
        if "text/html" in content_type:
            response.headers["Cache-Control"] = "no-cache"
        return response

    @app.route("/")
    def root() -> str:
        """Render the full link directory page."""
        app_config: AppConfig = app.config["GOHOME_APP_CONFIG"]
        directory: Directory = app.config["GOHOME_DIRECTORY"]
        themes: list[str] = app.config["GOHOME_THEMES"]

        active_theme = resolve_theme(app_config.default_theme, themes, "default")
        active_mode = ""

        return render_template(
            "base.html",
            site_title=app_config.site_title,
            page_title=None,
            page_description=None,
            items=directory.items,
            breadcrumbs=[("Home", None)],
            themes=themes,
            active_theme=active_theme,
            active_mode=active_mode,
            default_theme=app_config.default_theme,
        )

    @app.route("/<path:path>")
    def resolve_path(path: str) -> werkzeug.wrappers.Response | str:
        """Resolve a URL path to a link redirect or category page.

        Single-segment paths are normalized and looked up in the directory.
        Multi-segment paths and unknown slugs redirect to the root page.

        Args:
            path: The URL path after the domain.

        Returns:
            A 302 redirect for links and unknown paths, or rendered HTML
            for categories.
        """
        # Multi-segment paths are not supported — redirect to root
        if "/" in path:
            return redirect("/", code=302)

        app_config: AppConfig = app.config["GOHOME_APP_CONFIG"]
        directory: Directory = app.config["GOHOME_DIRECTORY"]
        themes: list[str] = app.config["GOHOME_THEMES"]
        slug = normalize_name(path)
        item = directory.slug_map.get(slug)

        if item is None:
            return redirect("/", code=302)

        if isinstance(item, LinkEntry):
            return redirect(item.url, code=302)

        # CategoryEntry — render the category page
        active_theme = resolve_theme(app_config.default_theme, themes, "default")
        active_mode = ""

        return render_template(
            "base.html",
            site_title=app_config.site_title,
            page_title=item.name,
            page_description=item.description,
            items=item.entries,
            breadcrumbs=[("Home", "/"), (item.name, None)],
            themes=themes,
            active_theme=active_theme,
            active_mode=active_mode,
            default_theme=app_config.default_theme,
        )

    @app.route("/themes/<theme_name>.css")
    def serve_theme_css(theme_name: str) -> Response:
        """Serve a custom theme CSS file from the config directory.

        Args:
            theme_name: The theme name (without ``.css`` extension).

        Returns:
            The CSS file contents with ``text/css`` content type.
        """
        app_config: AppConfig = app.config["GOHOME_APP_CONFIG"]
        css_path = Path(app_config.config_dir) / "themes" / f"{theme_name}.css"
        if not css_path.is_file():
            abort(404)
        return Response(
            css_path.read_text(encoding="utf-8"),
            mimetype="text/css",
        )
