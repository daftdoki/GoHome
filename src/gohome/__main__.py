"""CLI entry point for the GoHome application.

Run with ``python -m gohome [config_dir]`` to start the development
server.  The optional *config_dir* argument defaults to the current
working directory.

Host and port resolution priority:
    ``GOHOME_HOST`` / ``GOHOME_PORT`` env vars  >  ``config.yml``  >  defaults
"""

from __future__ import annotations

import os
import sys

from gohome import create_app


def main() -> None:
    """Parse CLI arguments and start the Flask development server.

    The first positional argument is the configuration directory.  Environment
    variables ``GOHOME_HOST`` and ``GOHOME_PORT`` take precedence over
    ``config.yml`` values, which in turn override the built-in defaults
    (``0.0.0.0`` / ``8080``).
    """
    config_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    app = create_app(config_dir)

    app_config = app.config["GOHOME_APP_CONFIG"]

    host = os.environ.get("GOHOME_HOST", app_config.host)
    port = int(os.environ.get("GOHOME_PORT", str(app_config.port)))

    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
