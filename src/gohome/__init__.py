"""GoHome — a self-hosted link directory and redirector service.

GoHome is a simple, themeable web application that serves a directory of
links and provides short-URL redirects.  Configure it with YAML files,
deploy it with Docker, and access your links at ``go/link-name``.

Use :func:`create_app` to build a configured Flask application instance.
"""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask

from gohome.config import load_app_config, load_directory
from gohome.models import AppConfig, CategoryEntry, Directory
from gohome.routes import register_routes
from gohome.themes import BUNDLED_THEMES, discover_themes


def create_app(config_dir: str = ".") -> Flask:
    """Build and configure the GoHome Flask application.

    Loads configuration from *config_dir*, validates the directory, sets up
    logging, discovers themes, registers a custom Jinja2 ``category`` test,
    and registers all routes.

    Args:
        config_dir: Path to the directory containing ``config.yml`` and
            ``directory.yml``.

    Returns:
        A fully configured Flask application ready to serve requests.
    """
    app_config: AppConfig = load_app_config(config_dir)
    directory: Directory = load_directory(config_dir)
    themes: list[str] = discover_themes(config_dir)

    # Configure logging
    log_level = getattr(logging, app_config.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    app = Flask(__name__)

    # Store config, directory, themes, and bundled theme set for route access
    app.config["GOHOME_APP_CONFIG"] = app_config
    app.config["GOHOME_DIRECTORY"] = directory
    app.config["GOHOME_THEMES"] = themes
    app.config["GOHOME_BUNDLED_THEMES"] = frozenset(BUNDLED_THEMES)

    # Register custom Jinja2 test: {% if item is category %}
    def _is_category(value: Any) -> bool:
        """Jinja2 test that checks if a value is a CategoryEntry."""
        return isinstance(value, CategoryEntry)

    app.jinja_env.tests["category"] = _is_category

    register_routes(app)

    return app
