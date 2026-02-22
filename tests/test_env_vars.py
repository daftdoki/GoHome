"""Tests for environment variable overrides of host and port."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from gohome import create_app


def _write_yaml(tmp_path: Path, filename: str, content: str) -> None:
    """Write a YAML string to a file in *tmp_path*."""
    (tmp_path / filename).write_text(content, encoding="utf-8")


class TestEnvVarOverrides:
    """Verify GOHOME_HOST and GOHOME_PORT env var priority."""

    def test_env_host_overrides_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GOHOME_HOST env var takes precedence over config.yml."""
        _write_yaml(tmp_path, "config.yml", 'host: "127.0.0.1"\n')
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        monkeypatch.setenv("GOHOME_HOST", "192.168.1.1")
        app = create_app(str(tmp_path))

        # Simulate what __main__.py does
        host = os.environ.get("GOHOME_HOST", app.config["GOHOME_APP_CONFIG"].host)
        assert host == "192.168.1.1"

    def test_env_port_overrides_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GOHOME_PORT env var takes precedence over config.yml."""
        _write_yaml(tmp_path, "config.yml", "port: 9090\n")
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        monkeypatch.setenv("GOHOME_PORT", "3000")
        app = create_app(str(tmp_path))

        port = int(
            os.environ.get("GOHOME_PORT", str(app.config["GOHOME_APP_CONFIG"].port))
        )
        assert port == 3000

    def test_config_used_without_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without env vars, config.yml values are used."""
        monkeypatch.delenv("GOHOME_HOST", raising=False)
        monkeypatch.delenv("GOHOME_PORT", raising=False)
        _write_yaml(tmp_path, "config.yml", 'host: "10.0.0.1"\nport: 5000\n')
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        app = create_app(str(tmp_path))

        host = os.environ.get("GOHOME_HOST", app.config["GOHOME_APP_CONFIG"].host)
        port = int(
            os.environ.get("GOHOME_PORT", str(app.config["GOHOME_APP_CONFIG"].port))
        )
        assert host == "10.0.0.1"
        assert port == 5000

    def test_defaults_without_config_or_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Without env vars or config.yml, built-in defaults are used."""
        monkeypatch.delenv("GOHOME_HOST", raising=False)
        monkeypatch.delenv("GOHOME_PORT", raising=False)
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        app = create_app(str(tmp_path))

        host = os.environ.get("GOHOME_HOST", app.config["GOHOME_APP_CONFIG"].host)
        port = int(
            os.environ.get("GOHOME_PORT", str(app.config["GOHOME_APP_CONFIG"].port))
        )
        assert host == "0.0.0.0"
        assert port == 8080

    def test_main_calls_run_with_env_vars(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The main() function passes env var values to app.run()."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: X\n    url: https://x.com\n",
        )
        monkeypatch.setenv("GOHOME_HOST", "1.2.3.4")
        monkeypatch.setenv("GOHOME_PORT", "4444")
        monkeypatch.setattr("sys.argv", ["gohome", str(tmp_path)])

        with patch("gohome.__main__.create_app") as mock_create:
            mock_app = mock_create.return_value
            mock_app.config = {
                "GOHOME_APP_CONFIG": type(
                    "Cfg", (), {"host": "0.0.0.0", "port": 8080}
                )()
            }
            from gohome.__main__ import main

            main()
            mock_app.run.assert_called_once_with(host="1.2.3.4", port=4444)
