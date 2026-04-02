"""Shared pytest fixtures for the GoHome test suite."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from gohome import create_app

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient

_DIRECTORY_YML = """\
directory:
  - name: Google
    url: https://google.com
    description: A search engine
    aliases:
      - search
  - name: Streaming
    description: Video services
    entries:
      - name: Netflix
        url: https://netflix.com
        description: Streaming service
        aliases:
          - nf
      - name: YouTube
        url: https://youtube.com
  - name: Kagi
    url: https://kagi.com
"""


@pytest.fixture
def sample_config_dir(tmp_path: Path) -> Path:
    """Create a minimal config directory with a valid directory.yml."""
    (tmp_path / "directory.yml").write_text(_DIRECTORY_YML, encoding="utf-8")
    return tmp_path


@pytest.fixture
def app(sample_config_dir: Path) -> Flask:
    """Create a GoHome Flask app from the sample config directory."""
    application = create_app(str(sample_config_dir))
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    """Create a Flask test client."""
    return app.test_client()
