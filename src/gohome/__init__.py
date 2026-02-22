"""GoHome — a self-hosted link directory and redirector service.

GoHome is a simple, themeable web application that serves a directory of
links and provides short-URL redirects.  Configure it with YAML files,
deploy it with Docker, and access your links at ``go/link-name``.

Use :func:`create_app` to build a configured Flask application instance.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from flask import Flask

from gohome.config import load_app_config, load_directory
from gohome.routes import register_routes

if TYPE_CHECKING:
    from gohome.models import AppConfig, Directory


def create_app(config_dir: str = ".") -> Flask:
    """Build and configure the GoHome Flask application.

    Loads configuration from *config_dir*, validates the directory, sets up
    logging, and registers all routes.

    Args:
        config_dir: Path to the directory containing ``config.yml`` and
            ``directory.yml``.

    Returns:
        A fully configured Flask application ready to serve requests.
    """
    app_config: AppConfig = load_app_config(config_dir)
    directory: Directory = load_directory(config_dir)

    # Configure logging
    log_level = getattr(logging, app_config.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    app = Flask(__name__)

    # Store config and directory on the app for access in routes
    app.config["GOHOME_APP_CONFIG"] = app_config
    app.config["GOHOME_DIRECTORY"] = directory

    register_routes(app)

    return app
