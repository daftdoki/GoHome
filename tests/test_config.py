"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest

from gohome.config import load_app_config, load_directory
from gohome.models import CategoryEntry, LinkEntry


def _write_yaml(tmp_path: Path, filename: str, content: str) -> None:
    """Write a YAML string to a file in *tmp_path*."""
    (tmp_path / filename).write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# load_app_config
# ---------------------------------------------------------------------------


class TestLoadAppConfig:
    """Verify config.yml loading and defaults."""

    def test_missing_config_uses_defaults(self, tmp_path: Path) -> None:
        """When config.yml is absent, all defaults apply."""
        cfg = load_app_config(str(tmp_path))
        assert cfg.site_title == "GoHome"
        assert cfg.port == 8080

    def test_custom_values(self, tmp_path: Path) -> None:
        """Explicit values in config.yml override defaults."""
        _write_yaml(
            tmp_path,
            "config.yml",
            'site_title: "MyLinks"\nport: 9090\n',
        )
        cfg = load_app_config(str(tmp_path))
        assert cfg.site_title == "MyLinks"
        assert cfg.port == 9090

    def test_unknown_keys_warns(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Unknown keys emit a warning but do not prevent startup."""
        _write_yaml(tmp_path, "config.yml", "bogus_key: true\n")
        cfg = load_app_config(str(tmp_path))
        assert cfg.site_title == "GoHome"
        assert "Unknown config key" in caplog.text

    def test_malformed_yaml_exits(self, tmp_path: Path) -> None:
        """Unparseable YAML causes sys.exit(1)."""
        (tmp_path / "config.yml").write_text(":\n  - :\n  bad: [", encoding="utf-8")
        with pytest.raises(SystemExit):
            load_app_config(str(tmp_path))

    def test_empty_config_uses_defaults(self, tmp_path: Path) -> None:
        """An empty config.yml file uses all defaults."""
        _write_yaml(tmp_path, "config.yml", "")
        cfg = load_app_config(str(tmp_path))
        assert cfg.site_title == "GoHome"


# ---------------------------------------------------------------------------
# load_directory — happy paths
# ---------------------------------------------------------------------------


class TestLoadDirectoryValid:
    """Verify valid directory.yml files load correctly."""

    def test_single_link(self, tmp_path: Path) -> None:
        """A directory with one link loads successfully."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: Google\n    url: https://google.com\n",
        )
        directory = load_directory(str(tmp_path))
        assert len(directory.items) == 1
        assert isinstance(directory.items[0], LinkEntry)
        assert directory.slug_map["google"].name == "Google"

    def test_category_with_links(self, tmp_path: Path) -> None:
        """A category with child links populates both category and link slugs."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Streaming\n"
                "    entries:\n"
                "      - name: Netflix\n"
                "        url: https://netflix.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        assert isinstance(directory.slug_map["streaming"], CategoryEntry)
        assert isinstance(directory.slug_map["netflix"], LinkEntry)

    def test_link_with_description(self, tmp_path: Path) -> None:
        """Descriptions are captured on link entries."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Kagi\n"
                "    url: https://kagi.com\n"
                "    description: A search engine\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        link = directory.slug_map["kagi"]
        assert isinstance(link, LinkEntry)
        assert link.description == "A search engine"

    def test_category_description(self, tmp_path: Path) -> None:
        """Descriptions are captured on category entries."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Media\n"
                "    description: Streaming services\n"
                "    entries:\n"
                "      - name: Netflix\n"
                "        url: https://netflix.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        cat = directory.slug_map["media"]
        assert isinstance(cat, CategoryEntry)
        assert cat.description == "Streaming services"

    def test_url_and_entries_treated_as_category(self, tmp_path: Path) -> None:
        """When both url and entries are present, entry is treated as category."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Mixed\n"
                "    url: https://ignored.com\n"
                "    entries:\n"
                "      - name: Child\n"
                "        url: https://child.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        assert isinstance(directory.slug_map["mixed"], CategoryEntry)

    def test_link_with_aliases(self, tmp_path: Path) -> None:
        """Aliases are stored on the entry and registered in slug_map."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: NAS\n"
                "    url: https://nas.local\n"
                "    aliases:\n"
                "      - qnap\n"
                "      - files\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        item = directory.slug_map["nas"]
        assert isinstance(item, LinkEntry)
        assert item.aliases == ("qnap", "files")
        assert directory.slug_map["qnap"] is item
        assert directory.slug_map["files"] is item

    def test_category_with_aliases(self, tmp_path: Path) -> None:
        """Category aliases are stored and registered in slug_map."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Streaming\n"
                "    aliases:\n"
                "      - media\n"
                "    entries:\n"
                "      - name: Netflix\n"
                "        url: https://netflix.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        cat = directory.slug_map["streaming"]
        assert isinstance(cat, CategoryEntry)
        assert cat.aliases == ("media",)
        assert directory.slug_map["media"] is cat

    def test_nested_link_with_aliases(self, tmp_path: Path) -> None:
        """Aliases on links inside categories are registered in slug_map."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Dev\n"
                "    entries:\n"
                "      - name: GitHub\n"
                "        url: https://github.com\n"
                "        aliases:\n"
                "          - gh\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        link = directory.slug_map["github"]
        assert isinstance(link, LinkEntry)
        assert link.aliases == ("gh",)
        assert directory.slug_map["gh"] is link

    def test_preserves_display_order(self, tmp_path: Path) -> None:
        """Items appear in the same order as the YAML file."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Bravo\n"
                "    url: https://b.com\n"
                "  - name: Alpha\n"
                "    url: https://a.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        assert directory.items[0].name == "Bravo"
        assert directory.items[1].name == "Alpha"


