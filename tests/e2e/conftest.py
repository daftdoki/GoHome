"""Pytest configuration and fixtures for GoHome E2E browser tests.

Provides a live WSGI server running the GoHome application with the
sample configuration directory, and integrates with pytest-playwright
for browser-based testing.  The ``base_url`` fixture lets tests call
``page.goto("/")`` with relative paths that resolve to the live server.
"""

from __future__ import annotations

import threading
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Playwright
from werkzeug.serving import make_server

from gohome import create_app

if TYPE_CHECKING:
    from playwright.sync_api import APIRequestContext
    from werkzeug.serving import BaseWSGIServer

SAMPLE_CONFIG_DIR = str(Path(__file__).resolve().parent.parent.parent / "sample_config")


def pytest_configure(config: pytest.Config) -> None:
    """Default to WebKit when no ``--browser`` flag is explicitly provided.

    WebKit is lighter weight than Chromium and sufficient for verifying
    cookie behaviour, page reloads, and DOM rendering.

    Args:
        config: The pytest configuration object.
    """
    if not config.getoption("--browser", default=None):
        config.option.browser = ["webkit"]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply the ``e2e`` marker to every test in this directory.

    This allows running or excluding E2E tests with ``-m e2e`` /
    ``-m 'not e2e'`` without decorating each test individually.

    Args:
        items: The collected test items to potentially modify.
    """
    e2e_dir = Path(__file__).parent
    e2e_marker = pytest.mark.e2e
    for item in items:
        if Path(item.fspath).is_relative_to(e2e_dir):
            item.add_marker(e2e_marker)


@pytest.fixture(scope="session")
def live_server() -> Generator[BaseWSGIServer, None, None]:
    """Start a GoHome WSGI server in a daemon thread for the test session.

    Uses port ``0`` so the OS assigns a free port, avoiding conflicts
    with other services.  The server is shut down after all E2E tests
    complete.

    Yields:
        The running ``BaseWSGIServer`` instance.
    """
    app = create_app(SAMPLE_CONFIG_DIR)
    server: BaseWSGIServer = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(
        target=server.serve_forever, daemon=True, name="e2e-server"
    )
    thread.start()
    yield server
    server.shutdown()


@pytest.fixture(scope="session")
def base_url(live_server: BaseWSGIServer) -> str:
    """Provide the base URL of the live server for pytest-playwright.

    pytest-playwright uses a fixture named ``base_url`` to resolve
    relative URLs passed to ``page.goto()``.  This fixture overrides
    the default (``None``) with the actual live server address.

    Args:
        live_server: The running WSGI server fixture.

    Returns:
        The base URL string, e.g. ``"http://127.0.0.1:54321"``.
    """
    host, port = live_server.server_address
    return f"http://{host}:{port}"


@pytest.fixture(scope="session")
def api_request_context(
    playwright: Playwright, base_url: str
) -> Generator[APIRequestContext, None, None]:
    """Provide a Playwright API request context for direct HTTP assertions.

    Unlike ``page.goto()``, the API request context does not follow
    redirects by default, making it ideal for verifying 302 responses
    without attempting to resolve external hostnames.

    Args:
        playwright: The Playwright instance provided by pytest-playwright.
        base_url: The base URL of the live server.

    Yields:
        An ``APIRequestContext`` bound to the live server.
    """
    context = playwright.request.new_context(base_url=base_url)
    yield context
    context.dispose()
