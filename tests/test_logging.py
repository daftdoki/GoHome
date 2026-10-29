"""Tests for logging setup in create_app."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from gohome import create_app

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_DIRECTORY = "directory:\n  - name: A\n    url: https://a.com\n"


@pytest.fixture(autouse=True)
def _isolated_logging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """Write a minimal directory, clear the env override, restore the root level.

    ``create_app`` sets the root logger's level, so each test restores it
    afterwards to keep the level from leaking into other tests.
    """
    monkeypatch.delenv("GOHOME_LOG_LEVEL", raising=False)
    (tmp_path / "directory.yml").write_text(_DIRECTORY, encoding="utf-8")
    root = logging.getLogger()
    previous = root.level
    yield
    root.setLevel(previous)


class TestLogging:
    """Verify log level handling and early config logging."""

    def test_invalid_log_level_warns_and_falls_back(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unknown log_level warns with the bad value and uses INFO."""
        (tmp_path / "config.yml").write_text("log_level: loud\n", encoding="utf-8")
        create_app(str(tmp_path))
        assert "loud" in caplog.text
        assert any(r.levelname == "WARNING" for r in caplog.records)
        assert logging.getLogger().level == logging.INFO

    def test_valid_log_level_applied(self, tmp_path: Path) -> None:
        """A valid log_level is applied to the root logger."""
        (tmp_path / "config.yml").write_text("log_level: error\n", encoding="utf-8")
        create_app(str(tmp_path))
        assert logging.getLogger().level == logging.ERROR

    def test_config_warnings_emitted_during_load(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warnings from config loading are emitted by create_app."""
        (tmp_path / "config.yml").write_text("bogus_key: 1\n", encoding="utf-8")
        create_app(str(tmp_path))
        assert "Unknown config key" in caplog.text