# ---------------------------------------------------------------------------
# load_directory — error paths
# ---------------------------------------------------------------------------


class TestLoadDirectoryErrors:
    """Verify that invalid directory configurations cause sys.exit(1)."""

    def test_missing_directory_yml(self, tmp_path: Path) -> None:
        """Missing directory.yml is a fatal error."""
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_malformed_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML syntax is a fatal error."""
        (tmp_path / "directory.yml").write_text("[bad: yaml:", encoding="utf-8")
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_missing_directory_key(self, tmp_path: Path) -> None:
        """YAML without a 'directory' key is a fatal error."""
        _write_yaml(tmp_path, "directory.yml", "links:\n  - name: X\n")
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_empty_directory_list(self, tmp_path: Path) -> None:
        """An empty directory list is a fatal error."""
        _write_yaml(tmp_path, "directory.yml", "directory: []\n")
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_missing_name_key(self, tmp_path: Path) -> None:
        """An entry without 'name' is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - url: https://example.com\n",
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_no_url_or_entries(self, tmp_path: Path) -> None:
        """An entry with neither 'url' nor 'entries' is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: Orphan\n",
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_empty_entries_list(self, tmp_path: Path) -> None:
        """A category with an empty entries list is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: Empty\n    entries: []\n",
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_empty_normalized_slug(self, tmp_path: Path) -> None:
        """A name that normalizes to empty string is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - name: '!!!'\n    url: https://example.com\n",
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_duplicate_slugs(self, tmp_path: Path) -> None:
        """Two entries that normalize to the same slug is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: My Link\n"
                "    url: https://a.com\n"
                "  - name: my-link\n"
                "    url: https://b.com\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_nested_category_skipped(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Nested categories are warned about and skipped."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Outer\n"
                "    entries:\n"
                "      - name: Inner\n"
                "        entries:\n"
                "          - name: Deep\n"
                "            url: https://deep.com\n"
            ),
        )
        directory = load_directory(str(tmp_path))
        assert "inner" not in directory.slug_map
        assert "Nested category" in caplog.text

    def test_non_mapping_entry(self, tmp_path: Path) -> None:
        """A non-mapping entry in the list is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            "directory:\n  - just a string\n",
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_alias_collides_with_name(self, tmp_path: Path) -> None:
        """An alias that collides with another entry's name is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Google\n"
                "    url: https://google.com\n"
                "    aliases:\n"
                "      - kagi\n"
                "  - name: Kagi\n"
                "    url: https://kagi.com\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_alias_collides_with_other_alias(self, tmp_path: Path) -> None:
        """Two entries with aliases that collide is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Google\n"
                "    url: https://google.com\n"
                "    aliases:\n"
                "      - search\n"
                "  - name: Kagi\n"
                "    url: https://kagi.com\n"
                "    aliases:\n"
                "      - search\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_alias_collides_with_own_name(self, tmp_path: Path) -> None:
        """An alias that normalizes to the same slug as its own name is fatal."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Google\n"
                "    url: https://google.com\n"
                "    aliases:\n"
                "      - google\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_alias_empty_slug(self, tmp_path: Path) -> None:
        """An alias that normalizes to an empty slug is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Google\n"
                "    url: https://google.com\n"
                "    aliases:\n"
                "      - '!!!'\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_alias_null_value(self, tmp_path: Path) -> None:
        """A null alias value is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Google\n"
                "    url: https://google.com\n"
                "    aliases:\n"
                "      - \n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_aliases_not_a_list(self, tmp_path: Path) -> None:
        """An aliases field that is not a list is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Google\n"
                "    url: https://google.com\n"
                "    aliases: not-a-list\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))

    def test_duplicate_slug_link_and_category(self, tmp_path: Path) -> None:
        """A link and category with the same slug is a fatal error."""
        _write_yaml(
            tmp_path,
            "directory.yml",
            (
                "directory:\n"
                "  - name: Streaming\n"
                "    url: https://streaming.com\n"
                "  - name: streaming\n"
                "    entries:\n"
                "      - name: Netflix\n"
                "        url: https://netflix.com\n"
            ),
        )
        with pytest.raises(SystemExit):
            load_directory(str(tmp_path))
