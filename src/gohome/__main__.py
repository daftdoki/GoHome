"""CLI entry point for the GoHome application.

Run with ``python -m gohome [config_dir]`` to start the development
server.  The optional *config_dir* argument defaults to the current
working directory.

Configuration resolution priority (highest wins):
    ``GOHOME_*`` env vars  >  ``config.yml``  >  built-in defaults

Environment variable overrides are applied during config loading — see
:func:`gohome.config.load_app_config` for details.
"""

from __future__ import annotations

import sys

from gohome import create_app


def main() -> None:
    """Parse CLI arguments and start the Flask development server.

    The first positional argument is the configuration directory.  All
    configuration values (including host and port) are resolved by
    :func:`~gohome.config.load_app_config`, which applies environment
    variable overrides before returning.
    """
    config_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    app = create_app(config_dir)

    app_config = app.config["GOHOME_APP_CONFIG"]
    app.run(host=app_config.host, port=app_config.port)


if __name__ == "__main__":
    main()
