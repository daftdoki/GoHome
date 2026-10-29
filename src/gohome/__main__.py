"""CLI entry point for the GoHome application.

Run with ``python -m gohome [config_dir]`` to start the waitress
production server.  The optional *config_dir* argument defaults to the
current working directory.  Waitress logs the address it serves on at
``info`` level.

Configuration resolution priority (highest wins):
    ``GOHOME_*`` env vars  >  ``config.yml``  >  built-in defaults

Environment variable overrides are applied during config loading — see
:func:`gohome.config.load_app_config` for details.
"""

from __future__ import annotations

import sys

import waitress

from gohome import create_app


def main() -> None:
    """Parse CLI arguments and serve the app with waitress.

    The first positional argument is the configuration directory.  All
    configuration values (including host and port) are resolved by
    :func:`~gohome.config.load_app_config`, which applies environment
    variable overrides before returning.  Blocks until the server is stopped.
    """
    config_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    app = create_app(config_dir)

    app_config = app.config["GOHOME_APP_CONFIG"]
    waitress.serve(app, host=app_config.host, port=app_config.port)


if __name__ == "__main__":
    main()
