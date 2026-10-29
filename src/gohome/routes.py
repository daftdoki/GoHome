"""Flask route handlers for the GoHome application.

Defines the root directory page, slug-based redirects and category
pages, the favicon, custom theme CSS serving, and a
``Cache-Control: no-cache`` hook for HTML responses.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import werkzeug
from flask import Flask, Response, abort, redirect, render_template, request

from gohome.models import AppConfig, Directory, LinkEntry
from gohome.normalize import normalize_name
from gohome.themes import resolve_theme

_NOTFOUND_MAX_LENGTH = 100


def append_query(url: str, query: bytes) -> str:
    """Append a raw query string to *url*, ahead of any fragment.

    The query bytes are decoded as Latin-1 so they round-trip unchanged,
    keeping percent-encoding and ``+`` exactly as the client sent them.
    If *url* already has a query, the new one is joined with ``&``.

    Args:
        url: The configured target URL.
        query: The raw incoming query string, without the leading ``?``.

    Returns:
        *url* unchanged when *query* is empty, otherwise *url* with the
        query added.
    """
    if not query:
        return url
    parts = urlsplit(url)
    extra = query.decode("latin-1")
    combined = f"{parts.query}&{extra}" if parts.query else extra
    return urlunsplit(parts._replace(query=combined))


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

    @app.route("/favicon.ico")
    def favicon() -> Response:
        """Serve the bundled favicon at the site root where browsers look."""
        return app.send_static_file("favicon.ico")

    @app.route("/")
    def root() -> str:
        """Render the full link directory page.

        A non-empty ``notfound`` query parameter (set by the redirect for
        unknown paths) adds a notice naming the missing link, truncated to
        ``_NOTFOUND_MAX_LENGTH`` characters.
        """
        app_config: AppConfig = app.config["GOHOME_APP_CONFIG"]
        directory: Directory = app.config["GOHOME_DIRECTORY"]
        themes: list[str] = app.config["GOHOME_THEMES"]
        bundled_themes: frozenset[str] = app.config["GOHOME_BUNDLED_THEMES"]

        active_theme, active_mode = _read_preferences(app_config, themes)

        return render_template(
            "base.html",
            site_title=app_config.site_title,
            page_title=None,
            page_description=None,
            items=directory.items,
            breadcrumbs=[("Home", None)],
            notfound=request.args.get("notfound", "")[:_NOTFOUND_MAX_LENGTH],
            themes=themes,
            active_theme=active_theme,
            active_mode=active_mode,
            default_theme=app_config.default_theme,
            bundled_themes=bundled_themes,
        )

    @app.route("/<path:path>")
    def resolve_path(path: str) -> werkzeug.wrappers.Response | str:
        """Resolve a URL path to a link redirect or category page.

        Single-segment paths are normalized and looked up in the directory.
        Multi-segment paths redirect to the root page. Unknown
        single-segment paths redirect to ``/?notfound=<path>`` so the root
        page can say which link was missing. Link redirects forward the
        request's query string to the target.

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
            return redirect(f"/?notfound={quote(path, safe='')}", code=302)

        if isinstance(item, LinkEntry):
            return redirect(append_query(item.url, request.query_string), code=302)

        # CategoryEntry — render the category page
        bundled_themes: frozenset[str] = app.config["GOHOME_BUNDLED_THEMES"]
        active_theme, active_mode = _read_preferences(app_config, themes)

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
            bundled_themes=bundled_themes,
        )

    def _read_preferences(app_config: AppConfig, themes: list[str]) -> tuple[str, str]:
        """Read theme and mode preferences from cookies.

        Falls back to the admin's default theme if the cookie references
        a removed theme.  Returns an empty mode string when no cookie is
        set (letting the browser's ``prefers-color-scheme`` decide).

        Args:
            app_config: Application configuration.
            themes: Available theme names.

        Returns:
            A ``(active_theme, active_mode)`` tuple.
        """
        cookie_theme = request.cookies.get("gohome_theme", "")
        cookie_mode = request.cookies.get("gohome_mode", "")

        active_theme = resolve_theme(
            cookie_theme if cookie_theme else app_config.default_theme,
            themes,
            app_config.default_theme,
        )
        active_mode = cookie_mode if cookie_mode in ("light", "dark") else ""

        return active_theme, active_mode

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
