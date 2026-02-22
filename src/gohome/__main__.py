"""CLI entry point for the GoHome application.

Run with ``python -m gohome [config_dir]`` to start the development
server.  The optional *config_dir* argument defaults to the current
working directory.
"""

from __future__ import annotations

import sys

from gohome import create_app


def main() -> None:
    """Parse CLI arguments and start the Flask development server.

    The first positional argument is the configuration directory.  Host and
    port default to the values in ``config.yml``; environment variable
    overrides are handled in Phase 8.
    """
    config_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    app = create_app(config_dir)

    app_config = app.config["GOHOME_APP_CONFIG"]
    host = app_config.host
    port = app_config.port

    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
