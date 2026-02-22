"""Tests for the sample configuration directory."""

from __future__ import annotations

from pathlib import Path

from gohome.config import load_app_config, load_directory


SAMPLE_CONFIG_DIR = str(Path(__file__).resolve().parent.parent / "sample_config")


class TestSampleConfig:
    """Verify the sample configuration loads without errors."""

    def test_loads_app_config(self) -> None:
        """sample_config/config.yml loads without errors."""
        cfg = load_app_config(SAMPLE_CONFIG_DIR)
        assert cfg.site_title == "GoHome"

    def test_loads_directory(self) -> None:
        """sample_config/directory.yml loads without errors."""
        directory = load_directory(SAMPLE_CONFIG_DIR)
        assert len(directory.items) > 0

    def test_expected_item_count(self) -> None:
        """The sample directory has the expected number of top-level items."""
        directory = load_directory(SAMPLE_CONFIG_DIR)
        # 2 links (Google, Wikipedia) + 1 category (Streaming) + 1 link (Kagi) + 1 category (Development)
        assert len(directory.items) == 5

    def test_all_slugs_unique(self) -> None:
        """All slugs in the sample directory are unique."""
        directory = load_directory(SAMPLE_CONFIG_DIR)
        slugs = list(directory.slug_map.keys())
        assert len(slugs) == len(set(slugs))
