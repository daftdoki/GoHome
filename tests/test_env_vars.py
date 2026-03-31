"""Tests for environment variable overrides of configuration settings.

Verifies that ``GOHOME_*`` environment variables take precedence over
``config.yml`` values and built-in defaults.  The overrides are applied
during config loading in :func:`gohome.config.load_app_config`.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from gohome import create_app
from gohome.models import AppConfig


def _write_yaml(tmp_path: Path, filename: str, content: str) -> None:
    """Write a YAML string to a file in *tmp_path*."""
    (tmp_path / filename).write_text(content, encoding="utf-8")


_MINIMAL_DIR = "directory:\n  - name: X\n    url: https://x.com\n"


class TestEnvVarOverrides:
    """Verify GOHOME_* env var priority over config.yml and defaults."""

    @pytest.mark.parametrize(
        ("yaml_content", "env_var", "env_value", "attr", "expected"),
        [
            (
                'host: "127.0.0.1"\n',
                "GOHOME_HOST",
                "192.168.1.1",
                "host",
                "192.168.1.1",
            ),
            ("port: 9090\n", "GOHOME_PORT", "3000", "port", 3000),
            (
                'site_title: "FromFile"\n',
                "GOHOME_SITE_TITLE",
                "FromEnv",
                "site_title",
                "FromEnv",
            ),
            (
                'log_level: "warning"\n',
                "GOHOME_LOG_LEVEL",
                "debug",
                "log_level",
                "debug",
            ),
            (
                'default_theme: "retro-green"\n',
                "GOHOME_DEFAULT_THEME",
                "retro-amber",
                "default_theme",
                "retro-amber",
            ),
        ],
        ids=["host", "port", "site_title", "log_level", "default_theme"],
    )
    def test_env_var_overrides_config(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        yaml_content: str,
        env_var: str,
        env_value: str,
        attr: str,
        expected: str | int,
    ) -> None:
        """Each GOHOME_* env var takes precedence over its config.yml value."""
        _write_yaml(tmp_path, "config.yml", yaml_content)
        _write_yaml(tmp_path, "directory.yml", _MINIMAL_DIR)
        monkeypatch.setenv(env_var, env_value)
        app = create_app(str(tmp_path))

        assert getattr(app.config["GOHOME_APP_CONFIG"], attr) == expected

    def test_config_used_without_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without env vars, config.yml values are used."""
        for var in (
            "GOHOME_HOST",
            "GOHOME_PORT",
            "GOHOME_SITE_TITLE",
            "GOHOME_LOG_LEVEL",
            "GOHOME_DEFAULT_THEME",
        ):
            monkeypatch.delenv(var, raising=False)
        _write_yaml(tmp_path, "config.yml", 'host: "10.0.0.1"\nport: 5000\n')
        _write_yaml(tmp_path, "directory.yml", _MINIMAL_DIR)
        app = create_app(str(tmp_path))

        cfg = app.config["GOHOME_APP_CONFIG"]
        assert cfg.host == "10.0.0.1"
        assert cfg.port == 5000

    def test_defaults_without_config_or_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without env vars or config.yml, built-in defaults are used."""
        for var in (
            "GOHOME_HOST",
            "GOHOME_PORT",
            "GOHOME_SITE_TITLE",
            "GOHOME_LOG_LEVEL",
            "GOHOME_DEFAULT_THEME",
        ):
            monkeypatch.delenv(var, raising=False)
        _write_yaml(tmp_path, "directory.yml", _MINIMAL_DIR)
        app = create_app(str(tmp_path))

        cfg = app.config["GOHOME_APP_CONFIG"]
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8080
        assert cfg.site_title == "GoHome"
        assert cfg.log_level == "info"
        assert cfg.default_theme == "default"

    def test_env_vars_work_without_config_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env vars apply even when config.yml does not exist."""
        _write_yaml(tmp_path, "directory.yml", _MINIMAL_DIR)
        monkeypatch.setenv("GOHOME_SITE_TITLE", "NoFile")
        monkeypatch.setenv("GOHOME_HOST", "10.0.0.5")
        monkeypatch.setenv("GOHOME_PORT", "9999")
        monkeypatch.setenv("GOHOME_LOG_LEVEL", "error")
        monkeypatch.setenv("GOHOME_DEFAULT_THEME", "retro-ansi")
        app = create_app(str(tmp_path))

        cfg = app.config["GOHOME_APP_CONFIG"]
        assert cfg.site_title == "NoFile"
        assert cfg.host == "10.0.0.5"
        assert cfg.port == 9999
        assert cfg.log_level == "error"
        assert cfg.default_theme == "retro-ansi"

    def test_invalid_port_env_var_exits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A non-integer GOHOME_PORT causes a clean exit."""
        _write_yaml(tmp_path, "directory.yml", _MINIMAL_DIR)
        monkeypatch.setenv("GOHOME_PORT", "not-a-number")
        with pytest.raises(SystemExit):
            create_app(str(tmp_path))

    def test_main_calls_run_with_resolved_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The main() function passes resolved config values to app.run()."""
        _write_yaml(tmp_path, "directory.yml", _MINIMAL_DIR)
        monkeypatch.setenv("GOHOME_HOST", "1.2.3.4")
        monkeypatch.setenv("GOHOME_PORT", "4444")
        monkeypatch.setattr("sys.argv", ["gohome", str(tmp_path)])

        with patch("gohome.__main__.create_app") as mock_create:
            mock_app = mock_create.return_value
            mock_app.config = {
                "GOHOME_APP_CONFIG": AppConfig(host="1.2.3.4", port=4444)
            }
            from gohome.__main__ import main

            main()
            mock_app.run.assert_called_once_with(host="1.2.3.4", port=4444)
