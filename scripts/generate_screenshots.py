"""Generate screenshots of all bundled GoHome themes for documentation.

This script starts a local GoHome server using the sample configuration,
then uses Playwright to capture screenshots of each bundled theme in the
specified mode. Screenshots are saved to ``docs/screenshots/`` for use
in README.md.

Usage::

    uv sync --extra screenshots
    uv run playwright install webkit
    uv run python scripts/generate_screenshots.py

The script must be run from the repository root.
"""

from __future__ import annotations

import socket
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, sync_playwright
from werkzeug.serving import BaseWSGIServer, make_server

# Repository root is two levels up from this script.
REPO_ROOT = Path(__file__).parent.parent
SAMPLE_CONFIG = str(REPO_ROOT / "sample_config")
OUTPUT_DIR = REPO_ROOT / "docs" / "screenshots"
PORT = 19876
BASE_URL = f"http://localhost:{PORT}"
VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 900


@dataclass(frozen=True)
class ScreenshotSpec:
    """Specification for a single screenshot to capture.

    Attributes:
        filename: Output PNG filename (relative to ``OUTPUT_DIR``).
        theme: Theme name to activate via the ``gohome_theme`` cookie.
        mode: Mode value to activate via the ``gohome_mode`` cookie.
            Use ``"light"`` or ``"dark"`` for an explicit mode, or ``""``
            to omit the cookie and let the browser's color scheme decide.
        description: Human-readable description used in log output.
    """

    filename: str
    theme: str
    mode: str
    description: str


SCREENSHOTS: list[ScreenshotSpec] = [
    ScreenshotSpec(
        "default-light.png", "default", "light", "Default theme, light mode"
    ),
    ScreenshotSpec("default-dark.png", "default", "dark", "Default theme, dark mode"),
    ScreenshotSpec(
        "retro-green-light.png",
        "retro-green",
        "light",
        "Retro green phosphor, light mode",
    ),
    ScreenshotSpec(
        "retro-green-dark.png", "retro-green", "dark", "Retro green phosphor, dark mode"
    ),
    ScreenshotSpec(
        "retro-amber-light.png",
        "retro-amber",
        "light",
        "Retro amber phosphor, light mode",
    ),
    ScreenshotSpec(
        "retro-amber-dark.png", "retro-amber", "dark", "Retro amber phosphor, dark mode"
    ),
    ScreenshotSpec(
        "retro-ansi-light.png", "retro-ansi", "light", "Retro ANSI terminal, light mode"
    ),
    ScreenshotSpec(
        "retro-ansi-dark.png", "retro-ansi", "dark", "Retro ANSI terminal, dark mode"
    ),
]


def start_server(config_dir: str, port: int) -> tuple[threading.Thread, BaseWSGIServer]:
    """Start a GoHome WSGI server in a background thread.

    Creates the Flask app from the given config directory and wraps it
    with Werkzeug's ``make_server`` so it can be shut down cleanly via
    ``server.shutdown()``.

    Args:
        config_dir: Path to the GoHome configuration directory.
        port: TCP port to bind on localhost.

    Returns:
        A ``(thread, server)`` tuple. The thread is already started and
        the server is accepting connections when this function returns.
    """
    # Import here so the script fails fast if gohome is not installed.
    from gohome import create_app  # type: ignore[import-untyped]

    app = create_app(config_dir)
    server: BaseWSGIServer = make_server("127.0.0.1", port, app, threaded=True)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread, server


def wait_for_server(port: int, timeout: float = 10.0) -> None:
    """Block until the server on the given port is accepting connections.

    Polls the TCP port up to ``timeout`` seconds. Exits with an error
    message if the server does not become ready in time.

    Args:
        port: TCP port to poll.
        timeout: Maximum number of seconds to wait before giving up.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    print(
        f"ERROR: Server on port {port} did not start within {timeout:.0f}s.",
        file=sys.stderr,
    )
    sys.exit(1)


def capture_screenshot(
    page: Page,
    base_url: str,
    spec: ScreenshotSpec,
    output_dir: Path,
) -> None:
    """Navigate to the root page and capture a screenshot for one spec.

    Sets ``gohome_theme`` and (optionally) ``gohome_mode`` cookies on
    the browser context before navigating so the server renders the
    correct theme and mode without any JavaScript interaction.

    Args:
        page: Playwright ``Page`` object to use for navigation.
        base_url: Base URL of the running GoHome server.
        spec: Screenshot specification describing theme, mode, and filename.
        output_dir: Directory where the PNG file will be written.
    """
    print(f"  Capturing {spec.filename} — {spec.description}")

    cookies = [{"name": "gohome_theme", "value": spec.theme, "url": base_url}]
    if spec.mode:
        cookies.append({"name": "gohome_mode", "value": spec.mode, "url": base_url})

    page.context.clear_cookies()
    page.context.add_cookies(cookies)
    page.goto(base_url)
    page.wait_for_load_state("networkidle")

    output_path = output_dir / spec.filename
    page.screenshot(path=str(output_path))


def main() -> None:
    """Entry point: start server, capture all screenshots, shut down.

    Starts a GoHome server against the sample config, iterates over
    ``SCREENSHOTS``, captures each one with Playwright, then shuts the
    server down regardless of success or failure.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Starting GoHome server on port {PORT}…")
    _thread, server = start_server(SAMPLE_CONFIG, PORT)
    try:
        wait_for_server(PORT)
        print("Server ready.")

        with sync_playwright() as pw:
            browser = pw.webkit.launch()
            context = browser.new_context(
                viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
            )
            page = context.new_page()

            print(f"Capturing {len(SCREENSHOTS)} screenshots into {OUTPUT_DIR}/")
            for spec in SCREENSHOTS:
                capture_screenshot(page, BASE_URL, spec, OUTPUT_DIR)

            browser.close()

        print("Done.")
    finally:
        print("Shutting down server…")
        server.shutdown()


if __name__ == "__main__":
    main()
