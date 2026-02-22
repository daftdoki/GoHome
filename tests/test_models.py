"""Tests for the data model classes."""

from types import MappingProxyType

import pytest

from gohome.models import AppConfig, CategoryEntry, Directory, LinkEntry


class TestLinkEntry:
    """Verify LinkEntry construction and immutability."""

    def test_construction(self) -> None:
        """A LinkEntry stores all provided fields."""
        link = LinkEntry(name="Google", slug="google", url="https://google.com")
        assert link.name == "Google"
        assert link.slug == "google"
        assert link.url == "https://google.com"
        assert link.description == ""

    def test_frozen(self) -> None:
        """LinkEntry instances are immutable."""
        link = LinkEntry(
            name="Google",
            slug="google",
            url="https://google.com",
            description="A search engine",
        )
        with pytest.raises(AttributeError):
            link.name = "Yahoo"  # type: ignore[misc]


class TestCategoryEntry:
    """Verify CategoryEntry construction and immutability."""

    def test_construction_with_entries(self) -> None:
        """A CategoryEntry holds a tuple of LinkEntry items."""
        child = LinkEntry(name="Netflix", slug="netflix", url="https://netflix.com")
        cat = CategoryEntry(name="Streaming", slug="streaming", entries=(child,))
        assert len(cat.entries) == 1
        assert cat.entries[0] is child

    def test_frozen(self) -> None:
        """CategoryEntry instances are immutable."""
        cat = CategoryEntry(name="Streaming", slug="streaming")
        with pytest.raises(AttributeError):
            cat.name = "Media"  # type: ignore[misc]


class TestDirectory:
    """Verify Directory construction and slug_map lookup."""

    def test_slug_map_lookup(self) -> None:
        """Items are retrievable by slug from slug_map."""
        link = LinkEntry(name="Kagi", slug="kagi", url="https://kagi.com")
        directory = Directory(
            items=(link,),
            slug_map=MappingProxyType({"kagi": link}),
        )
        assert directory.slug_map["kagi"] is link

    def test_slug_map_is_readonly(self) -> None:
        """slug_map cannot be mutated."""
        directory = Directory(items=(), slug_map=MappingProxyType({}))
        with pytest.raises(TypeError):
            directory.slug_map["new"] = LinkEntry(  # type: ignore[index]
                name="X", slug="x", url="https://x.com"
            )

    def test_nested_links_in_slug_map(self) -> None:
        """Links inside categories can appear in the top-level slug_map."""
        child = LinkEntry(name="Netflix", slug="netflix", url="https://netflix.com")
        cat = CategoryEntry(name="Streaming", slug="streaming", entries=(child,))
        slug_map = MappingProxyType({"streaming": cat, "netflix": child})
        directory = Directory(items=(cat,), slug_map=slug_map)
        assert directory.slug_map["netflix"] is child
        assert directory.slug_map["streaming"] is cat


class TestAppConfig:
    """Verify AppConfig defaults."""

    def test_defaults(self) -> None:
        """All fields have sensible default values."""
        cfg = AppConfig()
        assert cfg.site_title == "GoHome"
        assert cfg.host == "0.0.0.0"
        assert cfg.port == 8080
        assert cfg.log_level == "info"
        assert cfg.default_theme == "default"
        assert cfg.config_dir == "."
