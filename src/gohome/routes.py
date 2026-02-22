"""Flask route handlers for the GoHome application.

Defines the root directory page, slug-based redirects and category
pages, and a ``Cache-Control: no-cache`` hook for HTML responses.
"""

from __future__ import annotations

import werkzeug
from flask import Flask, Response, redirect

from gohome.models import AppConfig, CategoryEntry, Directory, LinkEntry
from gohome.normalize import normalize_name


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

        return _render_directory(app_config, directory)

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
        slug = normalize_name(path)
        item = directory.slug_map.get(slug)

        if item is None:
            return redirect("/", code=302)

        if isinstance(item, LinkEntry):
            return redirect(item.url, code=302)

        # CategoryEntry — render the category page
        return _render_category(app_config, directory, item)

    def _render_directory(app_config: AppConfig, directory: Directory) -> str:
        """Render the root directory page as simple HTML.

        Args:
            app_config: Application configuration.
            directory: The link directory.

        Returns:
            HTML string for the root page.
        """
        lines = [
            "<!DOCTYPE html>",
            "<html><head>",
            f"<title>{app_config.site_title}</title>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "</head><body>",
            f"<h1>{app_config.site_title}</h1>",
            "<nav>Home</nav>",
            '<ul class="directory">',
        ]
        for item in directory.items:
            if isinstance(item, CategoryEntry):
                desc = (
                    f' <span class="description">{item.description}</span>'
                    if item.description
                    else ""
                )
                lines.append(f'<li class="category"><h2>{item.name}</h2>{desc}<ul>')
                for link in item.entries:
                    link_desc = (
                        f' <span class="description">{link.description}</span>'
                        if link.description
                        else ""
                    )
                    lines.append(
                        f'<li class="link"><a href="{link.url}">{link.name}'
                        f"</a>{link_desc}</li>"
                    )
                lines.append("</ul></li>")
            else:
                desc = (
                    f' <span class="description">{item.description}</span>'
                    if item.description
                    else ""
                )
                lines.append(
                    f'<li class="link"><a href="{item.url}">{item.name}</a>{desc}</li>'
                )
        lines.append("</ul>")
        lines.append("</body></html>")
        return "\n".join(lines)

    def _render_category(
        app_config: AppConfig,
        directory: Directory,
        category: CategoryEntry,
    ) -> str:
        """Render a category page as simple HTML.

        Args:
            app_config: Application configuration.
            directory: The link directory (unused here but kept for symmetry).
            category: The category to render.

        Returns:
            HTML string for the category page.
        """
        _ = directory  # kept for future use
        lines = [
            "<!DOCTYPE html>",
            "<html><head>",
            f"<title>{app_config.site_title} — {category.name}</title>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "</head><body>",
            f"<h1>{app_config.site_title}</h1>",
            f'<nav><a href="/">Home</a> &gt; {category.name}</nav>',
            f"<h2>{category.name}</h2>",
        ]
        if category.description:
            lines.append(f'<p class="description">{category.description}</p>')
        lines.append('<ul class="directory">')
        for link in category.entries:
            desc = (
                f' <span class="description">{link.description}</span>'
                if link.description
                else ""
            )
            lines.append(
                f'<li class="link"><a href="{link.url}">{link.name}</a>{desc}</li>'
            )
        lines.append("</ul>")
        lines.append("</body></html>")
        return "\n".join(lines)
